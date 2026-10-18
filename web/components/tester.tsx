"use client";

import { Loader2, Plug, PlugZap, RotateCcw, ScanSearch, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { API_URL, anonymizeText, detectText, healthCheck, restoreText } from "@/lib/api";
import type { Entity, Strategy } from "@/lib/api";

const SAMPLE = `Contract between John Doe (john.doe@acme.org, phone (555) 123-4567) and Acme Corp. Pay to IBAN GB29NWBK60161331926819 on 03/15/2024 at ZIP 90210.`;

type Busy = "detect" | "anonymize" | "restore" | null;
type Status = "checking" | "offline" | "online";

function OfflineGate({ onRetry, checking }: { onRetry: () => void; checking: boolean }) {
  return (
    <div className="offline">
      <div className="offline-head">
        <Plug className="icon" size={18} />
        <h3>Connect your local engine</h3>
      </div>
      <p className="offline-text">
        Nemo runs entirely on your machine — this playground talks to the API at{" "}
        <span className="mono">{API_URL}</span>. Start the engine and the page connects
        automatically; nothing you paste here ever leaves your computer.
      </p>
      <div className="offline-steps">
        <div className="offline-cmd">docker compose up --build</div>
        <div className="offline-cmd">
          .venv\Scripts\uvicorn anonymizer.api:app --port 8000
        </div>
      </div>
      <div className="tester-row">
        <button type="button" className="btn btn-accent" onClick={onRetry} disabled={checking}>
          {checking ? <Loader2 className="icon spin" size={16} /> : <PlugZap className="icon" size={16} />}
          {checking ? "Checking…" : "Retry connection"}
        </button>
        <span className="offline-note">Auto-retries every 5 seconds.</span>
      </div>
    </div>
  );
}

export function Tester() {
  const [text, setText] = useState(SAMPLE);
  const [strategy, setStrategy] = useState<Strategy>("placeholder");
  const [ner, setNer] = useState(false);
  const [output, setOutput] = useState("");
  const [mappingId, setMappingId] = useState<string | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [busy, setBusy] = useState<Busy>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("checking");

  const check = useCallback(async () => {
    const healthy = await healthCheck();
    setStatus(healthy ? "online" : "offline");
    return healthy;
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  useEffect(() => {
    if (status !== "offline") return;
    const timer = setInterval(() => void check(), 5000);
    return () => clearInterval(timer);
  }, [status, check]);

  async function run(kind: Exclude<Busy, null>) {
    setBusy(kind);
    setError(null);
    try {
      if (kind === "detect") {
        const result = await detectText(text, ner);
        setEntities(result.entities);
        setOutput(text);
        setMappingId(null);
      } else if (kind === "anonymize") {
        const result = await anonymizeText(text, strategy, ner);
        setEntities(result.entities);
        setOutput(result.redacted);
        setMappingId(result.mapping_id);
      } else if (mappingId) {
        const result = await restoreText(mappingId, output);
        setOutput(result.text);
        setMappingId(null);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(null);
    }
  }

  if (status !== "online") {
    return (
      <div className="tester">
        {status === "checking" ? (
          <div className="msg assistant msg-loading">
            <Loader2 className="icon spin" size={16} />
            <span>Looking for the engine at {API_URL}…</span>
          </div>
        ) : (
          <OfflineGate onRetry={() => void check()} checking={false} />
        )}
      </div>
    );
  }

  return (
    <div className="tester">
      <div className="tester-row">
        <span className="engine-pill">
          <span className="engine-dot" />
          Engine connected
        </span>
        <span className="offline-note mono">{API_URL}</span>
      </div>

      <div>
        <div className="tester-label">Text to analyze</div>
        <textarea
          className="textarea"
          value={text}
          onChange={(event) => setText(event.target.value)}
          spellCheck={false}
          aria-label="Text to analyze"
        />
      </div>

      <div className="tester-row">
        <select
          className="select"
          value={strategy}
          onChange={(event) => setStrategy(event.target.value as Strategy)}
          aria-label="Redaction strategy"
          style={{ width: "auto" }}
        >
          <option value="placeholder">Placeholders</option>
          <option value="fake">Fake values</option>
        </select>

        <label className="pill" style={{ cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={ner}
            onChange={(event) => setNer(event.target.checked)}
          />
          Use NER
        </label>

        <button
          type="button"
          className="btn"
          onClick={() => run("detect")}
          disabled={busy !== null}
        >
          {busy === "detect" ? <Loader2 className="icon spin" size={16} /> : <ScanSearch className="icon" size={16} />}
          Detect
        </button>
        <button
          type="button"
          className="btn btn-accent"
          onClick={() => run("anonymize")}
          disabled={busy !== null}
        >
          {busy === "anonymize" ? <Loader2 className="icon spin" size={16} /> : <ShieldCheck className="icon" size={16} />}
          Anonymize
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => run("restore")}
          disabled={busy !== null || !mappingId}
        >
          {busy === "restore" ? <Loader2 className="icon spin" size={16} /> : <RotateCcw className="icon" size={16} />}
          Restore
        </button>
      </div>

      <p style={{ margin: 0, color: "var(--inkdim)", fontSize: 12.5 }}>
        {ner
          ? "NER downloads dslim/bert-base-NER on the first request, so it can take a while."
          : "NER is off: names and organisations are not detected. Enable it to include them."}
      </p>

      {error ? <p className="tester-error mono" style={{ margin: 0, fontSize: 12.5 }}>{error}</p> : null}

      <div>
        <div className="tester-label" style={{ marginBottom: 8 }}>
          Entities ({entities.length})
        </div>
        <div className="entities">
          {entities.length === 0 ? (
            <span className="pill">None detected</span>
          ) : (
            entities.map((entity, index) => (
              <span className="pill entity" key={`${entity.label}-${entity.start}-${index}`}>
                <strong>{entity.label}</strong>
                {entity.text}
                <span style={{ color: "var(--inkdim)" }}>{entity.source}</span>
              </span>
            ))
          )}
        </div>
      </div>

      <div>
        <div className="tester-label" style={{ marginBottom: 8 }}>
          Output
        </div>
        <div className="tester-output">
          {output || "Detect or anonymize to see the result."}
        </div>
      </div>

      {mappingId ? (
        <div className="tester-row">
          <span className="pill mono">mapping_id: {mappingId}</span>
          <span style={{ color: "var(--inkdim)", fontSize: 12.5 }}>
            Stored for 15 minutes. Restore before it expires.
          </span>
        </div>
      ) : null}
    </div>
  );
}
