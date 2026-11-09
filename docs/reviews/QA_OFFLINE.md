# Offline / Native QA Report

**Verdict: OFFLINE_PASS.** This approves the root operator to run only the two already-authorized outcome-blind subscription predicates as the next QA phase. It is not authentic transport admission, final QA, a protocol freeze, a study result, or course completion.

## Candidate identity and scope

- Reviewer-approved candidate: `e3b70d6e759697502ade5fce656eb084dc5c7ef7097adf0c8119be1c3295a094` (38 files).
- Scientific closure: `a075bf77f67ae31915f51b09e3d8e938f264e5effb82ee7621167a1cb8d5b6e5` (22 files).
- Independently recomputed both complete maps and canonical roots after QA: exact matches.
- Retained preflight record: `PASS`, `chatgpt_subscription` route recorded at `2026-11-09T16:50:42.654104Z`. This is the recorded preflight state, not a live assertion about authentication now.
- Current canonical private attempt inventory: 0 reservations, 0 receipts, 0 sidecars, no canary summary/run files, and no freeze. No authentic calls or study calls were made in this QA.
- The checkout has no Git commit (`HEAD` is absent); candidate binding therefore uses the reviewer-approved, complete preflight file map and digest, not a branch comparison.

## Acceptance criteria

| # | Criterion | Offline status | Evidence |
|---|---|---|---|
| A1 | Exact development/holdout counts, family split, and holdout labels | PASS | Retained preflight inventory: 8 development cases/2 families; 18 holdout/3 families; 12 defective and 6 correct, balanced 4/2 in each holdout family. `test_frozen_split_and_family_counts` passed. |
| A2 | Deterministic oracles, criterion coverage, defect witnesses, and label-free inputs | PASS | `test_oracle_covers_every_criterion_and_witnesses_each_defect` and `test_condition_payload_has_no_labels_or_sibling_markers` passed. |
| A3 | Condition parity, report proposition parity/framing, and count bounds | PASS | Retained preflight: report pair 81/83 words (2.41% difference) and 98/103 `o200k_base` proxy tokens (4.85%); tokenizer is explicitly proxy-only. Static source comparison confirms identical factual/evidence lines and decision rule; persuasive text explicitly recommends approval and PASS absent a criterion-level defect. |
| A4 | Fresh isolated, label-free, no-tool judge contexts and capture separation | PASS for offline design; authentic predicate pending | Prompt/parity, CLI config, environment filtering, tool-event rejection, marker handling, and custody paths are covered by the full suite. Authentic marker/tool behavior is gated on the two real predicates below. |
| A5 | Frozen alias/configuration, randomized schedule, no retries, and 120-turn cap | PASS for offline design | Protocol retains 104 study + at most 16 canary = 120 total; serial 180-second transport deadline. Budget/refusal/readmission tests passed. No attempt was reserved. |
| A6 | Exact attempt/receipt/raw joins, failure precedence, and process/directory custody | PASS for offline boundary; authentic evidence pending | Full evidence/runner/export tests passed; eight native Windows Job tests ran with no skips. Setup, launch, timeout, malformed output, missing/corrupt evidence, custody, and cleanup failures refuse a valid grade. |
| A7 | Separate grades, invalid/missing dispositions, paired analysis and missingness | PASS for offline design | Reducer tests for invalid/missing categories, verified prefixes, duplicate cells, and unattempted suffixes passed. No model observations exist. |
| A8 | Frozen estimands, intervals, bootstrap and wording gates | PASS for offline design | Protocol identity matches the approved closure; golden paired-count/missingness and finite Wilson-bound tests passed. No outcomes were used. |
| A9 | Frozen mitigation thresholds and no post-outcome tuning | PASS for offline design | Thresholds remain in the frozen protocol; code/spec identity matches reviewer approval. No outcomes or threshold changes exist. |
| A10 | Independent review/native QA followed by authentic two-predicate admission and final QA | PENDING authentic phase | `REVIEW_03.md` is APPROVED and this offline/native matrix passes. Authentic canary evidence and final QA remain outstanding by design. |
| A11 | Synthetic/public scope, sanitized projection replay, private raw custody | PASS for offline boundary | Export tests reject private sentinels and verify public projection replay. The real CLI smoke succeeded after private fixture deletion, without CLI/auth/profile access. There are no real producer outputs or public study results to release. |
| A12 | Course order and truthful user-owned activity status | PENDING course completion | Root-reported progress is 68%; the module is not complete. No human attendance or calendar commitment is claimed here. This is outside the offline software gate. |

## Test results and smoke execution

- Full suite: `python -B -m unittest discover -v` → exit 0; **66 tests passed, 0 failed, 0 skipped** in 12.114 seconds. This includes eight native Win32 Job/custody cases.
- Lint: `python -B -m ruff check --no-cache --select F study tests` → exit 0; “All checks passed!”
- Real portable CLI path: `python -B -m unittest tests.test_export.ExportIntegrationTests.test_real_export_public_replay_and_clean_cli -v` → exit 0; 1 test passed. It launches `python -S -B -m study analyze` in a subprocess from the repository root with `PATH` empty, `PYTHONPATH` removed, API route overrides removed, fake home/Codex profile paths, and the private evidence root absent. The public projection replay succeeds without CLI or authentication.
- Documented CLI help/no-side-effect checks: `python -B -m study {preflight,canary,freeze,run,analyze,export} --help` → exit 0 for all six commands. The mutating preflight command itself was not rerun because it writes the canonical private preflight receipt and this QA was authorized to write only this QA report; the retained preflight receipt and its full maps were independently reopened and checked.
- Build: N/A; no `pyproject.toml`, `setup.py`, `setup.cfg`, Makefile, or other project build target is present.
- Host startup diagnostic: Python printed `pip_system_certs: ERROR: could not inject truststore` with permission denied during lint/tests; the commands still exited 0 with complete pass summaries. This was an environment startup warning, not a project lint/test warning.

## Edge cases

- Duplicate JSON keys at nested/envelope/final boundaries: PASS; strict parser and runner/export parity tests passed.
- Empty, missing, corrupt, and invalid-UTF-8 evidence; tampered hashes/joins: PASS; evidence refusal tests passed without silently skipping files or falling back to public scope.
- Nonzero/timeout/malformed partial output, setup and launch failures: PASS; operational failure precedence and durable failure tests passed.
- Concurrent reservation/lock and exhausted/corrupt ledger: PASS; refusal tests passed.
- Native descendant cleanup, assignment/release/capture/cleanup faults, unrelated sentinel: PASS; all eight Win32 tests executed and passed.
- Public replay after removal of private data and in a scrubbed subprocess: PASS.
- Authentic producer event shape, subscription route at dispatch, marker non-echo, and real network/API failure: NOT TESTED in this phase; reserved for root-operated canaries and their retained producer captures.

## Defect-ledger verification

| Classes | Detector run and result |
|---|---|
| LEDGER-01, 07, 20 | Frozen split/oracle/input-parity tests and exact approved scientific map: CLEAN. |
| LEDGER-02, 09 | Ruff F rules exit 0; full imports and actual caller tests passed: CLEAN. |
| LEDGER-03 | Source trace confirms receipt timestamps originate from timezone-aware UTC; evidence parser rejects invalid timestamps: CLEAN by inspection and full suite. |
| LEDGER-04, 13, 33, 39 | Duplicate-key, corrupt/missing evidence, timeout/nonzero precedence, and failure-custody tests passed: CLEAN offline. Authentic producer failure behavior remains for authentic QA. |
| LEDGER-05, 06 | Budget/count constants verified against `study/protocol.json`; no financial figures changed or propagated: CLEAN / N-A. |
| LEDGER-08, 17, 28, 29, 36, 37, 47, 49 | Eight actual Win32 Job tests passed, covering bounded custody and task-owned cleanup faults: CLEAN offline. |
| LEDGER-10, 12 | Real runner compositions and clean public module CLI subprocess from repository-root cwd passed: CLEAN. |
| LEDGER-11 | README commands and public budget wording are current; parser/failure scope is recorded in spec/review. Grep also found stale internal `tasks/todo.md` statements saying 63 tests and review active. This QA cannot edit that file; update the progress note during closure. Historical REVIEW_02/03 counts remain dated evidence and should not be rewritten. |
| LEDGER-14, 21, 23, 27, 35 | Recomputed 38-file candidate and 22-file scientific maps/roots match exact approved identities: CLEAN. |
| LEDGER-15 | Archived-original RED and successor GREEN evidence is recorded in REVIEW_03; current native actual-caller, export and reducer tests pass. Authentic producer-derived replay remains pending. |
| LEDGER-16 | Exact subscription CLI route/configuration and both authentic predicates: PENDING; must be demonstrated before freeze. |
| LEDGER-30, 31 | Authorization refusal and backend identity handling tests passed offline; live route/backend facts remain pending canary: CLEAN offline / PENDING authentic. |
| LEDGER-32, 34 | Native lifecycle and actual command terminal exits observed; full suite terminal exit 0: CLEAN. |
| LEDGER-40, 41, 42, 48 | Offline fixtures remain distinct from producer evidence; analysis/source boundaries and portable replay tests passed: CLEAN offline. |
| LEDGER-18, 19, 22, 24, 25, 26, 38, 43, 44, 45, 46, 50 | N/A to this offline transport/parser repair, consistent with REVIEW_03 scope. |

## Guards

| Guard | Status | Evidence |
|---|---|---|
| All current tests pass | PASS | 66/66, no skips. |
| Build clean | N/A | No build command/configuration exists. |
| Lint clean | PASS | Ruff F exit 0. `ruff --version` resolved to 0.15.15. |
| Hooks alive | PASS | The configured local Python lint and shell-write guard hooks both exist. Private installation paths are omitted from this public report. |
| Security regression scan | PASS offline | No credential-shaped literals or user-input `eval` found. The sole `exec` is the deterministic oracle executing repository-stored synthetic case code. Existing tool/auth refusals are covered by tests. |
| Budgets/API and data integrity | PASS offline | Protocol remains 104/16/120; native and evidence tests preserve exact joins. No study data or output was written. |

One host diagnostic was reported above; there were no application warnings or failing commands. The independent reviewer is an AI reviewer; this report does not claim human peer review.

## Authentic QA handoff

The root operator may now run exactly the two authorized outcome-blind predicates once from the repository root:

```powershell
python -m study canary --authorize-subscription-calls --confirm-offline-review-and-native-qa
```

Require both producer-backed receipts to pass the exact predicates: structured response is `valid`, `PASS`, reason exactly `structured response available`; marker response is `valid`, `INDETERMINATE`, contains no tool event, and echoes no marker in either captured stream. Bind both to the unchanged candidate/scientific/config/predicate identities, the installed CLI and ChatGPT subscription route. Preserve complete private stdout/stderr, terminal and sidecar custody, hashes, byte counts, process/directory cleanup evidence; replay the actual captures through the production parser, verifier, runner receipt path, and public sanitizer/reducer. The two attempts consume two of the existing 16 canary allowance. Do not freeze or dispatch study cells before final QA reopens this evidence. Preserve every failed attempt; any readmission requires the existing explicit changed-premise path, fresh review/native QA, and remaining budget. Do not infer authentic admission or a study result from this OFFLINE_PASS.
