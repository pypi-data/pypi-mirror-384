from typing import List, Dict, Optional, Any, Union
from flotorch.sdk.utils.http_utils import (
    async_http_post, http_post, http_get, async_http_get, async_http_put, http_put, async_http_delete, http_delete
)



VECTORSTORE_ENDPOINT = "/openai/v1/vector_stores/"

async def async_search_vectorstore(
    base_url:str, 
    api_key:str,
    query:str, 
    vectorstore_id:str,
    max_number_of_result:Optional[int] = 5,
    ranker:Optional[str] = 'semantic',
    score_threshold:Optional[float] = 0.2, 
    rewrite_query:Optional[bool] = True
    ) -> Dict[str, Any]:
    
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload: Dict[str, Any] = {
        "query": query,
        "max_num_results": max_number_of_result,
        "ranking_options": {
            "ranker": ranker,
            "score_threshold": score_threshold
        },
        "rewrite_query": rewrite_query
    }
    
    url = f"{base_url.rstrip('/')}{VECTORSTORE_ENDPOINT}{vectorstore_id}/search" 
    
    return await async_http_post(url=url, headers = headers, json = payload)
    
def search_vectorstore(
    base_url:str, 
    api_key:str,
    query:str, 
    vectorstore_id:str,
    max_number_of_result:Optional[int] = 5,
    ranker:Optional[str] = 'semantic',
    score_threshold:Optional[float] = 0.2, 
    rewrite_query:Optional[bool] = True
    ) -> Dict[str, Any]:
    
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload: Dict[str, Any] = {
        "query": query,
        "max_num_results": max_number_of_result,
        "ranking_options": {
            "ranker": ranker,
            "score_threshold": score_threshold
        },
        "rewrite_query": rewrite_query
    }
    
    url = f"{base_url.rstrip('/')}{VECTORSTORE_ENDPOINT}{vectorstore_id}/search" 
    
    return http_post(url=url, headers = headers, json = payload)

def extract_vectorstore_texts(search_results: dict) -> list[str]:
    return [
        content_block['text']
        for item in search_results.get('data', [])
        for content_block in item.get('content', [])
        if isinstance(content_block, dict) and 'text' in content_block
    ]

def extract_top_search_results(
    api_response: Dict[str, Any],
    top_n: int = 3
) -> List[Dict[str, Any]]:
    if "data" not in api_response:
        return []

    results = []
    for item in api_response["data"]:
        filename = item.get("filename", "")
        score = item.get("score", 0.0)
        for content in item.get("content", []):
            if content.get("type") == "text":
                results.append({
                    "filename": filename.split("/")[-1],
                    "score": round(score, 3),
                    "text": content.get("text", "")
                })

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    return sorted_results[:top_n]
    


# Types
MemoryMessage = Dict[str, str]
MemoryMetadata = Dict[str, Any]
JSONType = Union[Dict[str, Any], List[Any]]


def _build_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


def _build_gateway_memory_url(base_url: str, provider_name: str) -> str:
    return f"{base_url.rstrip('/')}/v1/memory/{provider_name}"


# ---------------------- CREATE MEMORY ----------------------
async def async_add_memory(
    base_url: str,
    provider_name: str,
    api_key: str,
    messages: List[MemoryMessage],
    userId: Optional[str] = None,
    agentId: Optional[str] = None,
    appId: Optional[str] = None,
    sessionId: Optional[str] = None,
    metadata: Optional[MemoryMetadata] = None,
    timestamp: Optional[str] = None,
    providerParams: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Asynchronously create a new memory entry for an agent.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + "/memories"
    headers = _build_headers(api_key)
    payload = {
        "messages": messages,
        "userId": userId,
        "agentId": agentId,
        "appId": appId,
        "sessionId": sessionId,
        "metadata": metadata,
        "timestamp": timestamp,
        "providerParams": providerParams,
    }
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return await async_http_post(url, headers=headers, json=clean_payload)


def add_memory(
    base_url: str,
    provider_name: str,
    api_key: str,
    messages: List[MemoryMessage],
    userId: Optional[str] = None,
    agentId: Optional[str] = None,
    appId: Optional[str] = None,
    sessionId: Optional[str] = None,
    metadata: Optional[MemoryMetadata] = None,
    timestamp: Optional[str] = None,
    providerParams: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new memory entry for an agent.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + "/memories"
    headers = _build_headers(api_key)
    payload = {
        "messages": messages,
        "userId": userId,
        "agentId": agentId,
        "appId": appId,
        "sessionId": sessionId,
        "metadata": metadata,
        "timestamp": timestamp,
        "providerParams": providerParams,
    }
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return http_post(url, headers=headers, json=clean_payload)


# ---------------------- GET MEMORY BY ID ----------------------
async def async_get_memory(
    base_url: str,
    provider_name: str,
    api_key: str,
    memory_id: str,
) -> Dict[str, Any]:
    """
    Asynchronously retrieve a specific memory by its ID.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + f"/memories/{memory_id}"
    headers = _build_headers(api_key)
    return await async_http_get(url, headers=headers)


def get_memory(
    base_url: str,
    provider_name: str,
    api_key: str,
    memory_id: str,
) -> Dict[str, Any]:
    """
    Retrieve a specific memory by its ID.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + f"/memories/{memory_id}"
    headers = _build_headers(api_key)
    return http_get(url, headers=headers)


# ---------------------- UPDATE MEMORY ----------------------
async def async_update_memory(
    base_url: str,
    provider_name: str,
    api_key: str,
    memory_id: str,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Asynchronously update an existing memory.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + f"/memories/{memory_id}"
    headers = _build_headers(api_key)
    payload = {"content": content, "metadata": metadata}
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return await async_http_put(url, headers=headers, json=clean_payload)


def update_memory(
    base_url: str,
    provider_name: str,
    api_key: str,
    memory_id: str,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update an existing memory.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + f"/memories/{memory_id}"
    headers = _build_headers(api_key)
    payload = {"content": content, "metadata": metadata}
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return http_put(url, headers=headers, json=clean_payload)


# ---------------------- DELETE MEMORY ----------------------
async def async_delete_memory(
    base_url: str,
    provider_name: str,
    api_key: str,
    memory_id: str,
) -> Dict[str, Any]:
    """
    Asynchronously delete a memory by its ID.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + f"/memories/{memory_id}"
    headers = _build_headers(api_key)
    return await async_http_delete(url, headers=headers)


def delete_memory(
    base_url: str,
    provider_name: str,
    api_key: str,
    memory_id: str,
) -> Dict[str, Any]:
    """
    Delete a memory by its ID.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + f"/memories/{memory_id}"
    headers = _build_headers(api_key)
    return http_delete(url, headers=headers)


# ---------------------- SEARCH MEMORIES ----------------------
async def async_search_memories(
    base_url: str,
    provider_name: str,
    api_key: str,
    userId: Optional[str] = None,
    agentId: Optional[str] = None,
    appId: Optional[str] = None,
    sessionId: Optional[str] = None,
    createFrom: Optional[str] = None,
    createTo: Optional[str] = None,
    updateFrom: Optional[str] = None,
    updateTo: Optional[str] = None,
    categories: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    keywords: Optional[List[str]] = None,
    page: Optional[int] = 1,
    limit: Optional[int] = 20,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Asynchronously search for memories using filters and criteria.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + "/memories/search"
    headers = _build_headers(api_key)
    # Determine the final query string with precedence: explicit query > keywords > "*"
    query_value: str = "*"
    if isinstance(query, str) and query.strip():
        query_value = query
   
    payload = {
        "userId": userId,
        "agentId": agentId,
        "appId": appId,
        "sessionId": sessionId,
        "createFrom": createFrom,
        "createTo": createTo,
        "updateFrom": updateFrom,
        "updateTo": updateTo,
        "categories": categories,
        "metadata": metadata,
        "query": query_value,
        "page": page,
        "limit": limit,
    }
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return await async_http_post(url, headers=headers, json=clean_payload)


def search_memories(
    base_url: str,
    provider_name: str,
    api_key: str,
    userId: Optional[str] = None,
    agentId: Optional[str] = None,
    appId: Optional[str] = None,
    sessionId: Optional[str] = None,
    createFrom: Optional[str] = None,
    createTo: Optional[str] = None,
    updateFrom: Optional[str] = None,
    updateTo: Optional[str] = None,
    categories: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    keywords: Optional[List[str]] = None,
    page: Optional[int] = 1,
    limit: Optional[int] = 20,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search for memories using filters and criteria.
    """
    url = _build_gateway_memory_url(base_url, provider_name) + "/memories/search"
    headers = _build_headers(api_key)
    # Determine the final query string with precedence: explicit query > keywords > "*"
    query_value: str = "*"
    if isinstance(query, str) and query.strip():
        query_value = query
  
    payload = {
        "userId": userId,
        "agentId": agentId,
        "appId": appId,
        "sessionId": sessionId,
        "createFrom": createFrom,
        "createTo": createTo,
        "updateFrom": updateFrom,
        "updateTo": updateTo,
        "categories": categories,
        "metadata": metadata,
        "query": query_value,
        "page": page,
        "limit": limit,
    }
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return http_post(url, headers=headers, json=clean_payload)
