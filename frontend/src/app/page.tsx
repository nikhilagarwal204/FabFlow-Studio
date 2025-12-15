"use client";

import { useState } from "react";
import { VideoInputForm } from "@/components/VideoInputForm";
import type { UserInput } from "@/lib/validation";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (input: UserInput) => {
    setIsLoading(true);
    console.log("Submitting:", input);
    // TODO: Connect to backend API in future tasks
    // For now, just log the input
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

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
        <VideoInputForm onSubmit={handleSubmit} isLoading={isLoading} />
      </main>
    </div>
  );
}
