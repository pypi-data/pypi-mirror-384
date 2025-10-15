"""Flotorch Strands Agent implementation following Strands documentation patterns."""

import os
import time
from typing import Any, Dict, List, Optional, Union, cast
from pydantic import Field, create_model
from flotorch.strands.llm import FlotorchStrandsModel      
from flotorch.sdk.utils.http_utils import http_get
from flotorch.sdk.utils.logging_utils import log_error
from strands.agent.agent import Agent
from strands.types.content import Messages
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client

def sanitize_agent_name(name: str) -> str:
    """
    Sanitize agent name to be a valid identifier.
    Replaces invalid characters with underscores and ensures it starts with a letter or underscore.
    """
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = f"agent_{sanitized}"
    
    sanitized = re.sub(r'_+', '_', sanitized)
    
    sanitized = sanitized.strip('_')
    
    if not sanitized:
        sanitized = "agent"
    
    return sanitized

def schema_to_pydantic_model(name: str, schema: Dict[str, Any]) -> type:
    """
    Dynamically create a Pydantic model from a JSON schema dict.
    If only one property, use its name (capitalized) plus 'Input' or 'Output' as the model name.
    Otherwise, use the provided name.
    """
    properties = schema.get("properties", {})
    if len(properties) == 1:
        prop_name = next(iter(properties))
        if name.lower().startswith("input"):
            model_name = f"{prop_name.capitalize()}Input"
        elif name.lower().startswith("output"):
            model_name = f"{prop_name.capitalize()}Output"
        else:
            model_name = f"{prop_name.capitalize()}Schema"
    else:
        model_name = name
    
    fields = {}
    for prop, prop_schema in properties.items():
        field_type = str  # Default to string
        if prop_schema.get("type") == "integer":
            field_type = int
        elif prop_schema.get("type") == "number":
            field_type = float
        elif prop_schema.get("type") == "boolean":
            field_type = bool
        description = prop_schema.get("description", "")
        fields[prop] = (field_type, Field(description=description))
    
    return create_model(model_name, **fields)

class FlotorchStrandsAgent:
    """
    Flotorch Strands Agent manager. Builds Strands Agent from config on demand.
    Supports on-demand config reload based on interval in config['sync'].

    Args:
        agent_name: Name of the agent to load configuration for
        custom_tools: List of custom tools to add to the agent
        base_url: Flotorch API base URL. Defaults to FLOTORCH_BASE_URL env var
        api_key: Flotorch API key. Defaults to FLOTORCH_API_KEY env var
        session_manager: Optional session manager for state persistence
     
    Usage:
        agent_manager = FlotorchStrandsAgent("agent_name", custom_tools=[my_tool])
        agent = agent_manager.get_agent()
        result = agent("Hello, how can I help you?")
    """

    def __init__(
        self,
        agent_name: str,
        custom_tools: Optional[List[Any]] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        session_manager: Optional[Any] = None,
    ):
        self.agent_name = agent_name
        self.custom_tools = custom_tools or []
        self.session_manager = session_manager
        self.base_url = base_url or os.environ.get("FLOTORCH_BASE_URL")
        self.api_key = api_key or os.environ.get("FLOTORCH_API_KEY")
        
        if not self.base_url or not self.api_key:
            raise ValueError("base_url and api_key are required")

        self.config = self._fetch_agent_config(agent_name)
        self._agent = self._build_agent_from_config(self.config)
        self._last_reload = time.time()

    def _fetch_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Fetch agent configuration from Flotorch API."""
        if not self.base_url:
            raise ValueError("base_url is required to fetch agent configuration")
        
        if not self.api_key:
            raise ValueError("api_key is required to fetch agent configuration")

        url = f"{self.base_url.rstrip('/')}/v1/agents/{agent_name}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = http_get(url, headers=headers)
            return response
        except Exception as e:
            log_error("FlotorchStrandsAgent._fetch_agent_config", e)
            raise

    def _build_tools(self, config: Dict[str, Any]) -> List[Any]:
        """Build only custom tools (MCP tools loaded at runtime following Strands pattern)."""
        tools = []

        if self.custom_tools:
            tools.extend(self.custom_tools)

        self._mcp_configs = []
        for tool_cfg in config.get("tools", []):
            if tool_cfg.get("type") == "MCP":
                self._mcp_configs.append(tool_cfg)
        return tools

    def _create_mcp_client(self, tool_cfg: Dict[str, Any]) -> MCPClient:
        """Create MCP client for runtime use (following Strands pattern)."""
        cfg = tool_cfg.get("config", {})
        proxy_url = f"{self.base_url}/v1/mcps/{tool_cfg['name']}/proxy"
        headers = dict(cfg.get("headers", {}))
        transport = cfg.get("transport", "streamable_http")

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if transport == "HTTP_STREAMABLE":
            mcp_transport = "streamable_http"
        elif transport == "HTTP_SSE":
            mcp_transport = "sse"

        def create_transport():
            if mcp_transport == "streamable_http":
                return streamablehttp_client(proxy_url, headers=headers)
            elif mcp_transport == "sse":
                return sse_client(proxy_url, headers=headers)
            else:
                return streamablehttp_client(proxy_url, headers=headers)

        return MCPClient(create_transport)

    def _build_llm_from_config(self, config: Dict[str, Any]) -> FlotorchStrandsModel:
        """Build LLM instance from agent configuration."""
        llm_config = config.get("llm", {})
        model_id = llm_config.get("callableName", "default-model")
        
        return FlotorchStrandsModel(
            model_id=model_id,
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _build_agent_from_config(self, config: Dict[str, Any]) -> Agent:
        """Build Strands agent from configuration following Strands documentation pattern."""
        self._llm = self._build_llm_from_config(config)

        custom_tools = self._build_tools(config)

        system_prompt = config.get("systemPrompt", "")
        goal = config.get("goal", "")
        if goal:
            system_prompt += f"\nYour goal: {goal}"
        
        output_schema = None
        if "outputSchema" in config and config["outputSchema"] is not None:
            output_schema = schema_to_pydantic_model("OutputSchema", config["outputSchema"])
        
        agent_kwargs = {
            "model": self._llm,
            "tools": custom_tools,
            "system_prompt": system_prompt,
            "name": sanitize_agent_name(config.get("name", self.agent_name)),
            "description": config.get("goal", ""),
        }

        if self.session_manager:
            agent_kwargs["session_manager"] = self.session_manager
        
        agent = Agent(**agent_kwargs)
        
        agent._output_schema = output_schema
        
        return agent

    def get_agent(self) -> Agent:
        """Get the Strands agent with sync support."""
        return cast(Agent, AgentProxy(self))

    def _get_synced_agent(self) -> Agent:
        """Get agent with configuration sync if enabled."""
        sync_enabled = self.config.get('syncEnabled', False)
        if not sync_enabled:
            return self._agent
            
        sync_interval = self.config.get('syncInterval', 60)
        now = time.time()
        
        if now - self._last_reload > sync_interval:
            print("[Sync] Reload interval passed. Attempting to reload agent...")   
            try:
                new_config = self._fetch_agent_config(self.agent_name)
                if new_config and new_config != self.config:
                    self.config = new_config
                    self._agent = self._build_agent_from_config(self.config)
                    print("[Sync] Agent successfully reloaded.")
            except Exception as e:
                print(f"[Warning] [Sync] Failed to reload agent config. Using previous agent. Reason: {e}")
                
            finally:
                self._last_reload = now
        return self._agent

class AgentProxy:
    def __init__(self, manager: FlotorchStrandsAgent):
        """Initialize the proxy with the agent manager."""
        self._manager = manager

    def __getattr__(self, item: str) -> Any:
        """Delegate attribute access to the underlying agent."""
        return getattr(self._manager._get_synced_agent(), item)

    def __setattr__(self, key: str, value: Any) -> None:
        """Delegate attribute setting to the underlying agent."""
        if key == "_manager":
            return object.__setattr__(self, key, value)
        return setattr(self._manager._get_synced_agent(), key, value)

    def __call__(self, prompt: Union[str, Messages, None] = None, **kwargs: Any) -> Any:
        """Unified method: handles MCP tools, regular tools, and structured output."""
        agent = self._manager._get_synced_agent()
        return self._unified_agent_call(agent, prompt, **kwargs)
    
    def _unified_agent_call(self, agent, prompt, **kwargs):
        """Unified method that handles MCP tools, regular tools, and structured output."""
        mcp_configs = getattr(self._manager, '_mcp_configs', [])

        if mcp_configs:
            mcp_config = self._manager._mcp_configs[0]  
            
            try:
                mcp_client = self._manager._create_mcp_client(mcp_config)
                with mcp_client:
                    mcp_tools = mcp_client.list_tools_sync()

                    original_tools = dict(agent.tool_registry.registry)
                    print(f"Original tools: type(original_tools): {type(original_tools)}")
                    
                    try:
                        for tool in mcp_tools:
                            tool_name = getattr(tool, 'name', str(tool))
                            if tool_name not in agent.tool_registry.registry:
                                agent.tool_registry.register_tool(tool)
                            else:
                                print(f"⚠️ Tool {tool_name} already exists, skipping registration")

                        result = agent(prompt, **kwargs)
                        return self._apply_structured_output(agent, result, **kwargs)

                    finally:
                        agent.tool_registry.registry = original_tools

                        
            except Exception as e:
                log_error("AgentProxy._unified_agent_call", f"MCP tools failed, falling back to regular agent: {e}")
                result = agent(prompt, **kwargs)
                return self._apply_structured_output(agent, result, **kwargs)

        else:
            result = agent(prompt, **kwargs)
            return self._apply_structured_output(agent, result, **kwargs)

    def _apply_structured_output(self, agent, result, **kwargs):
        """Apply structured output if schema is defined."""
        if agent._output_schema:
            output_schema = getattr(agent, '_output_schema', None)
            prompt = f"{result}"
            structured_result = agent.structured_output(output_schema, prompt, **kwargs)
            return structured_result.model_dump() if hasattr(structured_result, 'model_dump') else structured_result.dict()
        else:
            return result
        