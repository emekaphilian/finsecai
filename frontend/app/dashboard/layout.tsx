"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { WorkspaceBanner } from "@/components/WorkspaceBanner";
import { getSession } from "@/lib/api";

function DashboardContent({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedTenantId = searchParams.get("tenant_id");

  useEffect(() => {
    const session = getSession();
    if (!session) {
      router.replace("/login");
    } else if (session.role === "owner" && !selectedTenantId) {
      router.replace("/owner");
    }
  }, [router, selectedTenantId]);

  return (
    <div className="flex bg-primary min-h-screen">
      <Sidebar />
      <main className="flex-1 px-8 py-8">
        <WorkspaceBanner />
        {children}
      </main>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<main className="min-h-screen bg-primary" />}>
      <DashboardContent>{children}</DashboardContent>
    </Suspense>
  );
}
