import { Icons, IconName } from "@/lib/icons";

interface MetricCardProps {
  title: string;
  value: number;
  icon: IconName;
}

export default function MetricCard({ title, value, icon }: MetricCardProps) {
  const IconComponent = Icons[icon];
  return (
    <div className="bg-ci-surface-container-lowest border border-ci-outline-variant rounded-xl p-card-padding flex flex-col justify-between min-h-[100px] min-w-0">
      <div className="flex flex-col gap-1 w-full min-w-0">
        <div className="flex items-center gap-2 mb-2 min-w-0">
          <IconComponent className="text-ci-primary w-5 h-5 shrink-0" />
          <span className="label-caps text-ci-secondary uppercase break-words leading-tight min-w-0">{title}</span>
        </div>
        <div className="metric-lg-mobile md:metric-lg font-bold text-ci-on-surface">{value}</div>
      </div>
    </div>
  );
}
