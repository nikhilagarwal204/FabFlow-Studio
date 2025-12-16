"""FabFlow Studio - FastAPI Backend Application."""
import uuid
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models import UserInput, Storyboard
from app.storyboard_generator import generate_storyboard
from app.fibo_client import FIBOClient
from app.frame_generator import FrameGeneratorService, GeneratedFrame
from app.video_compositor import VideoCompositorService, CompositeResult

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
