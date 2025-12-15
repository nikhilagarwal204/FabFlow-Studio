"""FabFlow Studio - FastAPI Backend Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

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
