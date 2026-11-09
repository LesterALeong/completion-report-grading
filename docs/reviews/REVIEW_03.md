## Verdict: APPROVED

Approval is for the unchanged offline candidate to proceed to native/authentic QA. Authentic subscription producer admission is still required before freeze, study calls and final QA/release.

Candidate: `e3b70d6e759697502ade5fce656eb084dc5c7ef7097adf0c8119be1c3295a094` (38 files). Scientific closure: `a075bf77f67ae31915f51b09e3d8e938f264e5effb82ee7621167a1cb8d5b6e5`.

## Issues Found

None requiring changes. REVIEW_02's sole blocking parser-consistency issue is closed.

## Evidence and scope

- Reopened every current candidate file against the preflight map and independently recomputed both closure roots. All match the identities above.
- Reopened candidate 02 archive, SHA-256 `8b9aa0f8d3c3e1e853b1e0549afe96b524deef4e5d2a96d7046b9a43a08c97b6`, and compared its preflight file map with the successor: exactly `study/codex_cli.py`, `tests/test_codex_cli.py`, `tests/test_export.py`, and `docs/PROJECT_LOG.md` changed; no removed files. Reused REVIEW_02's substantive inspection/evidence for unchanged files and the same SPEC A1-A12/repair plan.
- Inspected the entire production delta: both event envelopes and final structured outputs now use `evidence._json`, the same recursive duplicate-rejecting decoder as projection. Decode failures preserve envelope `protocol_invalid` versus final `invalid_output`; timeout/nonzero/custody precedence is unchanged. The dependency introduces no circular import or native-only public replay requirement.
- Independently executed exact archived `_validate_final` and `parse_event_stream` definitions with inert globals against the two original witnesses. Archived duplicate verdict and overwritten terminal-error envelopes both reproduce RED as `valid/PASS`. The successor returns `invalid_output` and `protocol_invalid` respectively, with no verdict; public projection replay returns the same statuses. No model calls occurred.
- Read the new regression matrix: both orders of verdict/reason/event-type/item-type/item-ID duplicate keys and nested duplicate keys are covered, with explicit nonzero-exit and timeout precedence assertions. Actual Windows inert runner -> private verifier -> exporter -> portable public reducer tests preserve failed-cell dispositions and zero valid grades for the two original witnesses.
- Independently ran `python -B -m unittest discover -v`: terminal exit 0, `Ran 66 tests in 10.642s`, `OK`, no skips. This includes eight actual Win32 Job tests, custody-fault cases, strict parser matrix, actual caller/resume verification and clean public replay CLI. Independently ran `python -B -m ruff check --no-cache --select F study tests`: exit 0, all checks passed. The host printed its truststore-injection diagnostic, but these offline commands reached successful terminal summaries without requiring network.
- Read the added 12 pre-outcome assumptions. They preserve the narrow authored-fixture scope, frozen treatment/metrics, single primary provider, missingness obligations and explicit authentic-admission limitation. No cases, reports, oracles, thresholds, mathematical analysis, budgets or model settings changed.
- Resource conclusion from REVIEW_02 remains applicable: 104 study + at most 16 canary = 120 attempts, serial 180-second inference deadlines, 8 MiB parse-input cap, at most 420,000 bootstrap draws for the four complete holdout comparisons. The prior native census measured about 68.1 GB RAM total and 30.1 GB available. This decoder substitution adds no new dataset or parallel compute load; the complete offline matrix finished in 10.642 seconds.

## Defect-Ledger Classes Checked

The authoritative ledger was read during REVIEW_02 in this same review session. Its unchanged-file findings remain applicable; the following names make the current gate explicit.

- LEDGER-01: clean — unchanged label/oracle exclusion, authored split and conditional claims; no trading look-ahead path.
- LEDGER-02/09/10: clean — full F lint, actual parser/import/caller paths and full test matrix.
- LEDGER-03: clean — unchanged aware UTC receipt timestamps, no broker clock.
- LEDGER-04: clean — duplicate-key failure hiding is now rejected; existing loud operational refusal and failure precedence remain covered.
- LEDGER-05/06: clean/n-a — named protocol counts/units unchanged; no financial figures propagated.
- LEDGER-07/20: clean — unchanged frozen acceptance/scientific gates and authorized transport-only repair.
- LEDGER-08: clean at offline phase — all native Windows cases execute; strict pacing/new HTTP/Git Bash paths are not involved.
- LEDGER-11/12: clean — exact repo cwd/module CLI composition and honest pre-outcome scope.
- LEDGER-13: clean — corrupt or missing evidence still blocks without public fallback.
- LEDGER-14/21/23/27/35: clean — exact archived/current maps, distinct identities and canonical digest roots reopened.
- LEDGER-15: clean for this repaired offline boundary — original RED and successor GREEN established using exact archived reader definitions and real successor runner/export/reducer. Authentic producer-derived canary evidence remains pending QA and cannot be replaced with these inert tests.
- LEDGER-16: pending authentic QA — subscription route, installed exact argv/configuration and both predicates must be admitted before freeze.
- LEDGER-17/32/47/49: clean for reviewed scope — unchanged native custody/cleanup paths and eight real fault tests pass; no runtime deletion before cleanup proof.
- LEDGER-28/29/36/37: clean — isolated task-owned tests, finite inspection deadlines, explicit cache configuration and no host `os.name` patching.
- LEDGER-30/31: clean at offline phase — authorization and backend-change refusal remain; no immutable model identity invented.
- LEDGER-33: clean — the previously inconsistent lifecycle representation is rejected consistently; hostile duplicate-key and end-to-end replay tests pass.
- LEDGER-34: clean — full terminal exit and test summary observed, not inferred from process disappearance.
- LEDGER-39: clean — timeout/nonzero/custody cause still takes precedence over malformed output.
- LEDGER-40/41/42/48: clean — authentic versus inert evidence remains distinct; unchanged exact tokenizer/cache workload and scientific/presentation separation; portable replay does not call Windows-only APIs.
- LEDGER-18/19/22/24/25/26/38/43/44/45/46/50: n/a for the same reasons recorded in REVIEW_02 — no corresponding broker, calendar, Git-commit fixture, renderer, replacement-release, production generated-program or binary-offset behavior.

## Positive Notes

The repair addresses the root cause with one shared decoder and a small production delta. Regression tests reproduce the ambiguous inputs, preserve operational failure precedence, and prove private/public agreement through actual runner/export composition. No scientific threshold or provider choice moved to accommodate an outcome.

## Gate Decision

PASS -> QA agent may proceed on this exact candidate. Full QA/release and freeze remain conditional on authentic subscription canaries, producer-derived evidence and privacy review. This is independent AI code review, not human peer review, authentic admission or a study result.
