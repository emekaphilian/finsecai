"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { changeCredentials, getSession } from "@/lib/api";

function ChangeCredentialsForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const session = getSession();
  const nextPath = searchParams.get("next") || (session?.role === "owner" ? "/owner" : "/dashboard");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [newEmail, setNewEmail] = useState(session?.email || "");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await changeCredentials(currentPassword, newPassword, newEmail.trim());
      router.replace(nextPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update credentials.");
    } finally {
      setLoading(false);
    }
  }

  if (!session) {
    return <main className="min-h-screen bg-primary p-6 text-text-secondary">Please sign in first.</main>;
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-primary px-6 py-16">
      <form onSubmit={handleSubmit} className="card w-full max-w-md space-y-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gold">Account setup</p>
          <h1 className="mt-2 text-2xl font-semibold">Update your credentials</h1>
          <p className="mt-2 text-sm text-text-secondary">Your administrator supplied temporary credentials. Set a new password before continuing.</p>
        </div>
        <input className="input w-full" type="email" placeholder="Email" value={newEmail} onChange={(event) => setNewEmail(event.target.value)} required />
        <input className="input w-full" type="password" placeholder="Current password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required />
        <input className="input w-full" type="password" minLength={8} placeholder="New password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required />
        <input className="input w-full" type="password" minLength={8} placeholder="Confirm new password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
        {error && <p className="text-sm text-danger">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={loading}>{loading ? "Updating..." : "Update credentials"}</button>
      </form>
    </main>
  );
}

export default function ChangeCredentialsPage() {
  return <Suspense><ChangeCredentialsForm /></Suspense>;
}
