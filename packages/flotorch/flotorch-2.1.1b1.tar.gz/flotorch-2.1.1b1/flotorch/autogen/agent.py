from typing import Any, Dict, List, cast, Sequence
import time
import os
import asyncio
import concurrent.futures
import logging
from autogen_core import AgentProxy
from pydantic import create_model, Field

from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool

# Configure logging to suppress AutoGen logs while keeping Flotorch logs
logging.getLogger("autogen_core").setLevel(logging.WARNING)
logging.getLogger("autogen_agentchat").setLevel(logging.WARNING)
logging.getLogger("autogen_ext").setLevel(logging.WARNING)

from flotorch.autogen.llm import FlotorchAutogenLLM
from flotorch.autogen.utils.autogen_utils import create_sse_tool, create_stream_tool

from flotorch.autogen.memory import FlotorchAutogenMemory
from flotorch.sdk.utils.http_utils import http_get
from flotorch.autogen.sessions import FlotorchAutogenSession

from flotorch.sdk.utils.logging_utils import (
    log_error,
    log_info,
    log_object_creation,
)
from flotorch.autogen.utils.autogen_utils import sanitize_name


def schema_to_pydantic_model(name: str, schema: dict):
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


class FlotorchAutogenAgent():
    """
    This class is used to create autogen agents from a config file.
    """

    def __init__(self, agent_name: str, memory: List[FlotorchAutogenMemory] = None, custom_tools: List[FunctionTool] = None, model_context: FlotorchAutogenSession = None, base_url: str = None, api_key: str = None):
        self.agent_name = agent_name
        self.memory = memory
        self.custom_tools = custom_tools
        self.model_context = model_context
        
        # Store base_url and api_key, using environment variables as fallback
        self.base_url = base_url or os.environ.get("FLOTORCH_BASE_URL")
        self.api_key = api_key or os.environ.get("FLOTORCH_API_KEY")

        self.config = self._fetch_agent_config(agent_name)
        self._agent = self._build_agent_from_config(self.config)
        self._last_reload = time.time()
        
        log_object_creation("FlotorchAutogenAgent", agent_name=self.agent_name)

    def _fetch_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Fetch agent config from API.
        """
        if not self.base_url:
            raise ValueError("base_url is required to fetch agent configuration")

        if not self.api_key:
            raise ValueError("api_key is required to fetch agent configuration")

        # Construct the API URL
        url = f"{self.base_url.rstrip('/')}/v1/agents/{agent_name}"

        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = http_get(url, headers=headers)
            return response
        except Exception as e:
            # Failure-only logging
            log_error("FlotorchAutogenAgent._fetch_agent_config", e)
            raise

    def _run_async_in_thread(self, async_func):
        """
        Run async function in a separate thread with its own event loop.
        This ensures proper isolation and execution of async code.
        """
        def run_in_thread():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_func())
            finally:
                loop.close()
        
        # Use ThreadPoolExecutor to run the async function
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_thread)
            return future.result()

    def _build_tools(self, config: Dict[str, Any]):
        """
        Builds the tools from the config using either http or sse
        """
        async def build_async_tools():
            tools = []

            if config.get('tools'):
                tasks = []
                for tool_config in config['tools']:
                    if tool_config.get('type') == 'MCP':
                        transport = tool_config.get('config', {}).get('transport')
                        if transport == 'HTTP_STREAMABLE':
                            tasks.append(create_stream_tool(tool_config, self.base_url, self.api_key))
                        elif transport == 'HTTP_SSE':
                            tasks.append(create_sse_tool(tool_config, self.base_url, self.api_key))

                # Wait for all tool creation tasks to complete
                if tasks:
                    try:
                        results = await asyncio.gather(*tasks)
                    except Exception as e:
                        # Failure-only logging; maintain behavior by re-raising
                        log_error("FlotorchAutogenAgent._build_tools.gather", e)
                        raise
                    for tool_list in results:
                        if isinstance(tool_list, list):
                            tools.extend(tool_list)
                        else:
                            tools.append(tool_list)
                
            if self.custom_tools:
                tools.extend(self.custom_tools)

            return tools

        # Run async tools building in a separate thread
        return self._run_async_in_thread(build_async_tools)

    def _build_agent_from_config(self, config: Dict[str, Any]):
        """
        Builds the agent from the config
        """
        llm = FlotorchAutogenLLM(
            model_id = config['llm']['callableName'],
            api_key = self.api_key,
            base_url = self.base_url
        )
        
        tools = self._build_tools(config)

        input_schema = None
        output_schema = None
        if "inputSchema" in config and config["inputSchema"] is not None:
            input_schema = schema_to_pydantic_model("InputSchema", config["inputSchema"])
        if "outputSchema" in config and config["outputSchema"] is not None:
            output_schema = schema_to_pydantic_model("OutputSchema", config["outputSchema"])

        agent_kwargs = dict(
            name= sanitize_name(config['name']),
            model_client=llm,
            tools=tools,
            system_message=config['systemPrompt'],
            output_content_type=output_schema,
        )
        if self.memory is not None:
            agent_kwargs['memory'] = self.memory

        if self.model_context is not None:
            agent_kwargs['model_context'] = self.model_context
        return AssistantAgent(**agent_kwargs)

    def get_agent(self):
        return cast(AssistantAgent, AgentProxy(self))

    def _get_synced_agent(self) -> AssistantAgent:
        """
        Returns the latest agent, reloading config if sync interval has passed.
        """
        sync_enabled = self.config.get('syncEnabled', False)
        if not sync_enabled:
            return self._agent
            
        sync_interval = self.config.get('syncInterval', 1000000)
        now = time.time()
        if now - self._last_reload > sync_interval:
            log_info("Sync interval passed, attempting to sync agent configuration")

            try:
                new_config = self._fetch_agent_config(self.agent_name)
                if new_config and new_config != self.config:
                    self.config = new_config
                    self._agent = self._build_agent_from_config(self.config)
                    log_info("Agent rebuilt with updated configuration")
                else:
                    log_info("No configuration changes detected, agent remains unchanged")

            except Exception as e:
                log_error("FlotorchAutogenAgent._get_synced_agent.reload", e)

            finally:
                self._last_reload = now
        return self._agent


class AgentProxy(AssistantAgent):
    def __init__(self, manager: "FlotorchAutogenAgent"):
        self._manager = manager

    def __getattr__(self, item):
        return getattr(self._manager._get_synced_agent(), item)

    def __setattr__(self, key, value):
        if key == "_manager":
            return object.__setattr__(self, key, value)
        return setattr(self._manager._get_synced_agent(), key, value)