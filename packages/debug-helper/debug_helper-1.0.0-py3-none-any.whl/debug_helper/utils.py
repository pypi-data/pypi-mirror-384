"""
Utility functions for the Debug Helper SDK.
"""

import os
import sys
import inspect
from typing import Optional, Tuple, Dict, Any
from pathlib import Path


def get_caller_info(skip_frames: int = 1) -> Tuple[str, int, str]:
    """
    Get information about the calling code.
    
    Args:
        skip_frames: Number of stack frames to skip
        
    Returns:
        Tuple of (file_name, line_number, function_name)
    """
    frame = inspect.currentframe()
    try:
        # Skip frames to get to the actual caller
        for _ in range(skip_frames + 1):
            frame = frame.f_back
            if frame is None:
                return "", 0, ""
        
        file_path = frame.f_code.co_filename
        file_name = os.path.basename(file_path) if file_path else ""
        line_number = frame.f_lineno
        function_name = frame.f_code.co_name
        
        return file_name, line_number, function_name
    finally:
        del frame


def sanitize_environment_variables(env_vars: Dict[str, str]) -> Dict[str, str]:
    """
    Remove sensitive information from environment variables.
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        Sanitized dictionary with sensitive values masked
    """
    sensitive_keys = {
        'password', 'secret', 'key', 'token', 'credential', 
        'auth', 'api_key', 'private', 'cert', 'ssl'
    }
    
    sanitized = {}
    for key, value in env_vars.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***MASKED***"
        else:
            sanitized[key] = value
    
    return sanitized


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def validate_log_file(file_path: Path, max_size_mb: int = 100) -> bool:
    """
    Validate a log file before upload.
    
    Args:
        file_path: Path to the log file
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        True if file is valid for upload
    """
    if not file_path.exists():
        return False
    
    if not file_path.is_file():
        return False
    
    # Check file size
    file_size = file_path.stat().st_size
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        return False
    
    return True


def extract_error_context(exception: Exception, context_lines: int = 3) -> Dict[str, Any]:
    """
    Extract contextual information from an exception.
    
    Args:
        exception: Python exception object
        context_lines: Number of context lines to include
        
    Returns:
        Dictionary with error context information
    """
    import traceback
    
    tb = exception.__traceback__
    if not tb:
        return {}
    
    # Get the last frame in the traceback
    while tb.tb_next:
        tb = tb.tb_next
    
    frame = tb.tb_frame
    code = frame.f_code
    
    context = {
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'file_name': os.path.basename(code.co_filename),
        'line_number': tb.tb_lineno,
        'function_name': code.co_name,
        'local_variables': {}
    }
    
    # Extract local variables (excluding sensitive ones)
    sensitive_vars = {'password', 'secret', 'key', 'token', 'credential'}
    for name, value in frame.f_locals.items():
        if not any(sensitive in name.lower() for sensitive in sensitive_vars):
            try:
                # Only include simple types to avoid serialization issues
                if isinstance(value, (str, int, float, bool, list, dict, tuple)):
                    context['local_variables'][name] = value
                else:
                    context['local_variables'][name] = str(type(value))
            except:
                context['local_variables'][name] = "<unable to serialize>"
    
    return context


class AutoIssueReporter:
    """
    Context manager for automatic issue reporting on exceptions.
    """
    
    def __init__(self, debug_logger, title_prefix: str = "Auto-reported"):
        self.debug_logger = debug_logger
        self.title_prefix = title_prefix
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            # Extract caller information
            file_name, line_number, function_name = get_caller_info(skip_frames=0)
            
            # Extract error context
            error_context = extract_error_context(exc_value)
            
            # Report the issue
            self.debug_logger.issue(
                title=f"{self.title_prefix}: {exc_type.__name__}",
                description=f"Automatically reported exception: {str(exc_value)}",
                file_name=file_name,
                line_number=line_number,
                function_name=function_name,
                exception=exc_value,
                environment_info=error_context
            )
        
        # Don't suppress the exception
        return False