"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSession } from "@/lib/api";
import { DemoSidebar } from "@/components/DemoSidebar";

export default function DemoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  useEffect(() => {
    const session = getSession();

    if (!session || !session.tenant_id) {
      router.push("/login?demo=1");
      return;
    }

    if (session.role === "owner") {
      router.push("/owner");
    }
  }, [router]);

  return (
    <div className="min-h-screen flex">
      <DemoSidebar />
      <main className="flex-1 min-w-0">
        {children}
      </main>
    </div>
  );
}