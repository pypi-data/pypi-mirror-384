"""
AnotiAI PII Masker - Cloud-powered PII detection and masking

A lightweight Python package for detecting and masking personally identifiable information (PII)
in text using cloud-based AI models with optional local fallback.

Examples:
    Basic usage with cloud inference:
        >>> from anotiai_pii_masker import WhosePIIGuardian
        >>> guardian = WhosePIIGuardian(api_key="your_key", endpoint_id="your_endpoint")
        >>> masked_text, pii_map = guardian.mask_text("My email is john@example.com")
        
    Using environment variables:
        >>> import os
        >>> os.environ["ANOTI_API_KEY"] = "your_key"
        >>> os.environ["ANOTI_ENDPOINT_ID"] = "your_endpoint"
        >>> guardian = WhosePIIGuardian()
        
    Local mode (requires heavy dependencies):
        >>> guardian = WhosePIIGuardian(local_mode=True)
"""

from .guardian import WhosePIIGuardian

# Import client components if available
try:
    from .client import ClientConfig, APIError, AuthenticationError, NetworkError, ValidationError
    _client_available = True
except ImportError:
    _client_available = False
    ClientConfig = None
    APIError = None
    AuthenticationError = None
    NetworkError = None
    ValidationError = None

__version__ = "1.0.0"
__author__ = "AnotiAI"
__email__ = "anotiai@anotiai.com"

# Main exports
__all__ = [
    "WhosePIIGuardian",
]

# Add client exports if available
if _client_available:
    __all__.extend([
        "ClientConfig",
        "APIError", 
        "AuthenticationError",
        "NetworkError", 
        "ValidationError"
    ])

# Convenience function for quick setup
def create_guardian(
    api_key: str = None,
    endpoint_id: str = None,
    local_mode: bool = False,
    **kwargs
) -> WhosePIIGuardian:
    """
    Convenience function to create a PII Guardian instance.
    
    Args:
        api_key: RunPod API key (or set ANOTI_API_KEY env var)
        endpoint_id: RunPod endpoint ID (or set ANOTI_ENDPOINT_ID env var)
        local_mode: Use local inference instead of cloud
        **kwargs: Additional arguments for WhosePIIGuardian
        
    Returns:
        Configured WhosePIIGuardian instance
    """
    return WhosePIIGuardian(
        api_key=api_key,
        endpoint_id=endpoint_id,
        local_mode=local_mode,
        **kwargs
    )
