"""Video Compositor for FabFlow Studio.

Assembles generated frames into a final video using FFmpeg.
Handles frame scaling, scene duration, and MP4 output.

Requirements:
- 5.1: Compositing_Engine SHALL assemble frames into a single video file
- 5.3: Compositing_Engine SHALL output video in MP4 format suitable for Instagram
- 5.5: Compositing_Engine SHALL match user-selected aspect ratio for final output
- 5.6: Compositing_Engine SHALL produce output matching user-selected duration (5-12 seconds)
"""
import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from app.frame_generator import GeneratedFrame, get_dimensions_for_aspect_ratio
from app.models import Storyboard, Scene


class CompositeResult(BaseModel):
    """Result of video compositing operation.
    
    Attributes:
        success: Whether compositing succeeded.
        video_path: Local path to the generated video file.
        video_url: URL to access the video (for serving).
        duration: Actual duration of the output video in seconds.
        error: Error message if compositing failed.
    """
    success: bool = Field(..., description="Whether compositing succeeded")
    video_path: str = Field(default="", description="Local path to video file")
    video_url: str = Field(default="", description="URL to access the video")
    duration: float = Field(default=0.0, description="Video duration in seconds")
    error: Optional[str] = Field(default=None, description="Error message if failed")


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available on the system.
    
    Returns:
        True if FFmpeg is installed and accessible, False otherwise.
    """
    return shutil.which("ffmpeg") is not None


def build_ffmpeg_command(
    frames: list[GeneratedFrame],
    storyboard: Storyboard,
    output_path: Path
) -> list[str]:
    """Build FFmpeg command for video compositing.
    
    Creates a command that:
    1. Takes each frame as input
    2. Scales to correct dimensions for aspect ratio
    3. Sets duration for each frame based on scene duration
    4. Concatenates all frames into a single video
    5. Outputs MP4 with H.264 codec
    
    Args:
        frames: List of generated frames (one per scene).
        storyboard: Storyboard with scene durations and aspect ratio.
        output_path: Path for the output video file.
        
    Returns:
        FFmpeg command as list of arguments.
        
    Requirements: 5.1, 5.3, 5.5, 5.6
    """
    width, height = get_dimensions_for_aspect_ratio(storyboard.aspect_ratio)
    
    # Build input arguments - one input per frame
    inputs = []
    for frame in frames:
        inputs.extend(["-loop", "1", "-i", frame.local_path])
    
    # Build filter complex for scaling and duration
    # Each frame gets scaled and shown for its scene duration
    filter_parts = []
    concat_inputs = []
    
    for i, (frame, scene) in enumerate(zip(frames, storyboard.scenes)):
        # Scale each input to target dimensions and set duration
        filter_parts.append(
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1,fps=24,trim=duration={scene.duration}[v{i}]"
        )
        concat_inputs.append(f"[v{i}]")
    
    # Concatenate all processed clips
    concat_filter = "".join(concat_inputs) + f"concat=n={len(frames)}:v=1:a=0[outv]"
    filter_complex = ";".join(filter_parts) + ";" + concat_filter
    
    # Build complete command
    cmd = ["ffmpeg", "-y"]  # -y to overwrite output
    cmd.extend(inputs)
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",  # Enable streaming
        str(output_path)
    ])
    
    return cmd


async def composite_video(
    frames: list[GeneratedFrame],
    storyboard: Storyboard,
    output_dir: Path,
    job_id: str
) -> CompositeResult:
    """Assemble frames into a final video using FFmpeg.
    
    Takes generated frames and creates an MP4 video with:
    - Correct aspect ratio dimensions
    - Scene durations as specified in storyboard
    - H.264 codec for Instagram compatibility
    
    Args:
        frames: List of generated frames (one per scene).
        storyboard: Storyboard with scene information.
        output_dir: Directory to store the output video.
        job_id: Unique job identifier for the video filename.
        
    Returns:
        CompositeResult with video path/URL or error.
        
    Requirements: 5.1, 5.3, 5.5, 5.6
    """
    # Validate inputs
    if not frames:
        return CompositeResult(
            success=False,
            error="No frames provided for compositing"
        )
    
    if len(frames) != len(storyboard.scenes):
        return CompositeResult(
            success=False,
            error=f"Frame count ({len(frames)}) doesn't match scene count ({len(storyboard.scenes)})"
        )
    
    # Check FFmpeg availability
    if not check_ffmpeg_available():
        return CompositeResult(
            success=False,
            error="FFmpeg is not installed or not available in PATH"
        )
    
    # Verify all frame files exist
    for frame in frames:
        if not Path(frame.local_path).exists():
            return CompositeResult(
                success=False,
                error=f"Frame file not found: {frame.local_path}"
            )
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{job_id}.mp4"
    
    # Build and execute FFmpeg command
    cmd = build_ffmpeg_command(frames, storyboard, output_path)
    
    try:
        # Run FFmpeg asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
            return CompositeResult(
                success=False,
                error=f"FFmpeg failed: {error_msg[:500]}"  # Truncate long errors
            )
        
        # Verify output file was created
        if not output_path.exists():
            return CompositeResult(
                success=False,
                error="FFmpeg completed but output file was not created"
            )
        
        # Calculate total duration
        total_duration = sum(scene.duration for scene in storyboard.scenes)
        
        return CompositeResult(
            success=True,
            video_path=str(output_path),
            video_url=f"/api/videos/{job_id}.mp4",
            duration=total_duration
        )
        
    except FileNotFoundError:
        return CompositeResult(
            success=False,
            error="FFmpeg executable not found"
        )
    except Exception as e:
        return CompositeResult(
            success=False,
            error=f"Compositing error: {str(e)}"
        )


class VideoCompositorService:
    """Service class for video compositing operations.
    
    Provides a high-level interface for compositing videos from frames.
    Manages output directory and video file lifecycle.
    
    Attributes:
        base_output_dir: Base directory for storing output videos.
    """
    
    def __init__(self, base_output_dir: Optional[Path] = None):
        """Initialize the video compositor service.
        
        Args:
            base_output_dir: Base directory for video storage.
        """
        self.base_output_dir = base_output_dir or Path("/tmp/fabflow")
    
    def get_video_output_dir(self, job_id: str) -> Path:
        """Get the output directory for a specific job's video.
        
        Args:
            job_id: Unique identifier for the job.
            
        Returns:
            Path to the job's video output directory.
        """
        return self.base_output_dir / job_id / "output"
    
    def get_video_path(self, job_id: str) -> Path:
        """Get the expected path for a job's output video.
        
        Args:
            job_id: Unique identifier for the job.
            
        Returns:
            Path to the job's output video file.
        """
        return self.get_video_output_dir(job_id) / f"{job_id}.mp4"
    
    async def composite(
        self,
        frames: list[GeneratedFrame],
        storyboard: Storyboard,
        job_id: str
    ) -> CompositeResult:
        """Composite frames into a video.
        
        Args:
            frames: List of generated frames.
            storyboard: Storyboard with scene information.
            job_id: Unique job identifier.
            
        Returns:
            CompositeResult with video path/URL or error.
            
        Requirements: 5.1, 5.3, 5.5, 5.6
        """
        output_dir = self.get_video_output_dir(job_id)
        return await composite_video(frames, storyboard, output_dir, job_id)
    
    def video_exists(self, job_id: str) -> bool:
        """Check if a video file exists for a job.
        
        Args:
            job_id: Unique identifier for the job.
            
        Returns:
            True if the video file exists, False otherwise.
        """
        return self.get_video_path(job_id).exists()
    
    def cleanup_job(self, job_id: str) -> bool:
        """Clean up all files for a job.
        
        Args:
            job_id: Unique identifier for the job.
            
        Returns:
            True if cleanup succeeded, False otherwise.
        """
        job_dir = self.base_output_dir / job_id
        if job_dir.exists():
            try:
                shutil.rmtree(job_dir)
                return True
            except Exception:
                return False
        return True
