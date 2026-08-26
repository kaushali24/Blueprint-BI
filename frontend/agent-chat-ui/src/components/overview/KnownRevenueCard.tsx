import AmountDisplay from "@/components/shared/AmountDisplay";
import { Icons } from "@/lib/icons";

interface KnownRevenueCardProps {
  knownTotalRevenue: string;
  ordersWithUnknownRevenueCount: number;
}

export default function KnownRevenueCard({
  knownTotalRevenue,
  ordersWithUnknownRevenueCount,
}: KnownRevenueCardProps) {
  return (
    <section className="flex flex-col items-center justify-center pt-2 pb-6 text-center gap-1">
      <h2 className="label-caps text-ci-secondary uppercase tracking-wider">Known Revenue</h2>
      <AmountDisplay amount={knownTotalRevenue} variant="hero" />
      <span className="body-sm text-ci-secondary mt-1">From confirmed orders with known amounts</span>
      {ordersWithUnknownRevenueCount > 0 && (
        <div className="flex items-start justify-center gap-1.5 mt-2 text-ci-secondary metadata max-w-sm md:max-w-md text-center px-2">
          <Icons.info className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
          <span className="break-words text-left sm:text-center">{ordersWithUnknownRevenueCount} confirmed order{ordersWithUnknownRevenueCount !== 1 ? 's' : ''} have amounts unavailable.</span>
        </div>
      )}
    </section>
  );
}
