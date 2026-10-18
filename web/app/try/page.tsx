import type { Metadata } from "next";

import { SiteHeader } from "@/components/site-header";
import { Tester } from "@/components/tester";

export const metadata: Metadata = {
  title: "Try it — Nemo",
  description: "Send text to the anonymizer API, redact it, then restore it.",
};

export default function TryPage() {
  return (
    <>
      <SiteHeader />
      <main className="container">
        <section className="hero" style={{ padding: "70px 0 0" }}>
          <p className="crumb">Playground</p>
          <h1 className="doc-title">Try it</h1>
          <p className="doc-sub">
            The playground connects to the Nemo engine running on your machine at your configured
            URL — nothing is uploaded anywhere. Start it with Docker or Uvicorn and it connects
            automatically.
          </p>
        </section>
        <Tester />
      </main>
    </>
  );
}
