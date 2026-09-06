"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, downloadReport, getActiveTenantId, getSession, scopedQuery } from "@/lib/api";
import { Incident } from "@/lib/types";

export default function ReportsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const session = getSession();

  useEffect(() => {
    const requestedTenantId = new URLSearchParams(window.location.search).get("tenant_id");
    const tenantId = session?.role === "owner" ? requestedTenantId : getActiveTenantId() || session?.tenant_id;
    apiFetch<Incident[]>(`/incidents?limit=200${tenantId ? `&tenant_id=${encodeURIComponent(tenantId)}` : ""}`)
      .then((data) => setIncidents(data.filter((incident) => Boolean(incident.analysis_json))))
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load reports."))
      .finally(() => setLoading(false));
  }, [session?.role, session?.tenant_id]);

  const scope = scopedQuery(
    session?.role === "owner"
      ? new URLSearchParams(typeof window === "undefined" ? "" : window.location.search).get("tenant_id")
      : getActiveTenantId() || session?.tenant_id
  );

  return (
    <div className="max-w-5xl">
      <p className="text-xs uppercase tracking-wide text-gold mb-2">Incident reporting</p>
      <h1 className="text-2xl font-semibold">Reports</h1>
      <p className="text-sm text-text-secondary mt-1 mb-6">Download a PDF for any incident with persisted intelligence analysis. Reports render that persisted analysis and its recorded evidence provenance.</p>
      {error && <p role="alert" className="mb-4 text-sm text-danger">{error}</p>}
      <section className="card overflow-x-auto">
        {loading ? <p className="py-8 text-center text-sm text-text-secondary">Loading report-ready incidents…</p> : incidents.length === 0 ? (
          <div className="py-8 text-center"><p className="text-sm text-text-secondary">No analyzed incidents are ready for a report.</p><Link href={`/dashboard/incidents${scope}`} className="inline-block mt-3 text-sm text-gold hover:underline">Review incidents</Link></div>
        ) : (
          <table className="w-full text-sm"><thead><tr className="border-b border-border text-left text-text-secondary"><th className="py-2 pr-4">Incident</th><th className="py-2 pr-4">User</th><th className="py-2 pr-4">Risk</th><th className="py-2 pr-4">Created</th><th className="py-2">Action</th></tr></thead><tbody>{incidents.map((incident) => (
            <tr key={incident.id} className="border-b border-border/50 last:border-0"><td className="py-3 pr-4"><Link href={`/dashboard/incidents/${incident.id}`} className="text-gold hover:underline">{incident.id.slice(0, 8)}</Link></td><td className="py-3 pr-4">{incident.user_id}</td><td className="py-3 pr-4">{incident.risk_score.toFixed(2)}</td><td className="py-3 pr-4">{incident.created_at ? new Date(incident.created_at).toLocaleDateString() : "—"}</td><td className="py-3"><button className="text-gold hover:underline" onClick={() => downloadReport(incident.id)}>Download PDF</button></td></tr>
          ))}</tbody></table>
        )}
      </section>
    </div>
  );
}
