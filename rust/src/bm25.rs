//! The scoring function compass.rs's resolve() ranks with -- split out on its
//! own so compass.rs stays just the resolve loop.

use crate::corpus::Corpus;

const K1: f64 = 1.5;
const B: f64 = 0.75;

fn idf(df: u32, n_docs: usize) -> f64 {
    (1.0 + (n_docs as f64 - df as f64 + 0.5) / (df as f64 + 0.5)).ln()
}

pub fn score(query_tokens: &[String], corpus: &Corpus, doc_idx: usize) -> f64 {
    let doc_len = corpus.doc_tokens[doc_idx].len() as f64;
    let freqs = &corpus.doc_freqs[doc_idx];
    let n_docs = corpus.tools.len();
    let mut total = 0.0;
    for tok in query_tokens {
        let f = match freqs.get(tok) {
            Some(&f) if f > 0 => f as f64,
            _ => continue,
        };
        let idf_val = idf(*corpus.df.get(tok).unwrap_or(&0), n_docs);
        let denom = f + K1 * (1.0 - B + B * doc_len / corpus.avgdl);
        total += idf_val * (f * (K1 + 1.0)) / denom;
    }
    total
}
