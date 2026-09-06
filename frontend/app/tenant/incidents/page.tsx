"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TenantIncidentsPage() {
  const router = useRouter();
  useEffect(() => router.replace("/dashboard/incidents"), [router]);
  return null;
}
