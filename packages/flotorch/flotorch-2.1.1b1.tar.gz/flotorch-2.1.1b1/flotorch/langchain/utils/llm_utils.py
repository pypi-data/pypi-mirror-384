"""
Core utility functions for Flotorch LangGraph integration.
These functions handle message and tool format conversions.
"""

import inspect
import json
from typing import Any, Dict, List, Union
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage, FunctionMessage
import logging

logger = logging.getLogger(__name__)


def convert_messages_to_dicts(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """Convert LangChain messages to the format expected by Flotorch SDK.
    Supports both tools (tool_calls + tool messages) and legacy functions
    (assistant.function_call + function messages) flows.
    """
    converted_messages = []
    
    # Track tool call IDs from the most recent assistant message for proper mapping
    last_tool_call_mapping = {}  # function_name -> tool_call_id

    for message in messages:
        if isinstance(message, SystemMessage):
            converted_messages.append({
                "role": "system",
                "content": message.content
            })
        elif isinstance(message, HumanMessage):
            converted_messages.append({
                "role": "user",
                "content": message.content
            })
        elif isinstance(message, AIMessage):
            # New tools API
            if message.tool_calls:
                content = message.content or ""
                tool_calls = []
                # Update mapping for function names to call IDs
                last_tool_call_mapping.clear()
                
                for tool_call in message.tool_calls:
                    call_id = tool_call.get("id", f"call_{tool_call.get('name', 'unknown')}")
                    function_name = tool_call.get("name", "")
                    
                    # Map function name to call ID for later FunctionMessage processing
                    last_tool_call_mapping[function_name] = call_id
                    
                    args = tool_call.get("args", {})
                    if isinstance(args, dict):
                        args_json = json.dumps(args)
                    else:
                        args_json = str(args)

                    tool_calls.append({
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": args_json
                        }
                    })

                converted_messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls
                })
            else:
                function_call = None
                try:
                    function_call = getattr(message, "additional_kwargs", {}).get("function_call")
                except Exception:
                    function_call = None

                if function_call:
                    # Convert legacy function_call to tools-style tool_calls for backend compatibility
                    function_name = function_call.get("name", "")
                    call_id = f"call_{function_name}"
                    
                    # Update mapping
                    last_tool_call_mapping.clear()
                    last_tool_call_mapping[function_name] = call_id
                    
                    arguments = function_call.get("arguments", {})
                    if isinstance(arguments, dict):
                        arguments = json.dumps(arguments)
                    elif not isinstance(arguments, str):
                        arguments = str(arguments)

                    converted_messages.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": arguments,
                                },
                            }
                        ],
                    })
                else:
                    # Regular assistant message without tool calls
                    converted_messages.append({
                        "role": "assistant",
                        "content": message.content
                    })
        elif isinstance(message, ToolMessage):
            # Always include tool messages - they are responses to tool calls
            converted_messages.append({
                "role": "tool",
                "content": message.content,
                "tool_call_id": message.tool_call_id,
                "name": getattr(message, "name", None)
            })
        elif isinstance(message, FunctionMessage):
            # Map legacy function result to tools-style tool message
            # Use the proper tool_call_id from our mapping
            function_name = getattr(message, "name", "")
            tool_call_id = last_tool_call_mapping.get(function_name, f"call_{function_name}")
            
            converted_messages.append({
                "role": "tool",
                "content": message.content,
                "tool_call_id": tool_call_id,
                "name": function_name
            })
        else:
            logger.warning(f"Unhandled message type: {type(message)}. Falling back to user.")
            converted_messages.append({
                "role": "user",
                "content": str(getattr(message, "content", "")),
            })

    return converted_messages


def convert_tools_to_format(tools: List[Union[BaseTool, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Convert LangChain tools to the format expected by Flotorch SDK (following ADK pattern)."""
    converted_tools = []

    for tool in tools:
        try:
            if isinstance(tool, BaseTool):
                name = getattr(tool, 'name', str(tool))

                description = getattr(tool, 'description', None)
                if not description:
                    description = getattr(tool, '__doc__', '')

                parameters = {"type": "object", "properties": {}, "required": []}

                if hasattr(tool, 'args_schema') and tool.args_schema:
                    
                    if hasattr(tool.args_schema, 'model_json_schema'):
                        schema = tool.args_schema.model_json_schema()
                        if isinstance(schema, dict):
                            parameters = schema
                    elif isinstance(tool.args_schema, dict):
                        parameters = tool.args_schema

                elif hasattr(tool, 'func') or hasattr(tool, '__call__'):
                    func = getattr(tool, 'func', tool)
                    sig = inspect.signature(func)
                    properties = {}
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        if param.annotation == int:
                            properties[param_name] = {"type": "integer"}
                        elif param.annotation == float:
                            properties[param_name] = {"type": "number"}
                        elif param.annotation == bool:
                            properties[param_name] = {"type": "boolean"}
                        else:
                            properties[param_name] = {"type": "string"}

                    parameters["properties"] = properties
                    parameters["required"] = [name for name, param in sig.parameters.items()
                                            if name != 'self' and param.default == param.empty]

                converted_tools.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters
                    }
                })
            elif isinstance(tool, dict):
                converted_tools.append(tool)

        except Exception as e:
            logger.error(f"Error converting tool {tool}: {e}")
            continue

    return converted_tools


def _extract_raw_message(response):
    """Extract raw message from Flotorch response."""
    if hasattr(response, "metadata") and "raw_response" in response.metadata:
        raw = response.metadata["raw_response"]
        if "choices" in raw and raw["choices"]:
            choice = raw["choices"][0]
            return choice.get("message", {})
    return None

def _parse_arguments(arguments):
    """Parse and serialize arguments."""
    if isinstance(arguments, dict):
        return json.dumps(arguments)
    return str(arguments)

def parse_flotorch_response_bind_tools(response) -> AIMessage:
    """Parse Flotorch response to AIMessage with tool calls support."""
    try:
        msg = _extract_raw_message(response)
        if msg:
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                parsed_tool_calls = []
                for tool_call in tool_calls:
                    arguments = tool_call["function"].get("arguments", {})
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            pass

                    parsed_tool_calls.append({
                        "id": tool_call.get("id", ""),
                        "name": tool_call["function"]["name"],
                        "args": arguments
                    })

                return AIMessage(
                    content=msg.get("content", ""),
                    tool_calls=parsed_tool_calls
                )

            return AIMessage(content=msg.get("content", getattr(response, "content", "")))

        return AIMessage(content=getattr(response, "content", ""))

    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return AIMessage(content=getattr(response, "content", ""))


def parse_flotorch_response_bind_functions(response) -> AIMessage:
    """Parse Flotorch response for legacy OpenAI functions agent.

    If the backend returns tool_calls, convert the FIRST tool_call into a
    legacy function_call dict to satisfy create_openai_functions_agent's
    output parser expectations.
    """
    try:
        msg = _extract_raw_message(response)
        if msg:
            # Map tool_calls -> function_call (use the first one)
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                first = tool_calls[0]
                args = first.get("function", {}).get("arguments", {})
                if isinstance(args, dict):
                    try:
                        args = json.dumps(args)
                    except Exception:
                        args = str(args)
                elif not isinstance(args, str):
                    args = str(args)

                return AIMessage(
                    content=msg.get("content", ""),
                    additional_kwargs={
                        "function_call": {
                            "name": first.get("function", {}).get("name", ""),
                            "arguments": args,
                        }
                    },
                )

            # Plain text fallback
            return AIMessage(content=msg.get("content", getattr(response, "content", "")))

        return AIMessage(content=getattr(response, "content", ""))

    except Exception as e:
        logger.error(f"Error parsing response (functions mode): {e}")
        return AIMessage(content=getattr(response, "content", ""))