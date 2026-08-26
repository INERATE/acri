//! Black-box parity tests against acri-core's public API, mirroring the
//! Python original's tests/test_compass.py -- same fixture, same five cases,
//! so behavior parity is actually verified, not assumed.

use acri_core::{index, resolve, Tool};
use std::collections::HashSet;

fn fixture_corpus() -> acri_core::Corpus {
    index(vec![
        Tool {
            name: "github_get_pull_request".into(),
            description: "fetch pull request details from github by number".into(),
        },
        Tool {
            name: "github_merge_pull_request".into(),
            description: "merge an approved pull request into the default branch".into(),
        },
        Tool { name: "postgres_query".into(), description: "execute sql against a postgres database table".into() },
        Tool { name: "weather_forecast".into(), description: "fetch forecast temperature for a city location".into() },
    ])
    .unwrap()
}

#[test]
fn resolve_excludes_tools_with_no_shared_term() {
    let corpus = fixture_corpus();
    let resolved = resolve("merge the github pull request", &corpus, 4);
    let names: HashSet<&str> = resolved.iter().map(|r| r.tool.name.as_str()).collect();
    assert_eq!(names, HashSet::from(["github_get_pull_request", "github_merge_pull_request"]));
}

#[test]
fn resolve_ranks_the_stronger_match_first() {
    let corpus = fixture_corpus();
    let resolved = resolve("merge the github pull request", &corpus, 4);
    assert_eq!(resolved[0].tool.name, "github_merge_pull_request");
}

#[test]
fn resolve_confidence_is_relative_to_best_match() {
    let corpus = fixture_corpus();
    let resolved = resolve("merge the github pull request", &corpus, 4);
    assert_eq!(resolved[0].score, 1.0);
    assert!(resolved.iter().all(|r| r.score > 0.0 && r.score <= 1.0));
    let scores: Vec<f64> = resolved.iter().map(|r| r.score).collect();
    let mut sorted_desc = scores.clone();
    sorted_desc.sort_by(|a, b| b.partial_cmp(a).unwrap());
    assert_eq!(scores, sorted_desc);
}

#[test]
fn resolve_returns_nothing_for_pure_noise() {
    let corpus = fixture_corpus();
    assert!(resolve("xyzzy plugh", &corpus, 5).is_empty());
}

#[test]
fn resolve_respects_k() {
    let corpus = fixture_corpus();
    assert_eq!(resolve("pull request", &corpus, 1).len(), 1);
}
