interface KpiCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
}

export function KpiCard({ label, value, subtitle }: KpiCardProps) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-text-secondary mb-2">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
      {subtitle ? <p className="text-xs text-text-secondary mt-1">{subtitle}</p> : null}
    </div>
  );
}
