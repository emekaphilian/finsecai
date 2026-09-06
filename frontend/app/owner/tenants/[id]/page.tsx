"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch, getSession } from "@/lib/api";
import { Tenant } from "@/lib/types";

interface TenantUser { id: string; email: string; role: string; status: string; }
interface TenantConfiguration { tenant_id: string; configuration: Record<string, unknown>; updated_at: string; }

export default function TenantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [users, setUsers] = useState<TenantUser[]>([]);
  const [configuration, setConfiguration] = useState<TenantConfiguration | null>(null);
  const [profile, setProfile] = useState({ name: "", description: "", industry: "", country: "" });
  const [newUser, setNewUser] = useState({ email: "", password: "", role: "analyst" });
  const [configText, setConfigText] = useState("{}");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (getSession()?.role !== "owner") return;
    Promise.all([
      apiFetch<Tenant>(`/tenants/${id}`),
      apiFetch<TenantUser[]>(`/tenants/${id}/users`),
      apiFetch<TenantConfiguration>(`/tenants/${id}/configuration`),
    ]).then(([tenantData, usersData, configData]) => {
      setTenant(tenantData);
      setProfile({ name: tenantData.name, description: tenantData.description, industry: tenantData.industry, country: tenantData.country });
      setUsers(usersData);
      setConfiguration(configData);
      setConfigText(JSON.stringify(configData.configuration, null, 2));
    }).catch((error) => setMessage(error instanceof Error ? error.message : "Unable to load tenant."));
  }, [id]);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    try {
      const updated = await apiFetch<Tenant>(`/tenants/${id}`, { method: "PATCH", body: JSON.stringify(profile) });
      setTenant(updated); setMessage("Company profile saved.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to save profile."); }
  }

  async function saveConfiguration(event: FormEvent) {
    event.preventDefault();
    try {
      const configurationValue = JSON.parse(configText) as Record<string, unknown>;
      const updated = await apiFetch<TenantConfiguration>(`/tenants/${id}/configuration`, { method: "PATCH", body: JSON.stringify({ configuration: configurationValue }) });
      setConfiguration(updated); setConfigText(JSON.stringify(updated.configuration, null, 2)); setMessage("Tenant configuration saved.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Configuration must be valid JSON."); }
  }

  async function addUser(event: FormEvent) {
    event.preventDefault();
    try {
      const created = await apiFetch<TenantUser>(`/tenants/${id}/users`, { method: "POST", body: JSON.stringify(newUser) });
      setUsers((current) => [...current, created]); setNewUser({ email: "", password: "", role: "analyst" }); setMessage("User provisioned.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to provision user."); }
  }

  if (getSession()?.role !== "owner") return <p className="text-text-secondary">Platform owner access required.</p>;
  if (!tenant) return <p className="text-text-secondary">{message || "Loading tenant..."}</p>;

  return (
    <div className="max-w-5xl">
      <Link href="/owner/tenants" className="text-sm text-gold hover:underline">Back to tenants</Link>
      <div className="flex items-start justify-between gap-4 mt-4 mb-8">
        <div><p className="text-xs uppercase tracking-wide text-gold mb-2">{tenant.tenant_type || "Unclassified"} · {tenant.status}</p><h1 className="text-2xl font-semibold">{tenant.name}</h1><p className="text-sm text-text-secondary mt-1">{tenant.incident_count} incidents · {tenant.user_count} users · {tenant.evidence_count} evidence · {tenant.report_count} reports · {tenant.configured ? "configured" : "not configured"}</p></div>
        <div className="flex gap-2">
          <Link href={`/dashboard/analytics?tenant_id=${tenant.id}`} className="btn-primary text-sm">Analytics</Link>
          <Link href={`/dashboard/copilot?tenant_id=${tenant.id}`} className="btn-primary text-sm">Copilot</Link>
          <Link href={`/dashboard/incidents?tenant_id=${tenant.id}`} className="btn-primary text-sm">Inspect incidents</Link>
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={saveProfile} className="card space-y-4">
          <div><h2 className="font-medium">Company profile</h2><p className="text-xs text-text-secondary mt-1">Stored on the tenant record.</p></div>
          <input className="input w-full" placeholder="Company name" value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} />
          <input className="input w-full" placeholder="Industry" value={profile.industry} onChange={(e) => setProfile({ ...profile, industry: e.target.value })} />
          <input className="input w-full" placeholder="Country" value={profile.country} onChange={(e) => setProfile({ ...profile, country: e.target.value })} />
          <textarea className="input w-full min-h-28" placeholder="Description" value={profile.description} onChange={(e) => setProfile({ ...profile, description: e.target.value })} />
          <button className="btn-primary" type="submit">Save profile</button>
        </form>
        <section className="card">
          <h2 className="font-medium mb-1">Users</h2><p className="text-xs text-text-secondary mb-4">Tenant administrators and operational users.</p>
          <div className="divide-y divide-border mb-4">{users.map((user) => <div key={user.id} className="py-3 flex justify-between text-sm"><span>{user.email}</span><span className="text-text-secondary">{user.role} · {user.status}</span></div>)}</div>
          <form onSubmit={addUser} className="space-y-3 border-t border-border pt-4"><p className="text-sm font-medium">Add user</p><input required className="input w-full" type="email" placeholder="Email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} /><input required minLength={8} className="input w-full" type="password" placeholder="Temporary password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} /><select className="input w-full" value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}><option value="analyst">Analyst</option><option value="admin">Admin</option><option value="compliance_officer">Compliance Officer</option><option value="viewer">Viewer</option></select><button className="btn-primary" type="submit">Provision user</button></form>
        </section>
        <form onSubmit={saveConfiguration} className="card lg:col-span-2 space-y-4"><div><h2 className="font-medium">Tenant configuration</h2><p className="text-xs text-text-secondary mt-1">Uses the existing tenant configuration model for extensible settings.</p></div><textarea className="input w-full min-h-52 font-mono text-xs" value={configText} onChange={(e) => setConfigText(e.target.value)} /><button className="btn-primary" type="submit">Save configuration</button></form>
      </div>
      {message && <p className="text-sm text-text-secondary mt-4">{message}</p>}
    </div>
  );
}