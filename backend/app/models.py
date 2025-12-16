"""Pydantic models for FabFlow Studio storyboard generation."""
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enhanced FIBO JSON Control Models (v2)
# =============================================================================

class CameraParams(BaseModel):
    """Camera parameters for FIBO structured prompt."""
    angle: Literal["close-up", "medium-shot", "wide-shot", "overhead", "low-angle", "three-quarter"] = Field(
        ..., description="Camera angle for the scene"
    )
    shot_type: Literal["product_hero", "detail", "lifestyle", "context"] = Field(
        ..., description="Type of shot"
    )


class LightingParams(BaseModel):
    """Lighting parameters for FIBO structured prompt."""
    style: Literal["soft-studio", "dramatic", "natural-window", "golden-hour", "product-spotlight"] = Field(
        ..., description="Lighting style for the scene"
    )
    direction: Literal["front", "side", "back", "top", "ambient"] = Field(
        ..., description="Light direction"
    )
    intensity: Literal["low", "medium", "high"] = Field(
        default="medium", description="Light intensity"
    )


class CompositionParams(BaseModel):
    """Composition parameters for FIBO structured prompt."""
    subject_position: Literal["center", "rule-of-thirds-left", "rule-of-thirds-right"] = Field(
        ..., description="Subject positioning in frame"
    )
    background: Literal["solid", "gradient", "environment", "studio"] = Field(
        ..., description="Background type"
    )
    depth_of_field: Literal["shallow", "medium", "deep"] = Field(
        default="medium", description="Depth of field"
    )


class StyleParams(BaseModel):
    """Style parameters for FIBO structured prompt."""
    color_palette: list[str] = Field(
        ..., min_length=1, description="Hex color codes for the scene"
    )
    material: Optional[str] = Field(
        default=None, description="Material type (fabric, leather, metal, etc.)"
    )
    mood: str = Field(..., description="Overall mood of the scene")
    aesthetic: Literal["professional", "artistic", "commercial", "editorial"] = Field(
        default="professional", description="Visual aesthetic"
    )


class SceneParameters(BaseModel):
    """Complete scene parameters for FIBO JSON generation."""
    scene_number: int = Field(..., ge=1, description="Scene number (1-indexed)")
    duration: float = Field(..., gt=0, description="Scene duration in seconds")
    scene_description: str = Field(..., min_length=1, description="Detailed scene description")
    camera: CameraParams = Field(..., description="Camera parameters")
    lighting: LightingParams = Field(..., description="Lighting parameters")
    composition: CompositionParams = Field(..., description="Composition parameters")
    style: StyleParams = Field(..., description="Style parameters")
    transition: Literal["fade", "dissolve", "cut", "cross-dissolve"] = Field(
        default="cross-dissolve", description="Transition effect to next scene"
    )


class EnhancedUserInput(BaseModel):
    """Enhanced user input with material and color control for FIBO JSON."""
    
    brand_name: str = Field(..., min_length=1, description="Brand name")
    product_name: str = Field(..., min_length=1, description="Product name")
    product_description: str = Field(..., min_length=1, description="Product description")
    duration: int = Field(default=8, ge=5, le=12, description="Video duration in seconds (5-12)")
    aspect_ratio: Literal["9:16", "1:1", "16:9"] = Field(
        default="9:16", description="Video aspect ratio"
    )
    
    # New fields for FIBO JSON control
    material: Optional[Literal["fabric", "leather", "metal", "wood", "glass", "plastic", "ceramic"]] = Field(
        default=None, description="Product material type"
    )
    primary_color: Optional[str] = Field(
        default=None, description="Primary color (hex format)"
    )
    secondary_color: Optional[str] = Field(
        default=None, description="Secondary color (hex format)"
    )
    style_mood: Optional[Literal["luxury", "minimal", "vibrant", "natural", "tech"]] = Field(
        default=None, description="Overall style mood"
    )

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Validate duration is within allowed range."""
        if v < 5 or v > 12:
            raise ValueError("Duration must be between 5 and 12 seconds")
        return v


class EnhancedStoryboard(BaseModel):
    """Storyboard with structured FIBO parameters."""
    
    brand_name: str = Field(..., description="Brand name")
    product_name: str = Field(..., description="Product name")
    total_duration: int = Field(..., ge=5, le=12, description="Total video duration in seconds")
    aspect_ratio: Literal["9:16", "1:1", "16:9"] = Field(..., description="Video aspect ratio")
    scenes: list[SceneParameters] = Field(
        ..., min_length=3, max_length=5, description="List of 3-5 scenes with structured parameters"
    )
    
    # Global parameters that can be modified for quick iteration
    global_material: Optional[str] = Field(
        default=None, description="Global material override"
    )
    global_color_palette: Optional[list[str]] = Field(
        default=None, description="Global color palette override"
    )

    @field_validator("scenes")
    @classmethod
    def validate_scenes(cls, v: list[SceneParameters]) -> list[SceneParameters]:
        """Validate scene count is within allowed range."""
        if len(v) < 3 or len(v) > 5:
            raise ValueError("Storyboard must contain 3-5 scenes")
        return v


# =============================================================================
# Original Models (v1)
# =============================================================================


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
