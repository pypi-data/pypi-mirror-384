"""
Warning suppression utilities for Flotorch ADK components.
Centralizes all warning filters to keep main code clean.
"""

import warnings
import logging
import sys
import io
import os
from contextlib import contextmanager


def suppress_adk_warnings():
    """Suppress all ADK, MCP, and async related warnings."""
    # Suppress ALL MCP and async related warnings
    warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*BaseAuthenticatedTool.*")
    warnings.filterwarnings("ignore", message=".*auth_config.*")
    warnings.filterwarnings("ignore", message=".*authentication.*")
    warnings.filterwarnings("ignore", message=".*FunctionTool.*")
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)


def suppress_adk_logging():
    """Suppress logging from ADK components that generate noise."""
    # Suppress MCP async errors in logs
    logging.getLogger("mcp").setLevel(logging.CRITICAL)
    logging.getLogger("anyio").setLevel(logging.CRITICAL)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    logging.getLogger("streamable_http").setLevel(logging.CRITICAL)
    
    # Completely disable asyncio debug logging
    logging.getLogger().setLevel(logging.ERROR)


class SuppressOutput:
    """Context manager to completely suppress all output including print statements"""
    def __init__(self):
        self._original_stdout = None
        self._original_stderr = None
        
    def __enter__(self):
        # Redirect to null device (works on Windows and Unix)
        try:
            # Try to open null device
            self._devnull = open(os.devnull, 'w')
        except:
            # Fallback to StringIO if devnull fails
            self._devnull = io.StringIO()
            
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self._devnull
        sys.stderr = self._devnull
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        try:
            self._devnull.close()
        except:
            pass


def setup_adk_environment():
    """
    One-time setup to suppress all ADK-related warnings and noise.
    Call this once at the beginning of your ADK application.
    """
    suppress_adk_warnings()
    suppress_adk_logging()


# Auto-setup when imported (optional - can be disabled by setting env var)
if not os.getenv('FLOTORCH_NO_AUTO_SUPPRESS', False):
    setup_adk_environment() 