"use client";

import { useEffect, useState } from "react";
import { apiFetch, getActiveTenantId } from "@/lib/api";
import { Tenant } from "@/lib/types";

export function WorkspaceBanner() {
  const [tenant, setTenant] = useState<Tenant | null>(null);

  useEffect(() => {
    const tenantId = getActiveTenantId();

    if (!tenantId) {
      return;
    }

    apiFetch<Tenant>(`/tenants/${tenantId}`)
      .then(setTenant)
      .catch(() => setTenant(null));
  }, []);

  if (!tenant) {
    return null;
  }

  return (
    <div className="mb-6 rounded-lg border border-border bg-surface px-4 py-3">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-gold">
            Active workspace
          </p>

          <p className="font-medium">
            {tenant.name}
          </p>

          <p className="text-xs text-text-secondary">
            {tenant.tenant_type || "Tenant"} · {tenant.status}
          </p>
        </div>

        <span className="badge badge-medium">
          Tenant scope
        </span>
      </div>
    </div>
  );
}