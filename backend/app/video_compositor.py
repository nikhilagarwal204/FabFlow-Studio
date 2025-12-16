"""Video Compositor for FabFlow Studio.

Assembles generated frames into a final video using FFmpeg.
Handles frame scaling, scene duration, transitions, and MP4 output.

Requirements:
- 5.1: Compositing_Engine SHALL assemble frames into a single video file
- 5.2: Compositing_Engine SHALL apply transition effects between scenes
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
from app.models import Storyboard, Scene, EnhancedStoryboard, SceneParameters
from typing import Union


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


def get_xfade_transition(transition_type: str) -> str:
    """Map storyboard transition type to FFmpeg xfade transition name.
    
    Args:
        transition_type: Transition type from storyboard ('fade', 'dissolve', 'cut', 'slide', 'cross-dissolve').
        
    Returns:
        FFmpeg xfade transition name.
    """
    transition_map = {
        "fade": "fade",
        "dissolve": "dissolve",
        "cross-dissolve": "dissolve",  # v2 storyboard uses cross-dissolve
        "cut": "fade",  # Use very short fade for cut effect
        "slide": "slideleft",
    }
    return transition_map.get(transition_type, "fade")


def get_transition_duration(transition_type: str) -> float:
    """Get the duration for a transition effect.
    
    Args:
        transition_type: Transition type from storyboard.
        
    Returns:
        Duration in seconds for the transition.
    """
    if transition_type == "cut":
        return 0.1  # Very short for cut effect
    return 0.5  # Standard transition duration


def build_ffmpeg_command(
    frames: list[GeneratedFrame],
    storyboard: Union[Storyboard, EnhancedStoryboard],
    output_path: Path,
    enable_transitions: bool = True
) -> list[str]:
    """Build FFmpeg command for video compositing.
    
    Creates a command that:
    1. Takes each frame as input
    2. Scales to correct dimensions for aspect ratio
    3. Sets duration for each frame based on scene duration
    4. Applies transition effects between scenes (fade, dissolve, slide)
    5. Concatenates all frames into a single video
    6. Outputs MP4 with H.264 codec
    
    Args:
        frames: List of generated frames (one per scene).
        storyboard: Storyboard with scene durations and aspect ratio.
        output_path: Path for the output video file.
        enable_transitions: Whether to apply transition effects between scenes.
        
    Returns:
        FFmpeg command as list of arguments.
        
    Requirements: 5.1, 5.2, 5.3, 5.5, 5.6
    """
    width, height = get_dimensions_for_aspect_ratio(storyboard.aspect_ratio)
    
    # Build input arguments - one input per frame
    inputs = []
    for frame in frames:
        inputs.extend(["-loop", "1", "-i", frame.local_path])
    
    # Build filter complex for scaling and duration
    filter_parts = []
    
    for i, (frame, scene) in enumerate(zip(frames, storyboard.scenes)):
        # Scale each input to target dimensions and set duration
        filter_parts.append(
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1,fps=24,trim=duration={scene.duration},setpts=PTS-STARTPTS[v{i}]"
        )
    
    if enable_transitions and len(frames) > 1:
        # Apply xfade transitions between consecutive clips
        # xfade requires chaining: v0 xfade v1 -> tmp0, tmp0 xfade v2 -> tmp1, etc.
        # 
        # The offset parameter in xfade specifies when the transition starts
        # relative to the START of the output stream (not the current clip).
        # After each xfade, the output duration is:
        #   duration_clip1 + duration_clip2 - transition_duration
        xfade_parts = []
        current_input = "[v0]"
        
        # Track the cumulative duration of the output stream
        cumulative_duration = storyboard.scenes[0].duration
        
        for i in range(len(frames) - 1):
            scene = storyboard.scenes[i]
            next_scene = storyboard.scenes[i + 1]
            transition_type = scene.transition
            xfade_name = get_xfade_transition(transition_type)
            transition_duration = get_transition_duration(transition_type)
            
            # Offset is where the transition starts in the output stream
            # It should be: cumulative_duration - transition_duration
            # This means the transition starts transition_duration seconds before
            # the current clip ends
            offset = cumulative_duration - transition_duration
            
            # Ensure offset is not negative (for very short scenes)
            offset = max(0, offset)
            
            next_input = f"[v{i + 1}]"
            output_label = f"[xf{i}]" if i < len(frames) - 2 else "[outv]"
            
            xfade_parts.append(
                f"{current_input}{next_input}xfade=transition={xfade_name}:"
                f"duration={transition_duration}:offset={offset:.2f}{output_label}"
            )
            
            current_input = f"[xf{i}]"
            
            # Update cumulative duration: add next scene duration minus overlap
            cumulative_duration = offset + next_scene.duration
        
        filter_complex = ";".join(filter_parts) + ";" + ";".join(xfade_parts)
    else:
        # No transitions - simple concatenation
        concat_inputs = "".join(f"[v{i}]" for i in range(len(frames)))
        concat_filter = f"{concat_inputs}concat=n={len(frames)}:v=1:a=0[outv]"
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
    storyboard: Union[Storyboard, EnhancedStoryboard],
    output_dir: Path,
    job_id: str
) -> CompositeResult:
    """Assemble frames into a final video using FFmpeg.
    
    Takes generated frames and creates an MP4 video with:
    - Correct aspect ratio dimensions
    - Scene durations as specified in storyboard
    - Transition effects between scenes (fade, dissolve, slide)
    - H.264 codec for Instagram compatibility
    
    Args:
        frames: List of generated frames (one per scene).
        storyboard: Storyboard with scene information.
        output_dir: Directory to store the output video.
        job_id: Unique job identifier for the video filename.
        
    Returns:
        CompositeResult with video path/URL or error.
        
    Requirements: 5.1, 5.2, 5.3, 5.5, 5.6
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
        storyboard: Union[Storyboard, EnhancedStoryboard],
        job_id: str
    ) -> CompositeResult:
        """Composite frames into a video with transitions.
        
        Args:
            frames: List of generated frames.
            storyboard: Storyboard with scene information and transitions.
            job_id: Unique job identifier.
            
        Returns:
            CompositeResult with video path/URL or error.
            
        Requirements: 5.1, 5.2, 5.3, 5.5, 5.6
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
