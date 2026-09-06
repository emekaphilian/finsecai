"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DemoCopilotPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard/copilot");
  }, [router]);

  return null;
}
