"use client";

import { FormEvent, useState } from "react";
import { changeCredentials, getSession } from "@/lib/api";

export default function Page() {
  const session = getSession();
  const [email, setEmail] = useState(session?.email || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function updateCredentials(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    try {
      await changeCredentials(currentPassword, newPassword, email.trim());
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage("Credentials updated successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update credentials.");
    }
  }

  return (
    <main className="p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <p className="text-xs uppercase tracking-wide text-gold">Platform Owner</p>
          <h1 className="text-3xl font-semibold mt-2">Settings</h1>
          <p className="text-text-secondary mt-2">Manage the platform owner account and security credentials.</p>
        </div>
        <form onSubmit={updateCredentials} className="card max-w-xl space-y-4">
          <h2 className="font-medium">Account security</h2>
          <input className="input w-full" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email / username" required />
          <input className="input w-full" type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} placeholder="Current password" required />
          <input className="input w-full" type="password" minLength={8} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} placeholder="New password" required />
          <input className="input w-full" type="password" minLength={8} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Confirm new password" required />
          {message && <p className="text-sm text-success">{message}</p>}
          {error && <p className="text-sm text-danger">{error}</p>}
          <button className="btn-primary" type="submit">Update credentials</button>
        </form>
      </div>
    </main>
  );
}
