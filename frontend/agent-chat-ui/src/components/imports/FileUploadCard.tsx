import { useCallback, useState } from "react";
import { ImportState } from "@/hooks/useZipUpload";
import { Icons } from "@/lib/icons";

interface FileUploadCardProps {
  state: ImportState;
  onSelectFile: (file: File) => void;
  onClearFile: () => void;
  onUpload: () => void;
  isUploading?: boolean;
}

function isValidZipFile(file: File): boolean {
  return file.name.toLowerCase().endsWith(".zip");
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUploadCard({
  state,
  onSelectFile,
  onClearFile,
  onUpload,
  isUploading = false,
}: FileUploadCardProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!isValidZipFile(file)) {
        setValidationMessage("Please choose a WhatsApp ZIP export.");
        return;
      }
      setValidationMessage(null);
      onSelectFile(file);
    },
    [onSelectFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFile(e.target.files[0]);
      }
      e.target.value = "";
    },
    [handleFile],
  );

  if (state.stage === "file_selected") {
    return (
      <div className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-md shadow-sm relative overflow-hidden">
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-ci-primary" aria-hidden="true" />
        <div className="flex justify-between items-center gap-3">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <div className="w-10 h-10 rounded bg-ci-surface-variant flex items-center justify-center text-ci-primary shrink-0">
              <Icons.FileArchive className="w-5 h-5" aria-hidden="true" />
            </div>
            <div className="flex flex-col min-w-0">
              <span
                className="font-body-md text-body-md text-ci-on-surface font-medium truncate"
                title={state.file.name}
              >
                {state.file.name}
              </span>
              <span className="font-metadata text-metadata text-ci-secondary">
                Ready to import ({formatFileSize(state.file.size)})
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClearFile}
            disabled={isUploading}
            className="text-ci-secondary hover:text-ci-error transition-colors p-2 rounded-full hover:bg-ci-error-container/20 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
            aria-label="Remove selected file"
          >
            <Icons.X className="w-5 h-5" />
          </button>
        </div>
        <button
          type="button"
          onClick={onUpload}
          disabled={isUploading}
          className="w-full bg-ci-primary hover:bg-ci-primary-container text-ci-on-primary font-body-md text-body-md font-medium py-3 px-4 rounded-lg flex justify-center items-center gap-2 transition-all shadow-sm active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed disabled:active:scale-100"
        >
          <Icons.Upload className="w-5 h-5" aria-hidden="true" />
          Import Conversations
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-stack-sm">
      <label
        className={`relative block w-full border-2 border-dashed rounded-xl p-8 transition-colors cursor-pointer group text-center shadow-sm ${
          isDragOver
            ? "border-ci-primary bg-ci-surface-container"
            : validationMessage
              ? "border-ci-error/40 bg-ci-error-container/5"
              : "border-ci-outline-variant bg-ci-surface-container-lowest hover:bg-ci-surface-container-low"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        htmlFor="whatsapp-zip-upload"
      >
        <input
          id="whatsapp-zip-upload"
          type="file"
          accept=".zip"
          className="sr-only"
          onChange={handleChange}
          disabled={isUploading}
          aria-label="Upload WhatsApp ZIP export"
        />
        <div className="flex flex-col items-center gap-stack-sm pointer-events-none">
          <div className="w-12 h-12 rounded-full bg-ci-surface-variant flex items-center justify-center text-ci-primary group-hover:scale-110 transition-transform">
            <Icons.CloudUpload className="w-6 h-6" aria-hidden="true" />
          </div>
          <p className="font-body-md text-body-md text-ci-on-surface font-medium mt-2">
            Drag &amp; Drop ZIP file or click to browse
          </p>
          <p className="font-metadata text-metadata text-ci-secondary">
            WhatsApp export (.zip) only
          </p>
        </div>
      </label>
      {validationMessage && (
        <p
          className="font-metadata text-metadata text-ci-error px-1"
          role="alert"
          aria-live="polite"
        >
          {validationMessage}
        </p>
      )}
    </div>
  );
}
