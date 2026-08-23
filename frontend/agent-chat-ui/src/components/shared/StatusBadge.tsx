"use client";

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  let styles = "";
  const label = status.charAt(0).toUpperCase() + status.slice(1);

  if (status === "confirmed" || status === "resolved") {
    styles = "bg-ci-primary-fixed text-ci-on-primary-fixed-variant";
  } else if (status === "pending" || status === "open") {
    styles = "bg-ci-tertiary-fixed text-ci-on-tertiary-fixed-variant";
  } else if (status === "cancelled") {
    styles = "bg-ci-error-container text-ci-on-error-container";
  } else {
    styles = "bg-ci-secondary-container text-ci-on-surface-variant";
  }

  return (
    <span
      role="status"
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase ${styles}`}
    >
      {label}
    </span>
  );
}
