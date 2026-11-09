# Ollama v2 Offline / Native QA

**Verdict: OFFLINE_PASS** for the exact reviewer-approved candidate below. Root may proceed with the already-authorized two outcome-blind local-model predicate canaries. This does not pass authentic admission, freeze, study execution, publication, or human peer review.

## Candidate identity

- Independently recomputed 56-file candidate map: exact match; SHA-256 `0424be7750a715f632ef700df04d35cc5e393715ac19c81d5c9aa45b134beafd`.
- Scientific closure: 25 files; SHA-256 `d2c2572ebcf506a162687a318e1410df11c37547f09363ec4d217891ee7f4027`, exact preflight map match.
- Candidate archive SHA-256 `9b6b9e333dcb895c00f3a5d5620202c5a370f95287606ecee59fc639745bd87e`; every archived candidate member matched the approved map.

## Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Offline/native QA precedes model calls | PASS | Full model-free and inert-native matrix passed; no inference, freeze, or study call occurred in QA. |
| 2 | Frozen runtime/config identity | PASS offline | Static request, schema, runtime expectation, route, and source identities are bound to candidate/preflight. Authentic pre-dispatch recheck remains pending. |
| 3 | Outcome-blind admission canaries | PENDING next gate | No v2 canary ran. The exact two predicate calls remain the authorized next phase, with failures charged and admission stopped on any mismatch. |
| 4 | Strict response/failure classification | PASS offline | Decoder, duplicate/schema/tool/thinking, missing/false `done`, model mismatch, HTTP/API error, timeout, incomplete/oversize body, and custody tests passed against inert fixtures. |
| 5 | Raw custody and private/public replay | PASS offline | Actual runner → export → public-analysis integration passed in a scrubbed subprocess. Producer bytes are synthetic; authentic capture replay remains pending. |
| 6 | Split, conditions, and budgets | PASS | Golden continuity and protocol tests passed; inventory remains 8 development / 18 holdout, 104 study / 16 canary / 120 total. |
| 7 | Frozen estimands and interpretation | PASS offline | Scientific golden, paired-count/missingness, and finite-bound tests passed; no outcomes exist to interpret. |
| 8 | Privacy-reviewed public release | PENDING | No release was created or reviewed in this QA. |

## Test results and smoke path

- `python -m ruff check --no-cache --select F study tests` → exit 0, “All checks passed.”
- `python -m unittest discover -v` → exit 0; 101 tests, 0 failures, 0 skips. Six inert HTTP-worker cases and eight native Windows Job cases executed. The initial sandboxed run could not connect to its ephemeral loopback fixtures (six `PermissionError` failures); rerunning with loopback permission passed. No test contacted Ollama or called a model.
- All eight README CLI commands were invoked in help-only form and exited 0. Actual unauthenticated `canary` and `run` subprocesses each exited 2 at the explicit local-call authorization gate.
- `tests.test_export_v2.ExportV2IntegrationTests.test_runner_export_public_analysis_and_clean_subprocess` passed within the full suite. It exercises the real caller/export/reducer path and a `python -S -B -m study analyze` subprocess with `PATH` empty, `PYTHONPATH` removed, and private state absent, using inert producers.
- Build: N/A; no build configuration/command is present. Ruff 0.15.15 resolves; both configured hook scripts exist. A host `pip_system_certs` truststore-injection permission diagnostic appeared at Python startup; it did not affect command exits or test results.

## Edge cases, ledger, and guards

Empty, malformed, duplicate-key, non-UTF-8, wrong-model, tool/thinking, invalid completion, HTTP failure, partial/oversized response, timeout, request drift, tampered evidence, missing private raw data, failed custody, budget exhaustion, and unattempted-cell accounting are covered by passing tests. LEDGER-01/05/06/07/20 detectors ran through protocol/oracle/request/history/golden tests; LEDGER-02/09/34 through Ruff, imports, and the full suite; LEDGER-03/04/13/33/39 through timestamp/evidence and transport failure-precedence tests; LEDGER-08/32/47/49 through native Job and inert HTTP tests; LEDGER-10/11/12/15 through CLI/help, docs, composition, and clean-cwd subprocess checks; LEDGER-14/21/23/27/35 through exact map/archive reopening. LEDGER-16/30/31 authentic route/runtime predicates remain for the next canary boundary. Broker, renderer, installation, and Git-mutation classes are N/A to this offline task.

Security scan found no credential-like literals or user-input `eval`; the sole `exec` is the restricted synthetic-code oracle in `study/oracle_checks.py`. Hook checks, authorization refusals, and test/build/lint guards passed. The two existing Codex v1 canaries remain charged and byte-bound: `2a22e64d73ff4fc6826545dd436ae518` is `protocol_invalid`, `5f300311400440739acbd82b78e33478` is `operational_unknown`; neither has a grade. Inventory is 2 historical canaries, 0 study attempts, 0 v2 canaries; no v2 admission summary or freeze exists. No live failure injection or authentic producer proof was attempted. This is independent AI QA, not human peer review.
