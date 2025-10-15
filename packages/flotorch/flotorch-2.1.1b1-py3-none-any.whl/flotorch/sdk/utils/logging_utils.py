import logging
import sys
import inspect
from typing import Optional, List, Dict, Any

# ANSI color codes for simple, dependency-free coloring
_RESET = "\033[0m"
_COLOR_CYAN = "\033[36m"
_COLOR_YELLOW = "\033[33m"
_COLOR_MAGENTA = "\033[35m"
_COLOR_GREEN = "\033[32m"
_COLOR_BLUE = "\033[34m"
_COLOR_DIM = "\033[2m"

# Try enabling Windows ANSI support (no-op if unavailable)
try:
    import colorama
    colorama.just_fix_windows_console()
except Exception:  # noqa: BLE001 - best-effort only
    pass


class _CategoryColorFormatter(logging.Formatter):
    """Colorize only the message part based on logger category or content.
    Does not alter existing messages; only wraps them with ANSI color codes for console output.
    """

    def __init__(self, fmt: str, datefmt: Optional[str] = None):
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        original_msg = record.msg
        try:
            message_text = str(original_msg)
            color_prefix = ""

            logger_name: str = record.name or ""
            # Category-based coloring
            if logger_name.startswith("flotorch.sdk.llm"):
                if "Tool Response:" in message_text or "Tool Call:" in message_text:
                    color_prefix = _COLOR_YELLOW  # Tool responses and tool calls only
                else:
                    color_prefix = _COLOR_CYAN  # LLM request/response
            elif logger_name.startswith("flotorch.sdk.session"):
                color_prefix = _COLOR_MAGENTA   # Session operations
            elif logger_name.startswith("flotorch.sdk.memory"):
                color_prefix = _COLOR_GREEN     # Memory/vectorstore
            elif logger_name.startswith("flotorch.sdk.utils.http_utils"):
                color_prefix = _COLOR_BLUE      # HTTP debug (if enabled)

            if color_prefix and sys.stdout.isatty():
                record.msg = f"{color_prefix}{message_text}{_RESET}"
            else:
                record.msg = original_msg

            return super().format(record)
        finally:
            record.msg = original_msg


# Global flag to track if logging is configured
_logging_configured = False

def _configure_logging_once():
    """Configure logging once globally."""
    global _logging_configured
    if not _logging_configured:
        # Configure root logger (best-effort). If another lib configured handlers,
        # basicConfig may be ignored, so we also enforce levels and handlers below.
        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
        except Exception:
            pass

        # Swap formatter with colorizing formatter on existing stream handlers (console only)
        root_logger = logging.getLogger()
        # Ensure root logger is at least INFO
        try:
            if root_logger.level > logging.INFO or root_logger.level == logging.NOTSET:
                root_logger.setLevel(logging.INFO)
        except Exception:
            pass

        # Ensure we have a stdout stream handler and set handler levels to INFO
        has_stdout_handler = False
        for h in list(root_logger.handlers):
            if isinstance(h, logging.StreamHandler):
                try:
                    # Mark if this handler writes to stdout
                    if getattr(h, 'stream', None) is sys.stdout:
                        has_stdout_handler = True
                except Exception:
                    pass
                try:
                    h.setFormatter(_CategoryColorFormatter(
                        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    ))
                except Exception:  # noqa: BLE001 - best-effort only
                    pass
                try:
                    # Ensure handler will emit INFO-level logs
                    h.setLevel(logging.INFO)
                except Exception:
                    pass

        if not has_stdout_handler:
            try:
                stdout_handler = logging.StreamHandler(sys.stdout)
                stdout_handler.setLevel(logging.INFO)
                stdout_handler.setFormatter(_CategoryColorFormatter(
                    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))
                root_logger.addHandler(stdout_handler)
            except Exception:
                pass

        # Suppress specific loggers completely
        logging.getLogger('httpx').setLevel(logging.ERROR)
        logging.getLogger('google_adk').setLevel(logging.ERROR)
        logging.getLogger('google_adk.google.adk.tools.base_authenticated_tool').setLevel(logging.ERROR)
        # Suppress LiteLLM noisy logs used by CrewAI integrations
        for _name in ('litellm', 'LiteLLM'):
            _logger = logging.getLogger(_name)
            _logger.setLevel(logging.ERROR)
            _logger.propagate = False

        _logging_configured = True


def _get_caller_logger() -> logging.Logger:
    """
    Automatically get the logger for the calling module.

    Returns:
        Logger instance for the calling module
    """
    # Configure logging once
    _configure_logging_once()

    # Get the calling frame (the module that called the logging function)
    # We need to go back 2 frames: 1 for the logging function, 1 for the actual caller
    caller_frame = inspect.currentframe().f_back.f_back

    # Get the module name from the calling frame
    if caller_frame and hasattr(caller_frame, 'f_globals'):
        module_name = caller_frame.f_globals.get('__name__', 'unknown')
    else:
        module_name = 'unknown'

    # Get logger for this module
    return logging.getLogger(module_name)


def log_object_creation(class_name: str, **kwargs) -> None:
    """
    Log object creation with key parameters.

    Args:
        class_name: Name of the class being created
        **kwargs: Key parameters to include in log
    """
    logger = _get_caller_logger()
    params = []
    for key, value in kwargs.items():
        # Mask sensitive information
        if any(sensitive in key.lower() for sensitive in ['key', 'token', 'password', 'secret']):
            value = '***'
        params.append(f"{key}={value}")

    param_str = ', '.join(params) if params else 'no parameters'
    logger.info(f"{class_name} initialized ({param_str})")


def log_info(message: str) -> None:
    """
    Log informational messages in a consistent format.

    Args:
        message: Information message to log
    """
    logger = _get_caller_logger()
    logger.info(message)


def log_error(operation: str, error: Exception) -> None:
    """
    Log errors in a consistent format.

    Args:
        operation: Description of the operation that failed
        error: The exception that occurred
    """
    logger = _get_caller_logger()
    logger.error(f"{operation} failed: {type(error).__name__}: {str(error)}")


def log_warning(message: str) -> None:
    """
    Log warnings in a consistent format.

    Args:
        message: Warning message
    """
    logger = _get_caller_logger()
    logger.warning(message)


def log_llm_request(model: str, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None, **kwargs) -> None:
    """
    Log LLM request details in a structured format.

    Args:
        model: Model identifier
        messages: List of messages being sent
        tools: Optional tools/functions available
        **kwargs: Additional parameters
    """
    logger = _get_caller_logger()

    # Extract system prompt, user query, and tool responses
    system_prompt = None
    user_query = None
    tool_responses = []

    # Get the latest user message (most recent interaction)
    for msg in reversed(messages):
        if msg.get("role") == "user" and user_query is None:
            content = msg.get("content", "")
            user_query = content[:300] + "..." if len(content) > 300 else content
            break

    # Get system prompt (usually the first message)
    for msg in messages:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            system_prompt = content[:200] + "..." if len(content) > 200 else content
            break

    # Extract tool responses only if the LAST assistant message in this request contains tool calls
    last_assistant_idx = -1
    for idx, msg in enumerate(messages):
        if msg.get("role") == "assistant":
            last_assistant_idx = idx

    if last_assistant_idx != -1:
        last_assistant_msg = messages[last_assistant_idx]
        last_tool_call_id_to_name: Dict[str, str] = {}
        if last_assistant_msg.get("tool_calls"):
            for tool_call in last_assistant_msg.get("tool_calls", []):
                tool_call_id = tool_call.get("id")
                tool_name = tool_call.get("function", {}).get("name")
                if tool_call_id and tool_name:
                    last_tool_call_id_to_name[tool_call_id] = tool_name

        # If the last assistant message had tool calls, log only matching tool responses that come after it
        if last_tool_call_id_to_name:
            for msg in messages[last_assistant_idx + 1:]:
                if msg.get("role") == "tool":
                    tool_call_id = msg.get("tool_call_id")
                    if tool_call_id in last_tool_call_id_to_name:
                        tool_name = last_tool_call_id_to_name.get(tool_call_id) or msg.get("name") or tool_call_id
                        tool_content = msg.get("content", "")
                        if len(tool_content) > 200:
                            tool_content = tool_content[:200] + "..."
                        tool_responses.append(f"{tool_name}: {tool_content}")

    # Format tools information
    tools_info = ""
    if tools:
        tool_names = [tool.get("function", {}).get("name", "unknown") for tool in tools if "function" in tool]
        tools_info = f", tools: [{', '.join(tool_names)}]" if tool_names else ""

    logger.info(f"LLM Request - model: {model}, messages-length: {len(messages)}{tools_info}")
    if user_query:
        logger.info(f"User Query: {user_query}")
    if tool_responses:
        for tool_response in tool_responses:
            logger.info(f"Tool Response: {tool_response}")
    if system_prompt:
        logger.debug(f"System Prompt: {system_prompt}")


def log_llm_response(model: str, content: str, tool_calls: Optional[List] = None, usage: Optional[Dict] = None, is_final_response: bool = False) -> None:
    """
    Log LLM response details in a structured format.

    Args:
        model: Model identifier
        content: Response content
        tool_calls: Optional tool calls made
        usage: Token usage information
        is_final_response: Whether this is the final response to the user
    """
    logger = _get_caller_logger()

    # Format tool calls with parameters
    tool_calls_info = ""
    if tool_calls:
        tool_details = []
        for tc in tool_calls:
            tool_name = tc.get("function", {}).get("name", "unknown")
            tool_args = tc.get("function", {}).get("arguments", "")

            # Try to parse and format arguments
            try:
                import json
                if isinstance(tool_args, str):
                    args_dict = json.loads(tool_args)
                else:
                    args_dict = tool_args

                # Format arguments nicely
                args_str = ", ".join([f"{k}={v}" for k, v in args_dict.items()])
                tool_details.append(f"{tool_name}({args_str})")
            except:
                # Fallback if parsing fails
                tool_details.append(f"{tool_name}({tool_args})")

        tool_calls_info = f", tool_calls: [{', '.join(tool_details)}]"
        
        # Log each tool call explicitly in yellow
        for tool_detail in tool_details:
            logger.info(f"Tool Call: {tool_detail}")

    # Format usage info
    usage_info = ""
    if usage:
        usage_info = f", tokens: {usage.get('total_tokens', 0)} ({usage.get('prompt_tokens', 0)}+{usage.get('completion_tokens', 0)})"

    logger.info(f"LLM Response - model: {model}{tool_calls_info}{usage_info}")

    # Always log content for final responses, or if there's meaningful content
    if is_final_response and content.strip():
        logger.info(f"Final Response: {content}")
    elif content.strip() and not tool_calls:
        # Log content when there are no tool calls (direct response)
        response_preview = content[:300] + "..." if len(content) > 300 else content
        logger.info(f"Response Content: {response_preview}")


def log_session_operation(operation: str, session_uid: Optional[str] = None, **params) -> None:
    """
    Log session operations in a structured format.

    Args:
        operation: Operation being performed (create, get, update, delete)
        session_uid: Session UID if applicable
        **params: Additional operation parameters
    """
    logger = _get_caller_logger()

    # Filter out sensitive information
    safe_params = {}
    for key, value in params.items():
        if any(sensitive in key.lower() for sensitive in ['key', 'token', 'password', 'secret']):
            safe_params[key] = '***'
        else:
            safe_params[key] = value

    uid_info = f" (uid: {session_uid})" if session_uid else ""
    params_info = f" - {safe_params}" if safe_params else ""
    logger.info(f"Session {operation.title()}{uid_info}{params_info}")


def log_memory_operation(operation: str, provider: str, memory_id: Optional[str] = None, **params) -> None:
    """
    Log memory operations in a structured format.

    Args:
        operation: Operation being performed (add, get, update, delete, search)
        provider: Memory provider name
        memory_id: Memory ID if applicable
        **params: Additional operation parameters
    """
    logger = _get_caller_logger()

    # Filter out sensitive information and large data
    safe_params = {}
    for key, value in params.items():
        if any(sensitive in key.lower() for sensitive in ['key', 'token', 'password', 'secret']):
            safe_params[key] = '***'
        elif key == 'messages' and isinstance(value, list):
            safe_params[key] = f"{len(value)} messages"
        elif isinstance(value, str) and len(value) > 100:
            safe_params[key] = value[:100] + "..."
        else:
            safe_params[key] = value

    id_info = f" (id: {memory_id})" if memory_id else ""
    params_info = f" - {safe_params}" if safe_params else ""
    logger.info(f"Memory {operation.title()} [{provider}]{id_info}{params_info}")


def log_vectorstore_operation(operation: str, vectorstore_id: str, **params) -> None:
    """
    Log vector store operations in a structured format.

    Args:
        operation: Operation being performed (search)
        vectorstore_id: Vector store identifier
        **params: Additional operation parameters
    """
    logger = _get_caller_logger()

    # Filter out sensitive information
    safe_params = {}
    for key, value in params.items():
        if any(sensitive in key.lower() for sensitive in ['key', 'token', 'password', 'secret']):
            safe_params[key] = '***'
        elif key == 'query' and isinstance(value, str) and len(value) > 100:
            safe_params[key] = value[:100] + "..."
        else:
            safe_params[key] = value

    params_info = f" - {safe_params}" if safe_params else ""
    logger.info(f"VectorStore {operation.title()} [{vectorstore_id}]{params_info}")


def log_http_request(method: str, url: str, status_code: Optional[int] = None, duration: Optional[float] = None) -> None:
    """
    Log HTTP requests in a structured format.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL (sensitive parts will be masked)
        status_code: Response status code
        duration: Request duration in seconds
    """
    logger = _get_caller_logger()

    # Mask sensitive parts of URL
    masked_url = url
    if 'api_key=' in url:
        masked_url = url.split('api_key=')[0] + 'api_key=***'

    status_info = f" -> {status_code}" if status_code is not None else ""
    duration_info = f" ({duration:.3f}s)" if duration is not None else ""
    logger.debug(f"HTTP {method} {masked_url}{status_info}{duration_info}") 