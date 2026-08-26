//! acri-core -- a faithful, minimal Rust port of acri's v0.1 resolver.
//!
//! Ports exactly: `acri/corpus.py` (Tool/Corpus/index), `acri/compass.py`
//! (BM25 resolve()), and their two small private deps `acri/_text.py`
//! (tokenize) and `acri/_synonyms.py` (ALIASES/expand). See README.md in
//! this directory for why this exists ahead of its own gate.
//!
//! Deliberately NOT ported: port, daemon, server, cli, config, gate, press,
//! sandbox, ledger, escape_hatch, router, adapters, schemas -- this is the
//! resolver core only, same as decisions.md frames v0.1 itself.

mod bm25;
mod compass;
mod corpus;
mod synonyms;
mod text;

pub use compass::{resolve, Resolved};
pub use corpus::{index, Corpus, Tool};
