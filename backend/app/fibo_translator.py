"""FIBO Structured Prompt Translator for enhanced JSON control.

Translates SceneParameters to FIBO API format for deterministic,
parameter-driven frame generation.

Requirements: 3.1, 3.2, 3.3, 3.4
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.models import SceneParameters


class FIBOStructuredPromptV2(BaseModel):
    """Enhanced structured prompt for FIBO API.
    
    Provides precise control over scene generation through structured JSON
    parameters that map directly to FIBO's structured-prompt-generate endpoint.
    
    Attributes:
        scene_description: Detailed text description of the scene.
        camera: Camera parameters (angle, shot_type).
        lighting: Lighting parameters (type, direction, intensity).
        composition: Composition parameters (subject_position, background, depth_of_field).
        style: Style parameters (color_palette, material, mood, aesthetic).
    """
    
    scene_description: str = Field(..., description="Detailed scene description")
    camera: dict = Field(..., description="Camera parameters for FIBO")
    lighting: dict = Field(..., description="Lighting parameters for FIBO")
    composition: dict = Field(..., description="Composition parameters for FIBO")
    style: dict = Field(..., description="Style parameters for FIBO")
    
    @classmethod
    def from_scene_parameters(cls, params: SceneParameters) -> "FIBOStructuredPromptV2":
        """Translate SceneParameters to FIBO structured prompt format.
        
        Maps all SceneParameters fields to FIBO API JSON structure,
        converting hyphenated values to underscored format as required
        by the FIBO API.
        
        Args:
            params: SceneParameters object with camera, lighting, composition,
                   and style settings.
                   
        Returns:
            FIBOStructuredPromptV2 ready for API submission.
            
        Requirements: 3.1, 3.2
        """
        return cls(
            scene_description=params.scene_description,
            camera={
                "angle": params.camera.angle.replace("-", "_"),
                "shot_type": params.camera.shot_type
            },
            lighting={
                "type": params.lighting.style.replace("-", "_"),
                "direction": params.lighting.direction,
                "intensity": params.lighting.intensity
            },
            composition={
                "subject_position": params.composition.subject_position.replace("-", "_"),
                "background": params.composition.background,
                "depth_of_field": params.composition.depth_of_field
            },
            style={
                "color_palette": params.style.color_palette,
                "material": params.style.material,
                "mood": params.style.mood,
                "aesthetic": params.style.aesthetic
            }
        )
    
    def to_api_payload(self, aspect_ratio: str = "9:16") -> dict:
        """Convert to FIBO API request payload.
        
        Builds the complete request payload for FIBO's structured-prompt-generate
        endpoint, including the structured_prompt object and generation parameters.
        
        Args:
            aspect_ratio: Video aspect ratio (9:16, 1:1, 16:9). Defaults to 9:16.
            
        Returns:
            Dictionary ready for JSON serialization to FIBO API.
            
        Requirements: 3.1, 3.2, 3.3
        """
        return {
            "structured_prompt": {
                "scene_description": self.scene_description,
                "camera": self.camera,
                "lighting": self.lighting,
                "composition": self.composition,
                "style": self.style
            },
            "num_results": 1,
            "aspect_ratio": aspect_ratio,
            "sync": True
        }
    
    @classmethod
    def from_api_payload(cls, payload: dict) -> "FIBOStructuredPromptV2":
        """Parse a FIBO API payload back to FIBOStructuredPromptV2.
        
        Reconstructs a FIBOStructuredPromptV2 from an API payload format,
        enabling round-trip serialization/deserialization.
        
        Args:
            payload: Dictionary in FIBO API payload format.
            
        Returns:
            FIBOStructuredPromptV2 instance.
            
        Requirements: 3.4
        """
        structured_prompt = payload.get("structured_prompt", payload)
        
        return cls(
            scene_description=structured_prompt["scene_description"],
            camera=structured_prompt["camera"],
            lighting=structured_prompt["lighting"],
            composition=structured_prompt["composition"],
            style=structured_prompt["style"]
        )
