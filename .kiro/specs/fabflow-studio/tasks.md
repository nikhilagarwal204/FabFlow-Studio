# Implementation Plan

## FabFlow Studio - Hackathon Prototype

Architecture: Next.js frontend (Vercel) + FastAPI backend (Railway/Render)

- [x] 1. Project Setup and Configuration
  - [x] 1.1 Initialize FastAPI backend project
    - Create Python project with FastAPI, uvicorn
    - Set up environment variables (OPENAI_API_KEY, BRIA_API_KEY)
    - Configure CORS for frontend
    - Create requirements.txt with dependencies (fastapi, uvicorn, openai, httpx, python-multipart)
    - _Requirements: 7.1_
  - [x] 1.2 Initialize Next.js frontend project
    - Create Next.js app with App Router and TypeScript
    - Install axios for API calls
    - Install UI components (shadcn/ui)
    - Configure environment variable for backend URL
    - _Requirements: 2.1_

- [ ] 2. User Input Interface
  - [ ] 2.1 Create input form component
    - Build form with brand name, product name, description fields
    - Add duration slider (5-12 seconds)
    - Add aspect ratio selector (9:16, 1:1, 16:9)
    - Implement client-side validation
    - _Requirements: 1.1, 1.3, 1.5, 1.6, 1.7_
  - [ ]* 2.2 Add image upload support
    - Add image upload with drag-and-drop support
    - Validate image MIME types (jpeg, png, webp)
    - _Requirements: 1.2_
  - [ ] 2.3 Create input validation utility
    - Implement validateUserInput function
    - Validate required fields, duration range, aspect ratio options
    - Return structured error messages
    - _Requirements: 1.1, 1.3, 1.5_

- [ ] 3. Storyboard Generation (Backend)
  - [ ] 3.1 Create Pydantic models for storyboard
    - Define Scene, FIBOPrompt, Storyboard, UserInput models
    - Add validation for duration (5-12), aspect ratio options
    - _Requirements: 2.1, 2.2, 2.5_
  - [ ] 3.2 Create OpenAI storyboard generator
    - Build prompt template for ad storyboard generation
    - Use OpenAI response_format for structured JSON output
    - Parse response into Storyboard model
    - _Requirements: 2.1, 2.2, 2.6, 2.7_
  - [ ] 3.3 Create /api/generate-storyboard endpoint
    - POST endpoint accepting UserInput
    - Return Storyboard JSON
    - Handle OpenAI errors gracefully
    - _Requirements: 1.4, 2.1_
  - [ ]* 3.4 Create storyboard preview component (Frontend)
    - Display generated scenes with descriptions
    - Show camera angle, lighting, duration for each scene
    - _Requirements: 2.4_

- [ ] 4. FIBO API Integration (Backend)
  - [ ] 4.1 Create FIBO API client class
    - Implement generate_image method for text-to-image
    - Implement poll_status method for async responses
    - Handle API errors and timeouts
    - _Requirements: 3.1, 3.2, 3.3, 7.1, 7.2, 7.3_
  - [ ]* 4.2 Add structured-prompt-generate support
    - Implement structured-prompt-generate endpoint call
    - Map storyboard scene data to structured prompt format
    - _Requirements: 3.1, 3.2_
  - [ ]* 4.3 Add translation endpoint support
    - Implement generate_with_reference method
    - Handle reference image URL in requests
    - _Requirements: 1.2, 3.1_
  - [ ]* 4.4 Implement retry logic
    - Retry failed FIBO requests up to 3 times
    - Exponential backoff between retries
    - _Requirements: 4.3_

- [ ] 5. Frame Generation Pipeline (Backend)
  - [ ] 5.1 Create frame generator service
    - Calculate frame count based on scene duration
    - Generate key frame for each scene using FIBO
    - Download and store frames locally
    - _Requirements: 4.1, 4.2, 4.4_

- [ ] 6. Video Compositing (Backend)
  - [ ] 6.1 Create FFmpeg compositing engine
    - Install FFmpeg on server (add to Dockerfile/requirements)
    - Scale frames to correct aspect ratio dimensions
    - Create video from frames with scene durations
    - Output MP4 file
    - _Requirements: 5.1, 5.3, 5.5, 5.6_
  - [ ]* 6.2 Add transition effects
    - Apply fade transitions between scenes using FFmpeg filters
    - _Requirements: 5.2_
  - [ ] 6.3 Create /api/generate-video endpoint
    - Full pipeline: storyboard -> frames -> video
    - Return job_id for progress polling
    - Serve final video file
    - _Requirements: 5.1, 5.4_

- [ ] 7. Job Status and Progress (Backend)
  - [ ] 7.1 Create job tracking system
    - Store job status in memory (dict for prototype)
    - Track stages: storyboard, frame-generation, compositing, complete
    - _Requirements: 6.1, 6.2_
  - [ ] 7.2 Create /api/job/{id}/status endpoint
    - Return current stage and progress percentage
    - _Requirements: 6.1, 6.2_
  - [ ] 7.3 Create /api/job/{id}/result endpoint
    - Return video URL when job is complete
    - _Requirements: 5.4, 6.4_

- [ ] 8. Frontend UI Components
  - [ ] 8.1 Create progress tracker component
    - Poll backend for job status
    - Display current pipeline stage with progress bar
    - _Requirements: 6.1, 6.2_
  - [ ] 8.2 Create video player component
    - Display final video with playback controls
    - Provide download button
    - _Requirements: 5.4, 6.4_
  - [ ]* 8.3 Implement error handling UI
    - Display user-friendly error messages
    - Provide retry options
    - _Requirements: 6.3_

- [ ] 9. End-to-End Integration
  - [ ] 9.1 Wire up frontend to backend
    - Connect form submission to /api/generate-video
    - Poll job status and update progress UI
    - Display video when complete
    - _Requirements: 1.4, 6.4_
  - [ ]* 9.2 Deploy backend to Railway/Render
    - Create Dockerfile with FFmpeg
    - Configure environment variables
    - Test full pipeline
    - _Requirements: All_
