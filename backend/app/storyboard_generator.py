"""OpenAI-powered storyboard generator for FabFlow Studio."""
import json
from openai import AsyncOpenAI

from app.config import get_settings
from app.models import UserInput, Storyboard, EnhancedUserInput, EnhancedStoryboard

STORYBOARD_SYSTEM_PROMPT = """You are an expert advertising creative director. Your task is to generate compelling video ad storyboards for Instagram.

Given brand and product information, create a storyboard with 3-5 scenes that tells a compelling visual story.

For each scene, provide:
- A detailed visual description (prompt) suitable for AI image generation
- Camera angle: close-up, medium-shot, wide-shot, overhead, or low-angle
- Lighting style: soft, dramatic, natural, studio, or golden-hour
- Subject position: center, rule-of-thirds-left, or rule-of-thirds-right
- Color palette: 2-4 hex colors that match the brand aesthetic
- Mood: emotional tone of the scene
- Duration: how long the scene should last (distribute across total duration)
- Transition: fade, dissolve, cut, or slide to next scene

Create visually striking scenes that:
1. Open with an attention-grabbing hook
2. Showcase the product's key features
3. Build emotional connection with the viewer
4. End with a memorable brand moment

Ensure scene durations sum to the requested total duration."""

STORYBOARD_USER_TEMPLATE = """Create a video ad storyboard for:

Brand: {brand_name}
Product: {product_name}
Description: {product_description}

Video Settings:
- Total Duration: {duration} seconds
- Aspect Ratio: {aspect_ratio}

Generate a storyboard with 3-5 scenes. Distribute the {duration} seconds across all scenes."""


def build_storyboard_prompt(user_input: UserInput) -> str:
    """Build the user prompt for storyboard generation."""
    return STORYBOARD_USER_TEMPLATE.format(
        brand_name=user_input.brand_name,
        product_name=user_input.product_name,
        product_description=user_input.product_description,
        duration=user_input.duration,
        aspect_ratio=user_input.aspect_ratio,
    )


# JSON schema for OpenAI structured output
STORYBOARD_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "brand_name": {"type": "string"},
        "product_name": {"type": "string"},
        "total_duration": {"type": "integer"},
        "aspect_ratio": {"type": "string", "enum": ["9:16", "1:1", "16:9"]},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_number": {"type": "integer"},
                    "duration": {"type": "number"},
                    "transition": {"type": "string", "enum": ["fade", "dissolve", "cut", "slide"]},
                    "fibo_prompt": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string"},
                            "camera_angle": {
                                "type": "string",
                                "enum": ["close-up", "medium-shot", "wide-shot", "overhead", "low-angle"]
                            },
                            "lighting_style": {
                                "type": "string",
                                "enum": ["soft", "dramatic", "natural", "studio", "golden-hour"]
                            },
                            "subject_position": {
                                "type": "string",
                                "enum": ["center", "rule-of-thirds-left", "rule-of-thirds-right"]
                            },
                            "color_palette": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "mood": {"type": "string"}
                        },
                        "required": ["prompt", "camera_angle", "lighting_style", "subject_position", "color_palette", "mood"],
                        "additionalProperties": False
                    }
                },
                "required": ["scene_number", "duration", "transition", "fibo_prompt"],
                "additionalProperties": False
            },
            "minItems": 3,
            "maxItems": 5
        }
    },
    "required": ["brand_name", "product_name", "total_duration", "aspect_ratio", "scenes"],
    "additionalProperties": False
}


async def generate_storyboard(user_input: UserInput) -> Storyboard:
    """Generate a storyboard using OpenAI GPT-4o with structured output.
    
    Args:
        user_input: User input containing brand, product, and video settings.
        
    Returns:
        A validated Storyboard object.
        
    Raises:
        ValueError: If OpenAI response cannot be parsed into a valid Storyboard.
        Exception: If OpenAI API call fails.
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    user_prompt = build_storyboard_prompt(user_input)
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "storyboard",
                "strict": True,
                "schema": STORYBOARD_JSON_SCHEMA,
            }
        },
        temperature=0.7,
    )
    
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned empty response")
    
    storyboard_data = json.loads(content)
    return Storyboard.model_validate(storyboard_data)


# =============================================================================
# Enhanced Storyboard Generator (v2) - FIBO JSON Control
# Requirements: 2.1, 2.2, 2.3, 2.4
# =============================================================================

ENHANCED_SYSTEM_PROMPT = """You are an expert advertising creative director specializing in e-commerce product videos.

Generate storyboards as structured FIBO JSON parameters for professional product photography.

For each scene, provide precise parameters:
- camera.angle: close-up, medium-shot, wide-shot, overhead, low-angle, three-quarter
- camera.shot_type: product_hero, detail, lifestyle, context
- lighting.style: soft-studio, dramatic, natural-window, golden-hour, product-spotlight
- lighting.direction: front, side, back, top, ambient
- lighting.intensity: low, medium, high
- composition.subject_position: center, rule-of-thirds-left, rule-of-thirds-right
- composition.background: solid, gradient, environment, studio
- composition.depth_of_field: shallow, medium, deep
- style.color_palette: 2-4 hex colors
- style.material: fabric, leather, metal, wood, glass, plastic, ceramic (if applicable)
- style.mood: descriptive mood
- style.aesthetic: professional, artistic, commercial, editorial

Create a visual progression:
1. Scene 1: Hero shot - dramatic product reveal
2. Scene 2-3: Detail shots - showcase features/materials
3. Scene 4-5: Lifestyle/context - product in use

Use incremental camera angle changes (+15° per scene) for smooth visual flow.
Ensure scene durations sum exactly to the requested total duration.
Generate between 3 and 5 scenes."""

ENHANCED_USER_TEMPLATE = """Create a video ad storyboard for:

Brand: {brand_name}
Product: {product_name}
Description: {product_description}

Video Settings:
- Total Duration: {duration} seconds
- Aspect Ratio: {aspect_ratio}

Material Preference: {material}
Primary Color: {primary_color}
Secondary Color: {secondary_color}
Style Mood: {style_mood}

Generate a storyboard with 3-5 scenes. Distribute the {duration} seconds across all scenes.
The sum of all scene durations MUST equal exactly {duration} seconds."""


def build_enhanced_storyboard_prompt(user_input: EnhancedUserInput) -> str:
    """Build the user prompt for enhanced storyboard generation.
    
    Args:
        user_input: Enhanced user input with material and color preferences.
        
    Returns:
        Formatted prompt string for OpenAI.
    """
    return ENHANCED_USER_TEMPLATE.format(
        brand_name=user_input.brand_name,
        product_name=user_input.product_name,
        product_description=user_input.product_description,
        duration=user_input.duration,
        aspect_ratio=user_input.aspect_ratio,
        material=user_input.material or "not specified",
        primary_color=user_input.primary_color or "not specified",
        secondary_color=user_input.secondary_color or "not specified",
        style_mood=user_input.style_mood or "professional",
    )


# JSON schema for enhanced storyboard with SceneParameters structure
ENHANCED_STORYBOARD_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "brand_name": {"type": "string"},
        "product_name": {"type": "string"},
        "total_duration": {"type": "integer"},
        "aspect_ratio": {"type": "string", "enum": ["9:16", "1:1", "16:9"]},
        "global_material": {"type": ["string", "null"]},
        "global_color_palette": {
            "type": ["array", "null"],
            "items": {"type": "string"}
        },
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_number": {"type": "integer"},
                    "duration": {"type": "number"},
                    "scene_description": {"type": "string"},
                    "camera": {
                        "type": "object",
                        "properties": {
                            "angle": {
                                "type": "string",
                                "enum": ["close-up", "medium-shot", "wide-shot", "overhead", "low-angle", "three-quarter"]
                            },
                            "shot_type": {
                                "type": "string",
                                "enum": ["product_hero", "detail", "lifestyle", "context"]
                            }
                        },
                        "required": ["angle", "shot_type"],
                        "additionalProperties": False
                    },
                    "lighting": {
                        "type": "object",
                        "properties": {
                            "style": {
                                "type": "string",
                                "enum": ["soft-studio", "dramatic", "natural-window", "golden-hour", "product-spotlight"]
                            },
                            "direction": {
                                "type": "string",
                                "enum": ["front", "side", "back", "top", "ambient"]
                            },
                            "intensity": {
                                "type": "string",
                                "enum": ["low", "medium", "high"]
                            }
                        },
                        "required": ["style", "direction", "intensity"],
                        "additionalProperties": False
                    },
                    "composition": {
                        "type": "object",
                        "properties": {
                            "subject_position": {
                                "type": "string",
                                "enum": ["center", "rule-of-thirds-left", "rule-of-thirds-right"]
                            },
                            "background": {
                                "type": "string",
                                "enum": ["solid", "gradient", "environment", "studio"]
                            },
                            "depth_of_field": {
                                "type": "string",
                                "enum": ["shallow", "medium", "deep"]
                            }
                        },
                        "required": ["subject_position", "background", "depth_of_field"],
                        "additionalProperties": False
                    },
                    "style": {
                        "type": "object",
                        "properties": {
                            "color_palette": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "material": {"type": ["string", "null"]},
                            "mood": {"type": "string"},
                            "aesthetic": {
                                "type": "string",
                                "enum": ["professional", "artistic", "commercial", "editorial"]
                            }
                        },
                        "required": ["color_palette", "material", "mood", "aesthetic"],
                        "additionalProperties": False
                    },
                    "transition": {
                        "type": "string",
                        "enum": ["fade", "dissolve", "cut", "cross-dissolve"]
                    }
                },
                "required": ["scene_number", "duration", "scene_description", "camera", "lighting", "composition", "style", "transition"],
                "additionalProperties": False
            },
            "minItems": 3,
            "maxItems": 5
        }
    },
    "required": ["brand_name", "product_name", "total_duration", "aspect_ratio", "global_material", "global_color_palette", "scenes"],
    "additionalProperties": False
}


async def generate_enhanced_storyboard(user_input: EnhancedUserInput) -> EnhancedStoryboard:
    """Generate a storyboard with structured FIBO parameters using OpenAI GPT-4o.
    
    This enhanced version generates storyboards with precise camera, lighting,
    composition, and style parameters that map directly to FIBO's structured
    prompt format for deterministic, high-quality product shots.
    
    Args:
        user_input: Enhanced user input containing brand, product, video settings,
                   and optional material/color preferences.
        
    Returns:
        An EnhancedStoryboard object with structured SceneParameters.
        
    Raises:
        ValueError: If OpenAI response cannot be parsed into a valid EnhancedStoryboard.
        Exception: If OpenAI API call fails.
        
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    user_prompt = build_enhanced_storyboard_prompt(user_input)
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ENHANCED_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "enhanced_storyboard",
                "strict": True,
                "schema": ENHANCED_STORYBOARD_JSON_SCHEMA,
            }
        },
        temperature=0.7,
    )
    
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned empty response")
    
    storyboard_data = json.loads(content)
    return EnhancedStoryboard.model_validate(storyboard_data)
