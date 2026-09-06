"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSession } from "@/lib/api";
import { OwnerSidebar } from "@/components/OwnerSidebar";

export default function OwnerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  useEffect(() => {
    const session = getSession();

    if (!session) {
      router.push("/owner-login");
      return;
    }

    if (session.role !== "owner") {
      router.push("/dashboard");
    }
  }, [router]);

  return (
    <div className="min-h-screen flex">
      <OwnerSidebar />

      <main className="flex-1 min-w-0">
        {children}
      </main>
    </div>
  );
}
