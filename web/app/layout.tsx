import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AnonShield — PII anonymization docs",
  description:
    "Local, reversible PII anonymization for English documents. REST API, CLI, Docker and MCP tools.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
