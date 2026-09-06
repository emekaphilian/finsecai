"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DemoReportsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard/reports");
  }, [router]);

  return null;
}
