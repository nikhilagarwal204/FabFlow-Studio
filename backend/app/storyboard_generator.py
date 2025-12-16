"""OpenAI-powered storyboard generator for FabFlow Studio."""
import json
from openai import AsyncOpenAI

from app.config import get_settings
from app.models import UserInput, Storyboard

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
