"use client";

import { useRef, useState } from "react";

type Message = { role: "user" | "assistant"; content: string };
type Source = { id: string; title: string };

export function Assistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const busy = Boolean(messages.length || loading || error);

  async function send() {
    const question = input.trim();
    if (!question || loading) return;
    const next = [...messages, { role: "user" as const, content: question }];
    setMessages(next);
    setInput("");
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? `HTTP ${response.status}`);
      setMessages([...next, { role: "assistant", content: data.reply }]);
      setSources(data.sources ?? []);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setLoading(false);
    }
  }

  function expand() {
    setOpen(true);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  if (!open && !busy) {
    return (
      <div className="assistant-dock">
        <button type="button" className="assistant-pill" onClick={expand} aria-label="Ask Nemo">
          <span className="assistant-orb" aria-hidden="true">
            <span className="material-symbols-outlined">robot_2</span>
          </span>
          <span className="assistant-pill-label">Ask Nemo</span>
        </button>
      </div>
    );
  }

  return (
    <div className={`assistant-dock ${busy ? "has-response" : ""}`}>
      {busy ? (
        <div className="assistant-response" role="status" aria-live="polite">
          <div className="assistant-head">
            <span className="assistant-orb" aria-hidden="true">
              <span className="material-symbols-outlined">robot_2</span>
            </span>
            <span className="assistant-title">Assistant</span>
          </div>
          <div className="assistant-log">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`msg ${message.role}`}>
                {message.content}
              </div>
            ))}
            {loading ? (
              <div className="msg assistant">
                <span className="material-symbols-outlined spin">progress_activity</span> thinking…
              </div>
            ) : null}
            {error ? <div className="msg assistant assistant-error">{error}</div> : null}
            {sources.length > 0 ? (
              <div className="assistant-sources">
                {sources.map((source) => (
                  <span className="pill" key={source.id}>
                    {source.title}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
      <div className="assistant-input">
        <input
          id="assistant-input"
          ref={inputRef}
          className="input"
          value={input}
          placeholder="Ask Nemo…"
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") send();
          }}
          aria-label="Question"
        />
        <button
          type="button"
          className="assistant-send"
          onClick={send}
          disabled={loading}
          aria-label="Send question"
        >
          <span className="material-symbols-outlined">arrow_upward</span>
        </button>
      </div>
    </div>
  );
}
