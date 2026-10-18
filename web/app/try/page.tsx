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
            Runs against the API at your configured URL. Nothing is stored beyond the 15-minute
            mapping.
          </p>
        </section>
        <Tester />
      </main>
    </>
  );
}
