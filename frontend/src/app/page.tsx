"use client";

import { useState, useCallback } from "react";
import { VideoInputForm } from "@/components/VideoInputForm";
import { ProgressTracker } from "@/components/ProgressTracker";
import { VideoPlayer } from "@/components/VideoPlayer";
import { ErrorDisplay } from "@/components/ErrorDisplay";
import api, { generateVideoV2, type EnhancedUserInputPayload } from "@/lib/api";
import type { UserInput } from "@/lib/validation";

type AppState = "input" | "generating" | "complete" | "error";

interface GenerateVideoResponse {
  job_id: string;
  message: string;
}

export default function Home() {
  const [appState, setAppState] = useState<AppState>("input");
  const [isLoading, setIsLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isV2Pipeline, setIsV2Pipeline] = useState(false);

  const handleSubmit = async (input: UserInput) => {
    setIsLoading(true);
    setError(null);

    try {
      // Map frontend UserInput to backend expected format
      // Use v2 endpoint if enhanced fields are provided, otherwise use v1
      const hasEnhancedFields = input.material || input.primaryColor || input.secondaryColor || input.styleMood;
      
      if (hasEnhancedFields) {
        // Use v2 API with typed payload
        const payload: EnhancedUserInputPayload = {
          brand_name: input.brandName,
          product_name: input.productName,
          product_description: input.productDescription,
          duration: input.duration,
          aspect_ratio: input.aspectRatio,
          material: input.material || null,
          primary_color: input.primaryColor || null,
          secondary_color: input.secondaryColor || null,
          style_mood: input.styleMood || null,
        };

        const result = await generateVideoV2(payload);
        setJobId(result.job_id);
        setIsV2Pipeline(true);
      } else {
        // Use v1 API for basic requests
        const payload = {
          brand_name: input.brandName,
          product_name: input.productName,
          product_description: input.productDescription,
          duration: input.duration,
          aspect_ratio: input.aspectRatio,
          product_image_url: null, // Image upload not implemented yet
        };

        const response = await api.post<GenerateVideoResponse>(
          "/api/generate-video",
          payload
        );
        setJobId(response.data.job_id);
        setIsV2Pipeline(false);
      }

      setAppState("generating");
    } catch (err) {
      console.error("Failed to start video generation:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to start video generation. Please try again."
      );
      setAppState("error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = useCallback((url: string) => {
    setVideoUrl(url);
    setAppState("complete");
  }, []);

  const handleError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setAppState("error");
  }, []);

  const handleReset = useCallback(() => {
    setAppState("input");
    setJobId(null);
    setVideoUrl(null);
    setError(null);
    setIsLoading(false);
    setIsV2Pipeline(false);
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 p-4 dark:bg-black">
      <main className="flex w-full max-w-lg flex-col items-center gap-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            FabFlow Studio
          </h1>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            Create stunning ad videos with AI
          </p>
        </div>

        {/* Input Form State */}
        {appState === "input" && (
          <VideoInputForm onSubmit={handleSubmit} isLoading={isLoading} />
        )}

        {/* Generating State - Show Progress Tracker */}
        {appState === "generating" && jobId && (
          <ProgressTracker
            jobId={jobId}
            onComplete={handleComplete}
            onError={handleError}
            isV2Pipeline={isV2Pipeline}
          />
        )}

        {/* Complete State - Show Video Player */}
        {appState === "complete" && videoUrl && (
          <VideoPlayer videoUrl={videoUrl} onReset={handleReset} />
        )}

        {/* Error State */}
        {appState === "error" && (
          <ErrorDisplay
            error={error || "An unexpected error occurred"}
            onRetry={handleReset}
          />
        )}
      </main>
    </div>
  );
}
