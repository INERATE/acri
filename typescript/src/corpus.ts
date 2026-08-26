// corpus — the capability index. Ingests tools into one searchable body, once.
// Ported from acri/corpus.py. `handler` (Python's optional dispatcher field)
// is not ported -- nothing in this resolver-only port calls it, same as the
// Python side ("resolution never calls it").

import { tokenize } from "./text.js";

export interface Tool {
  name: string;
  description: string;
  parameters?: Record<string, unknown>;
}

export interface Corpus {
  tools: Tool[];
  docTokens: string[][];
  docFreqs: Map<string, number>[];
  df: Map<string, number>;
  avgdl: number;
}

export function index(tools: Tool[]): Corpus {
  if (tools.length === 0) {
    throw new Error("index() needs at least one tool");
  }
  const docTokens = tools.map((t) => tokenize(`${t.name} ${t.description}`));
  const docFreqs: Map<string, number>[] = [];
  const df = new Map<string, number>();
  for (const tokens of docTokens) {
    const freqs = new Map<string, number>();
    for (const tok of tokens) freqs.set(tok, (freqs.get(tok) ?? 0) + 1);
    docFreqs.push(freqs);
    for (const tok of freqs.keys()) df.set(tok, (df.get(tok) ?? 0) + 1);
  }
  const avgdl = docTokens.reduce((sum, t) => sum + t.length, 0) / docTokens.length;
  return { tools: [...tools], docTokens, docFreqs, df, avgdl };
}
