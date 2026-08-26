//! Ports acri/_synonyms.py: query-side alias expansion for compass.
//!
//! Applied to the query only, never the corpus -- expanding doc text would
//! let a tool's description quietly start matching a synonym it never
//! claimed, and would shift df/idf for every other tool too.

use std::collections::HashMap;
use std::sync::LazyLock;

static ALIASES: LazyLock<HashMap<&'static str, &'static [&'static str]>> = LazyLock::new(|| {
    HashMap::from([
        ("pr", &["pull", "request"][..]),
        ("meeting", &["event"][..]),
        ("rain", &["weather"][..]),
        ("raining", &["weather"][..]),
        ("storm", &["weather"][..]),
        ("warning", &["alerts"][..]),
        ("warnings", &["alerts"][..]),
        ("text", &["sms", "message"][..]),
        ("sharpen", &["upscale", "resolution"][..]),
        ("money", &["refund", "charge"][..]),
    ])
});

pub fn expand(tokens: Vec<String>) -> Vec<String> {
    let mut expanded = tokens.clone();
    for tok in &tokens {
        if let Some(extra) = ALIASES.get(tok.as_str()) {
            expanded.extend(extra.iter().map(|s| s.to_string()));
        }
    }
    expanded
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn expands_a_known_alias_and_leaves_unknown_tokens_alone() {
        assert_eq!(expand(vec!["rain".into(), "today".into()]), vec!["rain", "today", "weather"]);
    }
}
