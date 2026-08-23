"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import PageHeader from "@/components/layout/PageHeader";
import AssistantMessage, {
  AssistantErrorMessage,
  AssistantTypingIndicator,
  ChatMessage,
} from "@/components/assistant/AssistantMessage";
import StarterQuestions from "@/components/assistant/StarterQuestions";
import AssistantComposer from "@/components/assistant/AssistantComposer";
import { Icons } from "@/lib/icons";
import { useBusinessId } from "@/providers/BusinessProvider";
import { apiClient } from "@/lib/api/client";

function WelcomeCard() {
  const capabilities = [
    "Known revenue",
    "Orders and their status",
    "Top products",
    "Customers and inquiries",
  ] as const;

  return (
    <div className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding shadow-sm relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 h-full bg-ci-primary" aria-hidden="true" />
      <div className="flex items-start gap-5">
        <div className="w-12 h-12 rounded-full bg-ci-surface-container-low flex items-center justify-center shrink-0 mt-1">
          <Icons.smart_toy className="w-6 h-6 text-ci-primary" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1 flex flex-col">
          <h2 className="font-headline-md text-headline-md text-ci-on-surface mb-1 break-words">
            What can I help you with today?
          </h2>
          <p className="font-body-md text-body-md text-ci-secondary mb-5">
            I can answer questions using your available business data. Try asking about:
          </p>
          <ul className="font-body-md text-body-md text-ci-secondary space-y-3">
            {capabilities.map((item) => (
              <li key={item} className="flex items-center gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-ci-primary block shrink-0" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default function AssistantThread() {
  const businessId = useBusinessId();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showError, setShowError] = useState(false);
  const [retryMessage, setRetryMessage] = useState<string | null>(null);

  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const isSendingRef = useRef(false);

  const scrollToBottom = useCallback(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending, showError, scrollToBottom]);

  const sendMessage = useCallback(
    async (text: string, options?: { isRetry?: boolean }) => {
      const trimmed = text.trim();
      if (!trimmed || isSendingRef.current) return;

      isSendingRef.current = true;
      setIsSending(true);
      setShowError(false);

      if (!options?.isRetry) {
        const userMessage: ChatMessage = {
          id: uuidv4(),
          role: "user",
          content: trimmed,
        };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
      }

      setRetryMessage(trimmed);

      try {
        const result = await apiClient.chat(businessId, trimmed);
        const assistantMessage: ChatMessage = {
          id: uuidv4(),
          role: "assistant",
          content: result.response,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setRetryMessage(null);
      } catch {
        setShowError(true);
      } finally {
        isSendingRef.current = false;
        setIsSending(false);
      }
    },
    [businessId],
  );

  const handleSend = useCallback(() => {
    sendMessage(input);
  }, [input, sendMessage]);

  const handleRetry = useCallback(() => {
    if (retryMessage) {
      sendMessage(retryMessage, { isRetry: true });
    }
  }, [retryMessage, sendMessage]);

  const showWelcome = messages.length === 0;
  const showStarters = messages.length === 0;

  return (
    <div className="flex flex-col min-h-[calc(100dvh-7rem)] md:min-h-[calc(100dvh-5rem)] w-full max-w-3xl mx-auto">
      <div className="shrink-0 pb-2">
        <PageHeader title="Ask ChatInsights" />
      </div>

      <div
        className="flex-1 overflow-y-auto pb-4 space-y-stack-md min-h-0"
        role="log"
        aria-label="Chat conversation"
        aria-live="polite"
      >
        {showWelcome && <WelcomeCard />}

        {messages.length > 0 && (
          <ul className="flex flex-col gap-stack-md list-none p-0 m-0" role="list">
            {messages.map((message) => (
              <li key={message.id} className="list-none">
                <AssistantMessage message={message} />
              </li>
            ))}
          </ul>
        )}

        {isSending && <AssistantTypingIndicator />}

        {showError && !isSending && (
          <AssistantErrorMessage onRetry={retryMessage ? handleRetry : undefined} />
        )}

        {showStarters && (
          <StarterQuestions onSelect={sendMessage} disabled={isSending} />
        )}

        <div ref={scrollAnchorRef} aria-hidden="true" className="h-1" />
      </div>

      <div className="sticky bottom-0 shrink-0 pb-20 md:pb-2 bg-ci-background z-10">
        <AssistantComposer
          value={input}
          onChange={setInput}
          onSend={handleSend}
          disabled={isSending}
        />
      </div>
    </div>
  );
}
