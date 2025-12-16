"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { EnhancedStoryboard, SceneParameters } from "@/lib/api";

// Types matching backend Storyboard model (v1)
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

interface EnhancedStoryboardPreviewProps {
  storyboard: EnhancedStoryboard;
}

const cameraAngleLabels: Record<string, string> = {
  "close-up": "Close-up",
  "medium-shot": "Medium Shot",
  "wide-shot": "Wide Shot",
  "overhead": "Overhead",
  "low-angle": "Low Angle",
  "three-quarter": "Three-Quarter",
};

const lightingLabels: Record<string, string> = {
  soft: "Soft",
  dramatic: "Dramatic",
  natural: "Natural",
  studio: "Studio",
  "golden-hour": "Golden Hour",
  "soft-studio": "Soft Studio",
  "natural-window": "Natural Window",
  "product-spotlight": "Product Spotlight",
};

const transitionLabels: Record<string, string> = {
  fade: "Fade",
  dissolve: "Dissolve",
  cut: "Cut",
  slide: "Slide",
  "cross-dissolve": "Cross Dissolve",
};

const shotTypeLabels: Record<string, string> = {
  product_hero: "Hero Shot",
  detail: "Detail",
  lifestyle: "Lifestyle",
  context: "Context",
};

const backgroundLabels: Record<string, string> = {
  solid: "Solid",
  gradient: "Gradient",
  environment: "Environment",
  studio: "Studio",
};

const aestheticLabels: Record<string, string> = {
  professional: "Professional",
  artistic: "Artistic",
  commercial: "Commercial",
  editorial: "Editorial",
};

// V1 Storyboard Preview (original)
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

// V2 Enhanced Storyboard Preview with structured parameters
export function EnhancedStoryboardPreview({ storyboard }: EnhancedStoryboardPreviewProps) {
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Enhanced Storyboard</CardTitle>
        <CardDescription>
          {storyboard.brand_name} - {storyboard.product_name} ({storyboard.total_duration}s, {storyboard.aspect_ratio})
        </CardDescription>
        {/* Global parameters */}
        {(storyboard.global_material || storyboard.global_color_palette) && (
          <div className="flex flex-wrap items-center gap-3 mt-2 pt-2 border-t border-border">
            {storyboard.global_material && (
              <span className="inline-flex items-center gap-1 text-xs bg-zinc-100 dark:bg-zinc-800 px-2 py-1 rounded">
                <MaterialIcon className="h-3 w-3" />
                {storyboard.global_material}
              </span>
            )}
            {storyboard.global_color_palette && storyboard.global_color_palette.length > 0 && (
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">Palette:</span>
                {storyboard.global_color_palette.map((color, idx) => (
                  <div
                    key={idx}
                    className="h-4 w-4 rounded-full border border-border"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4">
          {storyboard.scenes.map((scene) => (
            <EnhancedSceneCard key={scene.scene_number} scene={scene} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Enhanced scene card with full parameter display
function EnhancedSceneCard({ scene }: { scene: SceneParameters }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4">
      {/* Scene Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-foreground">
          Scene {scene.scene_number}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
            {scene.duration}s
          </span>
          <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
            {transitionLabels[scene.transition] || scene.transition}
          </span>
        </div>
      </div>

      {/* Scene Description */}
      <p className="text-sm text-foreground mb-3 leading-relaxed">
        {scene.scene_description}
      </p>

      {/* Camera Parameters */}
      <div className="mb-3">
        <h4 className="text-xs font-medium text-muted-foreground mb-1.5 flex items-center gap-1">
          <CameraIcon className="h-3 w-3" /> Camera
        </h4>
        <div className="flex flex-wrap gap-1.5">
          <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
            {cameraAngleLabels[scene.camera.angle] || scene.camera.angle}
          </span>
          <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
            {shotTypeLabels[scene.camera.shot_type] || scene.camera.shot_type}
          </span>
        </div>
      </div>

      {/* Lighting Parameters */}
      <div className="mb-3">
        <h4 className="text-xs font-medium text-muted-foreground mb-1.5 flex items-center gap-1">
          <LightbulbIcon className="h-3 w-3" /> Lighting
        </h4>
        <div className="flex flex-wrap gap-1.5">
          <span className="text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded">
            {lightingLabels[scene.lighting.style] || scene.lighting.style}
          </span>
          <span className="text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded">
            {scene.lighting.direction}
          </span>
          <span className="text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded">
            {scene.lighting.intensity} intensity
          </span>
        </div>
      </div>

      {/* Composition Parameters */}
      <div className="mb-3">
        <h4 className="text-xs font-medium text-muted-foreground mb-1.5 flex items-center gap-1">
          <GridIcon className="h-3 w-3" /> Composition
        </h4>
        <div className="flex flex-wrap gap-1.5">
          <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
            {scene.composition.subject_position.replace(/-/g, " ")}
          </span>
          <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
            {backgroundLabels[scene.composition.background] || scene.composition.background} bg
          </span>
          <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
            {scene.composition.depth_of_field} DoF
          </span>
        </div>
      </div>

      {/* Style Parameters */}
      <div>
        <h4 className="text-xs font-medium text-muted-foreground mb-1.5 flex items-center gap-1">
          <PaletteIcon className="h-3 w-3" /> Style
        </h4>
        <div className="flex flex-wrap items-center gap-2">
          {scene.style.material && (
            <span className="text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded">
              {scene.style.material}
            </span>
          )}
          <span className="text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded">
            {aestheticLabels[scene.style.aesthetic] || scene.style.aesthetic}
          </span>
          <span className="text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded italic">
            {scene.style.mood}
          </span>
          {/* Color Palette */}
          {scene.style.color_palette && scene.style.color_palette.length > 0 && (
            <div className="flex items-center gap-1 ml-1">
              {scene.style.color_palette.map((color, idx) => (
                <div
                  key={idx}
                  className="h-4 w-4 rounded-full border border-border shadow-sm"
                  style={{ backgroundColor: color }}
                  title={color}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
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

function GridIcon({ className }: { className?: string }) {
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
      <rect width="18" height="18" x="3" y="3" rx="2" />
      <path d="M3 9h18" />
      <path d="M3 15h18" />
      <path d="M9 3v18" />
      <path d="M15 3v18" />
    </svg>
  );
}

function PaletteIcon({ className }: { className?: string }) {
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
      <circle cx="13.5" cy="6.5" r=".5" fill="currentColor" />
      <circle cx="17.5" cy="10.5" r=".5" fill="currentColor" />
      <circle cx="8.5" cy="7.5" r=".5" fill="currentColor" />
      <circle cx="6.5" cy="12.5" r=".5" fill="currentColor" />
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.555C21.965 6.012 17.461 2 12 2z" />
    </svg>
  );
}

function MaterialIcon({ className }: { className?: string }) {
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
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.29 7 12 12 20.71 7" />
      <line x1="12" x2="12" y1="22" y2="12" />
    </svg>
  );
}
