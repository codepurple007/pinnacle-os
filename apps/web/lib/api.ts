export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  const text = await response.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!response.ok) {
    const detail =
      typeof data === "object" && data && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : response.statusText;
    throw new Error(detail);
  }
  return data as T;
}

export type Status = {
  founder: {
    name: string;
    email: string;
    timezone: string;
    writes_enabled: boolean;
    last_sync_at: string | null;
  };
  google: {
    connected: boolean;
    email: string | null;
    oauth_configured: boolean;
    scopes: string;
    readonly: boolean;
  };
  inbox: { message_count: number };
  phase: number;
  agent_can_send: boolean;
  agent_can_write_calendar: boolean;
};

export type InboxMessage = {
  id: string;
  thread_id: string;
  gmail_thread_id: string;
  subject: string;
  from_addr: string;
  snippet: string;
  body_text: string;
  sent_at: string | null;
};

export type AuditRow = {
  id: string;
  at: string | null;
  actor: string;
  action: string;
  entity_type: string;
  payload: Record<string, unknown>;
};
