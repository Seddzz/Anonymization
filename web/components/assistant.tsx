"use client";

import { Check, Copy } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

type Message = { role: "user" | "assistant"; content: string; at: number };
type Source = { id: string; title: string };

const SUGGESTIONS = [
  "What is Nemo?",
  "How do I anonymize a document?",
  "How does the NER detector work?",
  "Can I run it locally?",
];

function clock(at: number): string {
  return new Date(at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function CodeBlock({ lang, code }: { lang: string; code: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="codeblock md-codeblock">
      <div className="codeblock-head">
        <span>{lang || "code"}</span>
        <button
          type="button"
          className="codeblock-copy"
          onClick={handleCopy}
          aria-label="Copy code block"
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
        </button>
      </div>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}

function inline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0;
  let key = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    const token = match[0];
    if (token.startsWith("**")) {
      nodes.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else {
      nodes.push(<code key={key++}>{token.slice(1, -1)}</code>);
    }
    last = match.index + token.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

type ListItem = { num: number | null; text: string };

function renderMarkdown(text: string): ReactNode {
  const lines = text.split(/\r?\n/);
  const blocks: ReactNode[] = [];
  let list: ListItem[] = [];
  let listType: "ul" | "ol" | null = null;
  let key = 0;

  let inCode = false;
  let codeLang = "";
  let codeLines: string[] = [];

  const flush = () => {
    if (list.length === 0) return;
    const items = list.map((item, index) => <li key={index}>{inline(item.text)}</li>);
    if (listType === "ol") {
      const start = list[0].num ?? 1;
      blocks.push(
        <ol key={key++} start={start}>
          {items}
        </ol>,
      );
    } else {
      blocks.push(<ul key={key++}>{items}</ul>);
    }
    list = [];
    listType = null;
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const fenceMatch = /^```(\w*)\s*$/.exec(line.trim());
    if (fenceMatch) {
      flush();
      if (inCode) {
        blocks.push(<CodeBlock key={key++} lang={codeLang} code={codeLines.join("\n")} />);
        codeLines = [];
        codeLang = "";
        inCode = false;
      } else {
        inCode = true;
        codeLang = fenceMatch[1];
      }
      continue;
    }

    if (inCode) {
      codeLines.push(raw);
      continue;
    }

    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    const bullet = /^[-*•–—]\s+(.*)$/.exec(line);
    const numbered = /^(\d+)[.)]\s+(.*)$/.exec(line);
    if (heading) {
      flush();
      blocks.push(
        <p key={key++} className={`md-h md-h${heading[1].length}`}>
          {inline(heading[2])}
        </p>,
      );
    } else if (bullet) {
      if (listType && listType !== "ul") flush();
      listType = "ul";
      list.push({ num: null, text: bullet[1] });
    } else if (numbered) {
      if (listType && listType !== "ol") flush();
      listType = "ol";
      list.push({ num: Number.parseInt(numbered[1], 10), text: numbered[2] });
    } else if (line.trim() === "") {
      // Do not flush on blank lines so numbered list items separated by spaces stay in the same <ol>
    } else {
      flush();
      blocks.push(<p key={key++}>{inline(line)}</p>);
    }
  }
  flush();
  if (inCode) {
    blocks.push(<CodeBlock key={key++} lang={codeLang} code={codeLines.join("\n")} />);
  }
  return blocks;
}

export function Assistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [focused, setFocused] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const busy = Boolean(messages.length || loading || error);
  const open = (focused || busy) && !minimized;

  async function send(text?: string) {
    const question = (text ?? input).trim();
    if (!question || loading) {
      inputRef.current?.focus();
      return;
    }
    setMinimized(false);
    const next = [...messages, { role: "user" as const, content: question, at: Date.now() }];
    setMessages(next);
    setInput("");
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: next.map(({ role, content }) => ({ role, content })),
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? `HTTP ${response.status}`);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply, at: Date.now() },
      ]);
      setSources(data.sources ?? []);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open) logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading, open]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMinimized(true);
        setFocused(false);
        inputRef.current?.blur();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className={`assistant-dock ${open ? "is-open" : ""}`}>
      {open ? (
        <div className="assistant-response" role="status" aria-live="polite">
          <div className="assistant-log" ref={logRef}>
            {messages.length === 0 && !loading && !error ? (
              <div className="assistant-empty">
                <span className="assistant-empty-title">NEMO</span>
                <div className="assistant-suggestions">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      className="assistant-suggestion"
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => send(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
            {messages.map((message, index) => (
              <div key={index} className={`msg ${message.role}`}>
                {message.role === "assistant" ? (
                  <div className="msg-body">{renderMarkdown(message.content)}</div>
                ) : (
                  <span className="msg-body">{message.content}</span>
                )}
                <span className="msg-time">{clock(message.at)}</span>
              </div>
            ))}
            {loading ? (
              <div className="msg assistant msg-loading">
                <span className="material-symbols-outlined spin">progress_activity</span>
                <span>thinking…</span>
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
          onClick={() => send()}
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
          onFocus={() => {
            setFocused(true);
            setMinimized(false);
          }}
          onBlur={(event) => {
            const next = event.relatedTarget as Node | null;
            if (next && event.currentTarget.closest(".assistant-dock")?.contains(next)) return;
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
