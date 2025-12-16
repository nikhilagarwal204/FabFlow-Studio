import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Types for v2 API
export interface EnhancedUserInputPayload {
  brand_name: string;
  product_name: string;
  product_description: string;
  duration: number;
  aspect_ratio: "9:16" | "1:1" | "16:9";
  material?: string | null;
  primary_color?: string | null;
  secondary_color?: string | null;
  style_mood?: string | null;
}

export interface CameraParams {
  angle: "close-up" | "medium-shot" | "wide-shot" | "overhead" | "low-angle" | "three-quarter";
  shot_type: "product_hero" | "detail" | "lifestyle" | "context";
}

export interface LightingParams {
  style: "soft-studio" | "dramatic" | "natural-window" | "golden-hour" | "product-spotlight";
  direction: "front" | "side" | "back" | "top" | "ambient";
  intensity: "low" | "medium" | "high";
}

export interface CompositionParams {
  subject_position: "center" | "rule-of-thirds-left" | "rule-of-thirds-right";
  background: "solid" | "gradient" | "environment" | "studio";
  depth_of_field: "shallow" | "medium" | "deep";
}

export interface StyleParams {
  color_palette: string[];
  material?: string | null;
  mood: string;
  aesthetic: "professional" | "artistic" | "commercial" | "editorial";
}

export interface SceneParameters {
  scene_number: number;
  duration: number;
  scene_description: string;
  camera: CameraParams;
  lighting: LightingParams;
  composition: CompositionParams;
  style: StyleParams;
  transition: "fade" | "dissolve" | "cut" | "cross-dissolve";
}

export interface EnhancedStoryboard {
  brand_name: string;
  product_name: string;
  total_duration: number;
  aspect_ratio: "9:16" | "1:1" | "16:9";
  scenes: SceneParameters[];
  global_material?: string | null;
  global_color_palette?: string[] | null;
}

export interface ParameterModification {
  parameter_path: string;
  new_value: string | string[];
  apply_to_scenes: number[];
}

export interface ModificationResult {
  success: boolean;
  modified_scenes: number[];
  frames_to_regenerate: number[];
  message: string;
}

export interface JobStatus {
  job_id: string;
  stage: "queued" | "storyboard" | "frame-generation" | "compositing" | "complete" | "error";
  progress: number;
  message: string;
  error?: string;
}

export interface JobResult {
  job_id: string;
  success: boolean;
  video_url?: string;
  duration?: number;
  error?: string;
}

// V2 API functions
export async function generateStoryboardV2(input: EnhancedUserInputPayload): Promise<EnhancedStoryboard> {
  const response = await api.post<EnhancedStoryboard>("/api/v2/generate-storyboard", input);
  return response.data;
}

export async function generateVideoV2(input: EnhancedUserInputPayload): Promise<{ job_id: string; message: string }> {
  const response = await api.post<{ job_id: string; message: string }>("/api/v2/generate-video", input);
  return response.data;
}

export async function modifyParameter(jobId: string, modification: ParameterModification): Promise<ModificationResult> {
  const response = await api.post<ModificationResult>(`/api/v2/modify-parameter/${jobId}`, modification);
  return response.data;
}

export async function getJobParameters(jobId: string): Promise<EnhancedStoryboard> {
  const response = await api.get<EnhancedStoryboard>(`/api/v2/job/${jobId}/parameters`);
  return response.data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await api.get<JobStatus>(`/api/job/${jobId}/status`);
  return response.data;
}

export async function getJobResult(jobId: string): Promise<JobResult> {
  const response = await api.get<JobResult>(`/api/job/${jobId}/result`);
  return response.data;
}

export default api;
