"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  validateUserInput,
  DEFAULT_USER_INPUT,
  type UserInput,
  type AspectRatio,
  type ValidationResult,
} from "@/lib/validation";

interface VideoInputFormProps {
  onSubmit: (input: UserInput) => void;
  isLoading?: boolean;
}

export function VideoInputForm({ onSubmit, isLoading = false }: VideoInputFormProps) {
  const [brandName, setBrandName] = React.useState("");
  const [productName, setProductName] = React.useState("");
  const [productDescription, setProductDescription] = React.useState("");
  const [duration, setDuration] = React.useState(DEFAULT_USER_INPUT.duration);
  const [aspectRatio, setAspectRatio] = React.useState<AspectRatio>(DEFAULT_USER_INPUT.aspectRatio);
  const [errors, setErrors] = React.useState<string[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const input: UserInput = {
      brandName,
      productName,
      productDescription,
      duration,
      aspectRatio,
      productImage: null,
    };

    const validation: ValidationResult = validateUserInput(input);

    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }

    setErrors([]);
    onSubmit(input);
  };


  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle>Create Your Ad Video</CardTitle>
        <CardDescription>
          Enter your brand and product details to generate a professional ad video
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          {/* Error Messages */}
          {errors.length > 0 && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <ul className="list-disc pl-4 space-y-1">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Brand Name */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="brandName">Brand Name *</Label>
            <Input
              id="brandName"
              placeholder="e.g., Nike, Apple, Coca-Cola"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              disabled={isLoading}
            />
          </div>

          {/* Product Name */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="productName">Product Name *</Label>
            <Input
              id="productName"
              placeholder="e.g., Air Max 90, iPhone 15"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              disabled={isLoading}
            />
          </div>

          {/* Product Description */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="productDescription">Product Description *</Label>
            <Textarea
              id="productDescription"
              placeholder="Describe your product, its features, and what makes it special..."
              value={productDescription}
              onChange={(e) => setProductDescription(e.target.value)}
              disabled={isLoading}
              rows={4}
            />
          </div>

          {/* Duration Slider */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="duration">Video Duration</Label>
              <span className="text-sm text-muted-foreground">{duration} seconds</span>
            </div>
            <Slider
              id="duration"
              min={5}
              max={12}
              step={1}
              value={[duration]}
              onValueChange={(value) => setDuration(value[0])}
              disabled={isLoading}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>5s</span>
              <span>12s</span>
            </div>
          </div>

          {/* Aspect Ratio Selector */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="aspectRatio">Aspect Ratio</Label>
            <Select
              value={aspectRatio}
              onValueChange={(value: AspectRatio) => setAspectRatio(value)}
              disabled={isLoading}
            >
              <SelectTrigger id="aspectRatio" className="w-full">
                <SelectValue placeholder="Select aspect ratio" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="9:16">9:16 Vertical (Stories/Reels)</SelectItem>
                <SelectItem value="1:1">1:1 Square (Feed)</SelectItem>
                <SelectItem value="16:9">16:9 Horizontal (YouTube)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Submit Button */}
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? "Generating..." : "Generate Ad Video"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
