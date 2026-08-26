"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import PageHeader from "@/components/layout/PageHeader";
import CustomerCard, { CustomerCardSkeleton } from "@/components/customers/CustomerCard";
import EmptyState from "@/components/shared/EmptyState";
import ErrorState from "@/components/shared/ErrorState";
import { useBusinessId } from "@/providers/BusinessProvider";
import { apiClient } from "@/lib/api/client";
import { CustomerSummaryDTO } from "@/lib/api/types";

export default function CustomersPage() {
  const businessId = useBusinessId();
  const router = useRouter();

  const [customers, setCustomers] = useState<CustomerSummaryDTO[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const loadCustomers = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await apiClient.getCustomers(businessId);
      setCustomers(data);
    } catch {
      setError(true);
      setCustomers(null);
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadCustomers();
  }, [loadCustomers]);

  return (
    <div className="flex flex-col gap-stack-lg w-full">
      <div className="flex flex-col">
        <PageHeader title="Customers" showBack={true} />
        <div className="flex items-center justify-between gap-2 -mt-2">
          <p className="font-metadata text-metadata text-ci-secondary">
            Customers identified from your WhatsApp conversations.
          </p>
          {customers && customers.length > 0 && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-ci-surface-container text-ci-on-surface-variant border border-ci-outline-variant/30 shrink-0">
              {customers.length} {customers.length === 1 ? "Customer" : "Customers"}
            </span>
          )}
        </div>
      </div>

      {loading ? (
        <section
          className="grid grid-cols-1 md:grid-cols-2 gap-stack-md w-full"
          aria-busy="true"
          aria-label="Loading customers"
        >
          {Array.from({ length: 4 }).map((_, i) => (
            <CustomerCardSkeleton key={i} />
          ))}
        </section>
      ) : error ? (
        <ErrorState
          title="Could not load customers."
          message="There was a problem fetching your customers. Please try again."
          onRetry={loadCustomers}
        />
      ) : customers && customers.length === 0 ? (
        <EmptyState
          title="No customers identified yet."
          message="Import a WhatsApp conversation to start building your customer list."
          action={{
            label: "Go to Imports",
            onClick: () => router.push("/imports"),
          }}
          icon="group"
        />
      ) : (
        <section
          className="grid grid-cols-1 md:grid-cols-2 gap-stack-md w-full"
          aria-label="Customers list"
        >
          {customers?.map((customer) => (
            <CustomerCard key={customer.id} customer={customer} />
          ))}
        </section>
      )}
    </div>
  );
}
