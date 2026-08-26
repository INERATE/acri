//! Ports acri/compass.py: the resolver. Given a query, returns the k tools
//! that matter. BM25 (bm25.rs) scores query terms against tool text;
//! understanding is the model's job, this only does recall (narrow N tools
//! to k candidates).

use crate::bm25;
use crate::corpus::{Corpus, Tool};
use crate::synonyms::expand;
use crate::text::tokenize;

/// One ranked tool and acri's confidence in it. `score` is relative to the
/// best match for this query (1.0 = best), not a calibrated probability.
#[derive(Debug, Clone, PartialEq)]
pub struct Resolved {
    pub tool: Tool,
    pub score: f64,
}

/// Rank every tool in `corpus` against `query`, return the top k. Tools that
/// score zero (no shared term with the query) are dropped rather than padded
/// in -- an empty result means "nothing in this corpus matches".
pub fn resolve(query: &str, corpus: &Corpus, k: usize) -> Vec<Resolved> {
    if corpus.is_empty() {
        return Vec::new();
    }
    let query_tokens = expand(tokenize(query));
    let raw: Vec<f64> = (0..corpus.len()).map(|i| bm25::score(&query_tokens, corpus, i)).collect();
    // bm25 scores are always >= 0 by construction (idf > 0 for any valid df,
    // term frequency f >= 0), so seeding the fold at 0.0 is a true max, not a floor.
    let top = raw.iter().cloned().fold(0.0_f64, f64::max);
    if top <= 0.0 {
        return Vec::new();
    }
    let mut scored: Vec<Resolved> = (0..corpus.len())
        .filter(|&i| raw[i] > 0.0)
        .map(|i| Resolved { tool: corpus.tools[i].clone(), score: raw[i] / top })
        .collect();
    scored.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    scored.truncate(k);
    scored
}

// Behavioral tests mirroring tests/test_compass.py live in rust/tests/resolve.rs,
// as a black-box integration test against the public API only -- same split
// as the Python project itself (tests/ is a sibling of acri/, not inline).
