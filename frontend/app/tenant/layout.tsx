"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSession } from "@/lib/api";

export default function TenantLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const session = getSession();
    if (!session?.tenant_id || session.role === "owner") router.replace("/tenant-login");
  }, [router]);

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 border-r border-border p-6">
        <h2 className="mb-8 text-xl font-semibold">FinSecAI</h2>
        <nav className="space-y-3">
          <Link href="/tenant" className="block">Overview</Link>
          <Link href="/tenant/incidents" className="block">Incidents</Link>
          <Link href="/tenant/analytics" className="block">Analytics</Link>
          <Link href="/tenant/copilot" className="block">Copilot</Link>
          <Link href="/tenant/reports" className="block">Reports</Link>
        </nav>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
