"use client";

import { Loader2, RotateCcw, ScanSearch, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { API_URL, anonymizeText, detectText, restoreText } from "@/lib/api";
import type { Entity, Strategy } from "@/lib/api";

const SAMPLE = `Contract between John Doe (john.doe@acme.org, phone (555) 123-4567) and Acme Corp. Pay to IBAN GB29NWBK60161331926819 on 03/15/2024 at ZIP 90210.`;

type Busy = "detect" | "anonymize" | "restore" | null;

export function Tester() {
  const [text, setText] = useState(SAMPLE);
  const [strategy, setStrategy] = useState<Strategy>("placeholder");
  const [ner, setNer] = useState(false);
  const [output, setOutput] = useState("");
  const [mappingId, setMappingId] = useState<string | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [busy, setBusy] = useState<Busy>(null);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="tester">
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

      <p style={{ margin: 0, color: "var(--inkdim)", fontSize: 12 }}>
        API: <span className="mono">{API_URL}</span>
      </p>
    </div>
  );
}
