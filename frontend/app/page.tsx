import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BookOpenCheck,
  Check,
  FileText,
  Fingerprint,
  Network,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const capabilities = [
  { icon: Search, title: "Incident Triage", text: "Ingest incident data and prioritize what matters most with risk-based analysis." },
  { icon: Fingerprint, title: "Investigation & Evidence", text: "Collect, analyze, and connect incident evidence to support defensible investigations." },
  { icon: Activity, title: "Risk Intelligence", text: "Combine risk signals, anomaly analysis, and fraud indicators to support investigation and prioritization." },
  { icon: Network, title: "Framework Mapping", text: "Map supported investigation findings to security and compliance frameworks with traceable rationale and evidence." },
  { icon: Sparkles, title: "Grounded Copilot", text: "Ask questions about your authorized incident and evidence data and receive answers grounded in available evidence." },
  { icon: FileText, title: "Reporting", text: "Generate downloadable reports from completed investigations." },
];

export default function LandingPage() {
  return (
    <main className="landing-shell min-h-screen overflow-hidden bg-primary">
      <nav className="mx-auto flex max-w-7xl items-center justify-between border-b border-border/60 px-6 py-6 lg:px-10">
        <Link href="/" className="text-2xl font-semibold tracking-tight text-text-primary">FinSec<span className="text-gold">AI</span></Link>
        <div className="hidden items-center gap-7 text-sm text-text-secondary md:flex">
          <a href="#capabilities" className="hover:text-text-primary">Product</a><a href="#capabilities" className="hover:text-text-primary">Solutions</a><a href="#demo" className="hover:text-text-primary">Resources</a><span>Company</span><span>Pricing</span>
        </div>
        <div className="flex items-center gap-4 text-sm"><Link href="/tenant-login" className="hidden text-text-secondary hover:text-text-primary sm:inline">Sign in</Link><Link href="/login?demo=1" className="btn-primary flex items-center gap-2 px-4 py-2">Enter Demo Console <ArrowRight size={15} /></Link></div>
      </nav>

      <section className="relative mx-auto grid max-w-7xl gap-14 px-6 pb-24 pt-20 lg:grid-cols-[1.1fr_.9fr] lg:items-center lg:px-10 lg:pt-28">
        <div className="landing-glow" aria-hidden="true" /><div className="relative"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-gold">SOC command center</p><h1 className="mt-5 max-w-3xl text-5xl font-semibold leading-[1.05] tracking-tight text-text-primary md:text-7xl">See fraud before it clears.</h1><p className="mt-7 max-w-2xl text-lg leading-8 text-text-secondary">FinSecAI unifies incident triage, evidence, risk analysis, investigation, framework mapping, and reporting in one tenant-scoped security intelligence platform.</p><div className="mt-9 flex flex-wrap items-center gap-4"><Link href="/login?demo=1" className="btn-primary flex items-center gap-2 px-5 py-3">Enter Demo Console <ArrowRight size={17} /></Link><a href="#capabilities" className="btn-secondary flex items-center gap-2 px-5 py-3">Explore the product <BarChart3 size={17} /></a></div></div>
        <div className="relative rounded-xl border border-border bg-secondary/70 p-5 shadow-2xl shadow-black/20"><div className="flex items-center justify-between border-b border-border pb-4"><div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-gold" /><p className="text-xs font-semibold uppercase tracking-widest text-text-secondary">Live incident feed</p></div><span className="text-xs text-slate-500">Acme demo console</span></div><div className="flex min-h-64 flex-col items-center justify-center text-center"><Activity className="mb-4 text-gold" size={28} /><p className="text-sm font-medium text-text-primary">Demo incidents load after sign-in</p><p className="mt-2 max-w-xs text-xs leading-5 text-text-secondary">The public page does not display fabricated telemetry. Enter the Acme demonstration environment to review its seeded records and live risk results.</p><Link href="/login?demo=1" className="mt-5 text-sm font-medium text-gold hover:underline">Open the incident feed <ArrowRight className="ml-1 inline" size={14} /></Link></div></div>
      </section>

      <section className="border-y border-border/70 bg-secondary/30"><div className="mx-auto grid max-w-7xl gap-8 px-6 py-10 md:grid-cols-3 lg:px-10"><div className="flex gap-3"><BarChart3 className="text-gold" size={22} /><div><h2 className="font-semibold">Real-time risk scoring</h2><p className="mt-1 text-sm text-text-secondary">Prioritize incidents with model-generated risk signals.</p></div></div><div className="flex gap-3"><BookOpenCheck className="text-violet-300" size={22} /><div><h2 className="font-semibold">Evidence you can trust</h2><p className="mt-1 text-sm text-text-secondary">Connect investigation findings to available evidence.</p></div></div><div className="flex gap-3"><ShieldCheck className="text-info" size={22} /><div><h2 className="font-semibold">Built for compliance</h2><p className="mt-1 text-sm text-text-secondary">Keep analysis, governance, and reporting together.</p></div></div></div></section>

      <section id="capabilities" className="mx-auto max-w-7xl scroll-mt-8 px-6 py-24 lg:px-10"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-gold">One operating picture</p><h2 className="mt-4 max-w-2xl text-3xl font-semibold tracking-tight md:text-5xl">The work of security operations, connected.</h2><div className="mt-12 grid gap-px overflow-hidden rounded-xl border border-border bg-border md:grid-cols-2 lg:grid-cols-3">{capabilities.map(({ icon: Icon, title, text }) => <article key={title} className="bg-secondary p-7"><Icon className="text-violet-300" size={26} /><h3 className="mt-8 text-lg font-semibold">{title}</h3><p className="mt-3 text-sm leading-6 text-text-secondary">{text}</p></article>)}</div></section>

      <section id="demo" className="border-y border-border/70 bg-secondary/35"><div className="mx-auto grid max-w-7xl gap-12 px-6 py-20 lg:grid-cols-[1fr_auto] lg:items-center lg:px-10"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-gold">See FinSecAI in action</p><h2 className="mt-4 text-3xl font-semibold md:text-5xl">Try the Acme demonstration environment</h2><p className="mt-5 max-w-2xl text-text-secondary">Explore the platform using the seeded Acme tenant with demonstration incidents, evidence, analysis, investigations, and reporting.</p><div className="mt-7 grid gap-3 text-sm text-text-secondary sm:grid-cols-2"><span><Check className="mr-2 inline text-gold" size={15} />Investigate demonstration incidents</span><span><Check className="mr-2 inline text-gold" size={15} />Review evidence and risk analysis</span><span><Check className="mr-2 inline text-gold" size={15} />Explore investigation workflows</span><span><Check className="mr-2 inline text-gold" size={15} />Generate downloadable reports</span></div></div><div className="min-w-64 rounded-xl border border-border bg-primary p-6"><p className="text-sm font-semibold text-gold">Acme demonstration environment</p><p className="mt-2 text-sm leading-6 text-text-secondary">Explore FinSecAI using the seeded Acme demonstration tenant.</p><Link href="/login?demo=1" className="btn-primary mt-6 flex items-center justify-center gap-2 px-5 py-3">Enter Demo Console <ArrowRight size={17} /></Link><Link href="/tenant-login" className="mt-4 block text-center text-sm text-text-secondary hover:text-text-primary">Tenant / Client Login</Link><p className="mt-1 text-center text-xs text-slate-500">Access your organization's workspace</p></div></div></section>
      <footer className="mx-auto flex max-w-7xl items-center justify-between px-6 py-8 text-xs text-slate-500 lg:px-10"><span>FinSecAI - Security intelligence for fraud and compliance operations</span><Link href="/owner-login" className="hover:text-text-secondary">Platform owner access</Link></footer>
    </main>
  );
}
