//! Ports acri/corpus.py: the capability index. Ingests tools into one
//! searchable body, once.

use crate::text::tokenize;
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq)]
pub struct Tool {
    pub name: String,
    pub description: String,
}

pub struct Corpus {
    pub(crate) tools: Vec<Tool>,
    pub(crate) doc_tokens: Vec<Vec<String>>,
    pub(crate) doc_freqs: Vec<HashMap<String, u32>>,
    pub(crate) df: HashMap<String, u32>,
    pub(crate) avgdl: f64,
}

impl Corpus {
    pub fn len(&self) -> usize {
        self.tools.len()
    }
    pub fn is_empty(&self) -> bool {
        self.tools.is_empty()
    }
}

/// Build a searchable Corpus once. Reuse it across turns -- never rebuild per query.
pub fn index(tools: Vec<Tool>) -> Result<Corpus, &'static str> {
    if tools.is_empty() {
        return Err("index() needs at least one tool");
    }
    let doc_tokens: Vec<Vec<String>> =
        tools.iter().map(|t| tokenize(&format!("{} {}", t.name, t.description))).collect();
    let mut doc_freqs: Vec<HashMap<String, u32>> = Vec::with_capacity(doc_tokens.len());
    let mut df: HashMap<String, u32> = HashMap::new();
    for tokens in &doc_tokens {
        let mut freqs: HashMap<String, u32> = HashMap::new();
        for tok in tokens {
            *freqs.entry(tok.clone()).or_insert(0) += 1;
        }
        for tok in freqs.keys() {
            *df.entry(tok.clone()).or_insert(0) += 1;
        }
        doc_freqs.push(freqs);
    }
    let avgdl = doc_tokens.iter().map(|t| t.len()).sum::<usize>() as f64 / doc_tokens.len() as f64;
    Ok(Corpus { tools, doc_tokens, doc_freqs, df, avgdl })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn index_rejects_an_empty_tool_list() {
        assert!(index(vec![]).is_err());
    }

    #[test]
    fn index_builds_document_frequency_across_tools() {
        let corpus = index(vec![
            Tool { name: "a".into(), description: "fetch weather".into() },
            Tool { name: "b".into(), description: "fetch stock price".into() },
        ])
        .unwrap();
        assert_eq!(corpus.df.get("fetch"), Some(&2));
        assert_eq!(corpus.df.get("weather"), Some(&1));
    }
}
