"""
Utility functions for Flotorch ADK operations.
Contains functions for tool formatting, response parsing, and message processing.
"""

import json
import inspect
from typing import List, Dict, Any
from google.genai import types


def tools_to_openai_format(tools):
    """Convert tools to OpenAI format for LLM requests."""
    result = []
    for tool in tools:
        try:
            name = getattr(tool, 'name', getattr(tool, 'func', tool).__name__ if hasattr(getattr(tool, 'func', tool), '__name__') else str(tool))
            description = getattr(tool, 'description', getattr(getattr(tool, 'func', tool), '__doc__', '') or getattr(tool, '__doc__', ''))
            
            parameters = {"type": "object", "properties": {}, "required": []}
            
            if hasattr(tool, '_get_declaration'):
                try:
                    decl = tool._get_declaration()
                    if decl and decl.parameters and hasattr(decl.parameters, 'properties'):
                        properties = {}
                        for prop_name, prop_schema in decl.parameters.properties.items():
                            prop_type = getattr(prop_schema, 'type', None)
                            if prop_type and hasattr(prop_type, 'value'):
                                if prop_type.value == 'INTEGER': properties[prop_name] = {"type": "integer"}
                                elif prop_type.value == 'NUMBER': properties[prop_name] = {"type": "number"}
                                elif prop_type.value == 'BOOLEAN': properties[prop_name] = {"type": "boolean"}
                                else: properties[prop_name] = {"type": "string"}
                            else: properties[prop_name] = {"type": "string"}
                        parameters["properties"], parameters["required"] = properties, getattr(decl.parameters, 'required', [])
                except: pass
            elif hasattr(tool, 'input_schema'):
                schema = tool.input_schema
                if hasattr(schema, 'properties'):
                    parameters["properties"] = {name: {"type": "string"} for name in schema.properties}
                    parameters["required"] = getattr(schema, 'required', [])
                elif isinstance(schema, dict): parameters = schema
            elif hasattr(tool, 'func') or hasattr(tool, '__call__'):
                sig = inspect.signature(getattr(tool, 'func', tool))
                parameters["properties"] = {name: {"type": "string"} for name in sig.parameters}
                parameters["required"] = list(sig.parameters.keys())
            
            result.append({"type": "function", "function": {"name": name, "description": description, "parameters": parameters}})
        except: continue
    return result


def parse_function_response(response_content):
    """Parse function response content to extract text."""
    try:
        if hasattr(response_content, 'result') and hasattr(response_content.result, 'content'):
            content_list = response_content.result.content
            return content_list[0].text if content_list and hasattr(content_list[0], 'text') else str(response_content.result)
        elif hasattr(response_content, 'content'):
            content_list = response_content.content
            return content_list[0].text if content_list and hasattr(content_list[0], 'text') else str(response_content)
        elif isinstance(response_content, dict):
            if 'content' in response_content and isinstance(response_content['content'], list):
                content_list = response_content['content']
                return content_list[0]['text'] if content_list and isinstance(content_list[0], dict) and 'text' in content_list[0] else str(response_content)
            else:
                return json.dumps(response_content) if isinstance(response_content, dict) else str(response_content)
        else:
            return str(response_content)
    except:
        return str(response_content)


def parse_llm_response_with_tools(response_data):
    """Parse LLM response that may contain tool calls and return ADK-compatible parts."""
    try:
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            parts = []
            
            if "message" in choice:
                msg = choice["message"]
                if "tool_calls" in msg and msg["tool_calls"]:
                    # Limit to first tool call only to avoid conflicts
                    tool_call = msg["tool_calls"][0]
                    try:
                        fn_args = json.loads(tool_call["function"].get("arguments", "{}")) if isinstance(tool_call["function"].get("arguments", "{}"), str) else tool_call["function"].get("arguments", {})
                        parts.append({
                            "type": "function_call", 
                            "name": tool_call["function"]["name"], 
                            "args": fn_args, 
                            "id": tool_call.get("id", f"call_{tool_call['function']['name']}")
                        })
                    except Exception as e:
                        # If tool call parsing fails, convert to text
                        parts.append({"type": "text", "content": f"Let me help you with that query."})
                elif "function_call" in msg:
                    fn_call = msg["function_call"]
                    try:
                        fn_args = json.loads(fn_call.get("arguments", "{}")) if isinstance(fn_call.get("arguments", "{}"), str) else fn_call.get("arguments", {})
                        parts.append({
                            "type": "function_call", 
                            "name": fn_call["name"], 
                            "args": fn_args,
                            "id": f"call_{fn_call['name']}"
                        })
                    except Exception as e:
                        # If function call parsing fails, convert to text
                        parts.append({"type": "text", "content": f"Let me help you with that query."})
                elif "content" in msg and msg["content"]:
                    parts.append({"type": "text", "content": msg["content"]})
            elif "text" in choice:
                parts.append({"type": "text", "content": choice["text"]})
            
            return parts
        return []
    except Exception as e:
        # Return empty list if parsing fails completely
        return []


def process_session_events(session_events):
    """Process session events and convert to message format."""
    messages = []
    try:
        if session_events:
            recent_events = session_events[-10:] if len(session_events) > 10 else session_events
            for event in recent_events:
                if event.content and event.content.parts:
                    messages.extend([
                        {"role": event.author if event.author != "user" else "user", "content": part.text}
                        for part in event.content.parts if part.text
                    ] + [
                        {"role": "assistant", "content": "", "tool_calls": [{
                            "id": part.function_call.id, "type": "function",
                            "function": {"name": part.function_call.name, "arguments": json.dumps(part.function_call.args)}
                        }]} for part in event.content.parts if part.function_call
                    ] + [
                        {"role": "tool", "content": json.dumps(part.function_response.response) if isinstance(part.function_response.response, dict) else str(part.function_response.response), "tool_call_id": part.function_response.id}
                        for part in event.content.parts if part.function_response
                    ])
    except: pass
    return messages


def process_content_parts(content):
    """Process content parts and convert to message format."""
    messages = []
    try:
        if hasattr(content, "role") and hasattr(content, "parts"):
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    messages.append({"role": content.role, "content": part.text})
                elif hasattr(part, "function_call") and part.function_call:
                    messages.append({
                        "role": "assistant", "content": "", "tool_calls": [{
                            "id": part.function_call.id, "type": "function",
                            "function": {"name": part.function_call.name, "arguments": json.dumps(part.function_call.args)}
                        }]
                    })
                elif hasattr(part, "function_response") and part.function_response:
                    response_text = parse_function_response(part.function_response.response)
                    messages.append({"role": "tool", "content": response_text, "tool_call_id": part.function_response.id})
    except: pass
    return messages


def build_messages_from_request(llm_request):
    """Build messages from LLM request including system instruction, session events, and content."""
    messages = []
    
    # Add system instruction
    if hasattr(llm_request, "config") and getattr(llm_request.config, "system_instruction", None):
        messages.append({"role": "system", "content": llm_request.config.system_instruction})
    
    # Process session events
    try:
        if (ctx := getattr(llm_request, '_invocation_context', None)) and (session := ctx.session) and session.events:
            messages.extend(process_session_events(session.events))
    except: pass
    
    # Process current request contents
    for content in getattr(llm_request, "contents", []):
        messages.extend(process_content_parts(content))
    
    return messages 