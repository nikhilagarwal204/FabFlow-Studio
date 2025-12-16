"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { SceneParameters } from "@/lib/api";

interface SceneParameterCardProps {
  scene: SceneParameters;
  onModify: (sceneNumber: number, paramPath: string, value: string | string[]) => void;
  isModifying: boolean;
  frameUrl?: string;
}

const CAMERA_ANGLES = ["close-up", "medium-shot", "wide-shot", "overhead", "low-angle", "three-quarter"];
const SHOT_TYPES = ["product_hero", "detail", "lifestyle", "context"];
const LIGHTING_STYLES = ["soft-studio", "dramatic", "natural-window", "golden-hour", "product-spotlight"];
const LIGHTING_DIRECTIONS = ["front", "side", "back", "top", "ambient"];
const MATERIALS = ["fabric", "leather", "metal", "wood", "glass", "plastic", "ceramic"];
const MOODS = ["luxury", "minimal", "vibrant", "natural", "tech", "elegant", "modern", "classic"];

export function SceneParameterCard({ scene, onModify, isModifying, frameUrl }: SceneParameterCardProps) {
  const [primaryColor, setPrimaryColor] = React.useState(scene.style.color_palette[0] || "#000000");
  const [secondaryColor, setSecondaryColor] = React.useState(scene.style.color_palette[1] || "#ffffff");

  const handleApplyColors = () => {
    onModify(scene.scene_number, "style.color_palette", [primaryColor, secondaryColor]);
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center justify-between">
          <span>Scene {scene.scene_number}</span>
          <span className="text-sm font-normal text-muted-foreground">{scene.duration}s</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Frame Preview */}
        {frameUrl && (
          <div className="rounded-md overflow-hidden bg-muted aspect-video">
            <img src={frameUrl} alt={`Scene ${scene.scene_number}`} className="w-full h-full object-cover" />
          </div>
        )}

        {/* Scene Description */}
        <p className="text-sm text-muted-foreground">{scene.scene_description}</p>

        {/* Camera Controls */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Camera Angle</Label>
            <Select
              value={scene.camera.angle}
              onValueChange={(v) => onModify(scene.scene_number, "camera.angle", v)}
              disabled={isModifying}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CAMERA_ANGLES.map((angle) => (
                  <SelectItem key={angle} value={angle} className="text-xs">
                    {angle.replace("-", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Shot Type</Label>
            <Select
              value={scene.camera.shot_type}
              onValueChange={(v) => onModify(scene.scene_number, "camera.shot_type", v)}
              disabled={isModifying}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SHOT_TYPES.map((type) => (
                  <SelectItem key={type} value={type} className="text-xs">
                    {type.replace("_", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Lighting Controls */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Lighting Style</Label>
            <Select
              value={scene.lighting.style}
              onValueChange={(v) => onModify(scene.scene_number, "lighting.style", v)}
              disabled={isModifying}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LIGHTING_STYLES.map((style) => (
                  <SelectItem key={style} value={style} className="text-xs">
                    {style.replace("-", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Light Direction</Label>
            <Select
              value={scene.lighting.direction}
              onValueChange={(v) => onModify(scene.scene_number, "lighting.direction", v)}
              disabled={isModifying}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LIGHTING_DIRECTIONS.map((dir) => (
                  <SelectItem key={dir} value={dir} className="text-xs">
                    {dir}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Material */}
        <div className="space-y-1.5">
          <Label className="text-xs">Material</Label>
          <Select
            value={scene.style.material || ""}
            onValueChange={(v) => onModify(scene.scene_number, "style.material", v)}
            disabled={isModifying}
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="Select material" />
            </SelectTrigger>
            <SelectContent>
              {MATERIALS.map((mat) => (
                <SelectItem key={mat} value={mat} className="text-xs">
                  {mat}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Color Palette */}
        <div className="space-y-2">
          <Label className="text-xs">Color Palette</Label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={primaryColor}
              onChange={(e) => setPrimaryColor(e.target.value)}
              disabled={isModifying}
              className="h-8 w-10 cursor-pointer rounded border p-0.5"
            />
            <Input
              value={primaryColor}
              onChange={(e) => setPrimaryColor(e.target.value)}
              disabled={isModifying}
              className="h-8 text-xs font-mono flex-1"
            />
            <input
              type="color"
              value={secondaryColor}
              onChange={(e) => setSecondaryColor(e.target.value)}
              disabled={isModifying}
              className="h-8 w-10 cursor-pointer rounded border p-0.5"
            />
            <Input
              value={secondaryColor}
              onChange={(e) => setSecondaryColor(e.target.value)}
              disabled={isModifying}
              className="h-8 text-xs font-mono flex-1"
            />
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={handleApplyColors}
            disabled={isModifying}
            className="h-7 text-xs"
          >
            Apply Colors
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
