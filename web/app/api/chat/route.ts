import { NextResponse } from "next/server";

import { retrieve } from "@/lib/rag";

export const runtime = "nodejs";
export const maxDuration = 60;

const GROQ_URL = "https://api.groq.com/openai/v1/chat/completions";
const MODEL = process.env.GROQ_MODEL ?? "openai/gpt-oss-120b";

type Message = { role: "user" | "assistant"; content: string };

const SYSTEM = `You are the Nemo documentation assistant.
Answer questions about the Nemo PII anonymization project using ONLY the context below.
If the answer is not in the context, say you do not know and point the user to the documentation.
Be concise and technical, and prefer short paragraphs or bullet points.

Context:
`;

export async function POST(request: Request) {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "GROQ_API_KEY is not configured on the server." },
      { status: 500 },
    );
  }

  const body = (await request.json()) as { messages?: Message[] };
  const messages = (body.messages ?? [])
    .filter(
      (message) =>
        (message.role === "user" || message.role === "assistant") &&
        typeof message.content === "string",
    )
    .slice(-8);
  const question = [...messages].reverse().find((message) => message.role === "user")?.content ?? "";
  if (!question.trim()) {
    return NextResponse.json({ error: "A question is required." }, { status: 400 });
  }

  const sources = await retrieve(question, 4);
  const context = sources.map((source, index) => `[${index + 1}] ${source.title}\n${source.text}`).join("\n\n");

  const groqResponse = await fetch(GROQ_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: MODEL,
      temperature: 0.2,
      messages: [{ role: "system", content: SYSTEM + context }, ...messages.slice(-6)],
    }),
  });

  if (!groqResponse.ok) {
    const detail = await groqResponse.text();
    return NextResponse.json(
      { error: `Groq error ${groqResponse.status}: ${detail.slice(0, 200)}` },
      { status: 502 },
    );
  }

  const data = (await groqResponse.json()) as {
    choices?: { message?: { content?: string } }[];
  };
  const reply = data.choices?.[0]?.message?.content ?? "(no response)";

  return NextResponse.json({
    reply,
    sources: sources.map((source) => ({ id: source.id, title: source.title })),
  });
}
