"use client";

import { Icons } from "@/lib/icons";
import { useRouter } from "next/navigation";

interface PageHeaderProps {
  title: string;
  showBack?: boolean;
}

export default function PageHeader({ title, showBack = false }: PageHeaderProps) {
  const router = useRouter();

  return (
    <header className="sticky top-0 z-20 flex items-center gap-4 pt-4 md:pt-6 lg:pt-8 pb-4 mb-4 bg-ci-background -mx-4 md:-mx-6 lg:-mx-8 px-4 md:px-6 lg:px-8 border-b border-ci-outline-variant/10 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
      {showBack && (
        <button
          type="button"
          onClick={() => router.back()}
          className="p-2 -ml-2 rounded-full hover:bg-ci-surface-container-high transition-colors text-ci-on-surface outline-none focus-visible:ring-2 focus-visible:ring-ci-primary"
          aria-label="Go back"
        >
          <Icons.arrow_back className="w-6 h-6" />
        </button>
      )}
      <h1 className="headline-md text-ci-on-surface">{title}</h1>
    </header>
  );
}
