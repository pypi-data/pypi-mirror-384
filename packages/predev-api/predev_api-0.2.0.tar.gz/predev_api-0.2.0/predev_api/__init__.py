"""
predev_api - Python client for the Pre.dev Architect API

Generate comprehensive software specifications using AI.
"""

from .client import PredevAPI
from .exceptions import PredevAPIError, AuthenticationError, RateLimitError

__version__ = "0.1.1"
__all__ = ["PredevAPI", "PredevAPIError",
           "AuthenticationError", "RateLimitError"]
