"""Parameter Modification Service for FIBO JSON Pipeline.

Enables changing single parameters (material, color, etc.) in storyboards
without full regeneration, supporting quick iteration on product visuals.

Requirements: 4.1, 4.2, 4.3, 4.4
"""
from copy import deepcopy
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from app.models import EnhancedStoryboard, SceneParameters


class ParameterModification(BaseModel):
    """Request to modify a single parameter in a storyboard.
    
    Supports modifying parameters at various levels:
    - Global parameters (global_material, global_color_palette)
    - Scene-level parameters using dot notation (e.g., "style.material", "camera.angle")
    
    Attributes:
        parameter_path: Dot-notation path to the parameter (e.g., "style.material").
        new_value: The new value to set for the parameter.
        apply_to_scenes: Scene numbers to apply the change to. Empty list means all scenes.
    
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    
    parameter_path: str = Field(
        ...,
        description="Dot-notation path to the parameter (e.g., 'style.material', 'camera.angle')"
    )
    new_value: Any = Field(
        ...,
        description="New value for the parameter"
    )
    apply_to_scenes: list[int] = Field(
        default_factory=list,
        description="Scene numbers to apply to. Empty list means all scenes."
    )


class ModificationResult(BaseModel):
    """Result of a parameter modification operation.
    
    Provides information about which scenes were modified and which frames
    need to be regenerated, along with a snapshot of preserved parameters.
    
    Attributes:
        success: Whether the modification was successful.
        modified_scenes: List of scene numbers that were modified.
        frames_to_regenerate: List of scene numbers whose frames need regeneration.
        preserved_parameters: Dictionary showing parameters that remained unchanged.
        error: Error message if modification failed.
    
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    
    success: bool = Field(..., description="Whether the modification was successful")
    modified_scenes: list[int] = Field(
        default_factory=list,
        description="Scene numbers that were modified"
    )
    frames_to_regenerate: list[int] = Field(
        default_factory=list,
        description="Scene numbers whose frames need regeneration"
    )
    preserved_parameters: dict = Field(
        default_factory=dict,
        description="Parameters that remained unchanged"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if modification failed"
    )



def _get_nested_value(obj: Any, path: str) -> Any:
    """Get a nested value from an object using dot notation.
    
    Args:
        obj: The object to traverse (can be dict or Pydantic model).
        path: Dot-notation path (e.g., "style.material").
        
    Returns:
        The value at the specified path.
        
    Raises:
        KeyError: If the path doesn't exist.
    """
    parts = path.split(".")
    current = obj
    
    for part in parts:
        if isinstance(current, dict):
            current = current[part]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            raise KeyError(f"Path '{path}' not found: '{part}' doesn't exist")
    
    return current


def _set_nested_value(obj: Any, path: str, value: Any) -> None:
    """Set a nested value in an object using dot notation.
    
    Modifies the object in place.
    
    Args:
        obj: The object to modify (can be dict or Pydantic model).
        path: Dot-notation path (e.g., "style.material").
        value: The value to set.
        
    Raises:
        KeyError: If the path doesn't exist.
    """
    parts = path.split(".")
    current = obj
    
    # Navigate to the parent of the target
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current[part]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            raise KeyError(f"Path '{path}' not found: '{part}' doesn't exist")
    
    # Set the final value
    final_key = parts[-1]
    if isinstance(current, dict):
        current[final_key] = value
    elif hasattr(current, final_key):
        setattr(current, final_key, value)
    else:
        raise KeyError(f"Path '{path}' not found: '{final_key}' doesn't exist")


def _extract_preserved_parameters(scene: SceneParameters, modified_path: str) -> dict:
    """Extract parameters that were not modified for verification.
    
    Creates a snapshot of all parameters except the one being modified,
    useful for verifying parameter isolation.
    
    Args:
        scene: The scene to extract parameters from.
        modified_path: The path that was modified (to exclude).
        
    Returns:
        Dictionary of preserved parameter paths and their values.
    """
    preserved = {}
    
    # Extract all parameter paths and values
    param_paths = [
        ("camera.angle", scene.camera.angle),
        ("camera.shot_type", scene.camera.shot_type),
        ("lighting.style", scene.lighting.style),
        ("lighting.direction", scene.lighting.direction),
        ("lighting.intensity", scene.lighting.intensity),
        ("composition.subject_position", scene.composition.subject_position),
        ("composition.background", scene.composition.background),
        ("composition.depth_of_field", scene.composition.depth_of_field),
        ("style.color_palette", scene.style.color_palette),
        ("style.material", scene.style.material),
        ("style.mood", scene.style.mood),
        ("style.aesthetic", scene.style.aesthetic),
        ("scene_description", scene.scene_description),
        ("duration", scene.duration),
        ("transition", scene.transition),
    ]
    
    for path, value in param_paths:
        if path != modified_path:
            preserved[path] = value
    
    return preserved


def apply_parameter_modification(
    storyboard: EnhancedStoryboard,
    modification: ParameterModification
) -> tuple[EnhancedStoryboard, ModificationResult]:
    """Apply a single parameter change to a storyboard.
    
    Modifies the specified parameter in the storyboard while preserving
    all other parameters. Supports both global parameters and scene-level
    parameters.
    
    Args:
        storyboard: The storyboard to modify.
        modification: The modification to apply.
        
    Returns:
        Tuple of (modified_storyboard, modification_result).
        The modified_storyboard is a deep copy with the change applied.
        The modification_result contains information about what was changed.
        
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    # Create a deep copy to avoid mutating the original
    modified_storyboard = storyboard.model_copy(deep=True)
    
    # Determine which scenes to modify
    if modification.apply_to_scenes:
        target_scenes = modification.apply_to_scenes
    else:
        # Empty list means all scenes
        target_scenes = [scene.scene_number for scene in modified_storyboard.scenes]
    
    modified_scenes: list[int] = []
    frames_to_regenerate: list[int] = []
    preserved_parameters: dict = {}
    
    try:
        # Handle global parameters
        if modification.parameter_path.startswith("global_"):
            if modification.parameter_path == "global_material":
                modified_storyboard.global_material = modification.new_value
                # Also update all target scenes' style.material
                for scene in modified_storyboard.scenes:
                    if scene.scene_number in target_scenes:
                        preserved_parameters[scene.scene_number] = _extract_preserved_parameters(
                            scene, "style.material"
                        )
                        scene.style.material = modification.new_value
                        modified_scenes.append(scene.scene_number)
                        frames_to_regenerate.append(scene.scene_number)
                        
            elif modification.parameter_path == "global_color_palette":
                modified_storyboard.global_color_palette = modification.new_value
                # Also update all target scenes' style.color_palette
                for scene in modified_storyboard.scenes:
                    if scene.scene_number in target_scenes:
                        preserved_parameters[scene.scene_number] = _extract_preserved_parameters(
                            scene, "style.color_palette"
                        )
                        scene.style.color_palette = modification.new_value
                        modified_scenes.append(scene.scene_number)
                        frames_to_regenerate.append(scene.scene_number)
            else:
                return modified_storyboard, ModificationResult(
                    success=False,
                    error=f"Unknown global parameter: {modification.parameter_path}"
                )
        else:
            # Handle scene-level parameters
            for scene in modified_storyboard.scenes:
                if scene.scene_number in target_scenes:
                    # Capture preserved parameters before modification
                    preserved_parameters[scene.scene_number] = _extract_preserved_parameters(
                        scene, modification.parameter_path
                    )
                    
                    # Apply the modification
                    _set_nested_value(scene, modification.parameter_path, modification.new_value)
                    modified_scenes.append(scene.scene_number)
                    frames_to_regenerate.append(scene.scene_number)
        
        return modified_storyboard, ModificationResult(
            success=True,
            modified_scenes=modified_scenes,
            frames_to_regenerate=frames_to_regenerate,
            preserved_parameters=preserved_parameters
        )
        
    except KeyError as e:
        return modified_storyboard, ModificationResult(
            success=False,
            error=str(e)
        )
    except Exception as e:
        return modified_storyboard, ModificationResult(
            success=False,
            error=f"Failed to apply modification: {str(e)}"
        )
