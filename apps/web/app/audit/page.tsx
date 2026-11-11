"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { api, type AuditRow } from "@/lib/api";

export default function AuditPage() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<AuditRow[]>("/v1/audit")
      .then(setRows)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <Shell current="audit">
      <section className="card">
        <h2>Audit log</h2>
        <p className="muted">Every ingest, connect, disconnect, and kill-switch change is recorded.</p>
        {error ? <p className="error">{error}</p> : null}
        <table className="audit">
          <thead>
            <tr>
              <th>When</th>
              <th>Who</th>
              <th>Action</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.at ? new Date(row.at).toLocaleString() : "—"}</td>
                <td>{row.actor}</td>
                <td>{row.action}</td>
                <td>{row.payload?.subject ? String(row.payload.subject) : row.entity_type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </Shell>
  );
}
