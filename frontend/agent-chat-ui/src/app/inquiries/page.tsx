"use client";

import { useCallback, useEffect, useState } from "react";
import PageHeader from "@/components/layout/PageHeader";
import InquiryCard, { InquiryCardSkeleton } from "@/components/inquiries/InquiryCard";
import EmptyState from "@/components/shared/EmptyState";
import ErrorState from "@/components/shared/ErrorState";
import { useBusinessId } from "@/providers/BusinessProvider";
import { apiClient } from "@/lib/api/client";
import { InquirySummaryDTO } from "@/lib/api/types";

export default function InquiriesPage() {
  const businessId = useBusinessId();
  const [inquiries, setInquiries] = useState<InquirySummaryDTO[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const loadInquiries = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await apiClient.getInquiries(businessId);
      setInquiries(data);
    } catch {
      setError(true);
      setInquiries(null);
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => {
    loadInquiries();
  }, [loadInquiries]);

  return (
    <div className="flex flex-col gap-stack-lg w-full">
      <PageHeader title="Inquiries" />
      <p className="font-metadata text-metadata text-ci-secondary -mt-2">
        View customer questions and requests.
      </p>

      {loading ? (
        <section
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-stack-md w-full"
          aria-busy="true"
          aria-label="Loading inquiries"
        >
          {Array.from({ length: 3 }).map((_, i) => (
            <InquiryCardSkeleton key={i} />
          ))}
        </section>
      ) : error ? (
        <ErrorState
          title="Could not load inquiries."
          message="There was a problem fetching your inquiries. Please try again."
          onRetry={loadInquiries}
        />
      ) : inquiries && inquiries.length === 0 ? (
        <EmptyState
          title="No inquiries identified yet."
          message="Customer questions identified from your WhatsApp conversations will appear here."
          icon="forum"
        />
      ) : (
        <section
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-stack-md w-full"
          aria-label="Customer inquiries"
        >
          {inquiries?.map((inquiry) => (
            <InquiryCard key={inquiry.id} inquiry={inquiry} />
          ))}
        </section>
      )}
    </div>
  );
}
