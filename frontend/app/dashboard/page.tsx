"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { apiFetch, getActiveTenantId, getSession } from "@/lib/api";
import { AnalyticsSummary, EnterpriseSummary, Incident } from "@/lib/types";
import { KpiCard } from "@/components/KpiCard";

function riskHistogram(incidents: Incident[]) {
  const buckets = Array.from({ length: 10 }, (_, i) => ({ bucket: `${i / 10}-${(i + 1) / 10}`, count: 0 }));
  for (const inc of incidents) {
    const idx = Math.min(9, Math.floor(inc.risk_score * 10));
    buckets[idx].count += 1;
  }
  return buckets;
}

function confidenceHistogram(incidents: Incident[]) {
  const analyzed = incidents.filter((i) => i.confidence !== null);
  const buckets = Array.from({ length: 10 }, (_, i) => ({ bucket: `${i / 10}-${(i + 1) / 10}`, count: 0 }));
  for (const inc of analyzed) {
    const idx = Math.min(9, Math.floor((inc.confidence ?? 0) * 10));
    buckets[idx].count += 1;
  }
  return buckets;
}

export default function OverviewPage() {
  const router = useRouter();
  const session = getSession();
  const sessionRole = session?.role;
  const sessionTenantId = session?.tenant_id;
  const isOwner = sessionRole === "owner";
  const activeTenantId = getActiveTenantId();
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [flagBreakdown, setFlagBreakdown] = useState<Record<string, number>>({});
  const [enterprise, setEnterprise] = useState<EnterpriseSummary | null>(null);
  const [requestedTenantId, setRequestedTenantId] = useState<string | null>(null);
  const [tenantName, setTenantName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const workspaceTenantId = isOwner ? requestedTenantId : activeTenantId || sessionTenantId;
  const isTenantWorkspace = Boolean(workspaceTenantId && (!isOwner || requestedTenantId));

  useEffect(() => {
    if (!session) {
      router.push("/login");
      return;
    }

    const queryTenantId = new URLSearchParams(window.location.search).get("tenant_id");
    if (queryTenantId !== requestedTenantId) {
      setRequestedTenantId(queryTenantId);
    }

    if (isOwner && !queryTenantId) {
      apiFetch<EnterpriseSummary>("/analytics/enterprise-summary")
        .then(setEnterprise)
        .catch(() => setEnterprise(null))
        .finally(() => setLoading(false));
      return;
    }

    const selectedTenantId = isOwner ? queryTenantId : workspaceTenantId;
    const query = selectedTenantId ? `?tenant_id=${encodeURIComponent(selectedTenantId)}` : "";
    Promise.all([
      apiFetch<AnalyticsSummary>(`/analytics/summary${query}`),
      apiFetch<Incident[]>(`/incidents?limit=200${selectedTenantId ? `&tenant_id=${encodeURIComponent(selectedTenantId)}` : ""}`),
      apiFetch<Record<string, number>>(`/analytics/flag-breakdown${query}`),
      selectedTenantId
        ? apiFetch<{ name: string }>(`/tenants/${selectedTenantId}`)
        : Promise.resolve(null),
    ])
      .then(([summaryData, incidentsData, flagData, tenantData]) => {
        setSummary(summaryData);
        setIncidents(incidentsData);
        setFlagBreakdown(flagData);
        setTenantName(tenantData?.name || null);
      })
      .catch(() => {
        setSummary(null);
        setIncidents([]);
      })
      .finally(() => setLoading(false));
  }, [isOwner, requestedTenantId, router, sessionTenantId, workspaceTenantId]);

  if (!session) {
    return null;
  }

  if (isOwner && !isTenantWorkspace) {
    return (
      <div>
        <p className="text-xs uppercase tracking-wide text-gold mb-2">FinSecAI platform</p>
        <h1 className="text-2xl font-semibold mb-1">Enterprise overview</h1>
        <p className="text-sm text-text-secondary mb-8">
          Platform-wide metrics across all stored tenant records. Customer counts include only explicitly provisioned legitimate customers; historical benchmark and diagnostic records remain separate.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <KpiCard label="Total tenants" value={loading ? "…" : enterprise?.total_tenants ?? "—"} />
          <KpiCard label="Active customer tenants" value={loading ? "…" : enterprise?.active_customer_tenants ?? "—"} />
          <KpiCard label="Demo tenants" value={loading ? "…" : enterprise?.demo_tenants ?? "—"} />
          <KpiCard label="Total incidents" value={loading ? "…" : enterprise?.total_incidents ?? "—"} />
          <KpiCard label="High-risk incidents" value={loading ? "…" : enterprise?.high_risk_incidents ?? "—"} />
          <KpiCard label="Reports generated" value={loading ? "…" : enterprise?.reports_generated ?? "—"} />
        </div>
        <div className="card mt-6">
          <p className="text-sm font-medium mb-1">Enterprise-wide scope</p>
          <p className="text-sm text-text-secondary">
            Select a tenant from Enterprise tenants to inspect its incidents. Tenant users continue to receive only their own workspace metrics.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-gold mb-2">Tenant workspace</p>
      <h1 className="text-2xl font-semibold mb-1">{tenantName || "Current tenant"}</h1>
      <p className="text-sm text-text-secondary mb-6">
        Every incident currently loaded for this tenant. Risk and confidence are model outputs; governance flags indicate policy-relevant conditions that need analyst attention — not automatic guilt.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Total incidents" value={loading ? "…" : summary?.total_incidents ?? "—"} />
        <KpiCard
          label="Avg risk score"
          value={loading ? "…" : summary ? summary.avg_risk.toFixed(2) : "—"}
          subtitle={summary ? `${summary.high_risk_count} high risk` : undefined}
        />
        <KpiCard
          label="Avg confidence"
          value={loading ? "…" : summary ? summary.avg_confidence.toFixed(2) : "—"}
          subtitle={summary ? `${summary.analyzed_count} analyzed` : undefined}
        />
        <KpiCard label="Governance flags" value={loading ? "…" : summary?.governance_flags_count ?? "—"} />
      </div>

      <div className="card">
        <p className="text-sm font-medium mb-1">Risk score distribution</p>
        <p className="text-xs text-text-secondary mb-4">
          How many loaded incidents fall into each risk band — a healthy pipeline usually skews toward the low end, with a visible tail of genuinely high-risk cases worth investigating first.
        </p>
        {loading ? (
          <p className="text-sm text-text-secondary">Loading incident distribution…</p>
        ) : incidents.length === 0 ? (
          <p className="text-sm text-text-secondary">No incidents are available yet. Upload a CSV to start populating the feed.</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={riskHistogram(incidents)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="bucket" tick={{ fill: "#CBD5E1", fontSize: 11 }} />
            <YAxis tick={{ fill: "#CBD5E1", fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid #334155" }} />
            <Bar dataKey="count" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="card mt-4">
        <p className="text-sm font-medium mb-1">Confidence distribution</p>
        <p className="text-xs text-text-secondary mb-4">
          How confident the intelligence pipeline is in its own explanation for each analyzed incident — low confidence means "read the raw scores yourself," not "this incident is low risk."
        </p>
        {loading ? (
          <p className="text-sm text-text-secondary">Loading confidence distribution…</p>
        ) : incidents.length === 0 ? (
          <p className="text-sm text-text-secondary">No incidents are available yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={confidenceHistogram(incidents)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="bucket" tick={{ fill: "#CBD5E1", fontSize: 11 }} />
              <YAxis tick={{ fill: "#CBD5E1", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid #334155" }} />
              <Bar dataKey="count" fill="#60A5FA" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="card mt-4">
        <p className="text-sm font-medium mb-1">Governance flags by type</p>
        <p className="text-xs text-text-secondary mb-4">
          Which policy conditions are firing most often across this tenant's incidents right now.
        </p>
        {Object.keys(flagBreakdown).length === 0 ? (
          <p className="text-sm text-text-secondary">No governance flags currently raised.</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={Object.entries(flagBreakdown).map(([flag, count]) => ({ flag, count }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="flag" tick={{ fill: "#CBD5E1", fontSize: 10 }} />
              <YAxis tick={{ fill: "#CBD5E1", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid #334155" }} />
              <Bar dataKey="count" fill="#EF4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
