"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DemoIncidentsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard/incidents");
  }, [router]);

  return null;
}
