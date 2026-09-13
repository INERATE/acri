# Research and product evidence review

Reviewed 2026-09-13 against the public five-page PDF, research landing page,
repository base `f708f6e`, and primary sources below. This is an initial review,
not an exhaustive literature search or proof of novelty.

## Assessment

ACRI is useful as an importable, dependency-free lexical capability resolver.
Its current mechanism narrows the schemas sent to an LLM; the LLM still selects
functions and generates arguments. Neither MCP nor conventional function calling
is bypassed. Product usefulness does not require a previously unknown algorithm.
Research should test a falsifiable contribution rather than describe product ambition.

Claude's suggested external evaluation, baselines and statistical reporting are
directionally sound. Its claim that a new method is the only path to a strong
journal is too categorical. A rigorous systems or empirical contribution can
also be research. Acceptance cannot be inferred from software quality or stars.
IEEE is a publisher, not a journal quartile; choose an actual journal and check
its scope and current category/year ranking before preparing its template.

## Corrections the current manuscript needs

| Location | Finding | Required correction |
| --- | --- | --- |
| II, related work | Missing direct retrieval literature | Discuss RAG-MCP and ToolRet. Distinguish When2Call's tool-call judgment task from retrieval ranking. |
| II, MCP proposals | SEP-1821 is described as static filtering | Its proposal adds a `query` parameter to `tools/list`; cite the issue directly, and do not equate closed status with implementation or adoption. |
| III-B, Eq. 1 | Correct inequality under a restricted comparison is treated as a universal policy | State warm-cache assumptions, cache pricing, prefix scope and eligibility. Include first-write cost, TTL, changed intent, retries and task success. |
| III-A/B, architecture | Resolve-once enforcement is not implemented by `run()` | `run()` resolves each invocation; the daemon sends the last message only. Separate design intent from implemented behavior. |
| III-B, discovery | Discovery metadata is treated as complete recovery | `find_more_tools()` returns names/descriptions. Show how a newly found tool becomes callable with its schema and how execution results return to the model. |
| IV-A, recall | Synonyms were added after inspecting misses | Treat the existing fixtures as development data; freeze aliases before testing on unseen queries/catalogs. |
| IV-B, accuracy | Scoring checks the first tool name only | Label this tool-name selection. Evaluate argument correctness, clarification, abstention, multiple calls and execution success separately. |
| IV-B, production match | Assay omits the always-offered escape hatch | Add a production-equivalent arm or explicitly state this difference. |
| IV-C/D, noise | A two-point movement is called a noise floor | Table IV shows naive 72 to 84 between runs 2 and 3, and queries changed. Neither this comparison nor one-query granularity estimates stochastic uncertainty. |
| IV-C, arithmetic | Four- and two-point gaps are both called smaller than a two-point noise floor | Correct the comparison; remove the unsupported floor entirely. |
| IV-C, latency | Text says mean while `assay/report.py` prints median | Recover run records and label the statistic actually used. Do not infer cache state from latency. |
| Reproduction | Script names are provided without durable experimental records | Record commit, fixture hash, exact model/deployment, parameters, timestamps, errors and raw per-query outcomes. |

The local recall/scale scripts reproduced their existing fixture counts during
this review. That confirms reproducibility of those deterministic fixtures, not
generalization. No paid model evaluation was rerun during this review.

The landing page contains additional unsupported claims: the resolver is called
a zero-copy inverted index although the inspected implementation scans all tools;
reducing tool count is equated with reducing serialized schema tokens; a resolve-once
law is described as enforced. Correct those independently of the PDF. The website
and PDF were downloaded for review; their deployed contents have not been edited.

## A better cache comparison

For a prefix of C tokens over T eligible calls, let w be the first-write price
multiplier and d the cache-read multiplier, relative to uncached price p.
Assuming one write and all subsequent reads hit:

```
full retained prefix:  C * p * (w + (T - 1) * d)
new uncached subset:   T * r * C * p
subset is cheaper:    r < (w + (T - 1) * d) / T
```

This is a conditional derivation, not a new research result. The paper's `r < d`
is the warm-call comparison/asymptotic threshold under these assumptions. A
retained subset, partial hits, missed cache eligibility, lost conversation-prefix
reuse, retrieval overhead and task failures need separate terms. Use observed
cache usage rather than assuming every stable request gets a discount.

Provider documentation explicitly allows caching tool results as part of message
history, so statements that tool results are *never* cached are also incorrect.

## Product and research sequence

1. Close correctness defects and document supported scope. Keep the core small.
2. Measure catalog scaling, then compare posting-list retrieval against a fixed
   full-scan reference. Ranking equivalence is testable; accuracy improvement is a
   separate question and must not be claimed from faster execution alone.
3. Evaluate held-out ToolRet tasks with BM25, dense and hybrid baselines under
   comparable retrieval budgets. Keep the synthetic suite as regression coverage.
4. Evaluate call/ask/abstain behavior with When2Call and multi-turn task completion
   with an appropriate interactive benchmark such as tau-bench. Public benchmarks
   have their own synthetic elements and limitations; public does not mean unbiased.
5. Study adaptive discovery as a hypothesis: can a bounded policy preserve task
   success while reducing offered schemas and total measured cost? Compare against
   all-tools, fixed subsets, per-turn retrieval and provider-native discovery where
   supported. Include ablations, failures and repeated paired runs.

Do not guarantee a future result. A negative result that identifies when retrieval
hurts can still be useful research. Repeating deterministic BM25 on the same input
does not establish uncertainty in retrieval quality; evaluate varied held-out tasks.
For stochastic model comparisons, preserve paired per-query outcomes and resample
at the query/session level rather than treating repeated calls as independent tasks.

## Author block and attribution

For a single author genuinely doing the work at INERATE, a simple draft is:

```
Piyush Sharma
INERATE, [actual city], India
piyush@inerate.com
```

Use the exact journal template; the city placeholder must be replaced before
submission. One affiliation does not need artificial a/b markers. Two emails do
not imply two affiliations; choose a durable corresponding-author address and
provide an alternate in submission metadata if supported. Put the repository link
in code/data availability or reproduction, not in a crowded author line.

Affiliation describes where the work was done, not a reward to allocate. A college
does not become a coauthor merely because its faculty gave feedback, but do not
misrepresent actual institutional involvement, support or qualifying human
contributions. Solo authorship does not remove the duty to cite prior work.
IEEE requires disclosure of AI-generated article content, including code, where
applicable; editing/grammar assistance has different guidance. Follow the current
policy and describe actual use. An AI tool is not a human coauthor.

## Primary sources

- [ACRI paper](https://research.inerate.com/assets/acri_capability_resolver_paper.pdf)
- [ACRI research page](https://research.inerate.com/acri)
- [RAG-MCP](https://arxiv.org/abs/2505.03275)
- [ToolRet official implementation and datasets](https://github.com/mangopy/tool-retrieval-benchmark)
- [When2Call, NAACL 2025](https://aclanthology.org/2025.naacl-long.174/)
- [MCP SEP-1821](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1821)
- [Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [tau-bench](https://arxiv.org/abs/2406.12045)
- [IEEE article structure](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/)
- [IEEE authorship and ethics](https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/ethical-requirements/)
- [IEEE AI-content policy](https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/)
