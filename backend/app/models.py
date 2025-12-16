"""Pydantic models for FabFlow Studio storyboard generation."""
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class UserInput(BaseModel):
    """User input for video generation."""
    
    brand_name: str = Field(..., min_length=1, description="Brand name")
    product_name: str = Field(..., min_length=1, description="Product name")
    product_description: str = Field(..., min_length=1, description="Product description")
    duration: int = Field(default=8, ge=5, le=12, description="Video duration in seconds (5-12)")
    aspect_ratio: Literal["9:16", "1:1", "16:9"] = Field(
        default="9:16", description="Video aspect ratio"
    )
    product_image_url: Optional[str] = Field(
        default=None, description="Optional product image URL for reference"
    )

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Validate duration is within allowed range."""
        if v < 5 or v > 12:
            raise ValueError("Duration must be between 5 and 12 seconds")
        return v


class FIBOPrompt(BaseModel):
    """FIBO-compatible prompt for image generation."""
    
    prompt: str = Field(..., description="Detailed scene description for FIBO")
    camera_angle: Literal["close-up", "medium-shot", "wide-shot", "overhead", "low-angle"] = Field(
        ..., description="Camera angle for the scene"
    )
    lighting_style: Literal["soft", "dramatic", "natural", "studio", "golden-hour"] = Field(
        ..., description="Lighting style for the scene"
    )
    subject_position: Literal["center", "rule-of-thirds-left", "rule-of-thirds-right"] = Field(
        ..., description="Subject positioning in frame"
    )
    color_palette: Optional[list[str]] = Field(
        default=None, description="Hex color codes for the scene"
    )
    mood: Optional[str] = Field(default=None, description="Overall mood of the scene")


class Scene(BaseModel):
    """A single scene in the storyboard."""
    
    scene_number: int = Field(..., ge=1, description="Scene number (1-indexed)")
    duration: float = Field(..., gt=0, description="Scene duration in seconds")
    transition: Literal["fade", "dissolve", "cut", "slide"] = Field(
        ..., description="Transition effect to next scene"
    )
    fibo_prompt: FIBOPrompt = Field(..., description="FIBO prompt for this scene")


class Storyboard(BaseModel):
    """Complete storyboard for video generation."""
    
    brand_name: str = Field(..., description="Brand name")
    product_name: str = Field(..., description="Product name")
    total_duration: int = Field(..., ge=5, le=12, description="Total video duration in seconds")
    aspect_ratio: Literal["9:16", "1:1", "16:9"] = Field(..., description="Video aspect ratio")
    scenes: list[Scene] = Field(..., min_length=3, max_length=5, description="List of 3-5 scenes")

    @field_validator("scenes")
    @classmethod
    def validate_scenes(cls, v: list[Scene]) -> list[Scene]:
        """Validate scene count is within allowed range."""
        if len(v) < 3 or len(v) > 5:
            raise ValueError("Storyboard must contain 3-5 scenes")
        return v
