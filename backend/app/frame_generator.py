"""Frame Generator Service for FabFlow Studio.

Generates frames for each scene using FIBO API.
Handles frame calculation, image generation, and local storage.

Requirements:
- 4.1: Frame_Generator SHALL call FIBO_API and retrieve generated image
- 4.2: Frame_Generator SHALL produce frames based on scene duration and frame rate
- 4.4: Frames SHALL be stored in sequential order for compositing
"""
import asyncio
import uuid
from pathlib import Path
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from app.fibo_client import FIBOClient, FIBOError
from app.models import Scene, Storyboard


class GeneratedFrame(BaseModel):
    """Represents a single generated frame.
    
    Attributes:
        scene_number: The scene this frame belongs to.
        frame_index: Index of this frame within the scene.
        image_url: Remote URL of the generated image.
        local_path: Local file path where the frame is stored.
    """
    scene_number: int = Field(..., ge=1, description="Scene number (1-indexed)")
    frame_index: int = Field(..., ge=0, description="Frame index within scene")
    image_url: str = Field(..., description="Remote URL of generated image")
    local_path: str = Field(..., description="Local file path for the frame")


class FrameGenerationResult(BaseModel):
    """Result of frame generation for a scene or storyboard.
    
    Attributes:
        success: Whether all frames were generated successfully.
        frames: List of generated frames.
        errors: List of error messages for any failures.
    """
    success: bool = Field(..., description="Whether generation succeeded")
    frames: list[GeneratedFrame] = Field(default_factory=list, description="Generated frames")
    errors: list[str] = Field(default_factory=list, description="Error messages")


def calculate_frame_count(duration: float, fps: int = 24) -> int:
    """Calculate number of frames needed for a scene duration.
    
    For MVP, we generate 1 key frame per scene (FIBO generates the key frame).
    This function calculates how many frames would be needed at the target FPS,
    but the actual generation uses 1 frame per scene for the prototype.
    
    Args:
        duration: Scene duration in seconds.
        fps: Target frames per second (default 24).
        
    Returns:
        Number of frames needed (minimum 1).
        
    Requirements: 4.2
    """
    return max(1, int(duration * fps))


def get_dimensions_for_aspect_ratio(aspect_ratio: str) -> tuple[int, int]:
    """Get pixel dimensions for an aspect ratio.
    
    Args:
        aspect_ratio: One of "9:16", "1:1", or "16:9".
        
    Returns:
        Tuple of (width, height) in pixels.
    """
    ratios = {
        "9:16": (1080, 1920),  # Vertical/Stories
        "1:1": (1080, 1080),   # Square
        "16:9": (1920, 1080),  # Horizontal
    }
    return ratios.get(aspect_ratio, (1080, 1920))


async def download_image(image_url: str, local_path: Path) -> bool:
    """Download an image from URL to local storage.
    
    Args:
        image_url: URL of the image to download.
        local_path: Local path to save the image.
        
    Returns:
        True if download succeeded, False otherwise.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(image_url)
            if response.status_code == 200:
                # Ensure parent directory exists
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(response.content)
                return True
            return False
    except Exception:
        return False


async def generate_frames_for_scene(
    scene: Scene,
    aspect_ratio: str,
    fibo_client: FIBOClient,
    output_dir: Path,
    reference_image_url: Optional[str] = None
) -> FrameGenerationResult:
    """Generate frames for a single scene using FIBO API.
    
    For MVP: Generates 1 key frame per scene. FIBO generates the key frame,
    and FFmpeg will handle frame duplication during compositing.
    
    Args:
        scene: The scene to generate frames for.
        aspect_ratio: Target aspect ratio for the frames.
        fibo_client: FIBO API client instance.
        output_dir: Directory to store generated frames.
        reference_image_url: Optional reference image for translation API.
        
    Returns:
        FrameGenerationResult with generated frames or errors.
        
    Requirements: 4.1, 4.4
    """
    frames: list[GeneratedFrame] = []
    errors: list[str] = []
    
    try:
        # Build the prompt from scene's FIBO prompt
        fibo_prompt = scene.fibo_prompt
        full_prompt = (
            f"{fibo_prompt.prompt}. "
            f"Camera angle: {fibo_prompt.camera_angle}. "
            f"Lighting: {fibo_prompt.lighting_style}. "
            f"Subject position: {fibo_prompt.subject_position}."
        )
        
        if fibo_prompt.mood:
            full_prompt += f" Mood: {fibo_prompt.mood}."
        
        if fibo_prompt.color_palette:
            colors = ", ".join(fibo_prompt.color_palette)
            full_prompt += f" Color palette: {colors}."
        
        # Generate key frame using FIBO
        result = await fibo_client.generate_image(
            prompt=full_prompt,
            aspect_ratio=aspect_ratio,
            num_results=1
        )
        
        # Create local path for the frame
        frame_filename = f"scene_{scene.scene_number:02d}_frame_00.png"
        local_path = output_dir / frame_filename
        
        # Download the generated image
        download_success = await download_image(result.image_url, local_path)
        
        if download_success:
            frame = GeneratedFrame(
                scene_number=scene.scene_number,
                frame_index=0,
                image_url=result.image_url,
                local_path=str(local_path)
            )
            frames.append(frame)
        else:
            errors.append(f"Failed to download frame for scene {scene.scene_number}")
            
    except FIBOError as e:
        errors.append(f"Scene {scene.scene_number}: {e.message}")
    except Exception as e:
        errors.append(f"Scene {scene.scene_number}: Unexpected error - {str(e)}")
    
    return FrameGenerationResult(
        success=len(errors) == 0,
        frames=frames,
        errors=errors
    )



async def generate_all_frames(
    storyboard: Storyboard,
    fibo_client: FIBOClient,
    output_dir: Optional[Path] = None,
    reference_image_url: Optional[str] = None
) -> FrameGenerationResult:
    """Generate frames for all scenes in a storyboard.
    
    Processes each scene sequentially to generate key frames.
    Frames are stored in sequential order for compositing.
    
    Args:
        storyboard: The complete storyboard with all scenes.
        fibo_client: FIBO API client instance.
        output_dir: Directory to store frames. If None, creates a temp directory.
        reference_image_url: Optional reference image for all scenes.
        
    Returns:
        FrameGenerationResult with all generated frames or errors.
        
    Requirements: 4.1, 4.2, 4.4
    """
    # Create output directory if not provided
    if output_dir is None:
        job_id = str(uuid.uuid4())
        output_dir = Path("/tmp/fabflow") / job_id / "frames"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_frames: list[GeneratedFrame] = []
    all_errors: list[str] = []
    
    # Process scenes sequentially to maintain order (Requirement 4.4)
    for scene in storyboard.scenes:
        result = await generate_frames_for_scene(
            scene=scene,
            aspect_ratio=storyboard.aspect_ratio,
            fibo_client=fibo_client,
            output_dir=output_dir,
            reference_image_url=reference_image_url
        )
        
        all_frames.extend(result.frames)
        all_errors.extend(result.errors)
    
    # Sort frames by scene number and frame index to ensure sequential order
    all_frames.sort(key=lambda f: (f.scene_number, f.frame_index))
    
    return FrameGenerationResult(
        success=len(all_errors) == 0,
        frames=all_frames,
        errors=all_errors
    )


class FrameGeneratorService:
    """Service class for frame generation operations.
    
    Provides a high-level interface for generating frames from storyboards.
    Manages FIBO client lifecycle and output directory creation.
    
    Attributes:
        fibo_client: The FIBO API client instance.
        base_output_dir: Base directory for storing generated frames.
    """
    
    def __init__(
        self,
        fibo_client: Optional[FIBOClient] = None,
        base_output_dir: Optional[Path] = None
    ):
        """Initialize the frame generator service.
        
        Args:
            fibo_client: Optional FIBO client. Creates one if not provided.
            base_output_dir: Base directory for frame storage.
        """
        self.fibo_client = fibo_client or FIBOClient()
        self.base_output_dir = base_output_dir or Path("/tmp/fabflow")
    
    def create_job_directory(self, job_id: str) -> Path:
        """Create a directory for a specific job's frames.
        
        Args:
            job_id: Unique identifier for the job.
            
        Returns:
            Path to the job's frame directory.
        """
        job_dir = self.base_output_dir / job_id / "frames"
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir
    
    async def generate_frames(
        self,
        storyboard: Storyboard,
        job_id: Optional[str] = None,
        reference_image_url: Optional[str] = None
    ) -> FrameGenerationResult:
        """Generate all frames for a storyboard.
        
        Args:
            storyboard: The storyboard to generate frames for.
            job_id: Optional job ID. Generates one if not provided.
            reference_image_url: Optional reference image URL.
            
        Returns:
            FrameGenerationResult with generated frames.
            
        Requirements: 4.1, 4.2, 4.4
        """
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        output_dir = self.create_job_directory(job_id)
        
        return await generate_all_frames(
            storyboard=storyboard,
            fibo_client=self.fibo_client,
            output_dir=output_dir,
            reference_image_url=reference_image_url
        )
    
    def get_frame_count_for_storyboard(self, storyboard: Storyboard, fps: int = 24) -> int:
        """Calculate total frame count for a storyboard at given FPS.
        
        This is informational - actual generation produces 1 key frame per scene.
        
        Args:
            storyboard: The storyboard to calculate frames for.
            fps: Target frames per second.
            
        Returns:
            Total number of frames needed at the target FPS.
        """
        total = 0
        for scene in storyboard.scenes:
            total += calculate_frame_count(scene.duration, fps)
        return total
