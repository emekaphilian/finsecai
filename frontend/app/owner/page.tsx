"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, getSession } from "@/lib/api";
import { EnterpriseSummary, Tenant } from "@/lib/types";

export default function OwnerOverviewPage() {
  const [summary, setSummary] = useState<EnterpriseSummary | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (getSession()?.role !== "owner") return;

    Promise.all([
      apiFetch<EnterpriseSummary>("/analytics/enterprise-summary"),
      apiFetch<Tenant[]>("/tenants"),
    ])
      .then(([summaryData, tenantData]) => {
        setSummary(summaryData);
        setTenants(tenantData);
      })
      .finally(() => setLoading(false));
  }, []);

  if (getSession()?.role !== "owner") {
    return (
      <p className="p-6 text-text-secondary">
        Platform owner access required.
      </p>
    );
  }

  return (
    <main className="p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        <header>
          <p className="text-xs uppercase tracking-wide text-gold">
            Platform Owner
          </p>

          <h1 className="text-3xl font-semibold mt-2">
            Enterprise Overview
          </h1>

          <p className="text-text-secondary mt-2">
            Enterprise-wide visibility, tenant management and platform controls.
          </p>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card">
            <p className="text-sm text-text-secondary">Total tenants</p>
            <p className="text-2xl font-semibold mt-2">
              {loading ? "..." : summary?.total_tenants ?? "-"}
            </p>
          </div>

          <div className="card">
            <p className="text-sm text-text-secondary">Active customers</p>
            <p className="text-2xl font-semibold mt-2">
              {loading ? "..." : summary?.active_customer_tenants ?? "-"}
            </p>
          </div>

          <div className="card">
            <p className="text-sm text-text-secondary">Demo tenants</p>
            <p className="text-2xl font-semibold mt-2">
              {loading ? "..." : summary?.demo_tenants ?? "-"}
            </p>
          </div>

          <div className="card">
            <p className="text-sm text-text-secondary">Tenant users</p>
            <p className="text-2xl font-semibold mt-2">
              {loading
                ? "..."
                : tenants.reduce((total, tenant) => total + tenant.user_count, 0)}
            </p>
          </div>
        </section>

        <section className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="font-medium">Tenant Directory</h2>
              <p className="text-xs text-text-secondary mt-1">
                Manage and enter authorized tenant workspaces.
              </p>
            </div>

            <Link href="/owner/tenants" className="btn-primary text-sm">
              Manage tenants
            </Link>
          </div>

          <div className="divide-y divide-border">
            {tenants.slice(0, 10).map((tenant) => (
              <div
                key={tenant.id}
                className="py-4 flex items-center justify-between gap-4"
              >
                <div>
                  <p className="font-medium">{tenant.name}</p>
                  <p className="text-xs text-text-secondary mt-1">
                    {tenant.tenant_type || "Unclassified"} · {tenant.status} · {tenant.user_count} users · {tenant.incident_count} incidents
                  </p>
                </div>

                <Link
                  href={`/owner/tenants/${tenant.id}`}
                  className="text-sm text-gold hover:underline"
                >
                  View
                </Link>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
