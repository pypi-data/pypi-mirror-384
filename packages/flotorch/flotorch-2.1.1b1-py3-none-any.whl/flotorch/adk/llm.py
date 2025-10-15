from typing import AsyncGenerator, List, Dict
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from flotorch.sdk.llm import FlotorchLLM
from flotorch.adk.utils.adk_utils import tools_to_openai_format, parse_llm_response_with_tools, build_messages_from_request
from flotorch.sdk.utils.logging_utils import  log_object_creation, log_error, log_info
from pydantic import PrivateAttr
from flotorch.sdk.utils.llm_utils import convert_pydantic_to_custom_json_schema


class FlotorchADKLLM(BaseLlm):
    """ADK-compatible LLM wrapper using Flotorch gateway LLM."""
    _llm: FlotorchLLM = PrivateAttr()
    
    def __init__(self, model_id: str, api_key: str, base_url: str):
        super().__init__(model=model_id, api_key=api_key, base_url=base_url)
        self._llm = FlotorchLLM(model_id, api_key, base_url)
        
        # Log object creation
        log_object_creation("FlotorchADKLLM", model_id=model_id, base_url=base_url)

    async def generate_content_async(
        self, 
        llm_request: LlmRequest, 
        stream: bool = False
        ) -> AsyncGenerator[LlmResponse, None]:
        # Build messages using utility function
        messages = build_messages_from_request(llm_request)
        
        # Prepare tools if available
        tools = None
        if hasattr(llm_request, "tools_dict") and llm_request.tools_dict:
            tools = tools_to_openai_format(llm_request.tools_dict.values())
        
        response_format = None
        if hasattr(llm_request, "config") and getattr(llm_request.config, "response_schema", None):
            # Convert Pydantic model to JSON schema
            response = convert_pydantic_to_custom_json_schema(llm_request.config.response_schema)
            response_format = response["response_format"]
            


        # Call the LLM with individual parameters
        try:
            response = await self._llm.ainvoke(
                messages=messages,
                tools=tools,
                response_format = response_format,
                extra_body={}
            )
            
            # Parse response using utility function with better error handling
            try:
                response_data = response.metadata.get('raw_response', {})
                parsed_parts = parse_llm_response_with_tools(response_data)
                
                if parsed_parts:
                    parts = []
                    function_calls_found = False
                    
                    for part_data in parsed_parts:
                        if part_data["type"] == "function_call":
                            # Limit to single tool call to avoid issues
                            if not function_calls_found:
                                try:
                                    part = types.Part.from_function_call(name=part_data["name"], args=part_data["args"])
                                    if part.function_call and "id" in part_data:
                                        part.function_call.id = part_data["id"]
                                    parts.append(part)
                                    function_calls_found = True
                                except Exception as e:
                                    # If tool call creation fails, convert to text response
                                    parts.append(types.Part.from_text(text=f"I'll help you with that. Let me check..."))
                                    break
                            else:
                                # Skip additional tool calls to avoid conflicts
                                continue
                        elif part_data["type"] == "text":
                            parts.append(types.Part.from_text(text=part_data["content"]))
                    
                    if parts:
                        yield LlmResponse(content=types.Content(role="assistant", parts=parts))
                        return
                
                # Fallback to text response
                text_content = response.content if hasattr(response, 'content') and response.content else "I'm here to help you."
                yield LlmResponse(content=types.Content(role="assistant", parts=[types.Part(text=text_content)]))
                
            except Exception as parse_error:
                # If parsing fails, return text response
                text_content = response.content if hasattr(response, 'content') and response.content else "I apologize, but I encountered an issue. How can I help you?"
                yield LlmResponse(content=types.Content(role="assistant", parts=[types.Part(text=text_content)]))
                
        except Exception as llm_error:
            # Log error and return error message
            log_error("FlotorchADKLLM.generate_content_async", llm_error)
            error_text = "I'm experiencing some technical difficulties. Please try again."
            yield LlmResponse(content=types.Content(role="assistant", parts=[types.Part(text=error_text)]))