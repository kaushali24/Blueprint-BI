import { Icons } from "@/lib/icons";
import Link from "next/link";

export default function AssistantCTACard() {
  return (
    <section className="bg-ci-surface-container-low border border-ci-outline-variant rounded-xl p-card-padding flex flex-col justify-center gap-4 text-center md:text-left relative overflow-hidden h-full">
      <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10 pointer-events-none">
        <Icons.smart_toy className="w-32 h-32" />
      </div>
      <div className="z-10 flex flex-col gap-3">
        <h3 className="headline-md text-ci-on-surface">Ask ChatInsights</h3>
        <p className="metadata text-ci-secondary">Have a question about your business? Ask about your orders, products, customers, revenue or inquiries.</p>
      </div>
      <Link href="/assistant" className="z-10 mt-4 self-center md:self-start bg-ci-primary text-ci-on-primary rounded-full px-6 py-3 label-caps hover:bg-ci-primary-container transition-colors shadow-sm flex items-center gap-2 outline-none focus-visible:ring-2 focus-visible:ring-ci-primary focus-visible:ring-offset-2">
        <Icons.chat_bubble className="w-[18px] h-[18px]" />
        Ask ChatInsights
      </Link>
    </section>
  );
}
