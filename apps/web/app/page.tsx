"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { api, type Status } from "@/lib/api";

export default function DeskPage() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const data = await api<Status>("/v1/status");
    setStatus(data);
  }

  useEffect(() => {
    refresh().catch((err: Error) => setError(err.message));
    const params = new URLSearchParams(window.location.search);
    if (params.get("connected") === "1") {
      setNotice("Google is connected. Inbox sync is read-only.");
    }
  }, []);

  async function run(label: string, work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
      await refresh();
      setNotice(label);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function connectGoogle() {
    const data = await api<{ authorization_url: string }>("/v1/oauth/google/start", {
      method: "POST",
    });
    window.location.href = data.authorization_url;
  }

  if (!status) {
    return (
      <Shell current="desk">
        <p className="muted">{error || "Opening the desk…"}</p>
      </Shell>
    );
  }

  return (
    <Shell current="desk">
      {notice ? <div className="flash">{notice}</div> : null}
      {error ? <p className="error">{error}</p> : null}
      <div className="grid">
        <section className="card">
          <h2>{status.founder.name}</h2>
          <p className="muted">
            Founder desk for Pinnacle Marketing. The agent can read. It cannot send mail or
            change the calendar yet.
          </p>
          <ul className="status-list">
            <li>
              <span>Writes (kill switch)</span>
              <strong>{status.founder.writes_enabled ? "armed" : "paused"}</strong>
            </li>
            <li>
              <span>Agent can send</span>
              <strong>{status.agent_can_send ? "yes" : "no"}</strong>
            </li>
            <li>
              <span>Calendar writes</span>
              <strong>{status.agent_can_write_calendar ? "yes" : "no"}</strong>
            </li>
            <li>
              <span>Messages stored</span>
              <strong>{status.inbox.message_count}</strong>
            </li>
            <li>
              <span>Last sync</span>
              <strong>
                {status.founder.last_sync_at
                  ? new Date(status.founder.last_sync_at).toLocaleString()
                  : "never"}
              </strong>
            </li>
          </ul>
          <div className="row">
            <button
              disabled={busy}
              onClick={() =>
                run(
                  status.founder.writes_enabled
                    ? "Agent paused. Later phases will not send."
                    : "Writes armed. Phase 3 still cannot send.",
                  async () => {
                    await api("/v1/settings/kill-switch", {
                      method: "POST",
                      body: JSON.stringify({
                        writes_enabled: !status.founder.writes_enabled,
                      }),
                    });
                  }
                )
              }
            >
              {status.founder.writes_enabled ? "Pause agent" : "Resume writes"}
            </button>
            <button
              className="secondary"
              disabled={busy}
              onClick={() =>
                run("Tuesday corpus loaded into the store.", async () => {
                  await api("/v1/dev/seed-tuesday", { method: "POST" });
                })
              }
            >
              Load Tuesday inbox
            </button>
          </div>
        </section>
        <section className="card">
          <h2>Google</h2>
          <p className="muted">
            {status.google.connected
              ? `Connected as ${status.google.email}. Scopes are read-only.`
              : status.google.oauth_configured
                ? "Not connected. OAuth is configured on the server."
                : "OAuth client is not configured. Use Load Tuesday inbox to prove ingest without Google."}
          </p>
          <div className="row">
            <button
              disabled={busy || !status.google.oauth_configured}
              onClick={() => connectGoogle().catch((err: Error) => setError(err.message))}
            >
              Connect Gmail
            </button>
            <button
              className="secondary"
              disabled={busy || !status.google.connected}
              onClick={() =>
                run("Google disconnected.", async () => {
                  await api("/v1/oauth/google", { method: "DELETE" });
                })
              }
            >
              Disconnect
            </button>
            <button
              className="secondary"
              disabled={busy || !status.google.connected}
              onClick={() =>
                run("Read-only Gmail sync finished.", async () => {
                  await api("/v1/sync/gmail", { method: "POST" });
                })
              }
            >
              Sync inbox
            </button>
          </div>
        </section>
      </div>
    </Shell>
  );
}
