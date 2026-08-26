import { CustomerSummaryDTO } from "@/lib/api/types";
import { getCustomerInitials } from "@/lib/getCustomerInitials";

interface CustomerCardProps {
  customer: CustomerSummaryDTO;
}

export default function CustomerCard({ customer }: CustomerCardProps) {
  const customerName = customer.name.trim() || "Customer unavailable";
  const initials = getCustomerInitials(customer.name);

  const orderText =
    customer.order_count === 1
      ? "1 order"
      : `${customer.order_count} orders`;

  const inquiryText =
    customer.inquiry_count === 1
      ? "1 inquiry"
      : `${customer.inquiry_count} inquiries`;

  const countsSummary = `${orderText}, ${inquiryText}`;

  return (
    <article
      className="bg-ci-surface-container-lowest rounded-xl border border-ci-outline-variant p-card-padding shadow-sm flex items-center justify-between gap-4"
      aria-label={`Customer ${customerName}`}
    >
      <div className="flex items-center gap-3.5 min-w-0 flex-1">
        <div
          className="w-11 h-11 rounded-full bg-ci-secondary-container flex items-center justify-center text-ci-primary font-bold text-base shrink-0 select-none"
          aria-hidden="true"
        >
          {initials}
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="font-headline-md text-[16px] font-semibold text-ci-on-surface truncate">
            {customerName}
          </h2>
          <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2 mt-0.5">
            <p className="font-metadata text-metadata text-ci-secondary truncate">
              {countsSummary}
            </p>
            {customer.phone_number && (
              <>
                <span className="hidden sm:inline text-ci-outline-variant" aria-hidden="true">•</span>
                <p className="font-metadata text-metadata text-ci-secondary truncate">
                  {customer.phone_number}
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

export function CustomerCardSkeleton() {
  return (
    <div
      className="bg-ci-surface-container-lowest rounded-xl border border-ci-outline-variant p-card-padding shadow-sm flex items-center justify-between gap-4 animate-pulse"
      aria-hidden="true"
    >
      <div className="flex items-center gap-3.5 min-w-0 flex-1">
        <div className="w-11 h-11 rounded-full bg-ci-surface-container shrink-0" />
        <div className="min-w-0 flex-1 flex flex-col gap-2">
          <div className="h-4 w-32 bg-ci-surface-container rounded" />
          <div className="h-3 w-48 bg-ci-surface-container rounded" />
        </div>
      </div>
    </div>
  );
}
