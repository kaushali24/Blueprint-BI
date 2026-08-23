"use client";

import { Icons } from "@/lib/icons";

interface EmptyStateProps {
  title?: string;
  message: string;
  icon?: keyof typeof Icons;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export default function EmptyState({ title, message, icon = "info", action }: EmptyStateProps) {
  const IconComponent = Icons[icon] || Icons.info;

  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center bg-ci-surface rounded-xl border border-ci-outline-variant max-w-2xl mx-auto shadow-sm w-full">
      <div className="w-12 h-12 rounded-full bg-ci-surface-container flex items-center justify-center mb-4">
        <IconComponent className="w-6 h-6 text-ci-on-surface-variant" />
      </div>
      {title && <h3 className="headline-md text-ci-on-surface mb-2">{title}</h3>}
      <p className="body-md text-ci-on-surface-variant mb-4">{message}</p>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="px-4 py-2 bg-ci-primary text-ci-on-primary rounded-full font-semibold hover:bg-ci-primary/90 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ci-primary focus-visible:ring-offset-2"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
