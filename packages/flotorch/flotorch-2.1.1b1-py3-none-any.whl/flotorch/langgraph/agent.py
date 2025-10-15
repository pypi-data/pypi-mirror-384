import os
import asyncio
import time
from typing import Any, Dict, List, Optional, cast

from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from flotorch.langchain.llm import FlotorchLangChainLLM
from flotorch.sdk.utils.http_utils import http_get
from flotorch.sdk.utils.logging_utils import log_error
from pydantic import  Field, create_model

def sanitize_agent_name(name: str) -> str:
    """Sanitize agent name to be a valid identifier."""
    
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = f"agent_{sanitized}"
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')

    if not sanitized:
        sanitized = "agent"
    
    return sanitized

def schema_to_pydantic_model(name: str, schema: Dict[str, Any]):
    """Create a minimal Pydantic model from a JSON schema dict.

    Only supports primitive field types used in simple structured outputs.
    """
    properties = schema.get("properties", {}) or {}
    fields: Dict[str, Any] = {}
    for prop, prop_schema in properties.items():
        field_type = str
        t = (prop_schema or {}).get("type")
        if t == "integer":
            field_type = int
        elif t == "number":
            field_type = float
        elif t == "boolean":
            field_type = bool
        description = (prop_schema or {}).get("description", "")
        fields[prop] = (field_type, Field(description=description))
    return create_model(name, **fields)

class FlotorchLangGraphAgent:
    """
    Flotorch LangGraph Agent manager following LangGraph standards.
    """

    def __init__(
            self,
            agent_name: str,
            custom_tools: Optional[List[BaseTool]] = None,
            base_url: Optional[str] = None,
            api_key: Optional[str] = None,
            store: Optional[Any] = None,
            checkpointer: Optional[Any] = None
    ):
        """
        Initialize the LangGraph agent with configuration loading.
        
        Args:
            agent_name: Name of the agent to load configuration for
            custom_tools: List of custom tools to add to the agent
            base_url: Flotorch API base URL
            api_key: Flotorch API key
            store: Pre-created memory store object (optional)
            checkpointer: Pre-created session checkpointer object (optional)
            
        Usage: 
            client = FlotorchLangGraphAgent(
                agent_name ="langgraph", 
                base_url = os.getenv("FLOTORCH_BASE_URL"), 
                api_key = os.getenv("FLOTORCH_API_KEY"),
                custom_tools = tools, 
                checkpointer=session, 
                store=memory
            )
            agent = client.get_agent()
        """
        self.agent_name = agent_name
        self.custom_tools = custom_tools or []
        self.base_url = base_url or os.environ.get("FLOTORCH_BASE_URL")
        self.api_key = api_key or os.environ.get("FLOTORCH_API_KEY")

        if not self.base_url or not self.api_key:
            raise ValueError("base_url and api_key are required")

        self.config = self._fetch_agent_config(agent_name)
        self._llm = self._build_llm_from_config(self.config)
        self._store = store
        self._checkpointer = checkpointer
        self._last_reload = time.time()
        self._agent_graph = asyncio.run(self._build_agent_graph_from_config(self.config))
        
    def _fetch_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Fetch agent configuration from Flotorch API."""
        if not self.base_url:
            raise ValueError("base_url is required")
        if not self.api_key:
            raise ValueError("api_key is required")
        url = f"{self.base_url.rstrip('/')}/v1/agents/{agent_name}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        return http_get(url, headers=headers)

    def _build_llm_from_config(self, config: Dict[str, Any]) -> FlotorchLangChainLLM:
        """Build LLM instance from agent configuration."""
        llm_config = config.get("llm", {})
        model_id = llm_config.get("callableName", "default-model")
        
        return FlotorchLangChainLLM(
            model_id=model_id,
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def _build_mcp_tools(self, tool_cfg) -> List[BaseTool]:
        """Build MCP tools using MultiServerMCPClient."""
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            cfg = tool_cfg.get("config", {})
            tool_name = tool_cfg.get("name", "mcp_tool")
            proxy_url = f"{self.base_url}/v1/mcps/{tool_cfg['name']}/proxy" 
            headers = dict(cfg.get("headers", {}))
            transport = cfg.get("transport", "streamable_http")

            if not proxy_url:
                return []

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            if transport == "HTTP_STREAMABLE":
                mcp_transport = "streamable_http"
            elif transport == "HTTP_SSE":
                mcp_transport = "sse"
            else:
                return []

            mcp_server_config = {
                tool_name: {
                    "url": proxy_url,
                    "transport": mcp_transport,
                }
            }

            if headers:
                mcp_server_config[tool_name]["headers"] = headers

            client = MultiServerMCPClient(mcp_server_config)
            
            if not hasattr(self, '_mcp_clients'):
                self._mcp_clients = {}
            self._mcp_clients[tool_name] = client
            
            try:
                tools = await client.get_tools(server_name=tool_name)
            except Exception as mcp_error:
                log_error("FlotorchLangGraphAgent._build_mcp_tools", f"MCP connection failed for '{tool_name}': {mcp_error}")
                return []
            
            filtered_tools = self._filter_mcp_tools(tools, tool_cfg)
            
            wrapped_tools = []
            for tool in filtered_tools:
                wrapped_tool = self._make_tool_sync(tool)
                wrapped_tools.append(wrapped_tool)
            
            return wrapped_tools

        except Exception as e:
            log_error("FlotorchLangGraphAgent._build_mcp_tools", str(e))
            return []

    def _filter_mcp_tools(self, all_tools: List[BaseTool], tool_cfg) -> List[BaseTool]:
        """Filter MCP tools based on configuration."""
        filtered_tools = []
        tool_name = sanitize_agent_name(tool_cfg.get("name"))
        
        if tool_name:
            for tool in all_tools:
                if getattr(tool, 'name', None) == tool_name:
                    filtered_tools.append(tool)
        else:
            filtered_tools = all_tools

        return filtered_tools

    def _make_tool_sync(self, tool):
        """Make async MCP tool compatible with LangGraph's sync execution."""
        from langchain_core.tools import StructuredTool
        import asyncio
        
        def sync_wrapper(**kwargs):
            try:
                result = asyncio.run(tool.ainvoke(kwargs))
                print(f"TOOL RESULT: {tool.name} returned: {result}")
                return result
            except Exception as e:
                print(f"TOOL ERROR: {tool.name} failed: {e}")
                raise
        
        return StructuredTool(
            name=tool.name,
            description=tool.description,
            args_schema=tool.args_schema,
            func=sync_wrapper
        )

    async def _build_tools(self, config) -> List[BaseTool]:
        """Build all tools including custom and MCP tools."""
        tools = []
        
        if self.custom_tools:
            tools.extend(self.custom_tools)

        for tool_cfg in config.get("tools", []):
            if tool_cfg.get("type") == "MCP":
                try:
                    mcp_tools = await self._build_mcp_tools(tool_cfg)
                    tools.extend(mcp_tools)
                except Exception as e:
                    log_error("FlotorchLangGraphAgent._build_tools", f"Failed to build MCP tool '{tool_cfg.get('name')}': {e}")

        return tools

    async def _build_agent_graph_from_config(self, config) -> Any:
        """Build LangGraph agent from configuration."""
        system_prompt = config.get("systemPrompt", "You are a helpful assistant.")
        goal = config.get("goal", "")
        if goal:
            system_prompt += f"\n\nYour goal: {goal}"

        tools = await self._build_tools(config)
        
        agent_kwargs = {
            "model": self._llm,
            "tools": tools,
            "prompt": system_prompt,
        }

        output_schema = config.get("outputSchema")
        if isinstance(output_schema, dict) and output_schema.get("properties"):
            try:
                agent_kwargs['response_format'] = output_schema
            except Exception as e:
                print(f"Warning: Failed to create structured output: {e}")

        if self._store:
            agent_kwargs['store'] = self._store
        if self._checkpointer:
            agent_kwargs['checkpointer'] = self._checkpointer

        agent = create_react_agent(**agent_kwargs)
        return agent

    def _get_synced_agent_graph(self) -> Any:
        """Get agent graph with configuration sync if enabled."""
        sync_enabled = self.config.get("syncEnabled", False)
        sync_interval = self.config.get("syncInterval", 60)
        now = time.time()
        
        if sync_enabled and now - self._last_reload > sync_interval:
            print("[Sync] Reload interval passed. Attempting to reload agent...")

            try:
                new_config = self._fetch_agent_config(self.agent_name)
                if new_config and new_config != self.config:
                    self.config = new_config
                    self._llm = self._build_llm_from_config(self.config)         
                    self._agent_graph = asyncio.run(self._build_agent_graph_from_config(self.config))
                    
                    print("[Sync] Agent successfully reloaded.")

            except Exception as e:
                log_error("FlotorchLangGraphAgent._get_synced_agent_graph", str(e))
            finally:
                self._last_reload = now
        
        return self._agent_graph

    def get_agent(self):
        """Get the agent graph proxy (following LangGraph standards)."""
        return cast(Any, AgentGraphProxy(self))

class AgentGraphProxy:
    """Proxy class for LangGraph agent operations (following LangGraph standards)."""

    def __init__(self, manager: FlotorchLangGraphAgent):
        self._manager = manager

    def __getattr__(self, item):
        """Delegate attribute access to the underlying agent graph."""
        return getattr(self._manager._get_synced_agent_graph(), item)

    def __setattr__(self, key, value):
        """Delegate attribute setting to the underlying agent graph."""
        if key == "_manager":
            object.__setattr__(self, key, value)
        else:
            setattr(self._manager._get_synced_agent_graph(), key, value)