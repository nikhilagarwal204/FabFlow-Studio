"""FIBO API Client for image generation.

Handles communication with Bria's FIBO API including:
- Text-to-image generation
- Async polling for results
- Error handling and retries
"""
import asyncio
import httpx
import logging
from functools import wraps
from typing import Optional, TypeVar, Callable, Any, TYPE_CHECKING
from pydantic import BaseModel

from app.config import get_settings

if TYPE_CHECKING:
    from app.fibo_translator import FIBOStructuredPromptV2

logger = logging.getLogger(__name__)

T = TypeVar("T")


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


class FIBORetryExhaustedError(FIBOError):
    """Raised when all retry attempts have been exhausted."""
    
    def __init__(self, message: str, last_error: Optional[Exception] = None):
        self.last_error = last_error
        super().__init__(message, code="FIBO_RETRY_EXHAUSTED", retryable=False)


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for adding retry logic with exponential backoff to async functions.
    
    Retries failed FIBO requests up to max_retries times with exponential backoff.
    Only retries errors that are marked as retryable.
    
    Args:
        max_retries: Maximum number of retry attempts (default 3 per Requirement 4.3).
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        
    Returns:
        Decorated function with retry logic.
        
    Requirements: 4.3
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    return await func(*args, **kwargs)
                except FIBOError as e:
                    last_error = e
                    
                    # Don't retry non-retryable errors (e.g., 401 auth errors)
                    if not e.retryable:
                        logger.warning(
                            f"FIBO request failed with non-retryable error: {e.message}"
                        )
                        raise
                    
                    # Don't retry if we've exhausted all attempts
                    if attempt >= max_retries:
                        logger.error(
                            f"FIBO request failed after {max_retries} retries: {e.message}"
                        )
                        raise FIBORetryExhaustedError(
                            f"Failed after {max_retries} retries: {e.message}",
                            last_error=e
                        )
                    
                    # Calculate exponential backoff delay
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"FIBO request failed (attempt {attempt + 1}/{max_retries + 1}): "
                        f"{e.message}. Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    
                except (httpx.TimeoutException, httpx.RequestError) as e:
                    last_error = e
                    
                    # Don't retry if we've exhausted all attempts
                    if attempt >= max_retries:
                        logger.error(
                            f"FIBO request failed after {max_retries} retries: {str(e)}"
                        )
                        raise FIBORetryExhaustedError(
                            f"Failed after {max_retries} retries: {str(e)}",
                            last_error=e
                        )
                    
                    # Calculate exponential backoff delay
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"FIBO request failed (attempt {attempt + 1}/{max_retries + 1}): "
                        f"{str(e)}. Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
            
            # Should not reach here, but just in case
            raise FIBORetryExhaustedError(
                f"Failed after {max_retries} retries",
                last_error=last_error
            )
        
        return wrapper
    return decorator


class FIBOGenerationResult(BaseModel):
    """Result from FIBO image generation."""
    
    request_id: str
    image_url: str
    status: str = "completed"


class FIBOStructuredPrompt(BaseModel):
    """Structured prompt format for FIBO API.
    
    Maps storyboard scene data to FIBO's structured-prompt-generate format.
    """
    
    scene_description: str
    camera: dict
    lighting: dict
    composition: dict
    style: dict
    
    @classmethod
    def from_scene_prompt(
        cls,
        prompt: str,
        camera_angle: str,
        lighting_style: str,
        subject_position: str,
        color_palette: Optional[list[str]] = None,
        mood: Optional[str] = None
    ) -> "FIBOStructuredPrompt":
        """Create a structured prompt from storyboard scene data.
        
        Maps storyboard FIBOPrompt fields to FIBO API structured prompt format.
        
        Args:
            prompt: Scene description text.
            camera_angle: Camera angle (close-up, medium-shot, wide-shot, overhead, low-angle).
            lighting_style: Lighting style (soft, dramatic, natural, studio, golden-hour).
            subject_position: Subject position (center, rule-of-thirds-left, rule-of-thirds-right).
            color_palette: Optional list of hex color codes.
            mood: Optional mood description.
            
        Returns:
            FIBOStructuredPrompt ready for API submission.
        """
        # Map camera angle to FIBO format
        camera_angle_map = {
            "close-up": "close_up",
            "medium-shot": "medium_shot",
            "wide-shot": "wide_shot",
            "overhead": "overhead",
            "low-angle": "low_angle"
        }
        
        # Map lighting style to FIBO format
        lighting_map = {
            "soft": "soft",
            "dramatic": "dramatic",
            "natural": "natural",
            "studio": "studio",
            "golden-hour": "golden_hour"
        }
        
        # Map subject position to FIBO composition format
        position_map = {
            "center": "center",
            "rule-of-thirds-left": "rule_of_thirds_left",
            "rule-of-thirds-right": "rule_of_thirds_right"
        }
        
        return cls(
            scene_description=prompt,
            camera={
                "angle": camera_angle_map.get(camera_angle, camera_angle.replace("-", "_")),
                "shot_type": camera_angle_map.get(camera_angle, "medium_shot")
            },
            lighting={
                "style": lighting_map.get(lighting_style, lighting_style.replace("-", "_")),
                "intensity": "medium"
            },
            composition={
                "subject_position": position_map.get(subject_position, "center"),
                "framing": "standard"
            },
            style={
                "color_palette": color_palette or [],
                "mood": mood or "professional"
            }
        )
    
    def to_api_format(self) -> dict:
        """Convert to FIBO API request format.
        
        Returns:
            Dictionary ready for JSON serialization to FIBO API.
        """
        return {
            "scene_description": self.scene_description,
            "camera": self.camera,
            "lighting": self.lighting,
            "composition": self.composition,
            "style": self.style
        }


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

    @with_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
    async def generate_structured_image(
        self,
        structured_prompt: FIBOStructuredPrompt,
        aspect_ratio: str = "9:16",
        num_results: int = 1
    ) -> FIBOGenerationResult:
        """Generate an image using FIBO structured-prompt-generate API.
        
        Uses structured JSON prompts for deterministic control over
        camera, lighting, composition, and style.
        
        Args:
            structured_prompt: FIBOStructuredPrompt with scene parameters.
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
        
        # Build the prompt string from structured data for text-to-image endpoint
        # The structured prompt provides deterministic control via detailed description
        prompt_parts = [
            structured_prompt.scene_description,
            f"Camera: {structured_prompt.camera.get('angle', 'medium_shot')} shot",
            f"Lighting: {structured_prompt.lighting.get('style', 'natural')} lighting",
            f"Composition: subject {structured_prompt.composition.get('subject_position', 'center')}",
        ]
        
        if structured_prompt.style.get("mood"):
            prompt_parts.append(f"Mood: {structured_prompt.style['mood']}")
        
        if structured_prompt.style.get("color_palette"):
            colors = ", ".join(structured_prompt.style["color_palette"])
            prompt_parts.append(f"Color palette: {colors}")
        
        enhanced_prompt = ". ".join(prompt_parts)
        
        payload = {
            "prompt": enhanced_prompt,
            "num_results": num_results,
            "aspect_ratio": aspect_ratio,
            "sync": True
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

    @with_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
    async def generate_with_structured_prompt(
        self,
        structured_prompt: "FIBOStructuredPromptV2",
        aspect_ratio: str = "9:16"
    ) -> FIBOGenerationResult:
        """Generate an image using FIBO structured-prompt-generate endpoint.
        
        Uses the structured_prompt field in the API payload for deterministic
        control over camera, lighting, composition, and style parameters.
        
        Args:
            structured_prompt: FIBOStructuredPromptV2 with scene parameters.
            aspect_ratio: Aspect ratio for the image (9:16, 1:1, 16:9).
            
        Returns:
            FIBOGenerationResult with request_id and image_url.
            
        Raises:
            FIBOAPIError: If the API returns an error response.
            FIBOTimeoutError: If polling exceeds MAX_POLL_TIME.
            FIBOError: For other errors.
            
        Requirements: 5.1
        """
        endpoint = f"{self.BASE_URL}/v1/text-to-image/base/2.3"
        
        # Use the structured prompt's to_api_payload method for proper formatting
        payload = structured_prompt.to_api_payload(aspect_ratio)
        
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

    @with_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
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

    async def generate_from_scene(
        self,
        fibo_prompt: "FIBOPrompt",
        aspect_ratio: str = "9:16",
        num_results: int = 1
    ) -> FIBOGenerationResult:
        """Generate an image from a storyboard scene's FIBOPrompt.
        
        Convenience method that maps a FIBOPrompt model to a structured
        prompt and generates the image.
        
        Args:
            fibo_prompt: FIBOPrompt from a storyboard scene.
            aspect_ratio: Aspect ratio for the image (9:16, 1:1, 16:9).
            num_results: Number of images to generate (default 1).
            
        Returns:
            FIBOGenerationResult with request_id and image_url.
        """
        # Import here to avoid circular imports
        from app.models import FIBOPrompt as FIBOPromptModel
        
        structured_prompt = FIBOStructuredPrompt.from_scene_prompt(
            prompt=fibo_prompt.prompt,
            camera_angle=fibo_prompt.camera_angle,
            lighting_style=fibo_prompt.lighting_style,
            subject_position=fibo_prompt.subject_position,
            color_palette=fibo_prompt.color_palette,
            mood=fibo_prompt.mood
        )
        
        return await self.generate_structured_image(
            structured_prompt=structured_prompt,
            aspect_ratio=aspect_ratio,
            num_results=num_results
        )

    @with_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
    async def generate_with_reference(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        aspect_ratio: str = "9:16",
        num_results: int = 1
    ) -> FIBOGenerationResult:
        """Generate an image using FIBO translation endpoint with a reference image.
        
        Uses the reference image to maintain visual consistency when generating
        new images. This is useful when a user uploads a product image and wants
        the generated scenes to incorporate visual elements from that image.
        
        Args:
            image_url: URL of the reference image to use for translation.
            prompt: Optional text prompt to guide the generation.
            aspect_ratio: Aspect ratio for the output image (9:16, 1:1, 16:9).
            num_results: Number of images to generate (default 1).
            
        Returns:
            FIBOGenerationResult with request_id and image_url.
            
        Raises:
            FIBOAPIError: If the API returns an error response.
            FIBOTimeoutError: If polling exceeds MAX_POLL_TIME.
            FIBOError: For other errors.
            
        Requirements: 1.2, 3.1
        """
        endpoint = f"{self.BASE_URL}/v1/product/lifestyle_shot_by_text"
        
        payload = {
            "image_url": image_url,
            "num_results": num_results,
            "sync": True
        }
        
        # Add prompt if provided for scene guidance
        if prompt:
            payload["scene_description"] = prompt
        
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
                        f"FIBO translation API error: {response.text}",
                        status_code=response.status_code
                    )
                
                data = response.json()
                
                # Handle sync response - result is returned directly
                result = data.get("result")
                if result and len(result) > 0:
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
                    image_url_result = await self.poll_status(
                        request_id or "unknown",
                        status_url,
                        client
                    )
                    return FIBOGenerationResult(
                        request_id=request_id or "unknown",
                        image_url=image_url_result
                    )
                
                raise FIBOAPIError(
                    f"Invalid response from FIBO translation API: {data}"
                )
                
            except httpx.TimeoutException:
                raise FIBOTimeoutError("Request to FIBO translation API timed out")
            except httpx.RequestError as e:
                raise FIBOError(f"Network error communicating with FIBO translation API: {str(e)}")

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
