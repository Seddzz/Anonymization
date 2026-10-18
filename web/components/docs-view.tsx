"use client";

import { Gauge, Layers, ListOrdered, Rocket, Terminal } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useState } from "react";

import { GROUPS, SECTIONS } from "@/lib/content";

const GROUP_ICONS: Record<string, LucideIcon> = {
  "Getting started": Rocket,
  Concepts: Layers,
  Interfaces: Terminal,
  Quality: Gauge,
};

export function DocsView() {
  const [activeId, setActiveId] = useState(SECTIONS[0].id);
  const section = SECTIONS.find((item) => item.id === activeId) ?? SECTIONS[0];

  return (
    <div className="container docs-layout">
      <aside className="sidebar">
        <div className="sidebar-sticky">
          {GROUPS.map((group) => {
            const GroupIcon = GROUP_ICONS[group] ?? Layers;
            return (
              <div className="navgroup" key={group}>
                <div className="navgroup-title">
                  <GroupIcon className="icon" size={15} />
                  <span>{group}</span>
                </div>
                {SECTIONS.filter((item) => item.group === group).map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`navitem ${item.id === activeId ? "active" : ""}`}
                    onClick={() => setActiveId(item.id)}
                  >
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      </aside>

      <main className="doc-main">
        <p className="crumb">{section.group}</p>
        <h1 className="doc-title">{section.title}</h1>
        <p className="doc-sub">{section.subtitle}</p>
        <div className="prose">{section.body}</div>
      </main>

      <aside className="toc">
        <div className="sidebar-sticky">
          <div className="toc-title">
            <ListOrdered className="icon" size={15} />
            <span>On this page</span>
          </div>
          {section.toc.map((item) => (
            <a key={item.id} href={`#${item.id}`}>
              {item.label}
            </a>
          ))}
        </div>
      </aside>
    </div>
  );
}
