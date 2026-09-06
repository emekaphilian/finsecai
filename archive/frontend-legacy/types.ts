export interface Incident {
  id: string;
  user_id: string;
  amount: number;
  transaction_type: string;
  device_id: string;
  risk_score: number;
  anomaly_score: number;
  created_at: string;
  confidence: number | null;
  evidence_coverage: number | null;
  explanation: string | null;
  limitations: string | null;
  governance_flags: string | null;
  mitre_techniques: string | null;
  nist_controls: string | null;
}

export interface AnalyticsSummary {
  total_incidents: number;
  analyzed_count: number;
  avg_risk: number;
  avg_confidence: number;
  high_risk_count: number;
  governance_flags_count: number;
}

export interface PrecisionRecall {
  precision: number;
  recall: number;
  f1: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  true_negatives: number;
}

export interface DriftResult {
  drift_score: number;
  mean_shift: number;
  status: string;
}
