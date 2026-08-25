"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import PageHeader from "@/components/layout/PageHeader";
import OrderDetailsCard, {
  OrderDetailsCardSkeleton,
} from "@/components/orders/OrderDetailsCard";
import EvidenceMessageList from "@/components/orders/EvidenceMessageList";
import ErrorState from "@/components/shared/ErrorState";
import EmptyState from "@/components/shared/EmptyState";
import { useBusinessId } from "@/providers/BusinessProvider";
import { apiClient, ApiError } from "@/lib/api/client";
import { EvidenceMessageDTO, OrderDetailDTO } from "@/lib/api/types";

export default function OrderDetailsPage() {
  const businessId = useBusinessId();
  const params = useParams();
  const orderId = Number(params.id);

  const [order, setOrder] = useState<OrderDetailDTO | null>(null);
  const [evidence, setEvidence] = useState<EvidenceMessageDTO[]>([]);
  const [loadingOrder, setLoadingOrder] = useState(true);
  const [loadingEvidence, setLoadingEvidence] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [orderError, setOrderError] = useState(false);
  const [evidenceError, setEvidenceError] = useState(false);

  const loadOrderDetails = useCallback(async () => {
    if (Number.isNaN(orderId)) {
      setNotFound(true);
      setLoadingOrder(false);
      setLoadingEvidence(false);
      return;
    }

    setLoadingOrder(true);
    setLoadingEvidence(true);
    setNotFound(false);
    setOrderError(false);
    setEvidenceError(false);

    const [orderResult, evidenceResult] = await Promise.allSettled([
      apiClient.getOrder(businessId, orderId),
      apiClient.getOrderEvidence(businessId, orderId),
    ]);

    if (orderResult.status === "fulfilled") {
      setOrder(orderResult.value);
      setLoadingOrder(false);
    } else {
      setLoadingOrder(false);
      const reason = orderResult.reason;
      if (reason instanceof ApiError && reason.status === 404) {
        setNotFound(true);
      } else {
        setOrderError(true);
      }
      setLoadingEvidence(false);
      return;
    }

    if (evidenceResult.status === "fulfilled") {
      setEvidence(evidenceResult.value);
    } else {
      setEvidenceError(true);
      setEvidence([]);
    }
    setLoadingEvidence(false);
  }, [businessId, orderId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadOrderDetails();
  }, [loadOrderDetails]);

  if (notFound || Number.isNaN(orderId)) {
    return (
      <div className="flex flex-col gap-stack-lg w-full">
        <PageHeader title="Order Details" showBack />
        <EmptyState message="Order not found." icon="shopping_bag" />
      </div>
    );
  }

  if (orderError) {
    return (
      <div className="flex flex-col gap-stack-lg w-full">
        <PageHeader title="Order Details" showBack />
        <ErrorState
          title="Could not load order details."
          message="There was a problem fetching this order. Please try again."
          onRetry={loadOrderDetails}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-stack-lg w-full">
      <PageHeader title="Order Details" showBack />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-stack-lg">
        <section className="lg:col-span-5 flex flex-col gap-stack-sm">
          <h2 className="font-label-caps text-label-caps text-ci-secondary uppercase tracking-widest pl-1">
            ChatInsights Identified
          </h2>
          {loadingOrder || !order ? (
            <OrderDetailsCardSkeleton />
          ) : (
            <OrderDetailsCard order={order} />
          )}
        </section>

        <section className="lg:col-span-7 flex flex-col gap-stack-sm">
          <h2 className="font-label-caps text-label-caps text-ci-secondary uppercase tracking-widest pl-1">
            Supporting WhatsApp Messages
          </h2>
          <EvidenceMessageList
            messages={evidence}
            error={evidenceError}
            loading={loadingEvidence}
          />
        </section>
      </div>
    </div>
  );
}
