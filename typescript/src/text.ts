// text — tokenization shared by corpus (indexing) and compass (scoring).
// Ported from acri/_text.py -- both sides must tokenize identically or BM25
// scores a query against tokens the corpus was never split the same way.

const TOKEN_RE = /[a-z0-9]+/g;

// Same list as acri/_text.py's _STOPWORDS (the NLTK stoplist's
// non-contraction core) -- ported verbatim, not re-derived.
const STOPWORDS = new Set([
  "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
  "am", "of", "in", "on", "at", "to", "for", "with", "and", "or",
  "but", "this", "that", "these", "those", "what", "which", "who", "whom", "me",
  "my", "you", "your", "it", "its", "we", "they", "do", "does", "did",
  "into", "from", "by", "about", "up", "down", "out", "off", "over", "under",
  "again", "further", "then", "once", "here", "there", "when", "where", "why", "how",
  "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
  "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
  "s", "t", "can", "will", "just", "now", "if", "because", "as", "until",
  "while", "against", "between", "during", "before", "after", "above", "below",
]);

export function tokenize(text: string): string[] {
  // Strip apostrophes before splitting: "user's" -> "users" as one token,
  // not "user" + a stray "s" that then matches every other possessive.
  const normalized = text.toLowerCase().replace(/'/g, "").replace(/’/g, "");
  const matches = normalized.match(TOKEN_RE) ?? [];
  return matches.filter((t) => !STOPWORDS.has(t));
}
