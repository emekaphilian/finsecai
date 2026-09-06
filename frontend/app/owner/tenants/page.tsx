"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import {
  apiFetch,
  enterTenantWorkspace,
  getSession,
  setActiveTenantId,
} from "@/lib/api";
import { Tenant } from "@/lib/types";

const emptyForm = {
  company_name: "",
  description: "",
  industry: "",
  country: "",
  timezone: "UTC",
  business_description: "",
  compliance_requirements: "",
  email: "",
  password: "",
};

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  async function enterWorkspace(tenant: Tenant) {
    setMessage(null);
    try {
      await enterTenantWorkspace(tenant.id);
      setActiveTenantId(tenant.id);
      window.location.href = `/owner/tenants/${encodeURIComponent(tenant.id)}/workspace`;
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to enter workspace.");
    }
  }

  function loadTenants() {
    setLoading(true);
    apiFetch<Tenant[]>("/tenants")
      .then(setTenants)
      .catch((error) => setMessage(error instanceof Error ? error.message : "Unable to load tenants."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (getSession()?.role === "owner") loadTenants();
    else setLoading(false);
  }, []);

  async function createTenant(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setMessage(null);
    try {
      await apiFetch<Tenant>("/tenants", {
        method: "POST",
        body: JSON.stringify({
          company_name: form.company_name,
          description: form.description,
          industry: form.industry,
          country: form.country,
          timezone: form.timezone,
          configuration: {
            business_description: form.business_description,
            compliance_requirements: form.compliance_requirements,
          },
          initial_administrator: {
            email: form.email,
            password: form.password,
            role: "admin",
          },
        }),
      });
      setForm(emptyForm);
      setMessage("Tenant provisioned successfully.");
      loadTenants();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Tenant provisioning failed.");
    } finally {
      setCreating(false);
    }
  }

  if (getSession()?.role !== "owner") {
    return <p className="text-text-secondary">Platform owner access required.</p>;
  }

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-wide text-gold mb-2">Platform owner</p>
        <h1 className="text-2xl font-semibold mb-1">Enterprise tenants</h1>
        <p className="text-sm text-text-secondary">
          Manage customer workspaces and switch into their operational view without changing backend authorization boundaries.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <section className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-medium">Tenant directory</h2>
              <p className="text-xs text-text-secondary mt-1">{tenants.length} workspaces in the platform</p>
            </div>
            <span className="badge badge-medium">Owner scope</span>
          </div>
          {loading ? (
            <p className="text-sm text-text-secondary">Loading tenant directory...</p>
          ) : tenants.length === 0 ? (
            <p className="text-sm text-text-secondary">No tenants found.</p>
          ) : (
            <div className="divide-y divide-border">
              {tenants.map((tenant) => (
                <div key={tenant.id} className="py-4 first:pt-0 last:pb-0 flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium">{tenant.name}</p>
                    <p className="text-xs text-text-secondary mt-1">
                      <span className="text-gold">{tenant.tenant_type || "Unclassified"}</span> · {tenant.status} · {tenant.user_count} users · {tenant.incident_count} incidents · {tenant.evidence_count} evidence · {tenant.report_count} reports · {tenant.configured ? "configured" : "not configured"}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <Link href={`/owner/tenants/${tenant.id}`} className="text-sm text-text-secondary hover:text-gold">
                      View
                    </Link>
                    <button type="button" onClick={() => enterWorkspace(tenant)} className="text-sm text-gold hover:underline">
                      Enter workspace
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <form onSubmit={createTenant} className="card space-y-4">
          <div>
            <h2 className="font-medium">Provision tenant</h2>
            <p className="text-xs text-text-secondary mt-1">Creates a customer workspace and its first administrator.</p>
          </div>
          <input required className="input w-full" placeholder="Company name" value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} />
          <input className="input w-full" placeholder="Industry" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
          <input className="input w-full" placeholder="Country" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
          <textarea className="input w-full min-h-20" placeholder="What the company does" value={form.business_description} onChange={(e) => setForm({ ...form, business_description: e.target.value })} />
          <textarea className="input w-full min-h-20" placeholder="Compliance requirements" value={form.compliance_requirements} onChange={(e) => setForm({ ...form, compliance_requirements: e.target.value })} />
          <input className="input w-full" placeholder="Administrator email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input required minLength={8} className="input w-full" placeholder="Temporary password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <textarea className="input w-full min-h-20" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          {message && <p className="text-sm text-text-secondary">{message}</p>}
          <button className="btn-primary w-full" disabled={creating}>{creating ? "Provisioning..." : "Create tenant"}</button>
        </form>
      </div>
    </div>
  );
}