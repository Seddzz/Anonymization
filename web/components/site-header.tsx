"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Assistant } from "@/components/assistant";

const LINKS = [
  { href: "/docs", label: "Docs" },
  { href: "/try", label: "Test" },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="site-header">
      <div className="container header-row">
        <nav className="nav-links">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname.startsWith(link.href) ? "active" : ""}
            >
              {link.label}
            </Link>
          ))}
          <a href="https://github.com/Seddzz/Anonymization" target="_blank" rel="noreferrer">
            GitHub
          </a>
          <Assistant />
        </nav>
      </div>
    </header>
  );
}
