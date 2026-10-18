import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { InstallTabs } from "@/components/install-tabs";
import { RedactionPreview } from "@/components/redaction-preview";
import { SiteHeader } from "@/components/site-header";

export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <main className="container">
        <section className="hero">
          <div className="hero-copy">
            <h1>
              Strip PII before it reaches a model.
              <br />
              <span className="hero-accent">Put it back afterwards.</span>
            </h1>
            <p>
              Nemo is an API-first anonymizer for English documents. Detect names, emails, bank
              details and identifiers locally, redact them with placeholders or fake values, and
              reverse the change when you need to.
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
          </div>
          <RedactionPreview />
        </section>

        <InstallTabs />

        <footer style={{ padding: "64px 0 48px", color: "var(--inkdim)", fontSize: 13 }}>
          Built with FastAPI, PyMuPDF, transformers and MCP. MIT licensed.
        </footer>
      </main>
    </>
  );
}
