"""
RunPod API client for AnotiAI PII detection services.
"""

import json
import logging
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    APIError, AuthenticationError, NetworkError, 
    ValidationError, RateLimitError, ServerError
)
from .config import ClientConfig

logger = logging.getLogger(__name__)


class RunPodAPIClient:
    """Client for communicating with RunPod serverless endpoints."""
    
    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize the API client."""
        if config is None:
            config = ClientConfig.from_env()
        
        self.config = config
        self.session = self._create_session()
        
        # Validate that the RunPod-specific configuration is present
        if not self.config.runpod_api_key or not self.config.endpoint_id:
            raise ValidationError(
                "RunPod API key and endpoint ID are required. "
                "Set RUNPOD_API_KEY and ANOTIAI_ENDPOINT_ID environment variables "
                "or provide them in the configuration."
            )
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retries."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        # Set default headers for RunPod API
        session.headers.update({
            "Content-Type": "application/json"
        })
        
        return session
    
    def _make_request(self, action: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the RunPod endpoint."""
        url = f"{self.config.base_url}/{self.config.endpoint_id}/runsync"
        
        payload = {
            "input": {
                "action": action,
                **kwargs
            }
        }
        
        # Add RunPod API key to headers for this request
        headers = {
            "Authorization": f"Bearer {self.config.runpod_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.debug(f"Making request to {url} with action: {action}")
            response = self.session.post(
                url, 
                json=payload, 
                headers=headers,
                timeout=self.config.timeout
            )
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid RunPod API key or unauthorized access to the endpoint.")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 500:
                raise ServerError(f"Server error: {response.status_code}")
            elif response.status_code >= 400:
                raise APIError(f"Client error: {response.status_code}", response.status_code)
            
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("status") == "FAILED":
                error_msg = result.get("error", "Unknown error")
                raise APIError(f"Request failed: {error_msg}")

            if "output" in result:
                # The handler now returns an 'error' field at the top level of the output on failure
                if "error" in result["output"]:
                    raise APIError(result["output"]["error"])
                return result["output"]
            else:
                return result
                
        except requests.exceptions.Timeout:
            raise NetworkError(f"Request timeout after {self.config.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection error. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            raise APIError("Invalid response format from server")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the API endpoint. Does not require a user API key."""
        return self._make_request("health")
    
    def get_model_version(self, api_key: str) -> Dict[str, Any]:
        """Get the model version information."""
        return self._make_request("model_version", api_key=api_key)
    
    def mask_text(self, text: str, api_key: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Mask PII in the provided text.
        
        Args:
            text: The text to process
            api_key: The user's JWT API key for authentication and usage tracking.
            confidence_threshold: Minimum confidence threshold for PII detection
            
        Returns:
            A dictionary containing the masked text, PII map, and usage data.
        """
        if not text or not isinstance(text, str):
            raise ValidationError("Text must be a non-empty string")
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("api_key must be a non-empty string")
        if not 0 <= confidence_threshold <= 1:
            raise ValidationError("Confidence threshold must be between 0 and 1")
        
        return self._make_request(
            "mask",
            api_key=api_key,
            text=text,
            confidence_threshold=confidence_threshold
        )
    
    def unmask_text(self, masked_text: str, pii_map: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """
        Unmask PII in the provided text.
        
        Args:
            masked_text: The masked text
            pii_map: The PII mapping dictionary
            api_key: The user's JWT API key for authentication and usage tracking.
            
        Returns:
            A dictionary containing the unmasked text and usage data.
        """
        if not masked_text or not isinstance(masked_text, str):
            raise ValidationError("Masked text must be a non-empty string")
        if not pii_map or not isinstance(pii_map, dict):
            raise ValidationError("PII map must be a non-empty dictionary")
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("api_key must be a non-empty string")
        
        return self._make_request(
            "unmask",
            api_key=api_key,
            masked_text=masked_text,
            pii_map=pii_map
        )
    
    def detect_pii(self, text: str, api_key: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Detect PII in text without masking.
        
        Args:
            text: The text to analyze
            api_key: The user's JWT API key for authentication and usage tracking.
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Dictionary with detection results and usage data.
        """
        # The backend handler doesn't have a dedicated 'detect' action,
        # so we call 'mask' and the handler returns the necessary info.
        # This is inefficient but works without a backend change.
        # A future optimization would be a dedicated 'detect' action.
        return self._make_request(
            "mask",
            api_key=api_key,
            text=text,
            confidence_threshold=confidence_threshold
        )
