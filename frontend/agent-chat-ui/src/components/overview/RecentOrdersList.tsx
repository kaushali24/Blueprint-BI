import { RecentOrderDTO } from "@/lib/api/types";
import AmountDisplay from "@/components/shared/AmountDisplay";
import StatusBadge from "@/components/shared/StatusBadge";
import Link from "next/link";
import { formatDistanceToNow, parseISO } from "date-fns";

interface RecentOrdersListProps {
  orders: RecentOrderDTO[];
}

function formatTime(dateString: string) {
  try {
    const date = parseISO(dateString);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return dateString;
  }
}

export default function RecentOrdersList({ orders }: RecentOrdersListProps) {
  if (orders.length === 0) {
    return (
      <section className="flex flex-col gap-stack-gap-md w-full">
        <div className="flex items-center justify-between w-full">
          <h3 className="headline-md text-ci-on-surface">Recent Orders</h3>
        </div>
        <p className="body-md text-ci-secondary">No recent orders found.</p>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-stack-gap-md w-full">
      <div className="flex items-center justify-between w-full">
        <h3 className="headline-md text-ci-on-surface">Recent Orders</h3>
        <Link href="/orders" className="label-caps text-ci-primary hover:text-ci-primary-container transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ci-primary rounded-sm">
          View All
        </Link>
      </div>
      <div className="flex flex-col gap-3">
        {orders.map((order) => (
          <div key={order.id} className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 min-w-0">
            <div className="flex flex-col gap-1 w-full sm:w-auto min-w-0">
              <div className="flex items-center gap-2 flex-wrap min-w-0">
                <span className="body-md font-semibold text-ci-on-surface break-words">
                  {order.order_number || (order.customer_name ? `Order from ${order.customer_name}` : (order.first_product_name || `Order #${order.id}`))}
                </span>
                <StatusBadge status={order.status} />
              </div>
            </div>
            <div className="flex sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto mt-2 sm:mt-0">
              <AmountDisplay amount={order.total_amount} />
              <span className="metadata text-ci-secondary">{formatTime(order.created_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
