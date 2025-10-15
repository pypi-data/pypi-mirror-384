"""CrewAI LLM integration for Flotorch."""

import json
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from crewai.llms.base_llm import BaseLLM
from crewai.utilities.internal_instructor import InternalInstructor

from flotorch.sdk.llm import FlotorchLLM
from flotorch.sdk.utils.logging_utils import (
    log_error,
    log_object_creation)
from flotorch.sdk.utils.llm_utils import convert_pydantic_to_custom_json_schema


class FlotorchCrewAILLM(BaseLLM):
    """Flotorch LLM integration for CrewAI framework."""

    def __init__(
        self,
        model_id: str,
        api_key: str,
        base_url: str,
        temperature: Optional[float] = None,
        response_format: Optional[Any] = None,
        **kwargs
    ):
        """Initialize the FlotorchCrewAILLM.

        Args:
            model_id: The model identifier.
            api_key: API key for authentication.
            base_url: Base URL for the API.
            temperature: Temperature parameter for generation.
            response_format: Response format for structured output.
            **kwargs: Additional keyword arguments.
        """
        self.model = model_id
        self.temperature = temperature
        self.stop = []
        self.available_functions = {}
        self.response_format = response_format

        self.llm = FlotorchLLM(model_id, api_key, base_url)

        log_object_creation(
            "FlotorchCrewAILLM", model_id=model_id, base_url=base_url
        )
        self._patch_instructor_for_flotorch()

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        from_task: Optional[Any] = None,
        from_agent: Optional[Any] = None,
    ) -> Union[str, Any]:
        """Make a call to the LLM.

        Args:
            messages: Input messages as string or list of dictionaries.
            tools: Optional list of tools to use.
            callbacks: Optional list of callbacks.
            available_functions: Optional dictionary of available functions.
            from_task: Optional task context.
            from_agent: Optional agent context.

        Returns:
            The LLM response as string or tool calls.

        Raises:
            Exception: If the LLM call fails.
        """
        try:
            # Get parameters from CrewAI context if available
            temperature = self.temperature
            stop_words = self.stop.copy()
            
            # Extract parameters from agent if available
            if from_agent:
                if (
                    hasattr(from_agent, "temperature")
                    and from_agent.temperature is not None
                ):
                    temperature = from_agent.temperature
                if hasattr(from_agent, "stop") and from_agent.stop:
                    stop_words.extend(from_agent.stop)
            
            # Extract response format from task if available
            response_format = None
            if from_task:
                # Check for output_json in task
                if (
                    hasattr(from_task, "output_json")
                    and from_task.output_json
                ):
                    response = convert_pydantic_to_custom_json_schema(
                        from_task.output_json
                    )
                    response_format = response["response_format"]
                # Check for output_pydantic in task
                elif (
                    hasattr(from_task, "output_pydantic")
                    and from_task.output_pydantic
                ):
                    response = convert_pydantic_to_custom_json_schema(
                        from_task.output_pydantic
                    )
                    response_format = response["response_format"]

            # Fallback to instance response_format if set
            if (
                not response_format
                and self.response_format
                and isinstance(self.response_format, type)
                and issubclass(self.response_format, BaseModel)
            ):
                response = convert_pydantic_to_custom_json_schema(
                    self.response_format
                )
                response_format = response["response_format"]

            # Check if this is a ReAct format request (agent with tools)
            # If the system message contains ReAct format instructions,
            # don't use response_format
            is_react_format = False
            if isinstance(messages, list):
                is_react_format = any(
                    msg.get("role") == "system"
                    and (
                        "Thought:" in msg.get("content", "")
                        and "Action:" in msg.get("content", "")
                    )
                    for msg in messages
                )

            # Don't use response_format if this is a ReAct format request
            if is_react_format:
                response_format = None

            # Make the LLM call
            llm_kwargs = {
                "messages": messages,
                "response_format": response_format,
                "stop": stop_words,
            }
            
            # Only add temperature if it's not None
            if temperature is not None:
                llm_kwargs["temperature"] = temperature
            
            response = self.llm.invoke(**llm_kwargs)

            content = response.content or ""
            # Return the raw content string - CrewAI will handle the parsing
            return content

        except KeyError as e:
            log_error(
                f"KeyError in LLM call - missing key {e}. Messages: {messages}"
            )
            raise Exception(f"Missing required key in message: {e}")
        except Exception as e:
            log_error(f"LLM call failed: {str(e)}", error=e)
            raise Exception(f"FlotorchCrewaiLLM error: {str(e)}")


    def supports_function_calling(self) -> bool:
        """Check if the LLM supports function calling."""
        return True

    def supports_stop_words(self) -> bool:
        """Check if the LLM supports stop words."""
        return True
    
    def _patch_instructor_for_flotorch(self):
        """Patch CrewAI's InternalInstructor to use our FlotorchLLM."""
        try:
            if not hasattr(InternalInstructor, "_original_to_pydantic"):
                InternalInstructor._original_to_pydantic = (
                    InternalInstructor.to_pydantic
                )

            flotorch_llm = self

            def patched_to_pydantic(instructor_self):
                if (
                    hasattr(instructor_self, "llm")
                    and isinstance(instructor_self.llm, FlotorchCrewAILLM)
                ):
                    target_llm = instructor_self.llm
                    original_format = target_llm.response_format
                    target_llm.response_format = instructor_self.model

                    try:
                        response = target_llm.call([
                            {"role": "user", "content": instructor_self.content}
                        ])

                        if not response.strip().startswith("{"):
                            json_match = re.search(
                                r"\{.*\}", response, re.DOTALL
                            )
                            if json_match:
                                response = json_match.group(0)
                            else:
                                first_field = list(
                                    instructor_self.model.model_fields.keys()
                                )[0]
                                response = f'{{"{first_field}": "{response}"}}'

                        return instructor_self.model.model_validate(
                            json.loads(response)
                        )
                    finally:
                        target_llm.response_format = original_format
                else:
                    return instructor_self._original_to_pydantic()

            InternalInstructor.to_pydantic = patched_to_pydantic

        except Exception as e:
            log_error(f"Error applying InternalInstructor patch: {e}")


