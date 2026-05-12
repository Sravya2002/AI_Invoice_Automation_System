"""
Standardized error handling and retry utilities for the automation agent.
"""

import time
import functools
from dataclasses import dataclass, asdict
from typing import Optional, List, Callable, Any, Dict


@dataclass
class ErrorDetail:
    """Standardized error object across all tools."""
    error_code: str
    message: str
    step_name: str
    recommendation: str
    screenshot_path: Optional[str] = None
    recoverable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def retry_on_failure(max_retries: int = 2, backoff: int = 2):
    """
    Decorator to retry a function if it returns (False, result_dict) or raises an exception.
    
    Args:
        max_retries: Number of retry attempts.
        backoff: Seconds to wait between retries.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            # Extract logger if available in the first argument (self)
            logger = getattr(args[0], 'logger', None) if args else None

            for attempt in range(max_retries + 1):
                try:
                    success, result = func(*args, **kwargs)
                    if success:
                        return True, result
                    
                    last_error = result.get("error", "Unknown error")
                    if logger:
                        logger.log_warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {last_error}"
                        )
                except Exception as exc:
                    last_error = str(exc)
                    if logger:
                        logger.log_warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} raised exception in {func.__name__}: {last_error}"
                        )

                if attempt < max_retries:
                    time.sleep(backoff * (attempt + 1))
                else:
                    break
            
            return False, {"error": f"Max retries reached. Last error: {last_error}"}
        return wrapper
    return decorator


def categorize_error(exception: Exception) -> str:
    """Categorize Playwright/Python errors into standardized codes."""
    exc_str = str(exception).lower()
    if "timeout" in exc_str:
        return "TIMEOUT_ERROR"
    if "stale element" in exc_str or "element not found" in exc_str:
        return "UI_LAYOUT_CHANGED"
    if "login" in exc_str or "unauthorized" in exc_str:
        return "AUTH_FAILURE"
    if "download" in exc_str:
        return "DOWNLOAD_MISSING"
    return "UNKNOWN_ERROR"


def get_recommendation(error_code: str) -> str:
    """Provide actionable recommendations for specific error codes."""
    recommendations = {
        "TIMEOUT_ERROR": "Check internet connectivity or increase the timeout_ms in config.",
        "UI_LAYOUT_CHANGED": "The portal layout might have changed. Verify selectors in config.py.",
        "AUTH_FAILURE": "Check username/password and ensure the account is not locked.",
        "DOWNLOAD_MISSING": "Ensure the invoice link is correct and the file is ready for download.",
        "UNKNOWN_ERROR": "Check logs for detailed stack trace."
    }
    return recommendations.get(error_code, "Review the error message and logs.")
