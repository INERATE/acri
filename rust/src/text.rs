//! Ports acri/_text.py: tokenization shared by corpus (indexing) and compass
//! (scoring). Both sides must tokenize identically or BM25 scores against a
//! corpus the query was never consistently split against.

use std::collections::HashSet;
use std::sync::LazyLock;

static STOPWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    "a an the is are was were be been being am of in on at to for with and or
     but this that these those what which who whom me my you your it its we
     they do does did into from by about up down out off over under again
     further then once here there when where why how all any both each few
     more most other some such no nor not only own same so than too very s t
     can will just now if because as until while against between during
     before after above below"
        .split_whitespace()
        .collect()
});

/// Lowercase, strip apostrophes ("user's" -> "users", not "user" + a stray
/// "s"), split on runs of [a-z0-9], drop stopwords.
pub fn tokenize(text: &str) -> Vec<String> {
    let lower = text.to_lowercase().replace(['\'', '\u{2019}'], "");
    let mut tokens = Vec::new();
    let mut current = String::new();
    for c in lower.chars() {
        if c.is_ascii_lowercase() || c.is_ascii_digit() {
            current.push(c);
        } else if !current.is_empty() {
            tokens.push(std::mem::take(&mut current));
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens.into_iter().filter(|t| !STOPWORDS.contains(t.as_str())).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn drops_stopwords_and_splits_on_punctuation() {
        assert_eq!(tokenize("the user's PRs, and stuff"), vec!["users", "prs", "stuff"]);
    }
}
