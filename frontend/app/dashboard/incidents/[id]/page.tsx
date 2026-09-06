"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch, downloadReport } from "@/lib/api";
import { Incident } from "@/lib/types";
import { RiskBadge } from "@/components/RiskBadge";

interface MappingExplanation {
  tier?: string;
  rationale: string | string[];
  mitre: { id: string; name: string }[];
  nist: { id: string; name: string }[];
}

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [mapping, setMapping] = useState<MappingExplanation | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  function load() {
    apiFetch<Incident>(`/incidents/${id}`).then(setIncident).catch(() => {});
  }

  useEffect(load, [id]);

  useEffect(() => {
    apiFetch<{ evidence: typeof evidence }>(`/incidents/${id}/evidence`)
      .then((r) => setEvidence(r.evidence))
      .catch(() => {});
    apiFetch<MappingExplanation>(`/incidents/${id}/mapping-explanation`)
      .then(setMapping)
      .catch(() => {});
  }, [id]);

  async function analyze() {
    setAnalyzing(true);
    try {
      const updated = await apiFetch<Incident>(`/incidents/${id}/analyze`, { method: "POST" });
      setIncident(updated);
      // Refresh evidence and mapping after analysis
      apiFetch<{ evidence: typeof evidence }>(`/incidents/${id}/evidence`)
        .then((r) => setEvidence(r.evidence))
        .catch(() => {});
      apiFetch<MappingExplanation>(`/incidents/${id}/mapping-explanation`)
        .then(setMapping)
        .catch(() => {});
    } finally {
      setAnalyzing(false);
    }
  }

  async function feedback(label: "false_positive" | "true_positive") {
    await apiFetch(`/incidents/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ label }),
    });
    load();
  }

  if (!incident) return <p className="text-text-secondary">Loading…</p>;

  const validation = incident.analysis_json?.validation;
  const mitreMappings = (incident.analysis_json?.mitre || []).filter(
    (mapping) => mapping.status === "evidence_backed" && Boolean(mapping.supporting_evidence?.length)
  );
  const nistMappings = (incident.analysis_json?.nist || []).filter(
    (mapping) => mapping.status === "evidence_backed" && Boolean(mapping.supporting_evidence?.length)
  );
  const confidencePercent = incident.confidence != null ? `${(incident.confidence * 100).toFixed(0)}%` : "n/a";
  const coveragePercent = incident.evidence_coverage != null ? `${Math.round(incident.evidence_coverage * 100)}%` : "n/a";
  const statusTone = incident.analysis_json?.intelligence_status?.toLowerCase() === "validated"
    ? "border-success/40 bg-success/10 text-success"
    : incident.analysis_json?.intelligence_status?.toLowerCase() === "failed"
      ? "border-danger/40 bg-danger/10 text-danger"
      : "border-gold/40 bg-gold/10 text-gold";

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">{incident.id}</h1>
          <p className="text-text-secondary text-sm">{incident.user_id}</p>
        </div>
        <RiskBadge score={incident.risk_score} />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card">
          <p className="text-xs text-text-secondary">Amount</p>
          <p className="text-lg font-medium">${incident.amount.toLocaleString()}</p>
        </div>
        <div className="card">
          <p className="text-xs text-text-secondary">Anomaly score</p>
          <p className="text-lg font-medium">{incident.anomaly_score.toFixed(3)}</p>
        </div>
        <div className="card">
          <p className="text-xs text-text-secondary">Confidence</p>
          <p className="text-lg font-medium">{incident.confidence?.toFixed(2) ?? "—"}</p>
        </div>
      </div>

      <div className="card mb-6">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium">Intelligence analysis</p>
          <button onClick={analyze} disabled={analyzing} className="btn-primary text-xs">
            {analyzing ? "Analyzing…" : incident.explanation ? "Re-analyze" : "Run analysis"}
          </button>
        </div>
        <p className="text-sm text-text-secondary mb-2">
          {incident.explanation || "No analysis run yet."}
        </p>
        {incident.limitations && (
          <p className="text-xs text-text-secondary italic">{incident.limitations}</p>
        )}
      </div>

      <div className="card mb-6">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium">Investigation metadata</p>
          <div className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${statusTone}`}>
            {incident.analysis_json?.intelligence_status || "Pending"}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <div className="rounded-lg border border-border/60 bg-background/40 p-3">
            <p className="text-[11px] uppercase tracking-wide text-text-secondary mb-1">Evidence confidence</p>
            <p className="text-lg font-semibold">{confidencePercent}</p>
            <p className="text-xs text-text-secondary">Coverage {coveragePercent}</p>
          </div>
          <div className="rounded-lg border border-border/60 bg-background/40 p-3">
            <p className="text-[11px] uppercase tracking-wide text-text-secondary mb-1">Validation</p>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-success/30 bg-success/10 px-2 py-1 text-xs text-success">
                Schema {validation?.schema_valid ? "✓" : "•"}
              </span>
              <span className="rounded-full border border-success/30 bg-success/10 px-2 py-1 text-xs text-success">
                Grounded {validation?.evidence_grounded ? "✓" : "•"}
              </span>
              <span className="rounded-full border border-success/30 bg-success/10 px-2 py-1 text-xs text-success">
                Tenant {validation?.tenant_scope_valid ? "✓" : "•"}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-xs text-text-secondary uppercase mb-1">Model provenance</p>
            <p className="font-medium">
              {incident.risk_score_source === "model" && incident.model_version
                ? `FinSecAI model • ${incident.model_version}`
                : incident.risk_score_source === "uploaded"
                  ? "Uploaded dataset"
                  : "Not recorded"}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-secondary uppercase mb-1">LLM provider</p>
            <p className="font-medium">{incident.analysis_json?.llm_provider || incident.analysis_json?.llm_provider_error || incident.analysis_json?.validation?.status || "Unavailable"}</p>
          </div>
          <div>
            <p className="text-xs text-text-secondary uppercase mb-1">Retrieval method</p>
            <p className="font-medium">{incident.analysis_json?.retrieval_method || incident.analysis_json?.validation?.status || "Unavailable"}</p>
          </div>
          <div>
            <p className="text-xs text-text-secondary uppercase mb-1">Embedding model</p>
            <p className="font-medium">{incident.analysis_json?.embedding_model || evidence[0]?.metadata?.embedding_model || "Unavailable"}</p>
          </div>
        </div>
      </div>

      <div className="card mb-6">
        <p className="text-sm font-medium mb-2">Framework mapping</p>
        {mapping && <p className="text-xs text-text-secondary mb-3">{Array.isArray(mapping.rationale) ? mapping.rationale.join(" ") : mapping.rationale}</p>}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-text-secondary uppercase mb-1">MITRE ATT&amp;CK</p>
            {mitreMappings.length === 0 && <p className="text-sm text-text-secondary">No evidence-backed mappings are available.</p>}
            {mitreMappings.map((m: any) => {
              const id = m.id || m;
              const name = m.name || m.id || "";
              const badge = m.status === "evidence_backed" ? "Evidence-backed" : "Candidate";
              const tone = badge === "Evidence-backed" ? "text-success" : "text-gold";
              return (
                <div key={id} className="mb-2">
                  <p className="text-sm">
                    <span className="text-gold font-mono">{id}</span> — {name}
                  </p>
                  <div className="mt-1">
                    <span className={`rounded-full border px-2 py-1 text-xs ${tone}`}>{badge}</span>
                  </div>
                </div>
              );
            })}
          </div>
          <div>
            <p className="text-xs text-text-secondary uppercase mb-1">NIST controls</p>
            {nistMappings.length === 0 && <p className="text-sm text-text-secondary">No evidence-backed mappings are available.</p>}
            {nistMappings.map((c: any) => {
              const id = c.id || c;
              const name = c.name || c.id || "";
              const badge = c.status === "evidence_backed" ? "Evidence-backed" : "Candidate";
              const tone = badge === "Evidence-backed" ? "text-success" : "text-gold";
              return (
                <div key={id} className="mb-2">
                  <p className="text-sm">
                    <span className="text-gold font-mono">{id}</span> — {name}
                  </p>
                  <div className="mt-1">
                    <span className={`rounded-full border px-2 py-1 text-xs ${tone}`}>{badge}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="card mb-6">
        <p className="text-sm font-medium mb-2">Evidence used ({evidence.length})</p>
        {evidence.length === 0 && (
          <p className="text-sm text-text-secondary">
            No evidence chunks are tagged for this risk tier yet — this reflects the evidence store's current contents, not an analysis failure. Confidence and the explanation above are generated independently of evidence count.
          </p>
        )}
        {evidence.map((e, i) => (
          <div key={i} className="border-t border-border/50 pt-2 mt-2 first:border-0 first:pt-0 first:mt-0">
            <div className="flex items-center justify-between">
              <p className="text-xs text-gold font-mono">{e.framework_id}</p>
              <p className="text-xs text-text-secondary">Source: {e.source || (e.metadata && e.metadata.source) || 'unknown'}</p>
            </div>
            <p className="text-sm text-text-secondary">{e.text}</p>
            <p className="text-xs text-text-secondary mt-1">Similarity: {e.similarity != null ? `${(e.similarity * 100).toFixed(1)}%` : 'n/a'} • Embedding: {e.metadata?.embedding_model || 'n/a'}</p>
          </div>
        ))}
      </div>

      {incident.governance_flags && (
        <div className="card mb-6 border-danger/40">
          <p className="text-sm font-medium mb-2 text-danger">Governance flags</p>
          <p className="text-sm text-text-secondary">{incident.governance_flags}</p>
        </div>
      )}

      <div className="flex gap-3">
        <button onClick={() => feedback("false_positive")} className="border border-border rounded-lg px-4 py-2 text-sm hover:border-success hover:text-success">
          Mark false positive
        </button>
        <button onClick={() => feedback("true_positive")} className="border border-border rounded-lg px-4 py-2 text-sm hover:border-danger hover:text-danger">
          Mark true positive
        </button>
        {incident.analysis_json ? (
          <button onClick={() => downloadReport(incident.id)} className="btn-primary text-sm ml-auto">
            Download PDF report
          </button>
        ) : (
          <button onClick={analyze} disabled={analyzing} className="btn-primary text-sm ml-auto">
            {analyzing ? "Analyzing…" : "Run analysis to generate report"}
          </button>
        )}
      </div>
    </div>
  );
}
