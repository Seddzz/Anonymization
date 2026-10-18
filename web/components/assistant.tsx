"use client";

import { Bot, Loader2, Send, X } from "lucide-react";
import { useState } from "react";

type Message = { role: "user" | "assistant"; content: string };
type Source = { id: string; title: string };

export function Assistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <>
      <button
        type="button"
        className="btn"
        onClick={() => setOpen(true)}
        aria-label="Ask the assistant"
      >
        <Bot className="icon" size={16} />
        Ask
      </button>
      {open ? (
        <div className="assistant-panel" role="dialog" aria-label="Documentation assistant">
          <div className="assistant-head">
            <Bot className="icon" size={16} />
            <span className="assistant-title">Assistant</span>
            <button
              type="button"
              className="assistant-close"
              onClick={() => setOpen(false)}
              aria-label="Close assistant"
            >
              <X size={16} />
            </button>
          </div>
          <div className="assistant-log">
            {messages.length === 0 ? (
              <p className="assistant-hint">
                Ask about installation, the API, redaction strategies, the CLI or limitations.
              </p>
            ) : (
              messages.map((message, index) => (
                <div key={index} className={`msg ${message.role}`}>
                  {message.content}
                </div>
              ))
            )}
            {loading ? (
              <div className="msg assistant">
                <Loader2 className="icon spin" size={14} /> thinking…
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
          <div className="assistant-input">
            <input
              className="input"
              value={input}
              placeholder="Ask a question…"
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") send();
              }}
              aria-label="Question"
            />
            <button
              type="button"
              className="btn btn-accent"
              onClick={send}
              disabled={loading}
              aria-label="Send question"
            >
              <Send className="icon" size={16} />
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}
