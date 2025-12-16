"use client";

import * as React from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ErrorDisplayProps {
  error: string;
  onRetry: () => void;
  onReset?: () => void;
  retryLabel?: string;
  resetLabel?: string;
}

// Map technical errors to user-friendly messages
function getUserFriendlyMessage(error: string): { title: string; message: string; suggestion: string } {
  const lowerError = error.toLowerCase();

  // Network/Connection errors
  if (lowerError.includes("network") || lowerError.includes("fetch") || lowerError.includes("econnrefused")) {
    return {
      title: "Connection Error",
      message: "Unable to connect to the server.",
      suggestion: "Please check your internet connection and try again.",
    };
  }

  // Timeout errors
  if (lowerError.includes("timeout") || lowerError.includes("timed out")) {
    return {
      title: "Request Timed Out",
      message: "The server took too long to respond.",
      suggestion: "This might be due to high demand. Please try again in a moment.",
    };
  }

  // API/Server errors
  if (lowerError.includes("500") || lowerError.includes("internal server")) {
    return {
      title: "Server Error",
      message: "Something went wrong on our end.",
      suggestion: "Our team has been notified. Please try again later.",
    };
  }

  // Rate limiting
  if (lowerError.includes("429") || lowerError.includes("rate limit") || lowerError.includes("too many")) {
    return {
      title: "Too Many Requests",
      message: "You've made too many requests in a short time.",
      suggestion: "Please wait a moment before trying again.",
    };
  }

  // FIBO API specific errors
  if (lowerError.includes("fibo") || lowerError.includes("image generation")) {
    return {
      title: "Image Generation Failed",
      message: "We couldn't generate the images for your video.",
      suggestion: "Try adjusting your product description or try again.",
    };
  }

  // OpenAI/Storyboard errors
  if (lowerError.includes("openai") || lowerError.includes("storyboard")) {
    return {
      title: "Storyboard Generation Failed",
      message: "We couldn't create a storyboard for your video.",
      suggestion: "Try providing more details about your product.",
    };
  }

  // FFmpeg/Video processing errors
  if (lowerError.includes("ffmpeg") || lowerError.includes("video") || lowerError.includes("composit")) {
    return {
      title: "Video Processing Failed",
      message: "We couldn't assemble your video.",
      suggestion: "Please try again. If the problem persists, try a different aspect ratio.",
    };
  }

  // Validation errors
  if (lowerError.includes("validation") || lowerError.includes("invalid")) {
    return {
      title: "Invalid Input",
      message: "Some of your input couldn't be processed.",
      suggestion: "Please check your inputs and try again.",
    };
  }

  // Default fallback
  return {
    title: "Something Went Wrong",
    message: error || "An unexpected error occurred.",
    suggestion: "Please try again. If the problem persists, contact support.",
  };
}

export function ErrorDisplay({
  error,
  onRetry,
  onReset,
  retryLabel = "Try Again",
  resetLabel = "Start Over",
}: ErrorDisplayProps) {
  const { title, message, suggestion } = getUserFriendlyMessage(error);

  return (
    <Card className="w-full max-w-lg border-red-200 dark:border-red-900">
      <CardHeader className="text-center">
        <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/50">
          <svg
            className="h-6 w-6 text-red-600 dark:text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <CardTitle className="text-red-800 dark:text-red-200">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-center">
        <p className="text-sm text-red-600 dark:text-red-400">{message}</p>
        <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">{suggestion}</p>
      </CardContent>
      <CardFooter className="flex justify-center gap-3">
        <Button variant="destructive" onClick={onRetry}>
          {retryLabel}
        </Button>
        {onReset && (
          <Button variant="outline" onClick={onReset}>
            {resetLabel}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
