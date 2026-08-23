"use client";

import { Icons } from "@/lib/icons";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ title, message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-ci-error-container rounded-xl border border-ci-error/20">
      <div className="w-12 h-12 rounded-full bg-white/50 flex items-center justify-center mb-4">
        <Icons.info className="w-6 h-6 text-ci-on-error-container" />
      </div>
      {title && <h3 className="headline-md text-ci-on-error-container mb-2">{title}</h3>}
      <p className="body-md text-ci-on-error-container mb-4">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="px-4 py-2 bg-ci-on-error-container text-ci-error-container rounded-full font-semibold hover:opacity-90 transition-opacity outline-none focus-visible:ring-2 focus-visible:ring-ci-on-error-container focus-visible:ring-offset-2"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
