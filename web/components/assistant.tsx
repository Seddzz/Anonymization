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
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const busy = Boolean(messages.length || loading || error);
  const open = focused || busy;

  async function send() {
    const question = input.trim();
    if (!question || loading) {
      inputRef.current?.focus();
      return;
    }
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

  return (
    <div className={`assistant-dock ${open ? "is-open" : ""} ${busy ? "has-response" : ""}`}>
      {busy ? (
        <div className="assistant-response" role="status" aria-live="polite">
          <div className="assistant-head">
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
        <button
          type="button"
          className="assistant-orb"
          onClick={send}
          disabled={loading}
          aria-label="Send question"
        >
          <span className="material-symbols-outlined">arrow_upward</span>
        </button>
        <input
          id="assistant-input"
          ref={inputRef}
          className="input"
          value={input}
          placeholder="Ask Nemo"
          onChange={(event) => setInput(event.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => {
            if (!input.trim() && !busy) setFocused(false);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") send();
          }}
          aria-label="Question"
        />
      </div>
    </div>
  );
}
