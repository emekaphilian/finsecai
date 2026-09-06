"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, copilotSocketUrl, clearToken } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  text: string;
  streaming?: boolean;
}

export default function CopilotPage() {
  const router = useRouter();
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [connected, setConnected] = useState(false);
  const [llmStatus, setLlmStatus] = useState<{ provider: string | null; mode: string; detail?: string | null } | null>(null);
  const [summary, setSummary] = useState<import("@/lib/types").AnalyticsSummary | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const selectedTenantId = new URLSearchParams(window.location.search).get("tenant_id");
    setTenantId(selectedTenantId);
    const scope = selectedTenantId ? `?tenant_id=${encodeURIComponent(selectedTenantId)}` : "";
    apiFetch<import("@/lib/types").AnalyticsSummary>(`/analytics/summary${scope}`).then(setSummary).catch(() => {});
    apiFetch<{ provider: string | null; mode: string; detail?: string | null }>('/copilot/status').then(setLlmStatus).catch(() => {});
    const ws = new WebSocket(copilotSocketUrl(selectedTenantId));
    ws.onopen = () => setConnected(true);
    ws.onclose = (event) => {
      setConnected(false);
      if (event.code === 4401) {
        clearToken();
        router.push("/login");
      }
    };
    ws.onmessage = (event) => {
      if (event.data === "[[END]]") return;
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === "assistant" && last.streaming) {
          const copy = [...prev];
          copy[copy.length - 1] = { ...last, text: last.text + event.data };
          return copy;
        }
        return [...prev, { role: "assistant", text: event.data, streaming: true } as Message];
      });
    };
    wsRef.current = ws;
    return () => ws.close();
  }, []);

  function send() {
    if (!input.trim() || !wsRef.current) return;
    setMessages((prev) => [...prev, { role: "user", text: input }]);
    wsRef.current.send(input);
    setInput("");
  }

  return (
    <div className="max-w-2xl flex flex-col h-[80vh]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold">Copilot</h1>
          <p className="text-xs text-text-secondary">
            {tenantId ? "Tenant-scoped context" : "Current tenant context"} · grounded in the top 15 incidents by risk, out of {summary?.total_incidents ?? "—"} loaded.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs ${connected ? "text-success" : "text-text-secondary"}`}>
            {connected ? 'connected' : 'connecting…'}
          </span>
          <span className={`text-xs ${llmStatus?.provider ? 'text-success' : 'text-warning'}`}>
            {llmStatus?.provider ? `LLM: ${llmStatus.provider}` : `LLM: ${llmStatus?.detail || 'unavailable'}`}
          </span>
        </div>
      </div>

      <div className="card flex-1 overflow-y-auto mb-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-text-secondary text-sm">
            Ask about your incident data — e.g. &ldquo;which users have the most high-risk
            transfers?&rdquo;
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            <span
              className={`inline-block px-4 py-2 rounded-lg text-sm max-w-[85%] ${
                m.role === "user" ? "bg-gold/15 text-gold" : "bg-primary border border-border"
              }`}
            >
              {m.text}
            </span>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          className="input flex-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask the copilot…"
        />
        <button onClick={send} className="btn-primary">
          Send
        </button>
      </div>
    </div>
  );
}
