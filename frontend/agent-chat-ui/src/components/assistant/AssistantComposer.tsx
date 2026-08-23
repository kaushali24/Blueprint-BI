import { Send } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface AssistantComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
}

export default function AssistantComposer({
  value,
  onChange,
  onSend,
  disabled = false,
}: AssistantComposerProps) {
  const canSend = value.trim().length > 0 && !disabled;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSend) onSend();
    }
  };

  return (
    <div className="w-full bg-gradient-to-t from-ci-background via-ci-background to-transparent pt-4 pb-2 md:pb-0">
      <div className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-[32px] p-2 flex items-end gap-2 shadow-sm focus-within:border-ci-primary focus-within:ring-2 focus-within:ring-ci-primary/20 transition-all">
        <label htmlFor="assistant-composer-input" className="sr-only">
          Ask ChatInsights a question
        </label>
        <Textarea
          id="assistant-composer-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask in English, සිංහල or Singlish..."
          disabled={disabled}
          rows={1}
          className="flex-1 min-h-[44px] max-h-32 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 px-4 py-3 font-body-md text-body-md text-ci-on-surface placeholder:text-ci-secondary rounded-[24px] leading-relaxed"
        />
        <Button
          type="button"
          onClick={onSend}
          disabled={!canSend}
          size="icon"
          aria-label="Send message"
          className="rounded-full bg-ci-primary hover:bg-ci-primary-container text-ci-on-primary shrink-0 mb-1 mr-1 h-11 w-11 disabled:opacity-50"
        >
          <Send className="w-5 h-5" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
