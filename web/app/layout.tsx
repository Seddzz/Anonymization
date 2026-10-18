import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nemo — PII anonymization docs",
  description:
    "Local, reversible PII anonymization for English documents. REST API, CLI, Docker and MCP tools.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=arrow_upward,progress_activity"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
