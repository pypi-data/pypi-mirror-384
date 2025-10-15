"""
Flotorch Strands Model integration.

This module provides the FlotorchStrandsModel class that extends Strands' Model base class
and overrides the stream() and structured_output() methods to use Flotorch SDK instead
of direct model provider calls.
"""

import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, Union, TypeVar

from pydantic import BaseModel

from flotorch.sdk.llm import FlotorchLLM
from flotorch.sdk.utils.logging_utils import log_error, log_object_creation
from flotorch.strands.utils.strands_utils import (
    convert_strands_messages_to_flotorch,
    convert_strands_tools_to_flotorch,
    convert_flotorch_response_to_strands_stream,
    log_strands_integration
)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import Strands types with fallback for when Strands is not installed
try:
    from strands.models.model import Model
    from strands.types.content import Messages
    from strands.types.streaming import StreamEvent
    from strands.types.tools import ToolChoice, ToolSpec
except ImportError:
    Model = object
    Messages = List[Dict[str, Any]]
    StreamEvent = Dict[str, Any]
    ToolChoice = Dict[str, Any]
    ToolSpec = Dict[str, Any]

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class FlotorchStrandsModel(Model):
    """
    Flotorch integration for Strands Agents framework.

    This class extends Strands' Model base class and overrides the stream() and
    structured_output() methods to route LLM calls through Flotorch SDK instead
    of calling model providers directly.

    Attributes:
        flotorch_llm (FlotorchLLM): The underlying Flotorch LLM instance.
        config (Dict[str, Any]): Model configuration dictionary.
    """

    def __init__(
        self,
        model_id: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **model_config: Any
    ) -> None:
        """
        Initialize the Flotorch Strands Model.

        Args:
            model_id: Model identifier (e.g., "flotorch/model_name")
            api_key: API key for the model provider. If None, will try to get from
                    FLOTORCH_API_KEY environment variable
            base_url: Base URL for the Flotorch gateway. If None, will try to get from
                     FLOTORCH_GATEWAY_URL environment variable
            **model_config: Additional model configuration options
        """
        super().__init__()

        # Get API key from parameter or environment variable
        if api_key is None:
            api_key = os.getenv("FLOTORCH_API_KEY")
            if api_key is None:
                raise ValueError(
                    "API key must be provided either as parameter or set in FLOTORCH_API_KEY environment variable"
                )

        # Get base URL from parameter or environment variable
        if base_url is None:
            base_url = os.getenv("FLOTORCH_GATEWAY_URL")
            if base_url is None:
                raise ValueError(
                    "Base URL must be provided either as parameter or set in FLOTORCH_GATEWAY_URL environment variable"
                )

        # Initialize Flotorch LLM (no provider parameter - auto-detected by model_id)
        self.flotorch_llm = FlotorchLLM(
            model_id=model_id,
            api_key=api_key,
            base_url=base_url
        )

        # Store configuration
        self.config = {
            "model_id": model_id,
            "api_key": api_key,
            "base_url": base_url,
            **model_config
        }

        # Log object creation
        log_object_creation("FlotorchStrandsModel", model_id=model_id, base_url=base_url)

    def update_config(self, **model_config: Any) -> None:
        """
        Update the model configuration.

        Args:
            **model_config: Configuration overrides
        """
        self.config.update(model_config)

        # Update Flotorch LLM configuration if needed
        if "model_id" in model_config:
            self.flotorch_llm.model_id = model_config["model_id"]
        if "api_key" in model_config:
            self.flotorch_llm.api_key = model_config["api_key"]
        if "base_url" in model_config:
            self.flotorch_llm.base_url = model_config["base_url"]

        log_strands_integration(f"Updated model configuration: {model_config}")

    def get_config(self) -> Dict[str, Any]:
        """
        Get the current model configuration.

        Returns:
            Dict[str, Any]: Current model configuration
        """
        return self.config.copy()

    async def stream(
        self,
        messages: Messages,
        tool_specs: Optional[List[ToolSpec]] = None,
        system_prompt: Optional[str] = None,
        tool_choice: Optional[ToolChoice] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream conversation with the model using Flotorch SDK.

        This method overrides Strands' stream() method to route calls through
        Flotorch SDK instead of calling model providers directly.

        Args:
            messages: List of message objects to be processed by the model
            tool_specs: List of tool specifications to make available to the model
            system_prompt: System prompt to provide context to the model
            tool_choice: Selection strategy for tool invocation
            **kwargs: Additional keyword arguments for future extensibility

        Yields:
            StreamEvent: Formatted message chunks from the model in Strands format

        Raises:
            Exception: If an error occurs during streaming
        """
        try:
            log_strands_integration(f"Starting stream with {len(messages)} messages")

            # Convert Strands messages to Flotorch format
            flotorch_messages = convert_strands_messages_to_flotorch(messages)
            log_strands_integration(f"Converted {len(flotorch_messages)} messages to Flotorch format")

            # Convert tool specifications
            flotorch_tools = []
            if tool_specs:
                flotorch_tools = convert_strands_tools_to_flotorch(tool_specs)
                log_strands_integration(f"Converted {len(tool_specs)} tool specs to {len(flotorch_tools)} Flotorch tools")
            else:
                log_strands_integration("No tool specifications provided")

            # Prepare system prompt
            if system_prompt:
                flotorch_messages.insert(0, {
                    "role": "system",
                    "content": system_prompt
                })
                log_strands_integration("Added system prompt to messages")

            # Call Flotorch LLM using ainvoke (not streaming)
            log_strands_integration(f"Calling Flotorch LLM with {len(flotorch_messages)} messages and {len(flotorch_tools) if flotorch_tools else 0} tools")
            flotorch_response = await self.flotorch_llm.ainvoke(
                messages=flotorch_messages,
                tools=flotorch_tools if flotorch_tools else None,
                **kwargs
            )

            # Convert Flotorch response to Strands stream format
            stream_events = convert_flotorch_response_to_strands_stream(flotorch_response)
            log_strands_integration(f"Converted Flotorch response to {len(stream_events)} stream events")

            # Yield stream events
            for event in stream_events:
                yield event

            log_strands_integration("Stream completed successfully")

        except Exception as e:
            log_error("FlotorchStrandsModel.stream", e)
            # Yield error event in Strands format
            yield {
                "messageStop": {
                    "stopReason": "error",
                    "error": str(e)
                }
            }

    async def structured_output(
        self,
        output_model: Type[T],
        prompt: Messages,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Union[T, Any]], None]:
        """
        Get structured output from the model using Flotorch SDK.

        This method overrides Strands' structured_output() method to route calls
        through Flotorch SDK and convert the response to the expected format.

        Args:
            output_model: The Pydantic model class for structured output
            prompt: The prompt messages to use for the agent
            system_prompt: System prompt to provide context to the model
            **kwargs: Additional keyword arguments for future extensibility

        Yields:
            Dict[str, Union[T, Any]]: Model events with the last being the structured output

        Raises:
            Exception: If an error occurs during structured output generation
        """
        try:
            log_strands_integration(f"Starting structured output with {len(prompt)} messages")

            # Convert Strands messages to Flotorch format
            flotorch_messages = convert_strands_messages_to_flotorch(prompt)

            # Prepare system prompt
            if system_prompt:
                flotorch_messages.insert(0, {
                    "role": "system",
                    "content": system_prompt
                })

            # Convert Pydantic model to response format
            from flotorch.sdk.utils.llm_utils import convert_pydantic_to_custom_json_schema
            response_schema = convert_pydantic_to_custom_json_schema(output_model)
            response_format = response_schema["response_format"]

            # Call Flotorch LLM with response_format
            flotorch_response = await self.flotorch_llm.ainvoke(
                messages=flotorch_messages,
                response_format=response_format,
                **kwargs
            )

            # Parse the structured output from content
            content = flotorch_response.content if hasattr(flotorch_response, 'content') else ""
            try:
                parsed_data = json.loads(content)
                output_instance = output_model(**parsed_data)
                yield {"output": output_instance}
            except Exception as parse_error:
                log_error("FlotorchStrandsModel.structured_output.parse", parse_error)
                yield {"error": str(parse_error)}

            log_strands_integration("Structured output completed successfully")

        except Exception as e:
            log_error("FlotorchStrandsModel.structured_output", e)
            raise

