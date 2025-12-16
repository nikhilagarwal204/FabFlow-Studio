"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

// Types matching backend Storyboard model
export interface FIBOPrompt {
  prompt: string;
  camera_angle: "close-up" | "medium-shot" | "wide-shot" | "overhead" | "low-angle";
  lighting_style: "soft" | "dramatic" | "natural" | "studio" | "golden-hour";
  subject_position: "center" | "rule-of-thirds-left" | "rule-of-thirds-right";
  color_palette?: string[] | null;
  mood?: string | null;
}

export interface Scene {
  scene_number: number;
  duration: number;
  transition: "fade" | "dissolve" | "cut" | "slide";
  fibo_prompt: FIBOPrompt;
}

export interface Storyboard {
  brand_name: string;
  product_name: string;
  total_duration: number;
  aspect_ratio: "9:16" | "1:1" | "16:9";
  scenes: Scene[];
}

interface StoryboardPreviewProps {
  storyboard: Storyboard;
}

const cameraAngleLabels: Record<FIBOPrompt["camera_angle"], string> = {
  "close-up": "Close-up",
  "medium-shot": "Medium Shot",
  "wide-shot": "Wide Shot",
  "overhead": "Overhead",
  "low-angle": "Low Angle",
};

const lightingLabels: Record<FIBOPrompt["lighting_style"], string> = {
  soft: "Soft",
  dramatic: "Dramatic",
  natural: "Natural",
  studio: "Studio",
  "golden-hour": "Golden Hour",
};

const transitionLabels: Record<Scene["transition"], string> = {
  fade: "Fade",
  dissolve: "Dissolve",
  cut: "Cut",
  slide: "Slide",
};

export function StoryboardPreview({ storyboard }: StoryboardPreviewProps) {
  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle>Storyboard Preview</CardTitle>
        <CardDescription>
          {storyboard.brand_name} - {storyboard.product_name} ({storyboard.total_duration}s, {storyboard.aspect_ratio})
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4">
          {storyboard.scenes.map((scene) => (
            <div
              key={scene.scene_number}
              className="rounded-lg border border-border bg-muted/30 p-4"
            >
              {/* Scene Header */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-foreground">
                  Scene {scene.scene_number}
                </span>
                <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                  {scene.duration}s
                </span>
              </div>

              {/* Scene Description */}
              <p className="text-sm text-foreground mb-3 leading-relaxed">
                {scene.fibo_prompt.prompt}
              </p>

              {/* Scene Details */}
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                  <CameraIcon className="h-3 w-3" />
                  {cameraAngleLabels[scene.fibo_prompt.camera_angle]}
                </span>
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                  <LightbulbIcon className="h-3 w-3" />
                  {lightingLabels[scene.fibo_prompt.lighting_style]}
                </span>
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                  <ArrowRightIcon className="h-3 w-3" />
                  {transitionLabels[scene.transition]}
                </span>
              </div>

              {/* Color Palette (if present) */}
              {scene.fibo_prompt.color_palette && scene.fibo_prompt.color_palette.length > 0 && (
                <div className="flex items-center gap-2 mt-3">
                  <span className="text-xs text-muted-foreground">Colors:</span>
                  <div className="flex gap-1">
                    {scene.fibo_prompt.color_palette.map((color, idx) => (
                      <div
                        key={idx}
                        className="h-4 w-4 rounded-full border border-border"
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Mood (if present) */}
              {scene.fibo_prompt.mood && (
                <p className="text-xs text-muted-foreground mt-2 italic">
                  Mood: {scene.fibo_prompt.mood}
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Simple inline icons
function CameraIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3" />
    </svg>
  );
}

function LightbulbIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5" />
      <path d="M9 18h6" />
      <path d="M10 22h4" />
    </svg>
  );
}

function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}
