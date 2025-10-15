"""
Custom LangChain-compatible LLM for Flotorch.
Provides a BaseChatModel wrapper that routes calls through the Flotorch gateway.
"""

from typing import Any, Dict, List, Optional
from langchain_core.tools.base import BaseTool
from typing_extensions import Union
from pydantic import PrivateAttr
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from flotorch.sdk.llm import FlotorchLLM
from flotorch.langchain.utils.llm_utils import convert_messages_to_dicts, parse_flotorch_response_bind_tools, parse_flotorch_response_bind_functions, convert_tools_to_format


import logging

logger = logging.getLogger(__name__)

from pydantic import PrivateAttr

class FlotorchLangChainLLM(BaseChatModel):
    _model_id: str = PrivateAttr()
    _api_key: str = PrivateAttr()
    _base_url: str = PrivateAttr()
    _temperature: float = PrivateAttr()
    _llm: FlotorchLLM = PrivateAttr()

    def __init__(self, model_id: str, api_key: str, base_url: str, temperature: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        self._model_id = model_id
        self._api_key = api_key
        self._base_url = base_url
        self._temperature = temperature
        self._llm = FlotorchLLM(model_id, api_key, base_url)

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_id": self._model_id,
            "temperature": self._temperature,
            "base_url": self._base_url,
        }

    @property
    def _llm_type(self) -> str:
        """Return the type identifier for this LLM (used internally by LangChain)."""
        return "flotorch"
    


    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate a response from Flotorch synchronously.

        Args:
            messages: List of LangChain BaseMessage objects.
            stop: Optional list of stop sequences.
            run_manager: Optional run manager (callbacks).
            **kwargs: Extra arguments.

        Returns:
            ChatResult containing the AI response.
        """
        try:
            converted_messages = convert_messages_to_dicts(messages)
            extra_body = self._prepare_extra_body(stop, **kwargs)

            tools = getattr(self, '_tools', None)
            # Check which binding method was used
            # Use the stored binding type flag
            binding_method = getattr(self, '_binding_type', 'bind')

            response = self._llm.invoke(
                messages=converted_messages,
                tools=tools,
                extra_body=extra_body,
            )

            # Use appropriate parsing method based on binding method
            if binding_method == "bind_tools":
                ai_message = parse_flotorch_response_bind_tools(response)
            elif binding_method == "bind_functions":
                ai_message = parse_flotorch_response_bind_functions(response)
            else:
                # Default to tools parsing for any other case
                ai_message = parse_flotorch_response_bind_tools(response)

            
            return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except Exception as e:
            logger.error(f"Error in FlotorchLangchainLLM._generate: {e}")
            raise

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate a response from Flotorch asynchronously.

        Args:
            messages: List of LangChain BaseMessage objects.
            stop: Optional list of stop sequences.
            run_manager: Optional run manager (callbacks).
            **kwargs: Extra arguments.

        Returns:
            ChatResult containing the AI response.
        """
        try:
            converted_messages = convert_messages_to_dicts(messages)
            extra_body = self._prepare_extra_body(stop, **kwargs)

            tools = getattr(self, '_tools', None)
            
            # Check which binding method was used
            # Use the stored binding type flag
            binding_method = getattr(self, '_binding_type', 'bind')
            
            response = await self._llm.ainvoke(
                messages=converted_messages,
                tools=tools,
                extra_body=extra_body,
            )

            # Use appropriate parsing method based on binding method
            if binding_method == "bind_tools":
                ai_message = parse_flotorch_response_bind_tools(response)
            elif binding_method == "bind_functions":
                ai_message = parse_flotorch_response_bind_functions(response)
            else:
                # Default to tools parsing for any other case
                ai_message = parse_flotorch_response_bind_tools(response)
            
            return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except Exception as e:
            logger.error(f"Error in FlotorchLangchainLLM._agenerate: {e}")
            raise

    def bind(self, **kwargs: Any) -> "FlotorchLangChainLLM":
        """Bind arguments to the model."""
        # Create a new instance
        new_instance = self.__class__(
            model_id=self._model_id,
            api_key=self._api_key,
            base_url=self._base_url,
            temperature=self._temperature,
        )

        if 'functions' in kwargs:
            # LangChain create_openai_functions_agent uses this
            functions = kwargs['functions']
            new_instance._tools = [
                {
                    "type": "function",
                    "function": func
                }
                for func in functions
            ]
            new_instance._binding_type = "bind_functions"  
        
        return new_instance

    def bind_tools(
        self,
        tools: List[Union[BaseTool, Dict[str, Any]]],
        **kwargs: Any,
    ) -> "FlotorchLangChainLLM":
        """Bind tools to the model for tool calling.
        LangGraph create_react_agent uses this method.
        """
        converted_tools = convert_tools_to_format(tools)

        new_instance = self.__class__(
            model_id=self._model_id,
            api_key=self._api_key,
            base_url=self._base_url,
            temperature=self._temperature,
            **kwargs
        )

        new_instance._tools = converted_tools
        new_instance._binding_type = "bind_tools"  
        return new_instance

    @staticmethod
    def _prepare_extra_body(stop: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Prepare additional body parameters for Flotorch API calls.

        Args:
            stop: Optional stop sequences.
            **kwargs: Extra parameters.

        Returns:
            Dict of parameters to send to the API.
        """
        extra_body = {}
        if stop:
            extra_body["stop"] = stop
        extra_body.update(kwargs)
        return extra_body


    def with_structured_output(self, schema, **kwargs):
        """
        Custom implementation of with_structured_output for FlotorchLangChainLLM.
        Handles both Pydantic models and JSON schemas dynamically.
        """
        from langchain_core.runnables import RunnableLambda
        from pydantic import BaseModel
        
        is_pydantic_schema = isinstance(schema, type) and issubclass(schema, BaseModel)
        is_json_schema = isinstance(schema, dict) and schema.get("type") == "object"
        
        def generate_structured(messages, **kwargs):
            result = self._generate(messages, **kwargs)
            if result.generations:
                structured_response = self._parse_structured_output(result.generations[0].message, schema)
                return structured_response
            return None
        
        llm_runnable = RunnableLambda(generate_structured)
        
        if is_pydantic_schema:
            return llm_runnable
        elif is_json_schema:
            def ensure_dict_output(response):
                if hasattr(response, 'model_dump'):
                    return response.model_dump()
                return response
            
            return llm_runnable | RunnableLambda(ensure_dict_output)
        else:
            return llm_runnable
    
    def _parse_structured_output(self, response, schema):
        """Parse the response to match the structured schema."""
        from pydantic import BaseModel
        import json
        
        try:
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, dict) and 'content' in response:
                content = response['content']
            else:
                content = str(response)
            
            is_pydantic_schema = isinstance(schema, type) and issubclass(schema, BaseModel)
            is_json_schema = isinstance(schema, dict) and schema.get("type") == "object"
 
            try:
                parsed = json.loads(content)
            except:
                if is_pydantic_schema:
                    if hasattr(schema, 'model_fields'):
                        fields = schema.model_fields
                        first_field = list(fields.keys())[0] if fields else 'response'
                        field_values = {first_field: content}
                        return schema(**field_values)  
                elif is_json_schema:
                    properties = schema.get("properties", {})
                    first_property = list(properties.keys())[0] if properties else 'response'
                    return {first_property: content}
                return {"response": content}  
            
            if is_pydantic_schema:
                return schema(**parsed)
            elif is_json_schema:
                return parsed  
            return parsed 
            
        except Exception as e:
            logger.error(f"Error parsing structured output: {e}")
            if is_pydantic_schema:
                if hasattr(schema, 'model_fields'):
                    fields = schema.model_fields
                    first_field = list(fields.keys())[0] if fields else 'response'
                    return schema(**{first_field: str(response)})
            return {"response": str(response)} 