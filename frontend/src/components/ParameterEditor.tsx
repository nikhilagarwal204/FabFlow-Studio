"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import api from "@/lib/api";

// Types matching backend EnhancedUserInput
export type MaterialType = "fabric" | "leather" | "metal" | "wood" | "glass" | "plastic" | "ceramic";
export type StyleMood = "luxury" | "minimal" | "vibrant" | "natural" | "tech";

export interface ParameterModification {
  parameter_path: string;
  new_value: string | string[];
  apply_to_scenes: number[];
}

interface ParameterEditorProps {
  jobId: string;
  currentMaterial?: MaterialType | null;
  currentPrimaryColor?: string | null;
  currentSecondaryColor?: string | null;
  currentStyleMood?: StyleMood | null;
  onModificationApplied?: (result: ModificationResult) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
}

interface ModificationResult {
  modified_scenes: number[];
  frames_to_regenerate: number[];
  preserved_parameters: Record<string, unknown>;
}

const MATERIAL_OPTIONS: { value: MaterialType; label: string }[] = [
  { value: "fabric", label: "Fabric" },
  { value: "leather", label: "Leather" },
  { value: "metal", label: "Metal" },
  { value: "wood", label: "Wood" },
  { value: "glass", label: "Glass" },
  { value: "plastic", label: "Plastic" },
  { value: "ceramic", label: "Ceramic" },
];

const STYLE_MOOD_OPTIONS: { value: StyleMood; label: string }[] = [
  { value: "luxury", label: "Luxury" },
  { value: "minimal", label: "Minimal" },
  { value: "vibrant", label: "Vibrant" },
  { value: "natural", label: "Natural" },
  { value: "tech", label: "Tech" },
];

// Simple hex color validation
function isValidHexColor(color: string): boolean {
  return /^#[0-9A-Fa-f]{6}$/.test(color);
}

export function ParameterEditor({
  jobId,
  currentMaterial,
  currentPrimaryColor,
  currentSecondaryColor,
  currentStyleMood,
  onModificationApplied,
  onError,
  disabled = false,
}: ParameterEditorProps) {
  const [material, setMaterial] = React.useState<MaterialType | "">(currentMaterial || "");
  const [primaryColor, setPrimaryColor] = React.useState(currentPrimaryColor || "#000000");
  const [secondaryColor, setSecondaryColor] = React.useState(currentSecondaryColor || "#ffffff");
  const [styleMood, setStyleMood] = React.useState<StyleMood | "">(currentStyleMood || "");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [colorError, setColorError] = React.useState<string | null>(null);

  // Sync with props when they change
  React.useEffect(() => {
    if (currentMaterial) setMaterial(currentMaterial);
    if (currentPrimaryColor) setPrimaryColor(currentPrimaryColor);
    if (currentSecondaryColor) setSecondaryColor(currentSecondaryColor);
    if (currentStyleMood) setStyleMood(currentStyleMood);
  }, [currentMaterial, currentPrimaryColor, currentSecondaryColor, currentStyleMood]);

  const handleModifyParameter = async (parameterPath: string, newValue: string | string[]) => {
    if (disabled || isSubmitting) return;

    setIsSubmitting(true);
    setColorError(null);

    try {
      const modification: ParameterModification = {
        parameter_path: parameterPath,
        new_value: newValue,
        apply_to_scenes: [], // Empty means apply to all scenes
      };

      const response = await api.post<ModificationResult>(
        `/api/v2/modify-parameter/${jobId}`,
        modification
      );

      onModificationApplied?.(response.data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to modify parameter";
      onError?.(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMaterialChange = (value: string) => {
    const newMaterial = value as MaterialType;
    setMaterial(newMaterial);
    handleModifyParameter("style.material", newMaterial);
  };

  const handleStyleMoodChange = (value: string) => {
    const newMood = value as StyleMood;
    setStyleMood(newMood);
    handleModifyParameter("style.mood", newMood);
  };

  const handlePrimaryColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPrimaryColor(value);
  };

  const handleSecondaryColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSecondaryColor(value);
  };

  const handleApplyColors = () => {
    // Validate colors before applying
    if (!isValidHexColor(primaryColor)) {
      setColorError("Primary color must be a valid hex color (e.g., #FF5733)");
      return;
    }
    if (!isValidHexColor(secondaryColor)) {
      setColorError("Secondary color must be a valid hex color (e.g., #FF5733)");
      return;
    }
    setColorError(null);
    handleModifyParameter("style.color_palette", [primaryColor, secondaryColor]);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg">Edit Parameters</CardTitle>
        <CardDescription>
          Modify visual parameters to regenerate affected frames
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        {/* Material Selector */}
        <div className="flex flex-col gap-2">
          <Label htmlFor="material">Material</Label>
          <Select
            value={material}
            onValueChange={handleMaterialChange}
            disabled={disabled || isSubmitting}
          >
            <SelectTrigger id="material" className="w-full">
              <SelectValue placeholder="Select material type" />
            </SelectTrigger>
            <SelectContent>
              {MATERIAL_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Style Mood Selector */}
        <div className="flex flex-col gap-2">
          <Label htmlFor="styleMood">Style Mood</Label>
          <Select
            value={styleMood}
            onValueChange={handleStyleMoodChange}
            disabled={disabled || isSubmitting}
          >
            <SelectTrigger id="styleMood" className="w-full">
              <SelectValue placeholder="Select style mood" />
            </SelectTrigger>
            <SelectContent>
              {STYLE_MOOD_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Color Pickers */}
        <div className="flex flex-col gap-3">
          <Label>Color Palette</Label>
          
          <div className="flex items-center gap-3">
            <div className="flex flex-col gap-1.5 flex-1">
              <Label htmlFor="primaryColor" className="text-xs text-muted-foreground">
                Primary
              </Label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  id="primaryColorPicker"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  disabled={disabled || isSubmitting}
                  className="h-9 w-12 cursor-pointer rounded border border-input p-0.5"
                />
                <Input
                  id="primaryColor"
                  value={primaryColor}
                  onChange={handlePrimaryColorChange}
                  placeholder="#000000"
                  disabled={disabled || isSubmitting}
                  className="flex-1 font-mono text-sm"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5 flex-1">
              <Label htmlFor="secondaryColor" className="text-xs text-muted-foreground">
                Secondary
              </Label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  id="secondaryColorPicker"
                  value={secondaryColor}
                  onChange={(e) => setSecondaryColor(e.target.value)}
                  disabled={disabled || isSubmitting}
                  className="h-9 w-12 cursor-pointer rounded border border-input p-0.5"
                />
                <Input
                  id="secondaryColor"
                  value={secondaryColor}
                  onChange={handleSecondaryColorChange}
                  placeholder="#ffffff"
                  disabled={disabled || isSubmitting}
                  className="flex-1 font-mono text-sm"
                />
              </div>
            </div>
          </div>

          {colorError && (
            <p className="text-sm text-destructive">{colorError}</p>
          )}

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleApplyColors}
            disabled={disabled || isSubmitting}
            className="w-fit"
          >
            Apply Colors
          </Button>
        </div>

        {/* Loading indicator */}
        {isSubmitting && (
          <p className="text-sm text-muted-foreground">Applying changes...</p>
        )}
      </CardContent>
    </Card>
  );
}
