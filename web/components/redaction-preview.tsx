"use client";

import { useRef } from "react";

type Segment = { text: string; pii?: boolean };

const SEGMENTS: Segment[] = [
  { text: "Client " },
  { text: "Sarah Kellermann", pii: true },
  { text: " (born " },
  { text: "03/15/1989", pii: true },
  { text: ") transferred " },
  { text: "€4,200.00", pii: true },
  { text: " to IBAN " },
  { text: "DE89 3704 0044 0532 0130 00", pii: true },
  { text: " and confirmed it by email at " },
  { text: "sarah.k@nordwind.io", pii: true },
  { text: ". She can be reached on " },
  { text: "(555) 123-4567", pii: true },
  { text: " for any follow-up on the matter." },
];

function Layer({ variant }: { variant: "redacted" | "reveal" }) {
  return (
    <p className="doc-text">
      {SEGMENTS.map((segment, index) =>
        segment.pii ? (
          <span key={index} className={variant === "redacted" ? "redact" : "pii"}>
            {segment.text}
          </span>
        ) : (
          <span key={index}>{segment.text}</span>
        ),
      )}
    </p>
  );
}

export function RedactionPreview() {
  const figureRef = useRef<HTMLDivElement>(null);
  const revealRef = useRef<HTMLDivElement>(null);
  const lensRef = useRef<HTMLDivElement>(null);

  function track(clientX: number, clientY: number) {
    const figure = figureRef.current;
    if (!figure) return;
    const rect = figure.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    for (const node of [revealRef.current, lensRef.current]) {
      node?.style.setProperty("--mx", `${x}px`);
      node?.style.setProperty("--my", `${y}px`);
    }
  }

  return (
    <div
      className="doc-figure"
      ref={figureRef}
      onMouseMove={(event) => track(event.clientX, event.clientY)}
      onMouseEnter={(event) => {
        figureRef.current?.classList.add("is-active");
        track(event.clientX, event.clientY);
      }}
      onMouseLeave={() => figureRef.current?.classList.remove("is-active")}
    >
      <div className="doc-window">
        <div className="doc-bar">
          <span className="doc-dot" />
          <span className="doc-dot" />
          <span className="doc-dot" />
          <span className="doc-name">client-note.txt</span>
          <span className="doc-badge">6 PII</span>
        </div>
        <div className="doc-body">
          <Layer variant="redacted" />
          <div className="doc-reveal" ref={revealRef} aria-hidden="true">
            <Layer variant="reveal" />
          </div>
        </div>
      </div>
      <div className="doc-lens" ref={lensRef} aria-hidden="true" />
      <span className="doc-hint">Hover the document to reveal what Nemo hides</span>
    </div>
  );
}
