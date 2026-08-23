"use client";

import { useEffect, useState } from "react";
import { Icons } from "@/lib/icons";

interface ImportProgressProps {
  filename: string;
}

const PROCESSING_STEPS = [
  "Reading conversations",
  "Finding business messages",
  "Identifying business information",
  "Updating your overview",
] as const;

export default function ImportProgress({ filename }: ImportProgressProps) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveStep((prev) => (prev + 1) % PROCESSING_STEPS.length);
    }, 2200);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <div
      className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-md shadow-sm items-center text-center py-10"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="relative flex items-center justify-center mb-2">
        <div className="w-16 h-16 border-4 border-ci-surface-variant rounded-full" aria-hidden="true" />
        <div
          className="w-16 h-16 border-4 border-ci-primary border-t-transparent rounded-full animate-spin absolute top-0 left-0"
          aria-hidden="true"
        />
        <Icons.CloudUpload className="text-ci-primary absolute w-6 h-6" aria-hidden="true" />
      </div>

      <h3 className="font-headline-md text-headline-md text-ci-on-surface">
        Processing your WhatsApp conversations...
      </h3>

      <p className="font-metadata text-metadata text-ci-on-surface-variant max-w-sm mt-1">
        General progress feedback — this may take a moment while your export is processed.
      </p>

      <ul className="flex flex-col gap-2 mt-4 w-full max-w-xs text-left" aria-label="Processing steps">
        {PROCESSING_STEPS.map((step, index) => (
          <li
            key={step}
            className={`font-metadata text-metadata flex items-center gap-2 transition-opacity ${
              index === activeStep
                ? "text-ci-primary opacity-100"
                : "text-ci-secondary opacity-60"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                index === activeStep ? "bg-ci-primary animate-pulse" : "bg-ci-outline-variant"
              }`}
              aria-hidden="true"
            />
            {step}
          </li>
        ))}
      </ul>

      <div className="mt-4 px-3 py-1.5 bg-ci-surface-container-low rounded-lg border border-ci-outline-variant/30 flex items-center gap-2 max-w-full">
        <Icons.FileArchive className="w-4 h-4 text-ci-secondary shrink-0" aria-hidden="true" />
        <span
          className="font-metadata text-metadata text-ci-secondary truncate"
          title={filename}
        >
          {filename}
        </span>
      </div>
    </div>
  );
}
