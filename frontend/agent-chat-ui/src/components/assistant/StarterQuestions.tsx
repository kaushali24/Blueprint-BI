interface StarterQuestionsProps {
  onSelect: (question: string) => void;
  disabled?: boolean;
}

const STARTER_QUESTIONS = [
  "How many confirmed orders do I have?",
  "What is my known revenue?",
  "What are my top products?",
  "How many inquiries do I have?",
  "mage confirmed orders keeyak thiyenawada?",
] as const;

export default function StarterQuestions({ onSelect, disabled = false }: StarterQuestionsProps) {
  return (
    <div className="flex flex-col gap-3 mt-4">
      <p className="font-label-caps text-label-caps text-ci-secondary mb-2 px-2 uppercase tracking-widest">
        Suggested Queries
      </p>
      <div className="flex flex-wrap gap-3">
        {STARTER_QUESTIONS.map((question) => (
          <button
            key={question}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(question)}
            className="px-4 py-2 bg-ci-surface-container-lowest border border-ci-outline-variant hover:border-ci-primary hover:text-ci-primary transition-colors rounded-full font-metadata text-metadata text-ci-on-surface-variant text-left shadow-sm active:scale-95 duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-ci-outline-variant disabled:hover:text-ci-on-surface-variant outline-none focus-visible:ring-2 focus-visible:ring-ci-primary break-words max-w-full"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
