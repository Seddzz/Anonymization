import data from "./embeddings.json";

type Chunk = { id: string; title: string; text: string; vector: number[] };

export type Retrieved = { id: string; title: string; text: string; score: number };

const CHUNKS = (data as { chunks: Chunk[] }).chunks;

let extractorPromise: Promise<unknown> | null = null;

function getExtractor() {
  if (!extractorPromise) {
    extractorPromise = import("@huggingface/transformers").then(({ pipeline }) =>
      pipeline("feature-extraction", "Xenova/all-MiniLM-L6-v2", { dtype: "q8" }),
    );
  }
  return extractorPromise;
}

async function embed(text: string): Promise<number[]> {
  const extractor = (await getExtractor()) as (
    input: string[],
    options: { pooling: string; normalize: boolean },
  ) => Promise<{ data: Float32Array }>;
  const output = await extractor([text], { pooling: "mean", normalize: true });
  return Array.from(output.data);
}

function dot(a: number[], b: number[]): number {
  let sum = 0;
  for (let index = 0; index < a.length; index += 1) sum += a[index] * b[index];
  return sum;
}

function keywordFallback(query: string, k: number): Retrieved[] {
  const terms = query
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((term) => term.length > 2);
  return CHUNKS.map((chunk) => {
    const haystack = `${chunk.title} ${chunk.text}`.toLowerCase();
    const score = terms.reduce((sum, term) => sum + (haystack.includes(term) ? 1 : 0), 0);
    return { id: chunk.id, title: chunk.title, text: chunk.text, score };
  })
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
}

export async function retrieve(query: string, k = 4): Promise<Retrieved[]> {
  try {
    const queryVector = await embed(query);
    return CHUNKS.map((chunk) => ({
      id: chunk.id,
      title: chunk.title,
      text: chunk.text,
      score: dot(queryVector, chunk.vector),
    }))
      .sort((a, b) => b.score - a.score)
      .slice(0, k);
  } catch {
    return keywordFallback(query, k);
  }
}
