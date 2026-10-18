import { ArrowRight, Lock, Repeat, ScanSearch, Sparkles } from "lucide-react";
import Link from "next/link";

import { SiteHeader } from "@/components/site-header";

const FEATURES = [
  {
    icon: ScanSearch,
    title: "Three detectors, one shape",
    body: "Regex, checksum validation and transformer NER all emit the same Entity spans, with deterministic sources taking priority on overlap.",
  },
  {
    icon: Repeat,
    title: "Reversible by design",
    body: "Redact to stable placeholders or realistic fakes, then restore the exact originals from a short-lived mapping.",
  },
  {
    icon: Lock,
    title: "Local-first",
    body: "The pipeline runs on your machine. The NER model is downloaded once; no text is sent anywhere.",
  },
  {
    icon: Sparkles,
    title: "Four interfaces",
    body: "Use the REST API, the anon CLI, the Docker image, or the MCP tools from an agent — same engine underneath.",
  },
];

export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <main className="container">
        <section className="hero">
          <h1>
            Strip PII before it reaches a model.
            <br />
            <span className="hero-accent">Put it back afterwards.</span>
          </h1>
          <p>
            AnonShield is an API-first anonymizer for English documents. Detect names, emails,
            bank details and identifiers locally, redact them with placeholders or fake values,
            and reverse the change when you need to.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-accent" href="/docs">
              Read the docs
              <ArrowRight size={16} />
            </Link>
            <Link className="btn" href="/try">
              Try it in the browser
            </Link>
          </div>
        </section>

        <section className="card-grid" aria-label="Features">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <article className="card" key={feature.title}>
                <div className="card-ico">
                  <Icon className="icon" size={18} />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.body}</p>
              </article>
            );
          })}
        </section>

        <footer style={{ padding: "64px 0 48px", color: "var(--inkdim)", fontSize: 13 }}>
          Built with FastAPI, PyMuPDF, transformers and MCP. MIT licensed.
        </footer>
      </main>
    </>
  );
}
