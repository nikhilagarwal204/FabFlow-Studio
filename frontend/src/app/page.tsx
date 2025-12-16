"use client";

import { useState, useCallback } from "react";
import { VideoInputForm } from "@/components/VideoInputForm";
import { ProgressTracker } from "@/components/ProgressTracker";
import { VideoPlayer } from "@/components/VideoPlayer";
import api from "@/lib/api";
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

  const handleSubmit = async (input: UserInput) => {
    setIsLoading(true);
    setError(null);

    try {
      // Map frontend UserInput to backend expected format
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
          />
        )}

        {/* Complete State - Show Video Player */}
        {appState === "complete" && videoUrl && (
          <VideoPlayer videoUrl={videoUrl} onReset={handleReset} />
        )}

        {/* Error State */}
        {appState === "error" && (
          <div className="w-full max-w-lg rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950">
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900">
                <span className="text-2xl">⚠️</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-red-800 dark:text-red-200">
                  Something went wrong
                </h3>
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {error || "An unexpected error occurred"}
                </p>
              </div>
              <button
                onClick={handleReset}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
