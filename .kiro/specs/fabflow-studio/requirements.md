# Requirements Document

## Introduction

FabFlow Studio is a prototype AI-powered ad video creation platform designed for the Bria FIBO hackathon. The platform enables non-technical business owners to create short, Instagram-ready advertisement videos by simply providing their brand name, product description, or uploading a product image. The system leverages OpenAI GPT-4o for storyboard generation and Bria's FIBO API for deterministic, high-quality frame generation, producing polished video ads through an automated pipeline.

## Glossary

- **FabFlow_Studio**: The web-based ad video creation platform
- **FIBO_API**: Bria's image generation API that uses structured JSON prompts for deterministic visual generation
- **Storyboard_JSON**: A structured JSON object containing scene definitions, camera angles, durations, and visual styles
- **Scene**: A single visual segment of the ad video with specific composition, lighting, and subject parameters
- **Frame_Generator**: The component that calls FIBO API to generate individual frames for each scene
- **Compositing_Engine**: The component that assembles frames into a final video with transitions and effects
- **Structured_Prompt**: The JSON format required by FIBO API for image generation
- **LLM_Agent**: The OpenAI GPT-4o component that generates storyboards from user input

## Requirements

### Requirement 1

**User Story:** As a business owner, I want to input my brand and product information, so that I can start creating an ad video without technical knowledge.

#### Acceptance Criteria

1. WHEN a user enters a brand name and product description THEN the FabFlow_Studio SHALL accept the input and store it for processing
2. WHEN a user uploads a product image THEN the FabFlow_Studio SHALL validate the image format and store it for reference
3. WHEN a user provides incomplete information THEN the FabFlow_Studio SHALL display clear guidance on required fields
4. WHEN a user submits valid input THEN the FabFlow_Studio SHALL proceed to storyboard generation within 5 seconds
5. WHEN a user selects video duration THEN the FabFlow_Studio SHALL accept values between 5 and 12 seconds inclusive
6. WHEN a user selects aspect ratio THEN the FabFlow_Studio SHALL offer options for 9:16 vertical, 1:1 square, and 16:9 horizontal formats
7. WHEN a user does not select duration or aspect ratio THEN the FabFlow_Studio SHALL default to 8 seconds and 9:16 vertical

### Requirement 2

**User Story:** As a business owner, I want the system to automatically generate a creative storyboard, so that I don't need to plan video scenes manually.

#### Acceptance Criteria

1. WHEN the LLM_Agent receives brand and product information THEN the LLM_Agent SHALL generate a Storyboard_JSON containing 3-5 scenes
2. WHEN generating a Storyboard_JSON THEN the LLM_Agent SHALL include for each scene: camera angle, lighting style, color palette, subject positioning, and duration
3. WHEN a product image is provided THEN the LLM_Agent SHALL incorporate visual elements from the image into scene descriptions
4. WHEN the Storyboard_JSON is generated THEN the FabFlow_Studio SHALL display a preview of the planned scenes to the user
5. WHEN serializing the Storyboard_JSON THEN the FabFlow_Studio SHALL produce valid JSON that can be parsed back to the original structure
6. WHEN generating scene durations THEN the LLM_Agent SHALL distribute time across scenes to fit within the user-selected total duration
7. WHEN generating scenes THEN the LLM_Agent SHALL use the user-selected aspect ratio for all frame compositions

### Requirement 3

**User Story:** As a business owner, I want each scene converted to FIBO-compatible prompts, so that the AI can generate consistent, high-quality frames.

#### Acceptance Criteria

1. WHEN a Storyboard_JSON scene is processed THEN the FabFlow_Studio SHALL translate it into a valid FIBO Structured_Prompt
2. WHEN translating scenes THEN the FabFlow_Studio SHALL map storyboard parameters to FIBO JSON fields for camera, lighting, composition, and style
3. WHEN a translation is complete THEN the FabFlow_Studio SHALL validate the Structured_Prompt against FIBO API requirements
4. WHEN parsing a Structured_Prompt THEN the FabFlow_Studio SHALL reconstruct the original prompt data without loss

### Requirement 4

**User Story:** As a business owner, I want frames generated for each scene, so that my video has smooth, professional visuals.

#### Acceptance Criteria

1. WHEN the Frame_Generator receives a Structured_Prompt THEN the Frame_Generator SHALL call the FIBO_API and retrieve the generated image
2. WHEN generating frames for a scene THEN the Frame_Generator SHALL produce the number of frames specified by the scene duration and target frame rate
3. WHEN the FIBO_API returns an error THEN the Frame_Generator SHALL retry up to 3 times before reporting failure to the user
4. WHEN frames are generated THEN the Frame_Generator SHALL store them in sequential order for compositing

### Requirement 5

**User Story:** As a business owner, I want the final video assembled with smooth transitions, so that my ad looks professional and polished.

#### Acceptance Criteria

1. WHEN the Compositing_Engine receives all scene frames THEN the Compositing_Engine SHALL assemble them into a single video file
2. WHEN assembling scenes THEN the Compositing_Engine SHALL apply transition effects between scenes as specified in the Storyboard_JSON
3. WHEN the video is assembled THEN the Compositing_Engine SHALL output the video in MP4 format suitable for Instagram
4. WHEN compositing is complete THEN the FabFlow_Studio SHALL provide a download link to the user within 30 seconds of completion
5. WHEN assembling the video THEN the Compositing_Engine SHALL match the user-selected aspect ratio for the final output
6. WHEN assembling the video THEN the Compositing_Engine SHALL produce output matching the user-selected duration between 5 and 12 seconds

### Requirement 6

**User Story:** As a business owner, I want to see the progress of my video generation, so that I know the system is working and can estimate completion time.

#### Acceptance Criteria

1. WHEN video generation begins THEN the FabFlow_Studio SHALL display a progress indicator showing current stage
2. WHEN each stage completes THEN the FabFlow_Studio SHALL update the progress indicator with the next stage name
3. WHEN an error occurs during generation THEN the FabFlow_Studio SHALL display a clear error message with suggested actions
4. WHEN generation is complete THEN the FabFlow_Studio SHALL notify the user and display the final video preview

### Requirement 7

**User Story:** As a developer, I want the system to handle FIBO API responses asynchronously, so that the application remains responsive during generation.

#### Acceptance Criteria

1. WHEN the FabFlow_Studio sends a request to FIBO_API THEN the FabFlow_Studio SHALL handle the asynchronous response using the status service
2. WHEN polling for FIBO_API status THEN the FabFlow_Studio SHALL check at intervals of 2 seconds until completion
3. WHEN the FIBO_API request completes THEN the FabFlow_Studio SHALL retrieve and process the generated image immediately
4. WHEN multiple frames are requested THEN the FabFlow_Studio SHALL manage concurrent requests efficiently
