"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, getSession } from "@/lib/api";
import { EnterpriseSummary, Tenant } from "@/lib/types";
import { KpiCard } from "@/components/KpiCard";

const labels: Record<string, string> = {
  reports: "Reports",
  audit: "Audit",
  integrations: "Integrations",
  models: "Models",
  llm: "LLM",
  settings: "Settings",
  users: "Users",
  roles: "Roles & Permissions",
};

export default function OwnerConsolePage() {
  const [view, setView] = useState("users");
  const [summary, setSummary] = useState<EnterpriseSummary | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);

  useEffect(() => {
    if (getSession()?.role !== "owner") return;
    setView(new URLSearchParams(window.location.search).get("view") || "users");
    Promise.all([
      apiFetch<EnterpriseSummary>("/analytics/enterprise-summary"),
      apiFetch<Tenant[]>("/tenants"),
    ]).then(([summaryData, tenantData]) => {
      setSummary(summaryData);
      setTenants(tenantData);
    });
  }, []);

  if (getSession()?.role !== "owner") {
    return <p className="text-text-secondary">Platform owner access required.</p>;
  }

  return (
    <div className="max-w-6xl">
      <p className="text-xs uppercase tracking-wide text-gold mb-2">Platform administration</p>
      <h1 className="text-2xl font-semibold mb-1">{labels[view] || "Owner console"}</h1>
      <p className="text-sm text-text-secondary mb-8">
        Platform controls operate across explicitly provisioned enterprise tenants. Historical benchmark and diagnostic records remain excluded.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Legitimate tenants" value={summary?.total_tenants ?? "..."} />
        <KpiCard label="Active customers" value={summary?.active_customer_tenants ?? "..."} />
        <KpiCard label="Tenant users" value={tenants.reduce((total, tenant) => total + tenant.user_count, 0)} />
        <KpiCard label="Total incidents" value={summary?.total_incidents ?? "..."} />
      </div>

      <section className="card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-medium">Enterprise workspaces</h2>
            <p className="text-xs text-text-secondary mt-1">Choose a tenant to configure it or enter its operational workspace.</p>
          </div>
          <Link href="/dashboard/tenants" className="btn-primary text-sm">Manage tenants</Link>
        </div>
        <div className="divide-y divide-border">
          {tenants.map((tenant) => (
            <div key={tenant.id} className="py-3 flex items-center justify-between gap-4">
              <div>
                <p className="font-medium">{tenant.name}</p>
                <p className="text-xs text-text-secondary">{tenant.tenant_type || "Unclassified"} · {tenant.status} · {tenant.user_count} users · {tenant.incident_count} incidents</p>
              </div>
              <Link href={`/dashboard/tenants/${tenant.id}`} className="text-sm text-gold hover:underline">View</Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
