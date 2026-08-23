"use client";

interface AmountDisplayProps {
  amount: string | null;
  variant?: "hero" | "inline";
}

export default function AmountDisplay({ amount, variant = "inline" }: AmountDisplayProps) {
  if (amount === null) {
    return (
      <span className="metadata text-ci-secondary italic" aria-label="Amount unavailable">
        Amount unavailable
      </span>
    );
  }

  // Format as Rs. X,XXX
  const numericAmount = Number(amount);
  const formatted = new Intl.NumberFormat('en-IN', {
    style: 'decimal',
    maximumFractionDigits: 0
  }).format(numericAmount);

  if (variant === "hero") {
    return <span className="metric-lg-mobile md:metric-lg text-ci-primary">Rs. {formatted}</span>;
  }

  return <span className="body-md text-ci-primary font-bold">Rs. {formatted}</span>;
}
