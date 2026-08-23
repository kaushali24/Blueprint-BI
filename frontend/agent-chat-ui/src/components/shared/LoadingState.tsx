"use client";

import { Skeleton } from "@/components/ui/skeleton";

interface LoadingStateProps {
  rows?: number;
}

export default function LoadingState({ rows = 3 }: LoadingStateProps) {
  return (
    <div className="flex flex-col gap-4 w-full">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-4 bg-ci-surface-container rounded-xl border border-ci-outline-variant flex gap-4 items-center">
          <Skeleton className="w-12 h-12 rounded-full" />
          <div className="flex flex-col gap-2 flex-1">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/4" />
          </div>
        </div>
      ))}
    </div>
  );
}
