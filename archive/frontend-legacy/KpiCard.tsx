export function KpiCard({
  label,
  value,
  subtitle,
}: {
  label: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-text-secondary mb-2">{label}</p>
      <p className="text-2xl font-semibold text-gold">{value}</p>
      {subtitle && <p className="text-xs text-text-secondary mt-1">{subtitle}</p>}
    </div>
  );
}
