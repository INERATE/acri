// compass — the resolver. Given a query, returns the k tools that matter.
// Ported from acri/compass.py. No language understanding: BM25 scores query
// terms against tool text, weighting terms that are rare in the corpus.

import type { Corpus, Tool } from "./corpus.js";
import { tokenize } from "./text.js";
import { expand } from "./synonyms.js";

const K1 = 1.5;
const B = 0.75;

// `score` is relative to the best match for this query (1.0 = best), not a
// calibrated probability -- a 0.9 does not mean "90% sure".
export interface Resolved {
  tool: Tool;
  score: number;
}

function idf(df: number, nDocs: number): number {
  return Math.log(1 + (nDocs - df + 0.5) / (df + 0.5));
}

export function bm25(queryTokens: string[], corpus: Corpus, docIdx: number): number {
  const docLen = corpus.docTokens[docIdx].length;
  const freqs = corpus.docFreqs[docIdx];
  const nDocs = corpus.tools.length;
  let score = 0;
  for (const tok of queryTokens) {
    const f = freqs.get(tok);
    if (!f) continue;
    const termIdf = idf(corpus.df.get(tok) ?? 0, nDocs);
    const denom = f + K1 * (1 - B + (B * docLen) / corpus.avgdl);
    score += (termIdf * (f * (K1 + 1))) / denom;
  }
  return score;
}

// Tools that score zero (no shared term with the query) are dropped rather
// than padded in -- an empty result means "nothing in this corpus matches".
export function resolve(query: string, corpus: Corpus, k = 5): Resolved[] {
  if (corpus.tools.length === 0) return [];
  const queryTokens = expand(tokenize(query));
  const raw = corpus.tools.map((_, i) => bm25(queryTokens, corpus, i));
  const top = Math.max(...raw);
  if (top <= 0) return [];
  const scored: Resolved[] = [];
  for (let i = 0; i < corpus.tools.length; i++) {
    if (raw[i] > 0) scored.push({ tool: corpus.tools[i], score: raw[i] / top });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, k);
}
