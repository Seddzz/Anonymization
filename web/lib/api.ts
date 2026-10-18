export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export type Entity = {
  label: string;
  start: number;
  end: number;
  text: string;
  score: number;
  source: string;
};

export type Strategy = "placeholder" | "fake";

export type AnonymizeResponse = {
  redacted: string;
  mapping_id: string;
  entities: Entity[];
};

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`HTTP ${response.status}: ${detail.slice(0, 240)}`);
  }

  return (await response.json()) as T;
}

export function detectText(text: string, ner: boolean) {
  return post<{ entities: Entity[] }>("/detect", { text, ner });
}

export function anonymizeText(text: string, strategy: Strategy, ner: boolean) {
  return post<AnonymizeResponse>("/anonymize", { text, strategy, ner });
}

export function restoreText(mappingId: string, redacted: string) {
  return post<{ text: string }>("/restore", { mapping_id: mappingId, redacted });
}
