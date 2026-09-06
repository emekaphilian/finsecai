"use client";

import Link from "next/link";

export default function DemoOverviewPage() {
  return (
    <main className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        <header>
          <p className="text-xs uppercase tracking-wide text-gold">Acme Demo Tenant</p>
          <h1 className="text-3xl font-semibold mt-2">Demo Console</h1>
          <p className="text-text-secondary mt-2">
            Explore FinSecAI using the pre-populated Acme tenant environment.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Link href="/demo" className="card">
            <h2 className="font-medium">Overview</h2>
            <p className="text-sm text-text-secondary mt-2">Acme tenant overview and risk posture.</p>
          </Link>
          <Link href="/demo/incidents" className="card">
            <h2 className="font-medium">Incidents</h2>
            <p className="text-sm text-text-secondary mt-2">Review Acme security incidents.</p>
          </Link>
          <Link href="/demo/analytics" className="card">
            <h2 className="font-medium">Analytics</h2>
            <p className="text-sm text-text-secondary mt-2">Analyze Acme tenant activity.</p>
          </Link>
          <Link href="/demo/copilot" className="card">
            <h2 className="font-medium">Copilot</h2>
            <p className="text-sm text-text-secondary mt-2">Ask questions against Acme tenant data.</p>
          </Link>
          <Link href="/demo/reports" className="card">
            <h2 className="font-medium">Reports</h2>
            <p className="text-sm text-text-secondary mt-2">Review Acme tenant reports.</p>
          </Link>
        </section>
      </div>
    </main>
  );
}