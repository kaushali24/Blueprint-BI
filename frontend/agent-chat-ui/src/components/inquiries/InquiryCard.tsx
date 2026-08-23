import { InquirySummaryDTO } from "@/lib/api/types";
import StatusBadge from "@/components/shared/StatusBadge";
import { formatOrderDate } from "@/lib/formatOrderDate";
import { getCustomerInitials } from "@/lib/getCustomerInitials";
import { Icons } from "@/lib/icons";

interface InquiryCardProps {
  inquiry: InquirySummaryDTO;
}

export default function InquiryCard({ inquiry }: InquiryCardProps) {
  const customerLabel = inquiry.customer_name ?? "Customer unavailable";
  const initials = getCustomerInitials(inquiry.customer_name);
  const accentClass =
    inquiry.status === "resolved"
      ? "bg-ci-primary"
      : inquiry.status === "open"
        ? "bg-ci-tertiary-fixed-dim"
        : "bg-ci-outline-variant";

  return (
    <article className="bg-ci-surface-container-lowest rounded-xl border border-ci-outline-variant p-card-padding shadow-sm relative overflow-hidden flex flex-col justify-between min-h-[140px]">
      <div className={`absolute top-0 left-0 w-1 h-full ${accentClass}`} aria-hidden="true" />

      <div className="flex justify-between items-start gap-3 mb-3 pl-2">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className="w-8 h-8 rounded-full bg-ci-secondary-container flex items-center justify-center text-ci-primary font-bold text-sm shrink-0"
            aria-hidden="true"
          >
            {inquiry.customer_name ? (
              initials
            ) : (
              <Icons.group className="w-4 h-4 text-ci-secondary" aria-hidden="true" />
            )}
          </div>
          <h2 className="font-headline-md text-[16px] font-semibold text-ci-on-surface truncate">
            {customerLabel}
          </h2>
        </div>
        <time
          className="font-metadata text-metadata text-ci-secondary shrink-0"
          dateTime={inquiry.created_at}
        >
          {formatOrderDate(inquiry.created_at)}
        </time>
      </div>

      <p className="mb-4 pl-2 font-body-md text-body-md text-ci-on-surface-variant break-words">
        {inquiry.summary}
      </p>

      <div className="flex justify-between items-end pl-2 mt-auto">
        <StatusBadge status={inquiry.status} />
      </div>
    </article>
  );
}

export function InquiryCardSkeleton() {
  return (
    <div
      className="bg-ci-surface-container-lowest rounded-xl border border-ci-outline-variant p-card-padding shadow-sm relative overflow-hidden flex flex-col gap-3 animate-pulse min-h-[140px]"
      aria-hidden="true"
    >
      <div className="absolute top-0 left-0 w-1 h-full bg-ci-outline-variant/50" />
      <div className="flex justify-between items-start pl-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-ci-surface-container" />
          <div className="h-4 w-24 bg-ci-surface-container rounded" />
        </div>
        <div className="h-3 w-12 bg-ci-surface-container rounded" />
      </div>
      <div className="pl-2 flex flex-col gap-2">
        <div className="h-4 w-full bg-ci-surface-container rounded" />
        <div className="h-4 w-[80%] bg-ci-surface-container rounded" />
      </div>
      <div className="pl-2">
        <div className="h-6 w-16 bg-ci-surface-container rounded-full" />
      </div>
    </div>
  );
}
