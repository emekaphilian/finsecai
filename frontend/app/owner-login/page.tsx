"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { clearToken, getSession, login } from "@/lib/api";

export default function OwnerLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await login(email.trim(), password, "owner");
      if (getSession()?.role !== "owner") {
        clearToken();
        throw new Error("Platform owner access required.");
      }
      router.replace(result.must_change_password ? "/change-credentials?next=/owner" : "/owner");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to authenticate.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-primary px-6">
      <form onSubmit={handleSubmit} className="card w-full max-w-md space-y-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Platform Owner Login</h1>
            <p className="text-sm text-text-secondary mt-1">Access the FinSecAI enterprise console.</p>
          </div>
          <Link href="/" className="text-sm font-medium text-text-secondary hover:text-text-primary">Home</Link>
        </div>
        <input type="email" placeholder="Owner email" value={email} onChange={(e) => setEmail(e.target.value)} className="input w-full" required />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="input w-full" required />
        {error && <p className="text-sm text-danger">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={loading}>{loading ? "Signing in..." : "Sign in to Console"}</button>
      </form>
    </main>
  );
}
