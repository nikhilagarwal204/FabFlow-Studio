"""FabFlow Studio - FastAPI Backend Application."""
import uuid
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models import UserInput, Storyboard, EnhancedUserInput, EnhancedStoryboard
from app.storyboard_generator import generate_storyboard, generate_enhanced_storyboard
from app.fibo_client import FIBOClient
from app.frame_generator import (
    FrameGeneratorService,
    GeneratedFrame,
    EnhancedFrameGenerator,
    EnhancedGeneratedFrame,
    FrameGenerationResult,
)
from app.video_compositor import VideoCompositorService, CompositeResult
from app.parameter_modification import (
    ParameterModification,
    ModificationResult,
    apply_parameter_modification,
)

settings = get_settings()


# Job tracking models
class JobStatus(BaseModel):
    """Status of a video generation job."""
    job_id: str
    stage: Literal["queued", "storyboard", "frame-generation", "compositing", "complete", "error"]
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    message: str = ""
    error: Optional[str] = None


class JobResult(BaseModel):
    """Result of a completed video generation job."""
    job_id: str
    success: bool
    video_url: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None


# In-memory job storage (for prototype)
jobs: dict[str, JobStatus] = {}
job_results: dict[str, JobResult] = {}
job_storyboards: dict[str, Storyboard] = {}

# V2 job storage for enhanced storyboards and frames
job_enhanced_storyboards: dict[str, EnhancedStoryboard] = {}
job_enhanced_frames: dict[str, dict[int, EnhancedGeneratedFrame]] = {}


# Services (lazy initialization to avoid API key errors at import time)
_fibo_client: Optional[FIBOClient] = None
_frame_generator_service: Optional[FrameGeneratorService] = None
_video_compositor_service: Optional[VideoCompositorService] = None


def get_fibo_client() -> FIBOClient:
    """Get or create FIBO client instance."""
    global _fibo_client
    if _fibo_client is None:
        _fibo_client = FIBOClient()
    return _fibo_client


def get_frame_generator_service() -> FrameGeneratorService:
    """Get or create frame generator service instance."""
    global _frame_generator_service
    if _frame_generator_service is None:
        _frame_generator_service = FrameGeneratorService(fibo_client=get_fibo_client())
    return _frame_generator_service


def get_video_compositor_service() -> VideoCompositorService:
    """Get or create video compositor service instance."""
    global _video_compositor_service
    if _video_compositor_service is None:
        _video_compositor_service = VideoCompositorService()
    return _video_compositor_service


# Enhanced frame generator for v2 pipeline
_enhanced_frame_generator: Optional[EnhancedFrameGenerator] = None


def get_enhanced_frame_generator() -> EnhancedFrameGenerator:
    """Get or create enhanced frame generator instance."""
    global _enhanced_frame_generator
    if _enhanced_frame_generator is None:
        _enhanced_frame_generator = EnhancedFrameGenerator(fibo_client=get_fibo_client())
    return _enhanced_frame_generator

app = FastAPI(
    title="FabFlow Studio API",
    description="AI-powered ad video creation platform backend",
    version="0.1.0",
)

# Configure CORS for frontend
origins = [origin.strip() for origin in settings.frontend_url.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "FabFlow Studio API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms."""
    return {"status": "healthy"}


@app.post("/api/generate-storyboard", response_model=Storyboard)
async def generate_storyboard_endpoint(user_input: UserInput) -> Storyboard:
    """Generate a storyboard from user input using OpenAI.
    
    Args:
        user_input: Brand, product, and video settings.
        
    Returns:
        Generated storyboard with 3-5 scenes.
        
    Raises:
        HTTPException: If storyboard generation fails.
    """
    try:
        storyboard = await generate_storyboard(user_input)
        return storyboard
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_RESPONSE", "message": str(e), "retryable": True}
        )
    except Exception as e:
        error_message = str(e)
        if "api_key" in error_message.lower() or "authentication" in error_message.lower():
            raise HTTPException(
                status_code=500,
                detail={"code": "API_KEY_ERROR", "message": "OpenAI API key configuration error", "retryable": False}
            )
        raise HTTPException(
            status_code=500,
            detail={"code": "GENERATION_ERROR", "message": f"Failed to generate storyboard: {error_message}", "retryable": True}
        )


async def run_video_generation_pipeline(job_id: str, user_input: UserInput):
    """Background task to run the full video generation pipeline.
    
    Pipeline stages:
    1. Generate storyboard from user input
    2. Generate frames for each scene using FIBO
    3. Composite frames into final video using FFmpeg
    
    Args:
        job_id: Unique job identifier.
        user_input: User input for video generation.
        
    Requirements: 5.1, 5.4
    """
    try:
        # Stage 1: Generate storyboard
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="storyboard",
            progress=10,
            message="Generating storyboard..."
        )
        
        storyboard = await generate_storyboard(user_input)
        job_storyboards[job_id] = storyboard
        
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="storyboard",
            progress=25,
            message="Storyboard generated"
        )
        
        # Stage 2: Generate frames
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="frame-generation",
            progress=30,
            message="Generating frames..."
        )
        
        frame_result = await get_frame_generator_service().generate_frames(
            storyboard=storyboard,
            job_id=job_id,
            reference_image_url=user_input.product_image_url
        )
        
        if not frame_result.success:
            error_msg = "; ".join(frame_result.errors) if frame_result.errors else "Frame generation failed"
            jobs[job_id] = JobStatus(
                job_id=job_id,
                stage="error",
                progress=0,
                message="Frame generation failed",
                error=error_msg
            )
            job_results[job_id] = JobResult(
                job_id=job_id,
                success=False,
                error=error_msg
            )
            return
        
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="frame-generation",
            progress=70,
            message=f"Generated {len(frame_result.frames)} frames"
        )
        
        # Stage 3: Composite video
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="compositing",
            progress=75,
            message="Compositing video..."
        )
        
        composite_result = await get_video_compositor_service().composite(
            frames=frame_result.frames,
            storyboard=storyboard,
            job_id=job_id
        )
        
        if not composite_result.success:
            jobs[job_id] = JobStatus(
                job_id=job_id,
                stage="error",
                progress=0,
                message="Video compositing failed",
                error=composite_result.error
            )
            job_results[job_id] = JobResult(
                job_id=job_id,
                success=False,
                error=composite_result.error
            )
            return
        
        # Complete
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="complete",
            progress=100,
            message="Video generation complete"
        )
        
        job_results[job_id] = JobResult(
            job_id=job_id,
            success=True,
            video_url=composite_result.video_url,
            duration=composite_result.duration
        )
        
    except Exception as e:
        error_msg = str(e)
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="error",
            progress=0,
            message="Pipeline failed",
            error=error_msg
        )
        job_results[job_id] = JobResult(
            job_id=job_id,
            success=False,
            error=error_msg
        )


@app.post("/api/generate-video")
async def generate_video_endpoint(
    user_input: UserInput,
    background_tasks: BackgroundTasks
) -> dict:
    """Start full video generation pipeline.
    
    Runs the complete pipeline: storyboard -> frames -> video
    Returns immediately with a job_id for progress polling.
    
    Args:
        user_input: Brand, product, and video settings.
        background_tasks: FastAPI background tasks handler.
        
    Returns:
        Dictionary with job_id for polling progress.
        
    Requirements: 5.1, 5.4
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    jobs[job_id] = JobStatus(
        job_id=job_id,
        stage="queued",
        progress=0,
        message="Job queued"
    )
    
    # Start background task
    background_tasks.add_task(run_video_generation_pipeline, job_id, user_input)
    
    return {"job_id": job_id, "message": "Video generation started"}


@app.get("/api/job/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Get the current status of a video generation job.
    
    Args:
        job_id: Unique job identifier.
        
    Returns:
        Current job status with stage and progress.
        
    Raises:
        HTTPException: If job not found.
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"}
        )
    
    return jobs[job_id]


@app.get("/api/job/{job_id}/result", response_model=JobResult)
async def get_job_result(job_id: str) -> JobResult:
    """Get the result of a completed video generation job.
    
    Args:
        job_id: Unique job identifier.
        
    Returns:
        Job result with video URL if successful.
        
    Raises:
        HTTPException: If job not found or not complete.
        
    Requirements: 5.4
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"}
        )
    
    job_status = jobs[job_id]
    
    if job_status.stage not in ["complete", "error"]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "JOB_NOT_COMPLETE",
                "message": f"Job is still in progress: {job_status.stage}"
            }
        )
    
    if job_id not in job_results:
        raise HTTPException(
            status_code=500,
            detail={"code": "RESULT_NOT_FOUND", "message": "Job result not available"}
        )
    
    return job_results[job_id]


@app.get("/api/videos/{filename}")
async def serve_video(filename: str):
    """Serve a generated video file.
    
    Args:
        filename: Video filename (job_id.mp4).
        
    Returns:
        Video file response.
        
    Raises:
        HTTPException: If video file not found.
        
    Requirements: 5.4
    """
    # Extract job_id from filename
    if not filename.endswith(".mp4"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_FILENAME", "message": "Invalid video filename"}
        )
    
    job_id = filename[:-4]  # Remove .mp4 extension
    video_path = get_video_compositor_service().get_video_path(job_id)
    
    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "VIDEO_NOT_FOUND", "message": "Video file not found"}
        )
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=filename
    )


# =============================================================================
# V2 API Endpoints - Enhanced FIBO JSON Pipeline
# Requirements: 1.1, 7.1, 7.2
# =============================================================================


@app.post("/api/v2/generate-storyboard", response_model=EnhancedStoryboard)
async def generate_storyboard_v2_endpoint(user_input: EnhancedUserInput) -> EnhancedStoryboard:
    """Generate an enhanced storyboard with structured FIBO parameters.
    
    Uses GPT-4o to generate a storyboard with precise camera, lighting,
    composition, and style parameters that map directly to FIBO's
    structured prompt format.
    
    Args:
        user_input: Enhanced user input with brand, product, material,
                   color preferences, and video settings.
        
    Returns:
        EnhancedStoryboard with 3-5 scenes containing SceneParameters.
        
    Raises:
        HTTPException: If storyboard generation fails.
        
    Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 7.1
    """
    try:
        storyboard = await generate_enhanced_storyboard(user_input)
        return storyboard
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_RESPONSE", "message": str(e), "retryable": True}
        )
    except Exception as e:
        error_message = str(e)
        if "api_key" in error_message.lower() or "authentication" in error_message.lower():
            raise HTTPException(
                status_code=500,
                detail={"code": "API_KEY_ERROR", "message": "OpenAI API key configuration error", "retryable": False}
            )
        raise HTTPException(
            status_code=500,
            detail={"code": "GENERATION_ERROR", "message": f"Failed to generate storyboard: {error_message}", "retryable": True}
        )


async def run_video_generation_pipeline_v2(job_id: str, user_input: EnhancedUserInput):
    """Background task to run the enhanced v2 video generation pipeline.
    
    Pipeline stages:
    1. Generate enhanced storyboard with structured FIBO parameters
    2. Generate frames for each scene using FIBO structured prompts
    3. Composite frames into final video using FFmpeg
    
    Args:
        job_id: Unique job identifier.
        user_input: Enhanced user input for video generation.
        
    Requirements: 1.1, 5.1, 5.2, 5.4, 7.1, 7.2
    """
    try:
        # Stage 1: Generate enhanced storyboard
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="storyboard",
            progress=10,
            message="Generating enhanced storyboard..."
        )
        
        storyboard = await generate_enhanced_storyboard(user_input)
        job_enhanced_storyboards[job_id] = storyboard
        
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="storyboard",
            progress=25,
            message="Enhanced storyboard generated"
        )
        
        # Stage 2: Generate frames using structured prompts
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="frame-generation",
            progress=30,
            message="Generating frames with structured prompts..."
        )
        
        frame_generator = get_enhanced_frame_generator()
        frame_result = await frame_generator.generate_all_frames(
            storyboard=storyboard,
            job_id=job_id
        )
        
        if not frame_result.success:
            error_msg = "; ".join(frame_result.errors) if frame_result.errors else "Frame generation failed"
            jobs[job_id] = JobStatus(
                job_id=job_id,
                stage="error",
                progress=0,
                message="Frame generation failed",
                error=error_msg
            )
            job_results[job_id] = JobResult(
                job_id=job_id,
                success=False,
                error=error_msg
            )
            return
        
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="frame-generation",
            progress=70,
            message=f"Generated {len(frame_result.frames)} frames"
        )
        
        # Stage 3: Composite video
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="compositing",
            progress=75,
            message="Compositing video..."
        )
        
        # Create a compatible Storyboard for the compositor
        # The compositor expects the v1 Storyboard format
        from app.models import Scene, FIBOPrompt
        
        v1_scenes = []
        for scene in storyboard.scenes:
            v1_scene = Scene(
                scene_number=scene.scene_number,
                duration=scene.duration,
                transition="dissolve" if scene.transition == "cross-dissolve" else scene.transition,
                fibo_prompt=FIBOPrompt(
                    prompt=scene.scene_description,
                    camera_angle=scene.camera.angle if scene.camera.angle != "three-quarter" else "medium-shot",
                    lighting_style=scene.lighting.style.replace("-", " ").split()[0],  # soft-studio -> soft
                    subject_position=scene.composition.subject_position,
                    color_palette=scene.style.color_palette,
                    mood=scene.style.mood
                )
            )
            v1_scenes.append(v1_scene)
        
        v1_storyboard = Storyboard(
            brand_name=storyboard.brand_name,
            product_name=storyboard.product_name,
            total_duration=storyboard.total_duration,
            aspect_ratio=storyboard.aspect_ratio,
            scenes=v1_scenes
        )
        
        composite_result = await get_video_compositor_service().composite(
            frames=frame_result.frames,
            storyboard=v1_storyboard,
            job_id=job_id
        )
        
        if not composite_result.success:
            jobs[job_id] = JobStatus(
                job_id=job_id,
                stage="error",
                progress=0,
                message="Video compositing failed",
                error=composite_result.error
            )
            job_results[job_id] = JobResult(
                job_id=job_id,
                success=False,
                error=composite_result.error
            )
            return
        
        # Complete
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="complete",
            progress=100,
            message="Video generation complete"
        )
        
        job_results[job_id] = JobResult(
            job_id=job_id,
            success=True,
            video_url=composite_result.video_url,
            duration=composite_result.duration
        )
        
    except Exception as e:
        error_msg = str(e)
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="error",
            progress=0,
            message="Pipeline failed",
            error=error_msg
        )
        job_results[job_id] = JobResult(
            job_id=job_id,
            success=False,
            error=error_msg
        )


@app.post("/api/v2/generate-video")
async def generate_video_v2_endpoint(
    user_input: EnhancedUserInput,
    background_tasks: BackgroundTasks
) -> dict:
    """Start enhanced v2 video generation pipeline.
    
    Runs the complete v2 pipeline with structured FIBO JSON:
    storyboard -> structured frames -> video
    
    Returns immediately with a job_id for progress polling.
    
    Args:
        user_input: Enhanced user input with material and color preferences.
        background_tasks: FastAPI background tasks handler.
        
    Returns:
        Dictionary with job_id for polling progress.
        
    Requirements: 1.1, 7.1, 7.2
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    jobs[job_id] = JobStatus(
        job_id=job_id,
        stage="queued",
        progress=0,
        message="Job queued"
    )
    
    # Start background task
    background_tasks.add_task(run_video_generation_pipeline_v2, job_id, user_input)
    
    return {"job_id": job_id, "message": "Video generation started (v2 pipeline)"}


@app.post("/api/v2/modify-parameter/{job_id}")
async def modify_parameter_endpoint(
    job_id: str,
    modification: ParameterModification,
    background_tasks: BackgroundTasks
) -> dict:
    """Modify a single parameter in a job's storyboard and regenerate affected frames.
    
    Enables quick iteration by changing a single parameter (e.g., material, color)
    and regenerating only the affected frames while preserving all other parameters.
    
    Args:
        job_id: Unique job identifier.
        modification: Parameter modification request with path, value, and target scenes.
        background_tasks: FastAPI background tasks handler.
        
    Returns:
        Dictionary with modification result and regeneration status.
        
    Raises:
        HTTPException: If job not found or modification fails.
        
    Requirements: 4.1, 4.2, 4.3, 4.4, 7.1
    """
    # Check if job exists and has an enhanced storyboard
    if job_id not in job_enhanced_storyboards:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "JOB_NOT_FOUND",
                "message": f"Job {job_id} not found or not a v2 job"
            }
        )
    
    storyboard = job_enhanced_storyboards[job_id]
    
    # Apply the modification
    modified_storyboard, result = apply_parameter_modification(storyboard, modification)
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MODIFICATION_FAILED",
                "message": result.error or "Failed to apply parameter modification"
            }
        )
    
    # Update the stored storyboard
    job_enhanced_storyboards[job_id] = modified_storyboard
    
    # If there are frames to regenerate, start background task
    if result.frames_to_regenerate:
        # Update job status
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="frame-generation",
            progress=50,
            message=f"Regenerating {len(result.frames_to_regenerate)} frames..."
        )
        
        # Start regeneration in background
        background_tasks.add_task(
            regenerate_frames_for_modification,
            job_id,
            modified_storyboard,
            result.frames_to_regenerate
        )
    
    return {
        "success": True,
        "modified_scenes": result.modified_scenes,
        "frames_to_regenerate": result.frames_to_regenerate,
        "message": f"Modified {len(result.modified_scenes)} scenes, regenerating {len(result.frames_to_regenerate)} frames"
    }


async def regenerate_frames_for_modification(
    job_id: str,
    storyboard: EnhancedStoryboard,
    scenes_to_regenerate: list[int]
):
    """Background task to regenerate frames after parameter modification.
    
    Args:
        job_id: Unique job identifier.
        storyboard: Modified storyboard with updated parameters.
        scenes_to_regenerate: List of scene numbers to regenerate.
        
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    try:
        frame_generator = get_enhanced_frame_generator()
        
        # Get existing frames if available
        existing_frames = job_enhanced_frames.get(job_id, {})
        
        # Regenerate only the modified frames
        updated_frames = await frame_generator.regenerate_modified_frames(
            storyboard=storyboard,
            scenes_to_regenerate=scenes_to_regenerate,
            existing_frames=existing_frames,
            job_id=job_id
        )
        
        # Store updated frames
        job_enhanced_frames[job_id] = updated_frames
        
        # Update job status
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="complete",
            progress=100,
            message=f"Regenerated {len(scenes_to_regenerate)} frames"
        )
        
    except Exception as e:
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="error",
            progress=0,
            message="Frame regeneration failed",
            error=str(e)
        )


@app.get("/api/v2/job/{job_id}/parameters", response_model=EnhancedStoryboard)
async def get_job_parameters_endpoint(job_id: str) -> EnhancedStoryboard:
    """Get the current storyboard parameters for a v2 job.
    
    Returns the full EnhancedStoryboard with all scene parameters,
    useful for displaying current settings in the parameter editor.
    
    Args:
        job_id: Unique job identifier.
        
    Returns:
        EnhancedStoryboard with current parameters.
        
    Raises:
        HTTPException: If job not found.
        
    Requirements: 7.1, 7.2
    """
    if job_id not in job_enhanced_storyboards:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "JOB_NOT_FOUND",
                "message": f"Job {job_id} not found or not a v2 job"
            }
        )
    
    return job_enhanced_storyboards[job_id]
