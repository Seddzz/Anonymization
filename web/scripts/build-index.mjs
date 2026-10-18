import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { pipeline } from "@huggingface/transformers";

const here = dirname(fileURLToPath(import.meta.url));
const corpusPath = join(here, "..", "lib", "rag-corpus.json");
const outPath = join(here, "..", "lib", "embeddings.json");

const corpus = JSON.parse(readFileSync(corpusPath, "utf8"));
const extractor = await pipeline("feature-extraction", corpus.model, { dtype: "q8" });

const output = await extractor(
  corpus.chunks.map((chunk) => chunk.text),
  { pooling: "mean", normalize: true },
);
const [count, dims] = output.dims;
const data = output.data;

const chunks = corpus.chunks.map((chunk, index) => ({
  id: chunk.id,
  title: chunk.title,
  text: chunk.text,
  vector: Array.from(data.slice(index * dims, (index + 1) * dims)),
}));

writeFileSync(outPath, JSON.stringify({ model: corpus.model, dims, chunks }), "utf8");
console.log(`Wrote ${count} chunks (${dims}d) to ${outPath}`);
