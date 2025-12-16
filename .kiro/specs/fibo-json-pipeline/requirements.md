# Requirements Document

## Introduction

This specification enhances FabFlow Studio to fully leverage FIBO's JSON-native architecture for professional-grade product ad video generation. The key innovation is parameter-driven deterministic frame generation - enabling real-time customization (material, color, angle changes) without full regeneration. This transforms the platform from simple image stitching into a professional e-commerce video production tool that generates high-value product shots comparable to professional studio photography.

## Glossary

- **FIBO_JSON_Pipeline**: The enhanced video generation system using FIBO's structured JSON prompts for deterministic control
- **Structured_Prompt**: FIBO's JSON format enabling precise control over scene_description, camera, lighting, composition, and style parameters
- **Parameter_Isolation**: The ability to change a single parameter (e.g., material) while keeping all other visual elements deterministic
- **Key_Frame**: A single high-quality frame generated per scene using FIBO's structured prompt
- **Scene_Parameters**: The JSON object containing camera_angle, lighting_style, color_palette, material, composition settings
- **LLM_Planner**: GPT-4o component that translates creative briefs into structured FIBO JSON parameters
- **Frame_Compositor**: FFmpeg-based component that assembles key frames into video with transitions

## Requirements

### Requirement 1

**User Story:** As a business owner, I want to provide my product details and creative direction, so that the system generates professional product shots.

#### Acceptance Criteria

1. WHEN a user enters brand name, product name, and description THEN the FIBO_JSON_Pipeline SHALL accept the input for processing
2. WHEN a user specifies a material type (fabric, leather, metal, wood, glass) THEN the FIBO_JSON_Pipeline SHALL include the material in Structured_Prompt generation
3. WHEN a user specifies a color preference THEN the FIBO_JSON_Pipeline SHALL map the color to the Structured_Prompt color_palette field
4. WHEN a user selects video duration (5-12 seconds) THEN the FIBO_JSON_Pipeline SHALL distribute duration across generated scenes
5. WHEN a user selects aspect ratio (9:16, 1:1, 16:9) THEN the FIBO_JSON_Pipeline SHALL configure all Structured_Prompts for that ratio

### Requirement 2

**User Story:** As a business owner, I want the LLM to plan my video as a sequence of structured FIBO JSON prompts, so that each frame has precise visual control.

#### Acceptance Criteria

1. WHEN the LLM_Planner receives product information THEN the LLM_Planner SHALL generate 3-5 Scene_Parameters objects
2. WHEN generating Scene_Parameters THEN the LLM_Planner SHALL include camera_angle, lighting_style, subject_position, color_palette, and material for each scene
3. WHEN generating camera angles THEN the LLM_Planner SHALL use values from: close-up, medium-shot, wide-shot, overhead, low-angle, three-quarter
4. WHEN generating lighting styles THEN the LLM_Planner SHALL use values from: soft-studio, dramatic, natural-window, golden-hour, product-spotlight
5. WHEN generating scene transitions THEN the LLM_Planner SHALL specify incremental parameter changes (e.g., camera_angle +15° per scene) for visual continuity
6. WHEN serializing Scene_Parameters THEN the FIBO_JSON_Pipeline SHALL produce valid JSON that can be parsed back to the original structure

### Requirement 3

**User Story:** As a business owner, I want each scene converted to FIBO's structured prompt format, so that I get deterministic, high-quality product shots.

#### Acceptance Criteria

1. WHEN Scene_Parameters are processed THEN the FIBO_JSON_Pipeline SHALL translate them into valid FIBO Structured_Prompt JSON
2. WHEN translating to Structured_Prompt THEN the FIBO_JSON_Pipeline SHALL map: scene_description, camera.angle, camera.shot_type, lighting.type, lighting.direction, composition.subject_position, style.color_palette, style.mood
3. WHEN a Structured_Prompt is generated THEN the FIBO_JSON_Pipeline SHALL validate all required fields are present
4. WHEN parsing a Structured_Prompt THEN the FIBO_JSON_Pipeline SHALL reconstruct the original prompt data without loss

### Requirement 4

**User Story:** As a business owner, I want to change a single parameter (like material or color) and regenerate only affected frames, so that I can iterate quickly.

#### Acceptance Criteria

1. WHEN a user modifies a single parameter in Scene_Parameters THEN the FIBO_JSON_Pipeline SHALL identify which frames require regeneration
2. WHEN regenerating frames THEN the FIBO_JSON_Pipeline SHALL preserve all unchanged parameters in the Structured_Prompt
3. WHEN a material parameter changes THEN the FIBO_JSON_Pipeline SHALL update only the material field while keeping camera, lighting, and composition identical
4. WHEN a color parameter changes THEN the FIBO_JSON_Pipeline SHALL update only the color_palette field while keeping other parameters identical

### Requirement 5

**User Story:** As a business owner, I want key frames generated for each scene using FIBO's structured prompts, so that my video has professional product photography quality.

#### Acceptance Criteria

1. WHEN the Frame_Generator receives a Structured_Prompt THEN the Frame_Generator SHALL call FIBO's structured-prompt-generate endpoint
2. WHEN generating frames THEN the Frame_Generator SHALL produce one key frame per scene
3. WHEN FIBO API returns an error THEN the Frame_Generator SHALL retry up to 3 times with exponential backoff
4. WHEN frames are generated THEN the Frame_Generator SHALL download and store them in sequential order

### Requirement 6

**User Story:** As a business owner, I want the final video assembled with smooth transitions, so that my ad looks professional.

#### Acceptance Criteria

1. WHEN the Frame_Compositor receives all key frames THEN the Frame_Compositor SHALL assemble them into a single MP4 video
2. WHEN assembling scenes THEN the Frame_Compositor SHALL apply cross-dissolve transitions between frames
3. WHEN the video is assembled THEN the Frame_Compositor SHALL output H.264 MP4 optimized for Instagram
4. WHEN compositing is complete THEN the FIBO_JSON_Pipeline SHALL provide a download link within 30 seconds

### Requirement 7

**User Story:** As a business owner, I want to see generation progress, so that I know the system is working.

#### Acceptance Criteria

1. WHEN video generation begins THEN the FIBO_JSON_Pipeline SHALL display progress showing current stage
2. WHEN each stage completes THEN the FIBO_JSON_Pipeline SHALL update progress with the next stage
3. WHEN an error occurs THEN the FIBO_JSON_Pipeline SHALL display a clear error message with retry option
4. WHEN generation completes THEN the FIBO_JSON_Pipeline SHALL display the final video preview
