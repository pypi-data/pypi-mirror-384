"""
Utility functions for Strands integration with Flotorch.

Contains functions for message conversion, tool specification conversion,
and response processing between Strands and Flotorch formats.
"""

import json
import logging
from typing import Any, Dict, List

from flotorch.sdk.utils.logging_utils import log_error, log_info

logger = logging.getLogger(__name__)


def convert_strands_messages_to_flotorch(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convert Strands message format to Flotorch format.

    Args:
        messages: List of messages in Strands format

    Returns:
        List[Dict[str, str]]: List of messages in Flotorch format [{"role": "user", "content": "..."}]
    """
    try:
        flotorch_messages = []
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                # Extract text content from Strands content blocks
                content_blocks = msg["content"]
                text_content = ""

                for block in content_blocks:
                    if isinstance(block, dict):
                        if "text" in block:
                            text_content += block["text"]
                        elif "toolUse" in block:
                            # Convert tool use to text representation
                            tool_use = block["toolUse"]
                            text_content += f"[Tool Use: {tool_use.get('name', 'unknown')} with input: {json.dumps(tool_use.get('input', {}))}]"
                        elif "toolResult" in block:
                            # Convert tool result to text representation
                            tool_result = block["toolResult"]
                            text_content += f"[Tool Result: {tool_result.get('content', '')}]"

                if text_content.strip():  # Only add non-empty messages
                    flotorch_messages.append({
                        "role": msg["role"],
                        "content": text_content.strip()
                    })

        return flotorch_messages

    except Exception as e:
        log_error("convert_strands_messages_to_flotorch", e)
        return []


def convert_strands_tools_to_flotorch(tool_specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert Strands tool specifications to Flotorch format.

    Args:
        tool_specs: List of tool specifications in Strands format

    Returns:
        List[Dict[str, Any]]: List of tool specifications in Flotorch format (OpenAI format)
    """
    try:
        flotorch_tools = []
        for tool_spec in tool_specs:
            if isinstance(tool_spec, dict) and "name" in tool_spec:
                # Convert to OpenAI format that Flotorch expects
                flotorch_tool = {
                    "type": "function",
                    "function": {
                        "name": tool_spec["name"],
                        "description": tool_spec.get("description", ""),
                        "parameters": tool_spec.get("inputSchema", {}).get("json", {})
                    }
                }
                flotorch_tools.append(flotorch_tool)
                log_strands_integration(f"Converted tool: {tool_spec['name']}")

        log_strands_integration(f"Successfully converted {len(flotorch_tools)} tools to Flotorch format")
        return flotorch_tools

    except Exception as e:
        log_error("convert_strands_tools_to_flotorch", e)
        return []


def convert_flotorch_response_to_strands_stream(
    flotorch_response: Any
) -> List[Dict[str, Any]]:
    """
    Convert Flotorch response to Strands streaming format.

    Args:
        flotorch_response: LLMResponse from Flotorch SDK

    Returns:
        List[Dict[str, Any]]: List of Strands stream events
    """
    try:
        stream_events = []

        # Message start event
        stream_events.append({
            "messageStart": {
                "role": "assistant"
            }
        })

        # Check if response contains tool calls
        tool_calls = extract_tool_calls_from_flotorch_response(flotorch_response)
        log_strands_integration(f"Extracted {len(tool_calls)} tool calls from Flotorch response")

        if tool_calls:
            # Handle tool calls
            for tool_call in tool_calls:
                # Content block start for tool use
                stream_events.append({
                    "contentBlockStart": {
                        "start": {
                            "toolUse": {
                                "toolUseId": tool_call["toolUseId"],
                                "name": tool_call["name"]
                            }
                        }
                    }
                })

                # Tool use input delta - convert dict to JSON string
                input_data = tool_call["input"]
                if isinstance(input_data, dict):
                    input_json = json.dumps(input_data)
                    log_strands_integration(f"Converted tool input dict to JSON: {input_json}")
                else:
                    input_json = str(input_data)
                    log_strands_integration(f"Tool input already string: {input_json}")

                stream_events.append({
                    "contentBlockDelta": {
                        "delta": {
                            "toolUse": {
                                "input": input_json
                            }
                        }
                    }
                })

                # Content block stop
                stream_events.append({
                    "contentBlockStop": {}
                })

            # Message stop with tool use reason
            stream_events.append({
                "messageStop": {
                    "stopReason": "tool_use"
                }
            })
        else:
            # Handle text content
            content = flotorch_response.content if hasattr(flotorch_response, 'content') else ""

            if content:
                # Content block start for text
                stream_events.append({
                    "contentBlockStart": {
                        "start": {
                            "text": {}
                        }
                    }
                })

                # Text content delta
                stream_events.append({
                    "contentBlockDelta": {
                        "delta": {
                            "text": content
                        }
                    }
                })

                # Content block stop
                stream_events.append({
                    "contentBlockStop": {}
                })

            # Message stop with end turn reason
            stream_events.append({
                "messageStop": {
                    "stopReason": "end_turn"
                }
            })

        # Metadata with usage information
        if hasattr(flotorch_response, 'metadata') and flotorch_response.metadata:
            usage = flotorch_response.metadata.get('usage', {})
            if usage:
                stream_events.append({
                    "metadata": {
                        "usage": usage
                    }
                })

        return stream_events

    except Exception as e:
        log_error("convert_flotorch_response_to_strands_stream", e)
        return []


def extract_tool_calls_from_flotorch_response(
    flotorch_response: Any
) -> List[Dict[str, Any]]:
    """
    Extract tool calls from Flotorch response.

    Args:
        flotorch_response: LLMResponse from Flotorch SDK

    Returns:
        List[Dict[str, Any]]: List of tool use objects in Strands format
    """
    try:
        tool_calls = []

        # Check if response contains tool calls in metadata
        if hasattr(flotorch_response, 'metadata') and flotorch_response.metadata:
            raw_response = flotorch_response.metadata.get('raw_response', {})
            if raw_response and 'choices' in raw_response:
                message = raw_response['choices'][0].get('message', {})
                if 'tool_calls' in message:
                    for tool_call in message['tool_calls']:
                        # Parse the arguments JSON string
                        arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                        try:
                            arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                        except json.JSONDecodeError:
                            arguments = {}

                        tool_use = {
                            "toolUseId": tool_call.get("id", f"tool_{len(tool_calls)}"),
                            "name": tool_call.get("function", {}).get("name", ""),
                            "input": arguments
                        }
                        tool_calls.append(tool_use)
                        log_strands_integration(f"Extracted tool call: {tool_use['name']} with input type: {type(arguments)}")

        return tool_calls

    except Exception as e:
        log_error("extract_tool_calls_from_flotorch_response", e)
        return []


def create_strands_tool_result(
    tool_use_id: str,
    content: str,
    status: str = "success"
) -> Dict[str, Any]:
    """
    Create a Strands tool result from tool execution.

    Args:
        tool_use_id: ID of the tool use
        content: Result content
        status: Status of the tool execution

    Returns:
        Dict[str, Any]: Tool result in Strands format
    """
    return {
        "toolResult": {
            "toolUseId": tool_use_id,
            "content": content,
            "status": status
        }
    }


def log_strands_integration(message: str, level: str = "info") -> None:
    """
    Log messages specific to Strands integration.
    
    Args:
        message: Message to log
        level: Log level (info, error, debug)
    """
    if level == "error":
        log_error(f"[Strands Integration] {message}")
    else:
        log_info(f"[Strands Integration] {message}")

