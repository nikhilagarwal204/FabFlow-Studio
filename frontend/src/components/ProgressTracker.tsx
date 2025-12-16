"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import api, { getJobStatus, getJobResult, type JobStatus } from "@/lib/api";

type PipelineStage = JobStatus["stage"];

interface ProgressTrackerProps {
  jobId: string;
  onComplete: (videoUrl: string) => void;
  onError: (error: string) => void;
  isV2Pipeline?: boolean;
}

const STAGE_LABELS: Record<PipelineStage, string> = {
  queued: "Queued",
  storyboard: "Generating Storyboard",
  "frame-generation": "Generating Frames",
  compositing: "Creating Video",
  complete: "Complete",
  error: "Error",
};

// V2 pipeline has more descriptive labels
const STAGE_LABELS_V2: Record<PipelineStage, string> = {
  queued: "Queued",
  storyboard: "Planning Scenes with AI",
  "frame-generation": "Generating Product Shots",
  compositing: "Assembling Video",
  complete: "Complete",
  error: "Error",
};

const STAGE_DESCRIPTIONS: Record<PipelineStage, string> = {
  queued: "Your job is in the queue",
  storyboard: "Creating structured scene parameters with camera, lighting, and composition settings",
  "frame-generation": "Generating high-quality product frames using FIBO structured prompts",
  compositing: "Assembling frames into final video with smooth transitions",
  complete: "Your video is ready!",
  error: "Something went wrong",
};

const STAGE_ORDER: PipelineStage[] = [
  "queued",
  "storyboard",
  "frame-generation",
  "compositing",
  "complete",
];

export function ProgressTracker({ jobId, onComplete, onError, isV2Pipeline = false }: ProgressTrackerProps) {
  const [status, setStatus] = React.useState<JobStatus | null>(null);
  const [polling, setPolling] = React.useState(true);

  const stageLabels = isV2Pipeline ? STAGE_LABELS_V2 : STAGE_LABELS;

  React.useEffect(() => {
    if (!jobId || !polling) return;

    const pollStatus = async () => {
      try {
        const jobStatus = await getJobStatus(jobId);
        setStatus(jobStatus);

        if (jobStatus.stage === "complete") {
          setPolling(false);
          // Fetch the result to get the video URL
          const result = await getJobResult(jobId);
          if (result.success && result.video_url) {
            // Construct full URL using the API base URL
            const baseUrl = api.defaults.baseURL || "";
            const videoUrl = result.video_url.startsWith("http")
              ? result.video_url
              : `${baseUrl}${result.video_url}`;
            onComplete(videoUrl);
          }
        } else if (jobStatus.stage === "error") {
          setPolling(false);
          onError(jobStatus.error || "An unknown error occurred");
        }
      } catch (err) {
        console.error("Failed to poll job status:", err);
      }
    };

    // Poll immediately
    pollStatus();

    // Then poll every 2 seconds (as per Requirements 7.2)
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [jobId, polling, onComplete, onError]);

  if (!status) {
    return (
      <Card className="w-full max-w-lg">
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-600 dark:border-t-zinc-100" />
            <span className="ml-3 text-sm text-zinc-600 dark:text-zinc-400">
              Initializing...
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentStageIndex = STAGE_ORDER.indexOf(status.stage);

  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle className="text-lg">
          {isV2Pipeline ? "Creating Your Professional Ad" : "Generating Your Video"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-zinc-600 dark:text-zinc-400">
              {stageLabels[status.stage]}
            </span>
            <span className="font-medium">{status.progress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
            <div
              className="h-full bg-zinc-900 transition-all duration-300 dark:bg-zinc-100"
              style={{ width: `${status.progress}%` }}
            />
          </div>
        </div>

        {/* Stage Indicators */}
        <div className="space-y-3">
          {STAGE_ORDER.slice(1, -1).map((stage, index) => {
            const stageIndex = index + 1;
            const isActive = status.stage === stage;
            const isComplete = currentStageIndex > stageIndex;
            const isPending = currentStageIndex < stageIndex;

            return (
              <div key={stage} className="flex flex-col gap-1">
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium ${
                      isComplete
                        ? "bg-green-500 text-white"
                        : isActive
                        ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                        : "bg-zinc-200 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
                    }`}
                  >
                    {isComplete ? "✓" : stageIndex}
                  </div>
                  <span
                    className={`text-sm ${
                      isActive
                        ? "font-medium text-zinc-900 dark:text-zinc-100"
                        : isPending
                        ? "text-zinc-400 dark:text-zinc-600"
                        : "text-zinc-600 dark:text-zinc-400"
                    }`}
                  >
                    {stageLabels[stage]}
                  </span>
                  {isActive && (
                    <div className="ml-auto h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-600 dark:border-t-zinc-100" />
                  )}
                </div>
                {/* Show description for active stage in v2 pipeline */}
                {isV2Pipeline && isActive && (
                  <p className="ml-9 text-xs text-zinc-500 dark:text-zinc-400">
                    {STAGE_DESCRIPTIONS[stage]}
                  </p>
                )}
              </div>
            );
          })}
        </div>

        {/* Status Message */}
        {status.message && (
          <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">
            {status.message}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
