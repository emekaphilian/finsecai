interface RiskBadgeProps {
  score: number;
}

export function RiskBadge({ score }: RiskBadgeProps) {
  const tier = score >= 0.8 ? "high" : score >= 0.5 ? "medium" : "low";
  const classes = {
    high: "badge-high",
    medium: "badge-medium",
    low: "badge-low",
  }[tier];

  return <span className={`badge ${classes}`}>risk {score.toFixed(2)}</span>;
}
