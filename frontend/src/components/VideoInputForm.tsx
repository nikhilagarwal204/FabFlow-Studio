"use client";

import * as React from "react";
import Image from "next/image";
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
  isValidImageType,
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
  const [productImage, setProductImage] = React.useState<File | null>(null);
  const [errors, setErrors] = React.useState<string[]>([]);
  const [isDragging, setIsDragging] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const input: UserInput = {
      brandName,
      productName,
      productDescription,
      duration,
      aspectRatio,
      productImage,
    };

    const validation: ValidationResult = validateUserInput(input);

    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }

    setErrors([]);
    onSubmit(input);
  };

  const handleFileSelect = (file: File) => {
    if (isValidImageType(file)) {
      setProductImage(file);
      // Clear any previous image-related errors
      setErrors((prev) => prev.filter((e) => !e.includes("image")));
    } else {
      setErrors(["Product image must be a JPEG, PNG, or WebP file"]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleRemoveImage = () => {
    setProductImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
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

          {/* Product Image Upload */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="productImage">Product Image (Optional)</Label>
            <input
              ref={fileInputRef}
              type="file"
              id="productImage"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileInputChange}
              disabled={isLoading}
              className="hidden"
            />
            {productImage ? (
              <div className="relative rounded-md border border-border p-3">
                <div className="flex items-center gap-3">
                  <div className="h-16 w-16 flex-shrink-0 overflow-hidden rounded-md bg-muted relative">
                    <Image
                      src={URL.createObjectURL(productImage)}
                      alt="Product preview"
                      fill
                      className="object-cover"
                      unoptimized
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{productImage.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(productImage.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleRemoveImage}
                    disabled={isLoading}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ) : (
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
                className={`
                  flex flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed p-6 cursor-pointer transition-colors
                  ${isDragging 
                    ? "border-primary bg-primary/5" 
                    : "border-muted-foreground/25 hover:border-muted-foreground/50"
                  }
                  ${isLoading ? "pointer-events-none opacity-50" : ""}
                `}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-muted-foreground"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" x2="12" y1="3" y2="15" />
                </svg>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium text-foreground">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    JPEG, PNG, or WebP
                  </p>
                </div>
              </div>
            )}
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
