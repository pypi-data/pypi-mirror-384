from typing import List, Dict, Any, Optional,Type
from pydantic import BaseModel
from flotorch.sdk.utils.http_utils import async_http_post, http_post

LLM_ENDPOINT = "/api/openai/v1/chat/completions"

class LLMResponse(BaseModel):
    'data class for LLM response'
    metadata: Dict[str, Any] 
    content: str


def invoke(messages: List[Dict[str, str]], model_id: str, api_key: str, base_url: str, tools: Optional[List[Dict]] = None, response_format=None, extra_body: Optional[Dict] = None, **kwargs):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_id,
        "messages": messages,
        "extra_body": extra_body or {}
    }

    if tools:
        payload["tools"] = tools

    if response_format:
        payload["response_format"] = response_format

    payload.update(kwargs)

    url = f"{base_url.rstrip('/')}{LLM_ENDPOINT}"
    result = http_post(
        url=url,
        headers=headers,
        json=payload
    )
    return result


async def async_invoke(messages: List[Dict[str, str]], model_id: str, api_key: str, base_url: str, tools: Optional[List[Dict]] = None, response_format=None, extra_body: Optional[Dict] = None, **kwargs):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_id,
        "messages": messages,
        "extra_body": extra_body or {}
    }
    
    
    # Add tools if provided
    if tools:
        payload["tools"] = tools

    if response_format:
        payload["response_format"] = response_format
    
    # Add any additional kwargs to the payload
    payload.update(kwargs)
   
    result = await async_http_post(
        url=f"{base_url.rstrip('/')}{LLM_ENDPOINT}",
        headers=headers,
        json=payload
    )
    return result

def extract_metadata(response: Dict):
    metadata = {
        "inputTokens": str(response['usage']['prompt_tokens']),
        "outputTokens": str(response['usage']['completion_tokens']),
        "totalTokens": str(response['usage']['total_tokens']),
    }
    # Store raw response for tool call parsing
    metadata['raw_response'] = response
    return metadata

def parse_llm_response(response: Dict) -> LLMResponse:
    try:
        message = response['choices'][0]['message']
        # Handle both content and tool_calls
        if 'content' in message and message['content'] is not None:
            content = message['content']
        elif 'tool_calls' in message:
            content = ""
        else:
            content = ""
            
        metadata = extract_metadata(response)
        return LLMResponse(metadata=metadata, content=content)
    except (KeyError, IndexError) as e:
        raise ValueError(f"Failed to parse unexpected API response structure: {response}") from e


def convert_pydantic_to_custom_json_schema(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Converts a Pydantic BaseModel class to the custom JSON schema format used in 'response_format'.
    
    Args:
        model_class (Type[BaseModel]): The Pydantic model class.

    Returns:
        Dict[str, Any]: The custom formatted schema.
    """
    schema_dict = model_class.model_json_schema()

    return {
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    **schema_dict,
                    "additionalProperties": False  # Force strict object definition
                },
                "name": schema_dict.get("title", model_class.__name__),
                "strict": True
            }
        }
    }