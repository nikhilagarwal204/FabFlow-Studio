# Implementation Plan

## FIBO JSON Pipeline - Enhanced Video Generation

This plan enhances FabFlow Studio to leverage FIBO's JSON-native architecture for professional product ad generation.

- [x] 1. Enhanced Data Models
  - [x] 1.1 Create enhanced Pydantic models for FIBO JSON control
    - Add CameraParams, LightingParams, CompositionParams, StyleParams models
    - Create SceneParameters model combining all parameter types
    - Add EnhancedUserInput with material and color fields
    - Create EnhancedStoryboard model with global parameters
    - _Requirements: 1.2, 1.3, 2.2_
  - [ ]* 1.2 Write property test for scene parameters validation
    - **Property 4: Scene Parameters Have Valid Required Fields**
    - **Validates: Requirements 2.2, 2.3, 2.4**
  - [ ]* 1.3 Write property test for scene parameters round-trip
    - **Property 5: Scene Parameters Round-Trip**
    - **Validates: Requirements 2.6**

- [-] 2. FIBO Structured Prompt Translator
  - [x] 2.1 Create FIBOStructuredPromptV2 translator class
    - Implement from_scene_parameters() class method
    - Implement to_api_payload() method for FIBO API format
    - Map all parameter fields to FIBO JSON structure
    - _Requirements: 3.1, 3.2_
  - [ ]* 2.2 Write property test for translation completeness
    - **Property 6: Translation Produces Valid Complete Structured Prompt**
    - **Validates: Requirements 3.1, 3.2, 3.3**
  - [ ]* 2.3 Write property test for structured prompt round-trip
    - **Property 7: Structured Prompt Round-Trip**
    - **Validates: Requirements 3.4**

- [-] 3. Enhanced LLM Planner
  - [x] 3.1 Update storyboard generator for structured FIBO output
    - Create enhanced system prompt for FIBO JSON parameters
    - Update JSON schema for SceneParameters structure
    - Implement generate_enhanced_storyboard() function
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 3.2 Write property test for scene count validation
    - **Property 3: Scene Count Within Bounds**
    - **Validates: Requirements 2.1**
  - [ ]* 3.3 Write property test for duration distribution
    - **Property 2: Duration Distribution Sums to Total**
    - **Validates: Requirements 1.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Parameter Modification Service
  - [x] 5.1 Create parameter modification models and service
    - Create ParameterModification request model
    - Create ModificationResult response model
    - Implement apply_parameter_modification() function
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [ ]* 5.2 Write property test for parameter isolation
    - **Property 8: Parameter Modification Preserves Unchanged Fields**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [x] 6. Enhanced Frame Generator
  - [x] 6.1 Update FIBO client for structured prompt generation
    - Add generate_with_structured_prompt() method
    - Use structured_prompt field in API payload
    - _Requirements: 5.1_
  - [x] 6.2 Create EnhancedFrameGenerator service
    - Implement generate_frame_for_scene() using structured prompts
    - Implement regenerate_modified_frames() for parameter changes
    - _Requirements: 5.2, 5.4_
  - [ ]* 6.3 Write property test for frame count
    - **Property 9: Frame Count Equals Scene Count**
    - **Validates: Requirements 5.2**
  - [ ]* 6.4 Write property test for frame ordering
    - **Property 10: Frames Are Ordered by Scene Number**
    - **Validates: Requirements 5.4**

- [x] 7. API Endpoints
  - [x] 7.1 Create v2 API endpoints
    - POST /api/v2/generate-storyboard - enhanced storyboard generation
    - POST /api/v2/generate-video - full pipeline with structured FIBO
    - POST /api/v2/modify-parameter/{job_id} - parameter modification
    - GET /api/v2/job/{job_id}/parameters - get current parameters
    - _Requirements: 1.1, 7.1, 7.2_
  - [ ]* 7.2 Write property test for input parameter flow
    - **Property 1: Input Parameters Flow to Structured Prompt**
    - **Validates: Requirements 1.2, 1.3, 1.5**

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Frontend Parameter Editor
  - [x] 9.1 Create parameter editor component
    - Add material selector dropdown
    - Add color picker for primary/secondary colors
    - Add style mood selector
    - Wire to /api/v2/modify-parameter endpoint
    - _Requirements: 1.2, 1.3, 4.1_
  - [x] 9.2 Update VideoInputForm with enhanced fields
    - Add material type field
    - Add color preference fields
    - Add style mood selector
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 10. Integration and Polish
  - [ ] 10.1 Wire frontend to v2 backend endpoints
    - Update API client for v2 endpoints
    - Connect parameter editor to modify-parameter endpoint
    - Update progress tracker for new pipeline stages
    - _Requirements: 7.1, 7.2, 7.4_
  - [ ] 10.2 Update storyboard preview for structured parameters
    - Display camera, lighting, composition details
    - Show material and color palette
    - _Requirements: 2.2_
