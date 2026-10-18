"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

type Tab = {
  id: string;
  label: string;
  command: string;
  note: string;
};

const TABS: Tab[] = [
  {
    id: "pip",
    label: "pip",
    command:
      'pip install -e ".[dev]" --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple',
    note: "Prerequisite: Clone repo first (`git clone ...`). Run this command inside the project root directory.",
  },
  {
    id: "uv",
    label: "uv",
    command: 'uv pip install -e ".[dev]"',
    note: "Prerequisite: Clone repo first (`git clone ...`). Run this command inside the project root directory.",
  },
  {
    id: "docker",
    label: "docker",
    command: "docker compose up --build",
    note: "Prerequisite: Clone repo first. Requires Docker Desktop running. Starts the Nemo API on port 8000.",
  },
  {
    id: "git",
    label: "git",
    command: "git clone https://github.com/Seddzz/Nemo.git",
    note: "Step 1: Clone the repository to your local machine, then cd into the folder.",
  },
];

export function InstallTabs() {
  const [active, setActive] = useState(TABS[0].id);
  const [copied, setCopied] = useState(false);
  const current = TABS.find((tab) => tab.id === active) ?? TABS[0];

  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(current.command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="install" aria-label="Install Nemo">
      <h2>
        Get Nemo running.
        <br />
        <span className="hero-accent">Local, reversible, yours.</span>
      </h2>
      <p className="install-sub">
        Install with the tool you already use. No account, no uploads — every byte stays on your
        machine.
      </p>
      <div className="install-box">
        <div className="install-tabs" role="tablist">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={tab.id === active}
              className={`install-tab${tab.id === active ? " active" : ""}`}
              onClick={() => {
                setActive(tab.id);
                setCopied(false);
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="install-cmd">
          <code>{current.command}</code>
          <button
            type="button"
            className="install-copy"
            onClick={copyCommand}
            aria-label="Copy command"
          >
            {copied ? <Check size={15} /> : <Copy size={15} />}
          </button>
        </div>
        <div className="install-note">
          <span>{current.note}</span>
        </div>
      </div>
    </section>
  );
}
