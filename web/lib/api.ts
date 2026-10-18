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

export async function healthCheck(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 3500);
    const response = await fetch(`${API_URL}/health`, {
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timer);
    return response.ok;
  } catch {
    return false;
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error(
      `Can't reach the Nemo engine at ${API_URL}. Start it locally (docker compose up --build), then try again.`,
    );
  }

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
