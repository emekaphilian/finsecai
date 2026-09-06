"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

export default function OwnerTenantWorkspacePage() {
  const params = useParams();
  const tenantId = String(params.id);
  const query = `?tenant_id=${encodeURIComponent(tenantId)}`;

  return (
    <main className="p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <p className="text-xs uppercase tracking-wide text-gold">
            Tenant Workspace
          </p>

          <h1 className="text-3xl font-semibold mt-2">
            Tenant Operational Workspace
          </h1>

          <p className="text-sm text-text-secondary mt-2">
            Authorized platform-owner view of tenant {tenantId}.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Link href={`/owner/tenants/${tenantId}/workspace${query}`} className="card">
            Overview
          </Link>
          <Link href={`/dashboard/incidents${query}`} className="card">
            Incidents
          </Link>
          <Link href={`/dashboard/analytics${query}`} className="card">
            Analytics
          </Link>
          <Link href={`/dashboard/copilot${query}`} className="card">
            Copilot
          </Link>
          <Link href={`/dashboard/reports${query}`} className="card">
            Reports
          </Link>
        </div>
      </div>
    </main>
  );
}
