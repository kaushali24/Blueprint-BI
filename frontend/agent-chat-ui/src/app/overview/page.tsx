"use client";

import { useEffect, useState, useCallback } from "react";
import PageHeader from "@/components/layout/PageHeader";
import { useBusinessId } from "@/providers/BusinessProvider";
import { apiClient } from "@/lib/api/client";
import { BusinessAnalyticsReportDTO } from "@/lib/api/types";
import ErrorState from "@/components/shared/ErrorState";
import EmptyState from "@/components/shared/EmptyState";
import KnownRevenueCard from "@/components/overview/KnownRevenueCard";
import MetricCard from "@/components/overview/MetricCard";
import TopProductsList from "@/components/overview/TopProductsList";
import AssistantCTACard from "@/components/overview/AssistantCTACard";
import RecentOrdersList from "@/components/overview/RecentOrdersList";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouter } from "next/navigation";
import Link from "next/link";

function OverviewSkeleton() {
  return (
    <div className="flex flex-col gap-stack-gap-lg w-full">
      <section className="flex flex-col items-center justify-center py-stack-gap-md text-center">
        <Skeleton className="h-4 w-32 mb-2" />
        <Skeleton className="h-10 w-48" />
      </section>
      <section className="grid grid-cols-2 md:grid-cols-4 gap-stack-gap-md">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-lg p-card-padding flex flex-col justify-between min-h-[100px]">
            <div className="flex items-center justify-between w-full">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-6 w-6 rounded-full" />
            </div>
            <Skeleton className="h-8 w-12 mt-2" />
          </div>
        ))}
      </section>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-stack-gap-lg w-full">
        <section className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col gap-stack-gap-md">
          <Skeleton className="h-6 w-32" />
          <ul className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <li key={i} className="flex items-center justify-between py-2 border-b border-ci-surface-variant last:border-0">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-8" />
              </li>
            ))}
          </ul>
        </section>
        <section className="bg-ci-surface-container-low border border-ci-outline-variant rounded-xl p-card-padding flex flex-col justify-center gap-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-12 w-48 rounded-full" />
        </section>
      </div>
      <section className="flex flex-col gap-stack-gap-md w-full">
        <Skeleton className="h-6 w-32" />
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-lg p-card-padding h-20 w-full">
              <Skeleton className="w-full h-full" />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default function OverviewPage() {
  const businessId = useBusinessId();
  const [data, setData] = useState<BusinessAnalyticsReportDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const router = useRouter();

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const analytics = await apiClient.getAnalytics(businessId);
      setData(analytics);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData();
  }, [loadData]);

  return (
    <div className="flex flex-col gap-6 w-full h-full">
      <PageHeader title="Business Overview" />

      {loading ? (
        <OverviewSkeleton />
      ) : error ? (
        <ErrorState
          title="Could not load your business overview."
          message="There was a problem fetching your data. Please try again."
          onRetry={loadData}
        />
      ) : data ? (
        // Empty state check
        data.order_metrics.total_count === 0 &&
        data.customer_metrics.total_known_customers === 0 &&
        data.inquiry_metrics.total_count === 0 ? (
          <EmptyState
            title="No business insights yet."
            message="Import your WhatsApp conversations to start building your business overview."
            action={{
              label: "Import WhatsApp Conversations",
              onClick: () => router.push("/imports")
            }}
            icon="analytics"
          />
        ) : (
          <div className="flex flex-col gap-stack-gap-lg w-full">
            <KnownRevenueCard
              knownTotalRevenue={data.order_metrics.known_total_revenue}
              ordersWithUnknownRevenueCount={data.order_metrics.orders_with_unknown_revenue_count}
            />

            <section className="grid grid-cols-2 md:grid-cols-4 gap-stack-gap-md">
              <Link href="/orders?status=confirmed" className="block outline-none rounded-lg focus-visible:ring-2 focus-visible:ring-ci-primary h-full">
                <MetricCard
                  title="Confirmed Orders"
                  value={data.order_metrics.status_counts.confirmed ?? 0}
                  icon="check_circle"
                />
              </Link>
              <Link href="/orders?status=pending" className="block outline-none rounded-lg focus-visible:ring-2 focus-visible:ring-ci-primary h-full">
                <MetricCard
                  title="Pending Orders"
                  value={data.order_metrics.status_counts.pending ?? 0}
                  icon="pending_actions"
                />
              </Link>
              <Link href="/customers" className="block outline-none rounded-lg focus-visible:ring-2 focus-visible:ring-ci-primary h-full">
                <MetricCard
                  title="Customers"
                  value={data.customer_metrics.total_known_customers ?? 0}
                  icon="group"
                />
              </Link>
              <Link href="/inquiries?status=open" className="block outline-none rounded-lg focus-visible:ring-2 focus-visible:ring-ci-primary h-full">
                <MetricCard
                  title="Open Inquiries"
                  value={data.inquiry_metrics.status_counts.open ?? 0}
                  icon="forum"
                />
              </Link>
            </section>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-stack-gap-lg w-full">
              <TopProductsList products={data.product_metrics.top_products || []} />
              <AssistantCTACard />
            </div>

            <RecentOrdersList orders={data.order_metrics.recent_orders || []} />
          </div>
        )
      ) : null}
    </div>
  );
}
