import { EvidenceMessageDTO } from "@/lib/api/types";
import { Icons } from "@/lib/icons";
import { formatOrderDetailDate } from "@/lib/formatOrderDate";
import { parseISO } from "date-fns";

interface EvidenceMessageListProps {
  messages: EvidenceMessageDTO[];
  error?: boolean;
  loading?: boolean;
}

function formatEvidenceTime(sentAt: string | null): string | null {
  if (!sentAt) return null;
  try {
    const date = parseISO(sentAt);
    if (Number.isNaN(date.getTime())) return null;
    return formatOrderDetailDate(sentAt);
  } catch {
    return null;
  }
}

function EvidenceBubble({ message }: { message: EvidenceMessageDTO }) {
  const isBusiness = message.sender_type === "business";
  const isCustomer = message.sender_type === "customer";
  const alignEnd = isBusiness;
  const senderLabel = message.sender_name ?? "Unknown sender";
  const bubbleText = message.message_content ?? message.evidence_text;
  const timestamp = formatEvidenceTime(message.sent_at);

  const bubbleClasses = isBusiness
    ? "bg-ci-primary text-ci-on-primary rounded-2xl rounded-tr-sm shadow-sm"
    : isCustomer
      ? "bg-ci-surface-container-lowest text-ci-on-surface rounded-2xl rounded-tl-sm border-l-2 border-ci-primary ai-bubble-shadow"
      : "bg-ci-surface-container-lowest text-ci-on-surface rounded-2xl rounded-tl-sm border border-ci-outline-variant/50 ai-bubble-shadow";

  return (
    <article
      className={`flex flex-col max-w-[85%] ${alignEnd ? "items-end self-end" : "items-start"}`}
    >
      <span
        className={`font-metadata text-metadata text-ci-secondary mb-1 ${alignEnd ? "mr-2" : "ml-2"}`}
      >
        {senderLabel}
        {timestamp && (
          <span className="sr-only">{`, sent ${timestamp}`}</span>
        )}
      </span>
      <p className={`px-4 py-3 font-body-md text-body-md break-words ${bubbleClasses}`}>
        {bubbleText}
      </p>
    </article>
  );
}

export default function EvidenceMessageList({
  messages,
  error = false,
  loading = false,
}: EvidenceMessageListProps) {
  if (loading) {
    return (
      <div
        className="bg-ci-surface-container rounded-xl p-card-padding flex flex-col gap-4 animate-pulse"
        aria-busy="true"
        aria-label="Loading supporting messages"
      >
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className={`flex flex-col gap-2 max-w-[85%] ${i % 2 === 1 ? "self-end items-end" : ""}`}>
            <div className="h-3 w-16 bg-ci-surface-container-high rounded" />
            <div className="h-16 w-full bg-ci-surface-container-high rounded-2xl" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="bg-ci-surface-container rounded-xl p-card-padding border border-ci-outline-variant/50"
        role="status"
      >
        <p className="font-metadata text-metadata text-ci-secondary">
          Supporting messages could not be loaded.
        </p>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div
        className="bg-ci-surface-container rounded-xl p-card-padding border border-ci-outline-variant/50"
        role="status"
      >
        <p className="font-metadata text-metadata text-ci-secondary">
          No supporting messages available for this order.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-ci-surface-container-low border border-ci-outline-variant/30 rounded-xl p-card-padding flex flex-col gap-stack-md h-full relative overflow-hidden overflow-x-hidden min-w-0">
      <div
        className="absolute top-0 right-0 w-32 h-32 bg-ci-primary/5 rounded-bl-full pointer-events-none"
        aria-hidden="true"
      />
      <div className="flex-1 flex flex-col gap-4 z-10">
        {messages.map((message, index) => (
          <EvidenceBubble key={`${message.sent_at ?? "msg"}-${index}`} message={message} />
        ))}
      </div>
      <div className="mt-4 flex flex-col gap-4 z-10 border-t border-ci-outline-variant/30 pt-4">
        <p className="font-metadata text-metadata text-ci-secondary italic flex items-start gap-2">
          <Icons.info className="w-4 h-4 text-ci-primary mt-0.5 shrink-0" aria-hidden="true" />
          These messages support the information ChatInsights identified above.
        </p>
      </div>
    </div>
  );
}
