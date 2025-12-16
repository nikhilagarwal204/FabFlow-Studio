"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SceneParameterCard } from "./SceneParameterCard";
import { getJobParameters, modifyParameter, regenerateVideo, getJobStatus, getJobResult, type EnhancedStoryboard, api } from "@/lib/api";

interface VideoCompletionViewProps {
  videoUrl: string;
  jobId: string;
  isV2Pipeline: boolean;
  onReset: () => void;
  onRegenerating?: () => void;
  onRegenerateComplete?: (newVideoUrl: string) => void;
}

export function VideoCompletionView({
  videoUrl,
  jobId,
  isV2Pipeline,
  onReset,
  onRegenerating,
  onRegenerateComplete,
}: VideoCompletionViewProps) {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const [currentVideoUrl, setCurrentVideoUrl] = React.useState(videoUrl);
  const [currentJobId, setCurrentJobId] = React.useState(jobId);
  const [storyboard, setStoryboard] = React.useState<EnhancedStoryboard | null>(null);
  const [isLoadingParams, setIsLoadingParams] = React.useState(false);
  const [isModifying, setIsModifying] = React.useState(false);
  const [isRegenerating, setIsRegenerating] = React.useState(false);
  const [regenerationProgress, setRegenerationProgress] = React.useState(0);
  const [regenerationMessage, setRegenerationMessage] = React.useState("");
  const [modifiedScenes, setModifiedScenes] = React.useState<Set<number>>(new Set());
  const [error, setError] = React.useState<string | null>(null);

  // Fetch storyboard parameters when component mounts (only for v2 pipeline)
  React.useEffect(() => {
    if (isV2Pipeline && jobId) {
      fetchParameters();
    }
  }, [isV2Pipeline, jobId]);

  const fetchParameters = async () => {
    setIsLoadingParams(true);
    setError(null);
    try {
      const params = await getJobParameters(jobId);
      setStoryboard(params);
    } catch (err) {
      console.error("Failed to fetch parameters:", err);
      setError("Could not load scene parameters");
    } finally {
      setIsLoadingParams(false);
    }
  };

  const handleModifyParameter = async (sceneNumber: number, paramPath: string, value: string | string[]) => {
    if (!storyboard) return;

    setIsModifying(true);
    setError(null);

    try {
      const result = await modifyParameter(jobId, {
        parameter_path: paramPath,
        new_value: value,
        apply_to_scenes: [sceneNumber],
      });

      if (result.success) {
        // Mark scene as modified
        setModifiedScenes((prev) => new Set([...prev, sceneNumber]));
        // Refresh parameters
        await fetchParameters();
      }
    } catch (err) {
      console.error("Failed to modify parameter:", err);
      setError("Failed to apply parameter change");
    } finally {
      setIsModifying(false);
    }
  };

  const handleRegenerateVideo = async () => {
    if (!storyboard || modifiedScenes.size === 0) return;

    setIsRegenerating(true);
    setError(null);
    setRegenerationProgress(0);
    setRegenerationMessage("Starting regeneration...");

    try {
      // Start regeneration job
      const scenesToRegenerate = Array.from(modifiedScenes);
      const result = await regenerateVideo(currentJobId, scenesToRegenerate);
      const newJobId = result.job_id;

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const status = await getJobStatus(newJobId);
          setRegenerationProgress(status.progress);
          setRegenerationMessage(status.message);

          if (status.stage === "complete") {
            clearInterval(pollInterval);
            // Get the result
            const jobResult = await getJobResult(newJobId);
            if (jobResult.success && jobResult.video_url) {
              // Construct full URL from the API base URL
              const baseUrl = api.defaults.baseURL || "http://localhost:8000";
              const fullVideoUrl = jobResult.video_url.startsWith("http") 
                ? jobResult.video_url 
                : `${baseUrl}${jobResult.video_url}`;
              setCurrentVideoUrl(fullVideoUrl);
              setCurrentJobId(newJobId);
              setModifiedScenes(new Set());
              setIsRegenerating(false);
              // Refresh parameters for new job
              const params = await getJobParameters(newJobId);
              setStoryboard(params);
            }
          } else if (status.stage === "error") {
            clearInterval(pollInterval);
            setError(status.error || "Regeneration failed");
            setIsRegenerating(false);
          }
        } catch (err) {
          clearInterval(pollInterval);
          setError("Failed to check regeneration status");
          setIsRegenerating(false);
        }
      }, 1500);

    } catch (err) {
      console.error("Failed to start regeneration:", err);
      setError("Failed to start video regeneration");
      setIsRegenerating(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(currentVideoUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `fabflow-video-${Date.now()}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download failed:", error);
      window.open(currentVideoUrl, "_blank");
    }
  };

  return (
    <div className="w-full max-w-4xl space-y-6">
      {/* Video Player Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            {isRegenerating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                Regenerating Video...
              </>
            ) : (
              <>
                <span className="text-green-500">✓</span>
                Your Video is Ready
              </>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Regeneration Progress */}
          {isRegenerating && (
            <div className="space-y-2 p-4 bg-muted rounded-lg">
              <div className="flex justify-between text-sm">
                <span>{regenerationMessage}</span>
                <span>{regenerationProgress}%</span>
              </div>
              <div className="w-full bg-background rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${regenerationProgress}%` }}
                />
              </div>
            </div>
          )}

          <div className="overflow-hidden rounded-lg bg-black">
            <video
              key={currentVideoUrl}
              ref={videoRef}
              src={currentVideoUrl}
              controls
              autoPlay
              loop
              playsInline
              className="w-full max-h-[400px] object-contain"
            >
              Your browser does not support the video tag.
            </video>
          </div>

          <div className="flex gap-3">
            <Button onClick={handleDownload} className="flex-1" disabled={isRegenerating}>
              <DownloadIcon className="mr-2 h-4 w-4" />
              Download Video
            </Button>
            <Button variant="outline" onClick={onReset} className="flex-1" disabled={isRegenerating}>
              Create Another
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Parameter Editor Section - Only for v2 pipeline */}
      {isV2Pipeline && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center justify-between">
              <span>Scene Parameters</span>
              {modifiedScenes.size > 0 && (
                <span className="text-sm font-normal text-amber-600">
                  {modifiedScenes.size} scene(s) modified
                </span>
              )}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Adjust camera, lighting, material, and colors for each scene. Changes will require regenerating affected frames.
            </p>
          </CardHeader>
          <CardContent>
            {isLoadingParams ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <span className="ml-3 text-muted-foreground">Loading parameters...</span>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-destructive mb-4">{error}</p>
                <Button variant="outline" onClick={fetchParameters}>
                  Retry
                </Button>
              </div>
            ) : storyboard ? (
              <div className="space-y-4">
                {/* Storyboard Info */}
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground border-b pb-4">
                  <span><strong>Brand:</strong> {storyboard.brand_name}</span>
                  <span><strong>Product:</strong> {storyboard.product_name}</span>
                  <span><strong>Duration:</strong> {storyboard.total_duration}s</span>
                  <span><strong>Aspect:</strong> {storyboard.aspect_ratio}</span>
                </div>

                {/* Scene Cards */}
                <Tabs defaultValue="scene-1" className="w-full">
                  <TabsList className="w-full justify-start overflow-x-auto">
                    {storyboard.scenes.map((scene) => (
                      <TabsTrigger
                        key={scene.scene_number}
                        value={`scene-${scene.scene_number}`}
                        className={modifiedScenes.has(scene.scene_number) ? "border-amber-500 border" : ""}
                      >
                        Scene {scene.scene_number}
                        {modifiedScenes.has(scene.scene_number) && (
                          <span className="ml-1 text-amber-500">•</span>
                        )}
                      </TabsTrigger>
                    ))}
                  </TabsList>

                  {storyboard.scenes.map((scene) => (
                    <TabsContent key={scene.scene_number} value={`scene-${scene.scene_number}`}>
                      <SceneParameterCard
                        scene={scene}
                        onModify={handleModifyParameter}
                        isModifying={isModifying}
                      />
                    </TabsContent>
                  ))}
                </Tabs>

                {/* Regenerate Button */}
                {modifiedScenes.size > 0 && (
                  <div className="flex items-center justify-between pt-4 border-t">
                    <p className="text-sm text-muted-foreground">
                      {modifiedScenes.size} scene(s) have been modified and need regeneration.
                    </p>
                    <Button onClick={handleRegenerateVideo} disabled={isModifying || isRegenerating}>
                      {isRegenerating ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Regenerating...
                        </>
                      ) : (
                        <>
                          <RefreshIcon className="mr-2 h-4 w-4" />
                          Regenerate Frames
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">
                No parameter data available
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function DownloadIcon({ className }: { className?: string }) {
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
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function RefreshIcon({ className }: { className?: string }) {
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
      <path d="M21 2v6h-6" />
      <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
      <path d="M3 22v-6h6" />
      <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
    </svg>
  );
}
