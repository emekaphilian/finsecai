"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TenantAnalyticsPage() {
  const router = useRouter();
  useEffect(() => router.replace("/dashboard/analytics"), [router]);
  return null;
}
