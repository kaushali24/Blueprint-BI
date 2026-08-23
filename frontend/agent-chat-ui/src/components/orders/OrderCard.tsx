import Link from "next/link";
import { OrderSummaryDTO } from "@/lib/api/types";
import AmountDisplay from "@/components/shared/AmountDisplay";
import StatusBadge from "@/components/shared/StatusBadge";
import { formatOrderDate } from "@/lib/formatOrderDate";
import { Icons } from "@/lib/icons";

interface OrderCardProps {
  order: OrderSummaryDTO;
}

export default function OrderCard({ order }: OrderCardProps) {
  const customerLabel = order.customer_name ?? "Customer unavailable";
  const productLabel = order.first_product_name ?? "Product unavailable";
  const accessibleName = `Order for ${customerLabel}, ${productLabel}, ${order.status}`;

  return (
    <Link
      href={`/orders/${order.id}`}
      className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-3 shadow-sm hover:shadow-md transition-shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ci-primary focus-visible:ring-offset-2"
      aria-label={accessibleName}
    >
      <div className="flex justify-between items-start gap-3">
        <div className="min-w-0 flex-1">
          <h2 className="font-headline-md text-headline-md text-ci-on-surface line-clamp-2 break-words">
            {customerLabel}
          </h2>
          <p className="font-metadata text-metadata text-ci-secondary mt-1 line-clamp-2">
            {productLabel}
          </p>
        </div>
        <StatusBadge status={order.status} />
      </div>
      <div className="border-t border-ci-outline-variant/30 pt-3 flex justify-between items-end gap-3 mt-auto">
        <AmountDisplay amount={order.total_amount} />
        <p className="font-metadata text-metadata text-ci-secondary flex items-center gap-1 shrink-0">
          <Icons.pending_actions className="w-3.5 h-3.5" aria-hidden="true" />
          {formatOrderDate(order.created_at)}
        </p>
      </div>
    </Link>
  );
}

export function OrderCardSkeleton() {
  return (
    <div
      className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-3 shadow-sm animate-pulse"
      aria-hidden="true"
    >
      <div className="flex justify-between items-start gap-3">
        <div className="flex flex-col gap-2 flex-1">
          <div className="h-5 bg-ci-surface-container rounded w-2/5" />
          <div className="h-4 bg-ci-surface-container rounded w-3/5" />
        </div>
        <div className="h-6 w-20 bg-ci-surface-container rounded-full" />
      </div>
      <div className="border-t border-ci-outline-variant/30 pt-3 flex justify-between items-end">
        <div className="h-6 bg-ci-surface-container rounded w-24" />
        <div className="h-4 bg-ci-surface-container rounded w-16" />
      </div>
    </div>
  );
}
