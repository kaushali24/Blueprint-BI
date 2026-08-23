import { OrderDetailDTO } from "@/lib/api/types";
import AmountDisplay from "@/components/shared/AmountDisplay";
import StatusBadge from "@/components/shared/StatusBadge";
import { formatOrderDetailDate } from "@/lib/formatOrderDate";

interface OrderDetailsCardProps {
  order: OrderDetailDTO;
}

function ItemAmount({ amount }: { amount: string | null }) {
  if (amount === null) {
    return (
      <span className="font-metadata text-metadata text-ci-secondary italic">
        Amount unavailable
      </span>
    );
  }

  const numericAmount = Number(amount);
  const formatted = new Intl.NumberFormat("en-IN", {
    style: "decimal",
    maximumFractionDigits: 0,
  }).format(numericAmount);

  return (
    <span className="font-metadata text-metadata text-ci-on-surface font-medium">
      Rs. {formatted}
    </span>
  );
}

export default function OrderDetailsCard({ order }: OrderDetailsCardProps) {
  const customerLabel = order.customer_name ?? "Customer unavailable";

  return (
    <div className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-lg shadow-sm">
      <div className="flex justify-between items-start gap-3">
        <StatusBadge status={order.status} />
        <span className="font-metadata text-metadata text-ci-secondary shrink-0">
          {formatOrderDetailDate(order.created_at)}
        </span>
      </div>

      <div className="flex flex-col gap-2">
        <div>
          <span className="font-metadata text-metadata text-ci-secondary block mb-0.5">
            Customer
          </span>
          <span className="font-body-md text-body-md text-ci-on-surface font-semibold">
            {customerLabel}
          </span>
        </div>

        <div className="h-px w-full bg-ci-outline-variant/30" />

        <div>
          <span className="font-metadata text-metadata text-ci-secondary block mb-2">
            {order.items.length === 1 ? "Product" : "Products / Items"}
          </span>
          <ul className="flex flex-col gap-3">
            {order.items.map((item, index) => (
              <li
                key={`${item.product_name}-${index}`}
                className="flex flex-col gap-1 pb-3 border-b border-ci-outline-variant/20 last:border-0 last:pb-0"
              >
                <span className="font-body-md text-body-md text-ci-on-surface">
                  {item.product_name}
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-metadata text-metadata text-ci-secondary">
                  <span>Qty: {item.quantity}</span>
                  <span className="flex flex-col gap-0.5">
                    <span>Unit price</span>
                    <ItemAmount amount={item.unit_price} />
                  </span>
                  <span className="flex flex-col gap-0.5">
                    <span>Line total</span>
                    <ItemAmount amount={item.line_total} />
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-2 pt-4 border-t border-ci-outline-variant/30">
        <span className="font-metadata text-metadata text-ci-secondary block mb-1">
          Total Amount
        </span>
        <AmountDisplay amount={order.total_amount} variant="hero" />
      </div>
    </div>
  );
}

export function OrderDetailsCardSkeleton() {
  return (
    <div
      className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-md shadow-sm animate-pulse"
      aria-hidden="true"
    >
      <div className="flex justify-between items-start">
        <div className="h-6 w-24 bg-ci-surface-container rounded-full" />
        <div className="h-4 w-20 bg-ci-surface-container rounded" />
      </div>
      <div className="flex flex-col gap-3">
        <div className="h-4 w-16 bg-ci-surface-container rounded" />
        <div className="h-5 w-32 bg-ci-surface-container rounded" />
        <div className="h-px bg-ci-outline-variant/30" />
        <div className="h-4 w-20 bg-ci-surface-container rounded" />
        <div className="h-5 w-40 bg-ci-surface-container rounded" />
      </div>
      <div className="pt-4 border-t border-ci-outline-variant/30">
        <div className="h-4 w-24 bg-ci-surface-container rounded mb-2" />
        <div className="h-8 w-32 bg-ci-surface-container rounded" />
      </div>
    </div>
  );
}
