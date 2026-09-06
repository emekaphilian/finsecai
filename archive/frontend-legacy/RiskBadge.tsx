export function RiskBadge({ score }: { score: number }) {
  const tier = score > 0.7 ? "high" : score > 0.4 ? "medium" : "low";
  const cls = { high: "badge-high", medium: "badge-medium", low: "badge-low" }[tier];
  return <span className={`badge ${cls}`}>{tier} · {score.toFixed(2)}</span>;
}
