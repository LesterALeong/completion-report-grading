# Completion report grading study

Can normative approval pressure change whether a grader accepts code with a visible criterion violation? This repository defines a bounded, exploratory replication and extension using static synthetic Python utility functions. It is a code-local obvious-defect floor probe, not a realistic patch benchmark. It compares report-free, neutral-report, approval-pressure, and bundled evidence-first mitigation conditions on identical task and code bytes.

The plan contains 8 development cases in 2 task families and 18 held-out cases in 3 disjoint task families. The family taxonomy is declared in `study/protocol.json`; disjoint labels do not establish independent algorithms or statistical independence. Each case is assigned all four conditions. The separately preregistered v2 run uses the installed local `qwen3.5:9b-q4_K_M` model on Ollama 0.40.14, with its manifest digest, template, defaults and request controls recorded. The artifact digest does not guarantee identical GPU execution.

The original Codex v1 route closed after two outcome-blind startup failures and an observability audit, before any study grading. Its [operability report](docs/CODEX_OPERABILITY.md) and [historical protocol](docs/protocols/CODEX_V1.md) preserve that record. Provider selection for v2 precedes all grading outcomes; this project is not a model comparison.

## Offline setup and commands

Python 3.12 and `tiktoken==0.13.0` are expected. Model-free tests use local fixtures and the tokenizer cache at `../_tmp/completion-report-grading/tokenizer-cache` by default, configurable with `TIKTOKEN_CACHE_DIR`. Inference preflight checks the existing local Ollama server at the fixed loopback endpoint and the already-installed model; it does not download models. Live transport targets Windows. Public replay uses the standard library and does not need Ollama, Codex, authentication or a GPU.

From this repository root, run:

```powershell
python -m study preflight
python -m ruff check --no-cache --select F study tests
python -m unittest discover -v
```

`preflight` checks fixture composition, local oracle truth, condition input parity, report wording, and the cached `o200k_base` token-count proxy. The tokenizer is a parity proxy; it is not asserted to be the backend's native tokenizer. The static report manipulation audit must separately confirm matched factual/evidence claims and materially stronger approval pressure before calls.

After independent code review and native inert QA, the operator may run the two outcome-blind local canaries during authentic transport QA:

```powershell
python -m study canary --authorize-local-model-calls --confirm-offline-review-and-native-qa --changed-premise "Separately preregistered local v2 after retained Codex operational failures"
```

Complete authentic QA, then freeze before running any study cells:

```powershell
python -m study freeze
python -m study run --split development --authorize-local-model-calls
python -m study run --split holdout --authorize-local-model-calls
python -m study analyze --split holdout --bundle ../_tmp/completion-report-grading --scope private_raw_verified
```

Each model transport attempt consumes a reserved turn. Before resuming, the runner verifies the complete frozen attempt prefix and retained capture evidence. A failed study attempt stops execution and is never retried. A failed pre-freeze canary can be readmitted only after an explicit changed-source/configuration repair, using `--changed-premise` and the same budget. Study calls are serial. Private reservations, raw stdout/stderr, finite failure diagnostics, and receipts remain below `../_tmp/completion-report-grading/`, outside each fresh judge directory and Git.

Create a sanitized bundle from verified private evidence, then record its returned manifest hash:

```powershell
New-Item -ItemType Directory -Path results -Force | Out-Null
python -m study export --private-root ../_tmp/completion-report-grading --target results/study
```

Export targets are create-only. Public replay uses that bundle and its independently recorded manifest byte hash:

```powershell
python -m study analyze --split holdout --bundle results/study --scope public_projection_replay --manifest-sha256 <published-manifest-hash>
```

Public replay checks sanitized producer-derived projections, frozen source/input identities, and exact public artifacts. It cannot independently prove unpublished raw bytes. Private verification requires those raw captures and never silently falls back to public projections.

## Validity and interpretation

The ground truth is stored separately from judge-facing task fixtures and is not included in prompts. Each direct local API request supplies one user message containing the task, criteria, static code and assigned report, with an empty tool list and no dispatcher. The worker captures the unmodified response body and separate HTTP facts. Tool-call output is rejected, and malformed structured output and operational failures remain separate missing observations. This is audited logical separation rather than host-level isolation.

The task-owned HTTP client runs under bounded Windows Job custody. The existing Ollama daemon remains outside that Job and is never killed. A timeout or uncertain daemon completion stops the campaign as operationally unknown. The model's keep-alive interval is 60 seconds.

The planned total is 104 study attempts plus at most 16 outcome-blind canaries, with a cumulative cap of 120 across both versions. The two failed Codex attempts remain charged, leaving at most 14 local canaries. Holdout contains 12 defective cases and 6 correct controls, balanced within each of three task families. Analysis uses valid paired observations, planned denominators, missingness bounds, finite-sample Wilson intervals, and a fixed-seed paired bootstrap with 10,000 resamples. Intervals are descriptive and conditional on these authored fixtures. A null or below-threshold result is not evidence that the effect is absent.

There are no study results in this repository yet. Do not describe simulated or offline fixture outputs as model results. Primary-source citations and final public-result claims require separate verification and independent review.

See the [v2 specification](docs/SPEC.md), [local architecture](docs/OLLAMA_ARCHITECTURE.md), [historical architecture](docs/ARCHITECTURE.md), [related work](docs/RELATED_WORK.md), and [interview guide](docs/INTERVIEW_GUIDE.md).
