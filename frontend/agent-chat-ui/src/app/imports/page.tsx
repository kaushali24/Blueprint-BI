"use client";

import { useState, useCallback, useEffect } from "react";
import PageHeader from "@/components/layout/PageHeader";
import { apiClient } from "@/lib/api/client";
import { ImportBatchDTO } from "@/lib/api/types";
import { useBusinessId } from "@/providers/BusinessProvider";
import { useZipUpload } from "@/hooks/useZipUpload";
import { Icons } from "@/lib/icons";
import FileUploadCard from "@/components/imports/FileUploadCard";
import ImportProgress from "@/components/imports/ImportProgress";
import ImportResultCard from "@/components/imports/ImportResultCard";
import RecentImports from "@/components/imports/RecentImports";

const QUICK_STEPS = [
  "Open the customer chat in WhatsApp",
  'Choose "Export chat"',
  'Choose "Without media"',
  "Upload the exported ZIP here",
] as const;

export default function ImportsPage() {
  const businessId = useBusinessId();
  const { state, selectFile, clearFile, uploadFile, isUploading } = useZipUpload(businessId);
  const [showExportHelp, setShowExportHelp] = useState(false);
  const [recentImports, setRecentImports] = useState<ImportBatchDTO[] | null>(null);
  const [loadingImports, setLoadingImports] = useState(true);

  const loadImports = useCallback(async () => {
    setLoadingImports(true);
    try {
      const data = await apiClient.getRecentImports(businessId);
      setRecentImports(data);
    } catch {
      setRecentImports(null);
    } finally {
      setLoadingImports(false);
    }
  }, [businessId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadImports();
  }, [loadImports, state.stage]);

  const showInstructions =
    state.stage === "idle" || state.stage === "file_selected";

  return (
    <div className="flex flex-col gap-stack-lg w-full relative">
      <div
        className="fixed top-20 right-0 w-64 h-64 bg-ci-primary/5 rounded-full blur-3xl -z-10 pointer-events-none"
        aria-hidden="true"
      />

      <PageHeader title="Import WhatsApp Conversations" />

      <p className="font-metadata text-metadata text-ci-on-surface-variant -mt-2">
        Upload an exported WhatsApp chat ZIP to turn your conversations into business insights.
      </p>

      {showInstructions && (
        <section className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-md shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <h2 className="font-label-caps text-label-caps text-ci-on-surface-variant tracking-wider">
              Quick Steps
            </h2>
            <button
              type="button"
              onClick={() => setShowExportHelp((prev) => !prev)}
              className="font-metadata text-metadata text-ci-primary hover:text-ci-primary-container transition-colors font-medium flex items-center gap-1 group self-start"
              aria-expanded={showExportHelp}
            >
              How do I export a WhatsApp chat?
              <Icons.ArrowRight
                className={`w-4 h-4 transition-transform ${showExportHelp ? "rotate-90" : "group-hover:translate-x-1"}`}
                aria-hidden="true"
              />
            </button>
          </div>

          {showExportHelp && (
            <div
              className="bg-ci-surface-container-low p-3 rounded-lg border border-ci-outline-variant/30 font-metadata text-metadata text-ci-on-surface-variant"
              role="region"
              aria-label="WhatsApp export instructions"
            >
              In WhatsApp, open the chat → tap the menu (⋮) → Export chat → choose
              Without media → save the ZIP file, then upload it here.
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-stack-sm">
            {QUICK_STEPS.map((step, index) => (
              <div
                key={step}
                className="flex gap-4 items-center p-4 bg-ci-surface rounded-lg border border-ci-outline-variant/50 shadow-sm"
              >
                <div className="w-6 h-6 rounded-full bg-ci-surface-variant text-ci-primary flex items-center justify-center font-label-caps text-[10px] shrink-0">
                  {index + 1}
                </div>
                <span className="font-metadata text-metadata text-ci-on-surface">{step}</span>
              </div>
            ))}
          </div>

          <div className="bg-ci-surface-container-low p-3 rounded-lg flex gap-2 items-center mt-1 border border-ci-outline-variant/30">
            <Icons.info className="w-[18px] h-[18px] text-ci-secondary shrink-0" aria-hidden="true" />
            <span className="font-metadata text-metadata text-ci-secondary">
              You don&apos;t need to extract the ZIP.
            </span>
          </div>
        </section>
      )}

      <section className="flex flex-col gap-stack-md">
        {(state.stage === "idle" || state.stage === "file_selected") && (
          <FileUploadCard
            state={state}
            onSelectFile={selectFile}
            onClearFile={clearFile}
            onUpload={uploadFile}
            isUploading={isUploading}
          />
        )}

        {state.stage === "uploading" && <ImportProgress filename={state.file.name} />}

        {(state.stage === "success" ||
          state.stage === "warning" ||
          state.stage === "error") && (
          <ImportResultCard state={state} onReset={clearFile} />
        )}

        {showInstructions && (
          <RecentImports imports={recentImports} loading={loadingImports} />
        )}
      </section>
    </div>
  );
}
