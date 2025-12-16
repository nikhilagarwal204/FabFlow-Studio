"""FabFlow Studio - FastAPI Backend Application."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import UserInput, Storyboard
from app.storyboard_generator import generate_storyboard

settings = get_settings()

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
