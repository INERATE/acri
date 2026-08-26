// synonyms — query-side alias expansion for compass. Not corpus-facing.
// Ported from acri/_synonyms.py. Applied to the query only, never the corpus:
// expanding doc text here would let a tool's description quietly start
// matching queries for a synonym it never claimed, and would shift df/idf
// for every other tool too. Every entry traces to a real recall@5 miss in
// the Python repo's assay/diagnose.py, not a guess.

export const ALIASES: Readonly<Record<string, readonly string[]>> = {
  pr: ["pull", "request"],
  meeting: ["event"],
  rain: ["weather"],
  raining: ["weather"],
  storm: ["weather"],
  warning: ["alerts"],
  warnings: ["alerts"],
  text: ["sms", "message"],
  sharpen: ["upscale", "resolution"],
  money: ["refund", "charge"],
};

export function expand(tokens: string[]): string[] {
  const expanded = [...tokens];
  for (const tok of tokens) {
    expanded.push(...(ALIASES[tok] ?? []));
  }
  return expanded;
}
