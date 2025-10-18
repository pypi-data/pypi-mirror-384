"""
Decorator builders for securing MCP tools, prompts, and retrieval functions.

Provides a unified decorator factory that wraps the original MCP decorators
with conditional security guards.
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional

try:
    from mcp import tool as base_tool, prompt as base_prompt, retrieval as base_retrieval
except ImportError:
    # Fallback for testing or when mcp is not available
    def base_tool(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator
    
    def base_prompt(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator
    
    def base_retrieval(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

from .filters import sanitize_prompt
from .allowlist import validate_host
from .confirm import maybe_queue, PendingApproval
from .logchain import log_event


def _secure(base_deco: Callable) -> Callable:
    """
    Create a security-enhanced decorator factory from a base MCP decorator.
    
    Args:
        base_deco: The original MCP decorator (tool, prompt, or retrieval)
        
    Returns:
        A decorator factory that applies security guards conditionally
    """
    def builder(*dargs, confirm: bool = False, **dkwargs) -> Callable:
        """
        Build a secured decorator with optional confirmation requirement.
        
        Args:
            *dargs: Positional arguments passed to base decorator
            confirm: Whether to require approval for destructive actions
            **dkwargs: Keyword arguments passed to base decorator
            
        Returns:
            A decorator that applies security guards to the wrapped function
        """
        def inner(fn: Callable) -> Callable:
            @base_deco(*dargs, **dkwargs)
            @wraps(fn)
            def wrapper(*args, **kwargs) -> Any:
                # Extract SMCP configuration injected by runtime adapter
                cfg = kwargs.pop("_smcp_cfg", {})
                
                # Input sanitization guard (activates if SAFE_RE configured)
                if cfg.get("SAFE_RE"):
                    prompt_text = kwargs.get("prompt", "")
                    if prompt_text:
                        sanitize_prompt(prompt_text, cfg)
                
                # Host allowlist guard (activates if ALLOWED_HOSTS configured)
                if cfg.get("ALLOWED_HOSTS"):
                    target_host = kwargs.get("target", "")
                    if target_host:
                        validate_host(target_host, cfg)
                
                # Destructive action confirmation guard
                if confirm and maybe_queue(fn, args, kwargs, cfg):
                    raise PendingApproval(f"Action {fn.__name__} queued for approval")
                
                # Execute the wrapped function
                result = fn(*args, **kwargs)
                
                # Audit logging guard (activates if LOG_PATH configured)
                if cfg.get("LOG_PATH"):
                    log_event(fn.__name__, args, kwargs, result, cfg)
                
                return result
            return wrapper
        return inner
    return builder


# Create secured versions of MCP decorators
tool = _secure(base_tool)
prompt = _secure(base_prompt) 
retrieval = _secure(base_retrieval)
