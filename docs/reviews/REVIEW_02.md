## Verdict: CHANGES REQUIRED

Independent, model-free review of candidate `10c5d2e9c628800b2f56b8867c3423cd6b02f8f001ff29b1a00bcefd146a2061`, scientific closure `17e0689cbba81c9a8136dc13b5eef207c27354440b4d290aa84e659ec44459f1`. All 38 candidate file hashes were reopened against the private preflight map and matched. Reviewed the actual source, tests, SPEC A1-A12, repair plan, and previous RED review. No study/canary/model call, source edit, freeze, commit, or push was performed.

## Issues Found

- [BLOCKING] [study/codex_cli.py:146,182] The production event and final-output decoders use ordinary `json.loads`, which silently keeps the last duplicate object key. The public projection uses the duplicate-rejecting decoder in `study/evidence.py:64,336,378`. Consequently, the same captured bytes can be a valid private grade and an invalid public replay. Reproduced with a clean four-event lifecycle whose final text is `{"verdict":"FAIL","verdict":"PASS","reason":"checked"}`: `parse_event_stream(raw, 0)` returns `valid/PASS`, whereas parsing `project_stdout(raw)` returns `invalid_output`. Replacing the terminal event with `{"type":"error","type":"turn.completed"}` is also privately accepted as a valid PASS and publicly becomes `protocol_invalid`. This is an A6/A11 correctness defect: contradictory verdicts or an overwritten failure event can become a plausible grade, then export refuses at `PROJECTION_REPLAY_MISMATCH`. Reject duplicate keys at every nesting level in both production envelope decoding and final structured-output decoding, using semantics consistent with projection. Add tests for duplicate verdict/reason keys and duplicate envelope/item keys in both orders, exercising private replay and public export/projection. None may become a valid grade; retain existing timeout/nonzero/custody failure precedence. This is one parser-consistency repair, not a scientific protocol redesign.

## Verification and prior blocker closure

- Independently executed `python -B -m unittest discover -v`: exit 0, `Ran 63 tests in 8.600s`, `OK`, no skips. This includes all eight real Windows Job Object tests and actual inert runner/freeze/export/public-analysis/clean-CLI composition. Executed F-rule Ruff: exit 0, all checks passed. The environment printed a `pip_system_certs` truststore-injection diagnostic; these offline checks did not require network and reached successful terminal summaries.
- Prior blocker 1: caller signatures now agree; actual canary/study/resume compositions execute.
- Prior blocker 2: exact canary predicates, source/config/prompt bindings, retained failed attempts, changed-premise failed-canary readmission and budget checks are present. A stale successful admission safely refuses changed source/configuration instead of dispatching; this does not admit stale evidence. Readmission after an already successful admission is not implemented, but it does not defeat the required failed-canary recovery path.
- Prior blocker 3: orphan final, ordering, duplicate finals, tools, terminal errors and process-failure precedence are tested. The duplicate-key hole above remains in the strict parser boundary. Authentic producer compatibility remains a subsequent QA gate.
- Prior blocker 4: exact frozen schedule/input/config/source/receipt/sidecar joins and backend-change refusal now execute through the shared verifier; resume reopens the prefix.
- Prior blocker 5: assignment-before-release, timeout, lingering descendants, failed assignment/release, capture collision and failed cleanup-query paths execute against native Jobs. Unrelated sentinel processes survive; owned descendants are independently checked dead. Judge deletion requires proven custody.
- Prior blocker 6: private capture hashes, byte counts, bounded independent head/tail and finite failure facts are retained. Public projections remove raw diagnostics and distinguish public commitment replay from private raw verification.
- Resource arithmetic: 26 cases x 4 conditions = 104 study attempts; 104 + 16 canary allowance = 120 absolute. Serial inference deadlines are 120 x 180s = 21,600s (6 hours), plus bounded cleanup/inspection overhead. Four complete holdout bootstraps draw at most 10,000 x (12 + 12 + 12 + 6) = 420,000 values. Per-attempt retained parse input is capped at 8 MiB; even 120 such stdout captures total 960 MiB before object/projection overhead. The native memory census reported 68,065,943,552 bytes physical RAM and 30,093,606,912 available bytes. These authored fixtures and the nine-second offline matrix are feasible on this machine; no training/corpus load is present. Public replay loads bundle members together, so this conclusion concerns the frozen bounded campaign, not arbitrary enlarged external bundles.

## Defect-Ledger Classes Checked

- LEDGER-01: clean within this review — judge prompts exclude oracle/labels/sibling conditions; authored held-out families and conditional claims are explicit. No trading timing path.
- LEDGER-02: clean — full F lint and executed caller paths.
- LEDGER-03: clean — persisted operation timestamps use aware UTC; no broker clock logic.
- LEDGER-04: issue found above — overwritten event type can hide a failure. Native failures otherwise stop loudly.
- LEDGER-05: clean — call/time/size units come from named protocol/constants; no instrument sizing.
- LEDGER-06: n/a — no financial figures propagated; experiment counts derive from protocol/inventory.
- LEDGER-07: clean — unchanged scientific thresholds/cases/reports/statistical rules; repair plan limits transport changes.
- LEDGER-08: clean for offline native boundary — real Win32 tests passed; no strict pacing predicate, Git Bash/native CLI path conversion, or new HTTP path.
- LEDGER-09: clean — actual source inspected and full-file F lint rerun irrespective of write mechanism.
- LEDGER-10: clean — actual reserved-call/canary/study caller compositions execute.
- LEDGER-11: clean at this phase — documented module CLI and public replay exercised; authentic commands remain gated.
- LEDGER-12: clean — explicit repository working directory used.
- LEDGER-13: clean — missing/corrupt inventory/raw captures block; no private-to-public verification fallback.
- LEDGER-14: clean at offline phase — closure/config equality checked before dispatch; authentic CLI admission still required.
- LEDGER-15: issue found above at parser-to-projection composition. Authentic producer-derived fixture and actual canary evidence remain required during QA; inert fixtures do not satisfy that boundary.
- LEDGER-16: pending authentic QA — exact installed subscription route/argv must pass the two authorized predicates before freeze. This review does not claim that admission already occurred.
- LEDGER-17: clean — no imported runtime is deleted; judge cleanup follows custody proof.
- LEDGER-20: clean — transport repair scope and single-provider scientific contract preserved.
- LEDGER-21/23/27: clean — exact candidate map reopened; distinct review/scientific/admission identities and explicit files retained.
- LEDGER-28/36/37: clean — tests use isolated task-owned roots, explicit cache configuration and native platform branching, without mutating canonical freeze or patching `os.name`.
- LEDGER-29: clean for this scope — version/login inspection has finite deadlines; no installation/bootstrap occurs.
- LEDGER-30/31: clean at offline phase — subscription authorization flags required; exposed backend changes stop, absent backend identity is not invented.
- LEDGER-32: clean — native Job containment replaces direct-child/process-group inference and is fault-tested.
- LEDGER-33: issue found above — duplicate-key ambiguity admits a lifecycle representation the projection rejects.
- LEDGER-34: clean — exact terminal exit and complete unittest summary inspected.
- LEDGER-35: clean — canonical sorted-key JSON defines hash roots; file-byte map matches.
- LEDGER-39: clean — timeout/process/custody failure takes precedence over malformed partial stdout.
- LEDGER-40: clean — inert evidence is explicitly distinguished from authentic model/producer admission.
- LEDGER-41/42: clean — exact cached tokenizer workload is exercised; mutable presentation/review files excluded from scientific closure.
- LEDGER-47/48/49: clean for exercised native faults — acquired handles/processes owned within `finally`; assignment/release/query faults exercised on Windows; portable replay does not call Win32 APIs.
- LEDGER-18/19/22/24/25/26/38/43/44/45/46/50: n/a — no broker writer/market calendar/order recovery, test Git commit, external renderer, replacement governed release set, predecessor mutation, production generated program, Gateway callback or binary-offset path.

## Positive Notes

The repair is coherent and substantially closes the six original transport defects. Shared byte-bound evidence verification, conservative resume refusal, real descendant tests, and the clean public replay CLI are meaningful improvements. Scientific claims remain appropriately limited to authored code-local fixtures, approval framing and a bundled mitigation; no immutable backend weights or production-code generalization is claimed.

## Gate Decision

BLOCK -> Return the single parser-consistency issue to the implementer, then rerun the complete unchanged-candidate review/QA matrix. Authentic canaries belong after the offline review/native-QA gate, not before it. No actual producer admission, freeze, study validity or publication approval is conferred here.
