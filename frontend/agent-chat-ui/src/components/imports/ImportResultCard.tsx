import { Icons } from "@/lib/icons";
import { ImportState } from "@/hooks/useZipUpload";
import Link from "next/link";

interface ImportResultCardProps {
  state: Extract<ImportState, { stage: "success" | "warning" | "error" }>;
  onReset: () => void;
}

export default function ImportResultCard({ state, onReset }: ImportResultCardProps) {
  let warnings: string[] = [];
  if (state.stage === "warning" || state.stage === "success") {
    warnings = state.result.warnings ?? [];
  }

  const mediaWarnings = warnings.filter((w) =>
    w.toLowerCase().includes("advanced media interpretation was not performed"),
  );
  const otherWarnings = warnings.filter(
    (w) => !w.toLowerCase().includes("advanced media interpretation was not performed"),
  );

  const hasOnlyMediaWarnings = state.stage === "warning" && otherWarnings.length === 0;

  const isError = state.stage === "error";
  const isWarning = state.stage === "warning" && !hasOnlyMediaWarnings;
  const isSuccess = state.stage === "success" || hasOnlyMediaWarnings;

  return (
    <div
      className={`border rounded-xl p-card-padding flex flex-col gap-stack-md shadow-sm items-center text-center py-10 ${
        isError
          ? "bg-ci-error-container/10 border-ci-error/20"
          : isWarning
            ? "bg-ci-tertiary-fixed/30 border-ci-tertiary-fixed-dim/50"
            : "bg-ci-surface-container-lowest border-ci-outline-variant"
      }`}
      role="status"
      aria-live="polite"
    >
      <div
        className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${
          isError
            ? "bg-ci-error/10 text-ci-error"
            : isWarning
              ? "bg-ci-tertiary-fixed text-ci-on-tertiary-fixed-variant"
              : "bg-ci-primary/10 text-ci-primary"
        }`}
        aria-hidden="true"
      >
        {isError ? (
          <Icons.XCircle className="w-8 h-8" />
        ) : isWarning ? (
          <Icons.AlertTriangle className="w-8 h-8" />
        ) : (
          <Icons.CheckCircle className="w-8 h-8" />
        )}
      </div>

      <h3
        className={`font-headline-md text-headline-md ${
          isError ? "text-ci-error" : "text-ci-on-surface"
        }`}
      >
        {isError && "Import failed"}
        {isWarning && "Import completed with some warnings"}
        {isSuccess && "Import completed successfully"}
      </h3>

      <div className="font-metadata text-metadata text-ci-on-surface-variant max-w-sm mt-2 flex flex-col gap-2">
        {isError &&
          state.messages.map((msg, i) => (
            <p key={i}>{msg}</p>
          ))}

        {isWarning && (
          <p>
            Your WhatsApp conversation was processed, but some items need attention.
          </p>
        )}

        {isSuccess && (
          <p>Your WhatsApp conversation was processed successfully.</p>
        )}

        {(isWarning || isSuccess) && (
          <>
            {mediaWarnings.length > 0 && (
              <div className="text-left bg-ci-surface-container-high/60 p-3 rounded-lg mt-2 text-[13px] text-ci-on-surface-variant border border-ci-outline-variant/40 flex gap-2.5 items-start">
                <Icons.info className="w-4 h-4 mt-0.5 shrink-0 text-ci-on-surface-variant/70" aria-hidden="true" />
                <div>
                  <p className="font-medium text-ci-on-surface">
                    {mediaWarnings.length === 1
                      ? "Some media wasn\u2019t analyzed"
                      : `${mediaWarnings.length} media items weren\u2019t analyzed`}
                  </p>
                  <p className="mt-1">
                    This chat contains images or voice messages. ChatInsights imported the
                    conversation successfully, but advanced media interpretation isn't
                    included in this MVP.
                  </p>
                </div>
              </div>
            )}
            {otherWarnings.length > 0 && (
              <ul className="text-left bg-ci-tertiary-fixed/40 p-3 rounded-lg mt-2 list-disc list-inside text-[13px] text-ci-on-tertiary-fixed-variant border border-ci-tertiary-fixed-dim/40">
                {otherWarnings.map((warn, i) => (
                  <li key={i}>{warn}</li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mt-6 w-full max-w-sm">
        {(isSuccess || isWarning) && (
          <Link
            href="/overview"
            className="flex-1 bg-ci-primary hover:bg-ci-primary-container text-ci-on-primary font-body-md text-body-md font-medium py-2.5 px-4 rounded-lg flex justify-center items-center transition-all shadow-sm active:scale-[0.98]"
          >
            View Business Overview
          </Link>
        )}

        <button
          type="button"
          onClick={onReset}
          className={`flex-1 font-body-md text-body-md font-medium py-2.5 px-4 rounded-lg flex justify-center items-center transition-all active:scale-[0.98] ${
            isError
              ? "bg-ci-error hover:bg-ci-error/90 text-ci-on-error shadow-sm"
              : "bg-ci-surface-container hover:bg-ci-surface-container-high text-ci-on-surface border border-ci-outline-variant/50"
          }`}
        >
          {isError ? "Try Again" : "Import Another ZIP"}
        </button>
      </div>
    </div>
  );
}
