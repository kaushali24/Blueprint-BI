import { useState, useCallback, useRef } from "react";
import { apiClient, ApiError } from "@/lib/api/client";
import { ImportResultDTO } from "@/lib/api/types";

export type ImportState =
  | { stage: "idle" }
  | { stage: "file_selected"; file: File }
  | { stage: "uploading"; file: File }
  | { stage: "success"; result: ImportResultDTO }
  | { stage: "warning"; result: ImportResultDTO }
  | { stage: "error"; messages: string[] };

function mapResultToState(result: ImportResultDTO): ImportState {
  if (result.status === "failed" || !result.is_successful) {
    return {
      stage: "error",
      messages: translateResultErrors(result.errors),
    };
  }

  if (
    result.status === "completed_with_warnings" ||
    (result.warnings && result.warnings.length > 0)
  ) {
    return { stage: "warning", result };
  }

  if (result.status === "completed" && result.is_successful) {
    return { stage: "success", result };
  }

  return { stage: "error", messages: ["Import failed. Please try again."] };
}

function translateResultErrors(errors: string[] | undefined): string[] {
  if (!errors || errors.length === 0) {
    return ["Import failed. Please try again."];
  }

  const combined = errors.join(" ").toLowerCase();

  if (combined.includes("database is locked") || combined.includes("database is busy")) {
    return ["The database is busy. Please wait a moment and try again."];
  }

  if (combined.includes("zip") || combined.includes("archive")) {
    return [
      "We couldn't process this WhatsApp export. Please check the file and try again.",
    ];
  }

  if (combined.includes("was not found")) {
    return ["The selected demo business could not be found."];
  }

  return ["Import failed. Please try again."];
}

function translateApiError(error: ApiError): string[] {
  const detail = error.body?.detail ?? error.body;
  const rawErrors: string[] = Array.isArray(detail?.errors)
    ? detail.errors
    : typeof detail === "string"
      ? [detail]
      : [];

  if (error.status === 503) {
    return ["The database is busy. Please wait a moment and try again."];
  }

  if (error.status === 404) {
    return ["The selected demo business could not be found."];
  }

  return translateResultErrors(rawErrors);
}

export function useZipUpload(businessId: number) {
  const [state, setState] = useState<ImportState>({ stage: "idle" });
  const isUploadingRef = useRef(false);

  const selectFile = useCallback((file: File) => {
    setState({ stage: "file_selected", file });
  }, []);

  const clearFile = useCallback(() => {
    isUploadingRef.current = false;
    setState({ stage: "idle" });
  }, []);

  const uploadFile = useCallback(async () => {
    if (state.stage !== "file_selected" || isUploadingRef.current) return;

    const file = state.file;
    isUploadingRef.current = true;
    setState({ stage: "uploading", file });

    try {
      const result = await apiClient.uploadImport(businessId, file);
      setState(mapResultToState(result));
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = err.body?.detail ?? err.body;
        if (
          detail &&
          typeof detail === "object" &&
          "status" in detail &&
          "is_successful" in detail
        ) {
          setState(mapResultToState(detail as ImportResultDTO));
        } else {
          setState({ stage: "error", messages: translateApiError(err) });
        }
      } else {
        setState({ stage: "error", messages: ["Import failed. Please try again."] });
      }
    } finally {
      isUploadingRef.current = false;
    }
  }, [state, businessId]);

  return {
    state,
    selectFile,
    clearFile,
    uploadFile,
    isUploading: state.stage === "uploading",
  };
}
