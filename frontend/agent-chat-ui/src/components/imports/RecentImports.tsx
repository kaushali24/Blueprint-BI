import { ImportBatchDTO } from "@/lib/api/types";
import StatusBadge from "@/components/shared/StatusBadge";
import { formatDistanceToNow, parseISO } from "date-fns";
import { Skeleton } from "@/components/ui/skeleton";

interface RecentImportsProps {
  imports: ImportBatchDTO[] | null;
  loading: boolean;
}

function formatTime(dateString: string) {
  try {
    const date = parseISO(dateString);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return dateString;
  }
}

export default function RecentImports({ imports, loading }: RecentImportsProps) {
  if (loading) {
    return (
      <section className="flex flex-col gap-stack-gap-md w-full mt-6">
        <h3 className="headline-md text-ci-on-surface">Recent Imports</h3>
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex justify-between h-[72px]">
              <div className="flex flex-col justify-center gap-2">
                <Skeleton className="h-4 w-40" />
              </div>
              <div className="flex flex-col justify-center items-end gap-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (!imports || imports.length === 0) {
    return null;
  }

  return (
    <section className="flex flex-col gap-stack-gap-md w-full mt-6">
      <h3 className="headline-md text-ci-on-surface">Recent Imports</h3>
      <div className="flex flex-col gap-3">
        {imports.map((imp) => (
          <div key={imp.id} className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 min-w-0">
            <div className="flex flex-col gap-1 min-w-0">
              <span className="body-md font-semibold text-ci-on-surface truncate" title={imp.source_file_name || imp.import_name}>
                {imp.source_file_name || imp.import_name}
              </span>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <StatusBadge status={imp.status} />
              <span className="metadata text-ci-secondary">{formatTime(imp.created_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
