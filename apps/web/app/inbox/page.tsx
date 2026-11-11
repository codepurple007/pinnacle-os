"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { api, type InboxMessage } from "@/lib/api";

export default function InboxPage() {
  const [messages, setMessages] = useState<InboxMessage[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<InboxMessage[]>("/v1/inbox/messages")
      .then(setMessages)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <Shell current="inbox">
      <section className="card">
        <h2>Stored mail</h2>
        <p className="muted">
          These rows live in PinnacleOS, not in a chatbot. Nothing here has been sent by the
          agent.
        </p>
        {error ? <p className="error">{error}</p> : null}
        {messages.length === 0 ? (
          <p className="muted">Empty. Load the Tuesday inbox from the desk.</p>
        ) : null}
        {messages.map((message) => (
          <article className="mail" key={message.id}>
            <h3>{message.subject}</h3>
            <p className="muted">{message.from_addr}</p>
            <p>{message.snippet}</p>
            <button
              className="secondary"
              onClick={() => setOpenId(openId === message.id ? null : message.id)}
            >
              {openId === message.id ? "Hide thread" : "Open thread"}
            </button>
            {openId === message.id ? <pre>{message.body_text}</pre> : null}
          </article>
        ))}
      </section>
    </Shell>
  );
}
