"""
Flotorch Autogen LLM integration module.

This module provides the FlotorchAutogenLLM class that integrates Flotorch LLM
with the Autogen framework for chat completion capabilities.
"""

from typing import Sequence, Union, AsyncGenerator
import json
from pydantic import PrivateAttr
from autogen_core.tools import Tool, ToolSchema
from autogen_core import FunctionCall

from autogen_core.models import (
    ChatCompletionClient,
    LLMMessage,
    CreateResult,
    RequestUsage,
    ModelInfo,
    ModelFamily,
    ModelCapabilities,
)

from flotorch.sdk.llm import FlotorchLLM
from flotorch.autogen.utils.autogen_utils import process_llmmessage, convert_tools
from flotorch.sdk.utils.llm_utils import convert_pydantic_to_custom_json_schema
from flotorch.sdk.utils.logging_utils import log_error, log_object_creation

class FlotorchAutogenLLM(ChatCompletionClient):
    """
    This class is used to create and manage autogen LLMs.
    """

    _llm: FlotorchLLM = PrivateAttr()

    def __init__(self, model_id: str, api_key: str, base_url: str):
        self._llm = FlotorchLLM(model_id, api_key, base_url)
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        
        log_object_creation("FlotorchAutogenLLM", model_id=model_id, base_url=base_url)
        
    async def create(self, messages, tools=None, json_output=None, **kwargs):
        # Keep original messages to detect tool execution phase
        original_messages = messages
        messages = process_llmmessage(messages)
        converted_tools = convert_tools(tools) if tools else []

        # Enable structured output only when either:
        # - no tools are provided, or
        # - we are in the reflection/finalization step (tool results present)
        response_format = None
        if json_output:
            # Detect if tool execution results are present in the conversation
            try:
                from autogen_core.models import FunctionExecutionResultMessage
                has_tool_results = any(isinstance(m, FunctionExecutionResultMessage) for m in original_messages)
            except Exception:
                has_tool_results = False

            enable_structured_output = (not converted_tools) or has_tool_results

            if enable_structured_output:
                response = convert_pydantic_to_custom_json_schema(json_output)
                response_format = response["response_format"]

        try:
            response = await self._llm.ainvoke(
                messages=messages, tools=converted_tools, response_format=response_format
            )
        except Exception as e:
            # Failure-only logging
            log_error("FlotorchAutogenLLM.create.invoke", e)
            raise

        raw_response = response.metadata.get("raw_response", {})
        choices = raw_response.get("choices", [])

        content_str = ""
        function_calls = []

        for choice in choices:
            message = choice.get("message", {})

            # Check for tool calls first
            if message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    func = tool_call.get("function", {})
                    raw_args = func.get("arguments")
                    args_str = (
                        json.dumps(raw_args)
                        if isinstance(raw_args, dict)
                        else str(raw_args)
                    )
                    function_calls.append(
                        FunctionCall(
                            name=func.get("name"),
                            arguments=args_str,
                            id=tool_call.get("id"),
                        )
                    )
            # If no tool calls, it's a content response (text or structured JSON).
            elif message.get("content") is not None:
                content_str += message.get("content", "")

        # If there were no tool calls and structured output was requested but not enforced,
        # perform a follow-up call with structured response enabled to get valid JSON.
        if (not function_calls) and json_output and (response_format is None):
            try:
                response_schema = convert_pydantic_to_custom_json_schema(json_output)
                structured_response_format = response_schema["response_format"]
                followup = await self._llm.ainvoke(
                    messages=messages,
                    tools=converted_tools,
                    response_format=structured_response_format,
                )
                raw_followup = followup.metadata.get("raw_response", {})
                followup_choices = raw_followup.get("choices", [])
                # Reset content_str to prefer structured reply
                content_str = ""
                for choice in followup_choices:
                    message = choice.get("message", {})
                    if message.get("content") is not None:
                        content_str += message.get("content", "")
            except Exception as e:
                # Log but do not mask original result; agent may handle text fallback
                log_error("FlotorchAutogenLLM.create.followup_structured", e)

        if function_calls:
            result_content = function_calls
            result_finish_reason = "function_calls"
        else:
            # If there were no tool calls, the content is the final answer.
            result_content = content_str
            result_finish_reason = "stop"

        usage = RequestUsage(
            prompt_tokens=int(response.metadata.get("inputTokens", 0)),
            completion_tokens=int(response.metadata.get("outputTokens", 0)),
        )

        return CreateResult(
            finish_reason=result_finish_reason,
            content=result_content,
            usage=usage,
            cached=False,
        )

    async def create_stream(
        self, messages: Sequence[LLMMessage], **kwargs
    ) -> AsyncGenerator[Union[str, CreateResult], None]:
        try:
            result = await self.create(messages, **kwargs)
        except Exception as e:
            log_error("FlotorchAutogenLLM.create_stream", e)
            raise
        if isinstance(result.content, str):
            yield result.content
        yield result

    async def close(self):
        pass

    def actual_usage(self) -> RequestUsage:
        pass

    def total_usage(self) -> RequestUsage:
        pass

    def count_tokens(
        self, messages: Sequence[LLMMessage], *, tools: Sequence[Tool | ToolSchema] = []
    ) -> int:
        pass

    def remaining_tokens(
        self, messages: Sequence[LLMMessage], *, tools: Sequence[Tool | ToolSchema] = []
    ) -> int:
        return super().remaining_tokens(messages, tools=tools)

    @property
    def model_info(self) -> ModelInfo:
        return ModelInfo(
            family=ModelFamily.UNKNOWN,
            context_length=8192,
            token_limit=4096,
            vision=False,
            json_output=True,
            function_calling=True,
            structured_output=True,
        )

    @property
    def capabilities(self) -> ModelCapabilities:
        # This is deprecated, but required by the abstract class.
        # We can just return the contents of model_info.
        info = self.model_info
        return {
            "vision": info.get("vision", False),
            "function_calling": True,
            "json_output": info.get("json_output", False),
            "structured_output": info.get("structured_output", False),
            "token_limit": info.get("token_limit", 4096),
            "context_length": info.get("context_length", 8192),
        }