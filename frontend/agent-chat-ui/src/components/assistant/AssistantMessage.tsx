import { Icons } from "@/lib/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type ChatMessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string;
}

interface AssistantMessageProps {
  message: ChatMessage;
}

export default function AssistantMessage({ message }: AssistantMessageProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end" role="listitem">
        <div
          className="bg-ci-primary text-ci-on-primary rounded-2xl rounded-tr-sm px-4 py-3 max-w-[85%] font-body-md text-body-md shadow-sm break-words"
          aria-label="Your message"
        >
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start" role="listitem">
      <div
        className="bg-ci-surface-container-lowest border-l-2 border-ci-primary rounded-r-xl rounded-bl-xl px-4 py-3 max-w-[90%] ai-bubble-shadow break-words"
        aria-label="ChatInsights response"
      >
        <div className="flex items-center gap-2 mb-2 text-ci-primary font-label-caps text-label-caps">
          <Icons.smart_toy className="w-4 h-4" aria-hidden="true" />
          ChatInsights
        </div>
        <div className="font-body-md text-body-md text-ci-on-surface whitespace-normal">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
              ul: ({ node, ...props }) => (
                <ul className="list-disc pl-5 mb-2 last:mb-0 space-y-1" {...props} />
              ),
              ol: ({ node, ...props }) => (
                <ol className="list-decimal pl-5 mb-2 last:mb-0 space-y-1" {...props} />
              ),
              li: ({ node, ...props }) => <li className="pl-1" {...props} />,
              strong: ({ node, ...props }) => (
                <strong className="font-semibold text-ci-on-surface" {...props} />
              ),
              em: ({ node, ...props }) => <em className="italic" {...props} />,
              code: ({ node, ...props }) => (
                <code
                  className="bg-ci-surface-container-high text-ci-on-surface px-1.5 py-0.5 rounded-md text-sm font-mono break-words"
                  {...props}
                />
              ),
              pre: ({ node, ...props }) => (
                <pre
                  className="bg-ci-surface-container-high p-3 rounded-md mb-2 last:mb-0 overflow-x-auto text-sm font-mono text-ci-on-surface"
                  {...props}
                />
              ),
              a: ({ node, ...props }) => (
                <a
                  className="text-ci-primary hover:underline underline-offset-2"
                  target="_blank"
                  rel="noopener noreferrer"
                  {...props}
                />
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export function AssistantTypingIndicator() {
  return (
    <div className="flex justify-start" role="status" aria-live="polite" aria-busy="true">
      <div className="bg-ci-surface-container-lowest border-l-2 border-ci-primary rounded-r-xl rounded-bl-xl px-4 py-3 max-w-[90%] ai-bubble-shadow">
        <div className="flex items-center gap-2 text-ci-secondary font-metadata text-metadata">
          <span className="flex gap-1" aria-hidden="true">
            <span className="w-2 h-2 rounded-full bg-ci-primary/40 animate-pulse" />
            <span className="w-2 h-2 rounded-full bg-ci-primary/60 animate-pulse [animation-delay:150ms]" />
            <span className="w-2 h-2 rounded-full bg-ci-primary/80 animate-pulse [animation-delay:300ms]" />
          </span>
          ChatInsights is thinking…
        </div>
      </div>
    </div>
  );
}

export function AssistantErrorMessage({
  onRetry,
}: {
  onRetry?: () => void;
}) {
  return (
    <div className="flex justify-start" role="alert" aria-live="assertive">
      <div className="bg-ci-error-container/20 border border-ci-error/20 rounded-xl px-4 py-3 max-w-[90%]">
        <p className="font-body-md text-body-md text-ci-on-error-container mb-2">
          ChatInsights is temporarily unavailable. Please try again.
        </p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="font-metadata text-metadata text-ci-primary font-semibold hover:underline outline-none focus-visible:ring-2 focus-visible:ring-ci-primary rounded-sm px-1"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
