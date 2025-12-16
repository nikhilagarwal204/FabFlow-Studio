"""FIBO API Client for image generation.

Handles communication with Bria's FIBO API including:
- Text-to-image generation
- Async polling for results
- Error handling and retries
"""
import asyncio
import httpx
from typing import Optional
from pydantic import BaseModel

from app.config import get_settings


class FIBOError(Exception):
    """Base exception for FIBO API errors."""
    
    def __init__(self, message: str, code: str = "FIBO_ERROR", retryable: bool = True):
        self.message = message
        self.code = code
        self.retryable = retryable
        super().__init__(message)


class FIBOTimeoutError(FIBOError):
    """Raised when FIBO API polling times out."""
    
    def __init__(self, message: str = "FIBO API request timed out"):
        super().__init__(message, code="FIBO_TIMEOUT", retryable=True)


class FIBOAPIError(FIBOError):
    """Raised when FIBO API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message, code="FIBO_API_ERROR", retryable=status_code != 401)


class FIBOGenerationResult(BaseModel):
    """Result from FIBO image generation."""
    
    request_id: str
    image_url: str
    status: str = "completed"


class FIBOClient:
    """Client for interacting with Bria's FIBO API.
    
    Handles text-to-image generation with async polling for results.
    
    Attributes:
        BASE_URL: Base URL for FIBO API endpoints.
        POLL_INTERVAL: Seconds between status polls.
        MAX_POLL_TIME: Maximum seconds to wait for completion.
    """
    
    BASE_URL = "https://engine.prod.bria-api.com"
    POLL_INTERVAL = 2  # seconds between polls (per Requirement 7.2)
    MAX_POLL_TIME = 60  # maximum polling time in seconds
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize FIBO client.
        
        Args:
            api_key: FIBO API key. If not provided, reads from settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.bria_api_key
        if not self.api_key:
            raise FIBOError(
                "FIBO API key not configured",
                code="FIBO_CONFIG_ERROR",
                retryable=False
            )
        self.headers = {
            "api_token": self.api_key,
            "Content-Type": "application/json"
        }

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        num_results: int = 1
    ) -> FIBOGenerationResult:
        """Generate an image using FIBO text-to-image API.
        
        Sends a request to the FIBO API and polls for the result.
        
        Args:
            prompt: Text description of the image to generate.
            aspect_ratio: Aspect ratio for the image (9:16, 1:1, 16:9).
            num_results: Number of images to generate (default 1).
            
        Returns:
            FIBOGenerationResult with request_id and image_url.
            
        Raises:
            FIBOAPIError: If the API returns an error response.
            FIBOTimeoutError: If polling exceeds MAX_POLL_TIME.
            FIBOError: For other errors.
        """
        endpoint = f"{self.BASE_URL}/v1/text-to-image/base/2.3"
        
        payload = {
            "prompt": prompt,
            "num_results": num_results,
            "aspect_ratio": aspect_ratio,
            "sync": True  # Use sync mode for simpler response handling
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    endpoint,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 401:
                    raise FIBOAPIError(
                        "Invalid FIBO API key",
                        status_code=401
                    )
                
                if response.status_code != 200 and response.status_code != 202:
                    raise FIBOAPIError(
                        f"FIBO API error: {response.text}",
                        status_code=response.status_code
                    )
                
                data = response.json()
                
                # Handle sync response - result is returned directly
                result = data.get("result")
                if result and len(result) > 0:
                    # API returns 'urls' array, not 'url'
                    urls = result[0].get("urls")
                    if urls and len(urls) > 0:
                        return FIBOGenerationResult(
                            request_id=result[0].get("uuid", "sync-request"),
                            image_url=urls[0]
                        )
                
                # Fallback to async polling if sync didn't return result directly
                request_id = data.get("sid")
                status_url = data.get("status_url")
                
                if status_url:
                    image_url = await self.poll_status(request_id or "unknown", status_url, client)
                    return FIBOGenerationResult(
                        request_id=request_id or "unknown",
                        image_url=image_url
                    )
                
                raise FIBOAPIError(
                    f"Invalid response from FIBO API: {data}"
                )
                
            except httpx.TimeoutException:
                raise FIBOTimeoutError("Request to FIBO API timed out")
            except httpx.RequestError as e:
                raise FIBOError(f"Network error communicating with FIBO API: {str(e)}")

    async def poll_status(
        self,
        request_id: str,
        status_url: str,
        client: Optional[httpx.AsyncClient] = None
    ) -> str:
        """Poll FIBO status endpoint until completion.
        
        Polls every POLL_INTERVAL seconds until the request completes
        or MAX_POLL_TIME is exceeded.
        
        Args:
            request_id: The request ID from the initial API call.
            status_url: The status URL to poll.
            client: Optional httpx client to reuse.
            
        Returns:
            The URL of the generated image.
            
        Raises:
            FIBOTimeoutError: If polling exceeds MAX_POLL_TIME.
            FIBOAPIError: If the API returns an error status.
        """
        should_close_client = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=30.0)
        
        try:
            elapsed_time = 0
            
            while elapsed_time < self.MAX_POLL_TIME:
                await asyncio.sleep(self.POLL_INTERVAL)
                elapsed_time += self.POLL_INTERVAL
                
                try:
                    response = await client.get(
                        status_url,
                        headers=self.headers
                    )
                    
                    if response.status_code != 200:
                        raise FIBOAPIError(
                            f"Status check failed: {response.text}",
                            status_code=response.status_code
                        )
                    
                    data = response.json()
                    status = data.get("status", "").lower()
                    
                    if status == "completed":
                        result = data.get("result", [])
                        if result and len(result) > 0:
                            # API returns 'urls' array, not 'url'
                            urls = result[0].get("urls")
                            if urls and len(urls) > 0:
                                return urls[0]
                        raise FIBOAPIError(
                            "Completed but no image URL in response"
                        )
                    
                    elif status == "failed":
                        error_msg = data.get("error", "Unknown error")
                        raise FIBOAPIError(f"Image generation failed: {error_msg}")
                    
                    # Status is still processing, continue polling
                    
                except httpx.TimeoutException:
                    # Timeout on status check, continue polling
                    continue
                except httpx.RequestError as e:
                    raise FIBOError(f"Network error during status check: {str(e)}")
            
            # Exceeded max poll time
            raise FIBOTimeoutError(
                f"FIBO request {request_id} did not complete within {self.MAX_POLL_TIME} seconds"
            )
        finally:
            if should_close_client:
                await client.aclose()
