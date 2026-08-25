"use client";

import { useCallback, useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import PageHeader from "@/components/layout/PageHeader";
import OrderCard, { OrderCardSkeleton } from "@/components/orders/OrderCard";
import EmptyState from "@/components/shared/EmptyState";
import ErrorState from "@/components/shared/ErrorState";
import { useBusinessId } from "@/providers/BusinessProvider";
import { apiClient } from "@/lib/api/client";
import { OrderSummaryDTO } from "@/lib/api/types";

function OrdersContent() {
  const businessId = useBusinessId();
  const searchParams = useSearchParams();
  const statusParam = searchParams.get("status") || undefined;

  const [orders, setOrders] = useState<OrderSummaryDTO[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await apiClient.getOrders(businessId, statusParam);
      setOrders(data);
    } catch {
      setError(true);
      setOrders(null);
    } finally {
      setLoading(false);
    }
  }, [businessId, statusParam]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadOrders();
  }, [loadOrders]);

  return (
    <>
      {loading ? (
        <section
          className="grid grid-cols-1 md:grid-cols-2 gap-stack-md w-full"
          aria-busy="true"
          aria-label="Loading orders"
        >
          {Array.from({ length: 3 }).map((_, i) => (
            <OrderCardSkeleton key={i} />
          ))}
        </section>
      ) : error ? (
        <ErrorState
          title="Could not load orders."
          message="There was a problem fetching your orders. Please try again."
          onRetry={loadOrders}
        />
      ) : orders && orders.length === 0 ? (
        <EmptyState message="No orders identified yet." icon="shopping_bag" />
      ) : (
        <section className="grid grid-cols-1 md:grid-cols-2 gap-stack-md w-full">
          {orders?.map((order) => (
            <OrderCard key={order.id} order={order} />
          ))}
        </section>
      )}
    </>
  );
}

export default function OrdersPage() {
  return (
    <div className="flex flex-col gap-stack-lg w-full">
      <PageHeader title="Orders" />
      <p className="font-metadata text-metadata text-ci-secondary -mt-2">
        View your recent orders.
      </p>

      <Suspense fallback={
        <section
          className="grid grid-cols-1 md:grid-cols-2 gap-stack-md w-full"
          aria-busy="true"
          aria-label="Loading orders"
        >
          {Array.from({ length: 3 }).map((_, i) => (
            <OrderCardSkeleton key={i} />
          ))}
        </section>
      }>
        <OrdersContent />
      </Suspense>
    </div>
  );
}
