"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface VideoPlayerProps {
  videoUrl: string;
  onReset?: () => void;
}

export function VideoPlayer({ videoUrl, onReset }: VideoPlayerProps) {
  const videoRef = React.useRef<HTMLVideoElement>(null);

  const handleDownload = async () => {
    try {
      const response = await fetch(videoUrl);
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
      // Fallback: open in new tab
      window.open(videoUrl, "_blank");
    }
  };

  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <span className="text-green-500">✓</span>
          Your Video is Ready
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Video Player */}
        <div className="overflow-hidden rounded-lg bg-black">
          <video
            ref={videoRef}
            src={videoUrl}
            controls
            autoPlay
            loop
            playsInline
            className="w-full"
          >
            Your browser does not support the video tag.
          </video>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button onClick={handleDownload} className="flex-1">
            <DownloadIcon className="mr-2 h-4 w-4" />
            Download Video
          </Button>
          {onReset && (
            <Button variant="outline" onClick={onReset} className="flex-1">
              Create Another
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
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
