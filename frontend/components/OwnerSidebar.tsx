"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

const links = [
  { href: "/owner", label: "Enterprise Overview" },
  { href: "/owner/tenants", label: "Tenant Directory" },
  { href: "/owner/reports", label: "Enterprise Reports" },
  { href: "/owner/audit", label: "Audit" },
  { href: "/owner/integrations", label: "Integrations" },
  { href: "/owner/models", label: "Models" },
  { href: "/owner/llm", label: "LLM" },
  { href: "/owner/settings", label: "Settings" },
];

export function OwnerSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="w-64 shrink-0 border-r border-border min-h-screen px-4 py-6 flex flex-col bg-primary">
      <div className="px-2 mb-8">
        <div className="text-lg font-semibold">
          FinSec<span className="text-gold">AI</span>
        </div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-text-secondary mt-1">
          Platform Administration
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        {links.map((link) => {
          const active =
            pathname === link.href ||
            (link.href !== "/owner" && pathname.startsWith(`${link.href}/`));

          return (
            <Link
              key={link.href}
              href={link.href}
              className={`block px-3 py-2.5 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-gold/15 text-gold font-medium"
                  : "text-text-secondary hover:bg-secondary hover:text-text-primary"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={() => {
          clearToken();
          router.push("/owner-login");
        }}
        className="text-sm text-text-secondary hover:text-danger px-3 py-2 text-left"
      >
        Sign out
      </button>
    </aside>
  );
}
