# FabFlow Studio

AI-powered ad video creation platform for Instagram. Users provide brand/product details and the system generates professional video ads.

## Core Workflow

1. User submits brand name, product name, description, duration (5-12s), and aspect ratio
2. Backend generates a storyboard (3-5 scenes) using OpenAI GPT-4o
3. FIBO API (Bria) generates key frames for each scene
4. FFmpeg composites frames into final MP4 video
5. User downloads/views the completed video

## Key Features

- Storyboard generation with scene-by-scene prompts
- Support for 9:16 (Stories/Reels), 1:1 (Feed), 16:9 (YouTube) aspect ratios
- Background job processing with real-time progress polling
- Video output optimized for Instagram (H.264, MP4)
