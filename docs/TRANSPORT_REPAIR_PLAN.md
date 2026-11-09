# Transport repair plan

**Gate: PASS for one consolidated offline repair.** This plan supersedes only the transport, custody, identity, and replay portions of `docs/ARCHITECTURE.md`. It does not admit the archived RED candidate, authorize this agent to make model calls, or change the scientific method. The root operator retains the already authorized subscription-only execution role.

## Authentic startup amendment

The first authorized structured canary returned the requested constant response with clean native custody, but a preceding provider error item reported that Code Mode's host was disabled. Admission stopped. This consumed one canary reservation and no study cell. The original receipt, capture and source identity remain unchanged; its initial conservative `protocol_invalid`/tool flag is not evidence that the model invoked a content tool.

The bounded recovery plan uses the documented nested `features.code_mode.enabled=false` configuration instead of the scalar `--disable code_mode`, while keeping `code_mode_host` disabled. The installed model catalog declares `code_mode_only`; whether nested configuration prevents bootstrap remains an unresolved operability question. A feature-list result alone cannot establish it. See the [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

Add failure-only parsing for the authentic `item.type=error` shape and a sanitized producer-derived regression. A provider error must remain operationally unknown even if a later final says PASS; it is distinct from a content-tool invocation. Private/public replay must agree. Then obtain fresh review/native QA and use the existing explicit changed-premise readmission path. If the same bootstrap failure recurs, close this configuration path. Host enablement requires a separate capability audit; it must not be used merely to suppress the error. A different provider requires a separate preregistration based on operational failure, with no substitution inside this protocol.

## 1. Spec review and interpretation

The six blockers in `docs/reviews/REVIEW_01.md` are reproducible design gaps in the current implementation. `_execute_reserved_call` lacks `identity_before` although `run_split` supplies it and its own body references it. `run_canaries` accepts any valid verdict and trusts an unbound PASS summary. `parse_event_stream` accepts an orphan final. `_receipt_matches_cell` checks CLI digest syntax rather than frozen equality and omits process custody. `subprocess.run(timeout=...)` establishes neither descendant containment nor bounded inherited-pipe cleanup. Native output is discarded and broad exception handling removes the failure cause.

Preserve the existing reports, tasks, oracles, prompts, model alias/effort, schedule, statistics, thresholds, and split. The canonical allowance is `study/protocol.json:turn_budget`: 104 study attempts, at most 16 pre-freeze outcome-blind canary attempts, 120 overall. An attempt is consumed by durable reservation before transport, including a launch failure. No failed study cell is retried or replaced. There have been no real model calls at the time of this repair request.

Two specification clarifications are necessary and do not change the method:

1. Offline code review and native inert QA precede the root's authentic canaries. Authentic producer admission is then completed during QA and required for final QA/release and freeze. Do not require authentic canary evidence before allowing that same canary. Replace the misleading final-QA confirmation wording with an explicit offline-review/inert-QA prerequisite.
2. Keep raw inference stdout/stderr private with useful diagnostics. Publish only a deterministic sanitized producer-derived projection and portable evidence manifest. Public replay cannot prove the contents of unpublished raw bytes; it verifies exact public artifact commitments, lifecycle/classification replay, and the recorded private-to-public verification attestation. Label that boundary explicitly. Never silently replace a requested full private verification with public-only verification.

No unresolved technical preference blocks implementation. If the installed CLI cannot support the required no-tools/configuration contract or authentic lifecycle, stop as BLOCKED before study calls; do not broaden the parser or change settings after looking at grading outcomes.

## 2. Files affected

| File | Action and reason |
| --- | --- |
| `study/codex_cli.py` | Modify argv/config inspection, strict event parser, transport result contract, private capture and native supervisor integration. |
| `study/windows_job.py` | Create a small Windows-only Job Object adapter with bounded task-owned process custody; lazy import from transport. No process census framework. |
| `study/transport_worker.py` | Create the tiny inert-until-released wrapper; launch CLI only after reading the parent's release payload. |
| `study/evidence.py` | Create one shared, portable identity/receipt/projection verifier used by runner and reducer; standard library only. Keep schemas and deterministic sanitization here rather than duplicating checks. |
| `study/runner.py` | Modify reservation/receipt lifecycle, signatures, canary predicates/readmission, separate identities, freeze binding and resume verification. |
| `study/analysis.py` | Modify evidence ingestion/reconciliation to require verified frozen artifacts and replay; leave all statistical functions unchanged. |
| `study/__main__.py` | Modify command arguments to identify private versus public evidence bundles and explicit pre-freeze changed-premise canary admission; update prerequisite naming. |
| `study/protocol.json` | Modify only supported web-search disablement and explicit canary predicate/config definitions if stored as data. Preserve the scientific design and all allowance values. |
| `tests/test_codex_cli.py` | Replace mock-only transport assumptions; add strict lifecycle, failure precedence, diagnostics, configuration and projection tests. |
| `tests/test_runner.py` | Add actual runner-call composition, admission/readmission, reservation/failure, identity and resume mutation tests. |
| `tests/test_analysis.py` | Require frozen evidence bundles; add exact identity/cleanup/backend/hash mutation and public replay tests while retaining statistical checks. |
| `tests/test_windows_job.py` | Create native inert process-chain success/timeout/cleanup-fault tests, including an unrelated sentinel process. |
| `tests/fixtures/transport_helper.py` | Create a model-free child/descendant producer usable by the real supervisor, with selectable valid/malformed/failure streams and inherited-handle scenarios. |
| `tests/test_protocol.py` | Update expected supported configuration and verify preserved budgets/prompt/case identities. |
| `docs/SPEC.md` | Clarify A4/A6/A10/A11 custody, evidence and two-phase QA semantics without changing estimands or gates. |
| `docs/ARCHITECTURE.md` | Link this superseding repair and remove contradictory instructions to discard all native diagnostics. |
| `README.md` | Document exact offline lint/tests, two-phase QA, canary attempts, freeze and portable replay commands. Presentation edits must not invalidate frozen scientific identity. |
| `.gitattributes` | Ensure exact-byte hashed source and any retained JSON/JSONL fixtures have stable LF checkout bytes; retain existing governance where already sufficient. |
| `tasks/todo.md` | Track this consolidated repair and review/QA evidence. |
| `tasks/lessons.md` | Create/update the concrete boundary-test lesson for this correction. |

Runtime artifacts are created below the existing `../_tmp/completion-report-grading/` private root: create-only reservations, receipts, native captures, canary attempt/admission records, native QA receipts, freeze and export custody records. Public replay artifacts belong in a task-created `results/transport-admission/` or study-result bundle only after root privacy review. These are artifacts, not a new harness. No deletion of RED archives, failed attempts, or prior reviews is permitted. No new dependency or dependency installation is needed.

## 3. Ordered implementation plan

### Step 1: Define one identity and evidence contract

In `study/evidence.py` and `runner.py:candidate_files`, distinguish:

- Scientific closure: exact `study/` source/data/config/schema/prompt bytes and `docs/SPEC.md`, excluding caches. Hash its complete sorted path-to-digest map with existing `canonical_json`/SHA-256 conventions. This includes transport/parser/analysis implementations; a change to them invalidates admission. Do not include README, tasks, results, or review documents in this closure.
- Review-candidate closure: exact code, tests, applicable spec/plan and test-fixture identity recorded by independent review/QA. It can be broader and is not the ongoing scientific freeze equality check.
- Freeze digest: digest of the complete canonical, create-only freeze document, with no self-referential digest field. Freeze contains exact scientific map/digest, protocol/configuration, ordered schedule, admitted CLI identity, canary predicate definitions/digest and successful admission evidence digests.

Every reservation, receipt and export must join its exact slot/attempt to that closure, CLI version/binary/config digest, requested alias/effort, prompt/input hash map and applicable freeze or pre-freeze admission digest. Do not compare two self-reported digests without reopening the referenced bytes. Preserve UTC-aware timestamps. Use exact key maps, types and enumerated statuses, rejecting booleans where integers are required.

### Step 2: Implement bounded native process custody

In the new `windows_job.py`, use standard-library `ctypes` Win32 handles and explicit error checks. Parent owns a Job configured with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and no breakaway. Launch only the task-owned Python wrapper, with hidden-window flags, which blocks reading a bounded start payload on stdin. Assign that wrapper to the Job before sending any payload. On assignment failure, kill/wait only that inert wrapper and refuse; it has not launched Codex. Close all handles deterministically.

The wrapper in `transport_worker.py` must import and start safely from its absolute path under a clean environment; it must not depend on repository cwd or PYTHONPATH. After release, it starts the exact argv using `shell=False`, child-only environment, approved judge cwd, prompt stdin, and private stdout/stderr file handles outside the judge cwd. Its children inherit Job membership. No model command may appear before the release read. Do not allow the Job handle to be inherited by the wrapper. The wrapper writes a small private terminal record containing the actual CLI return code and finite launch/write failure information; parent completion alone is not CLI success.

Use a single monotonic inference deadline and a separate fixed cleanup deadline. Files replace stdout/stderr pipes so descendants holding handles cannot hang parent `communicate`. At timeout or supervisor error, call `TerminateJobObject`; wait/query active process count with a finite deadline. Require Job ActiveProcesses=0 before successful teardown, including normal CLI completion. A lingering child, failed query, timeout, forced cleanup, or unresolved custody is operationally unknown and stops the run even if a valid final was already written. A timeout remains operationally unknown when captured stdout ends in malformed JSON. Persist owned wrapper/CLI/observed descendant IDs and phase facts privately; Job membership is the authoritative containment proof. Never kill processes by image name, scan user processes for deletion, or use `taskkill` globally.

Handle parent exceptions before/after release, wrapper death, CLI launch failure, descendant exit races, and capture/terminal-record read faults. Keep required cleanup attempts bounded. Do not delete a judge directory while Job absence is unproven. A directory cleanup failure is recorded separately and invalidates acceptance. On non-Windows, live execution refuses explicitly; imports, parser, reducer and public replay remain usable.

### Step 3: Preserve diagnostic custody and strict lifecycle parsing

In `codex_cli.py:ProcessResult`, carry finite `failed_step`, `last_completed_step`, `fault_code`, timeout/exit/cleanup facts, raw-file digests/byte counts, bounded head and tail, and explicit truncation. Keep useful sanitized exception class/message privately; never dump environment, auth files or login output. Bound each diagnostic slice in raw bytes independently and retain a terminal-only sentinel in the tail. Large streams may be read incrementally; never read an unbounded stream into memory merely to print it.

Implement parser state transitions in `parse_event_stream`: exactly one thread start, one turn start, allowed reasoning/message items while the turn is active, exactly one completed final agent message, and exactly one successful terminal turn completion. Require supported item IDs/lifecycle relationships when authentic producer evidence exposes them; do not invent mandatory fields absent from that evidence. Reject orphan finals, duplicates, completion-before-start, content after terminal, unknown/tool events and malformed envelopes. Allow only producer-admitted optional metadata, never a broad permissive fallback. A clean lifecycle with schema-invalid final is `invalid_output`; missing/incomplete lifecycle without process failure is operationally unknown; forbidden/malformed event topology is `protocol_invalid`.

Apply failure precedence explicitly: timeout, nonzero/unknown CLI exit, terminal failure/error or unresolved process custody yields `operational_unknown`, regardless of truncated malformed stdout. Retain independent protocol-violation flags even when operational status takes precedence. With clean successful process custody, protocol violations precede final-schema validation. Only the fully clean route may emit `valid` plus a verdict. Multiple backend identities in a stream are contradictory; absence is recorded as unexposed, not inferred from the alias.

Remove unnecessary `--ignore-rules` from argv and configuration manifest. Keep read-only sandbox and the current normal safety boundary. Confirm supported explicit `web_search="disabled"` configuration from installed capabilities without a model call; include it in the effective config digest, or BLOCK if the required restriction cannot be enforced. Preserve the subscription environment filter, fresh contexts and all current no-tool controls. Put finite bounds on version/login/help subprocesses too; they do not consume model turns but cannot hang preflight.

### Step 4: Repair runner composition and immutable attempt accounting

In `runner.py:_execute_reserved_call`, add a consistent keyword-only `identity_before` contract and update every caller. Complete side-effect-free validation before reservation. Once reserved, use one outer try/finally covering judge creation, marker staging, capture setup, dispatch, process cleanup, directory cleanup and receipt persistence. A setup exception after reservation still produces an explicit terminal failure receipt; if persistence itself fails, leave the create-only reservation consumed and block resume. Never fabricate an empty successful receipt in a broad exception handler.

Retain create-only per-attempt reservations and terminal receipts. Serialize execution with a task-local create-only operator lock so separate runner processes cannot race global allowance counting. An existing/stale lock blocks rather than being silently reclaimed. Verify reservation inventory and counts before each new attempt. Failed/unreadable/corrupt inventory is BLOCKED, not an empty ledger. Reservation counts are authoritative, including attempts missing receipts.

In `run_canaries`, bind predicate definitions, scientific closure, CLI/configuration, requested model, concrete prompt, private marker digest and evidence hashes. The structured canary requires `valid` with verdict PASS and its requested exact reason. The marker canary requires `valid` with verdict INDETERMINATE, no tool event, no marker leakage in either captured output, and clean process/directory custody. A valid FAIL/PASS on the wrong canary is a failed predicate. Never infer predicate success from status alone.

Use unique pre-freeze canary attempt IDs. Preserve failed attempts and summaries unchanged. Readmission requires an explicit changed-premise reason plus old/new configuration or source identity and the relevant repair, before dispatch, all within the same 16/120 caps. Repeating unchanged failure has no admission path. A successful admission references the exact two successful predicate receipts for the same scientific/configuration identity; only those predicates are required, not a new study or extra scenarios. A stale PASS summary is rejected on any mismatch. No canary readmission after freeze.

### Step 5: Make freeze, resume and reducer consume the same verifier

In `runner.py:freeze_protocol/_load_verified_freeze/run_split`, replace ad hoc existing-receipt trust with the shared verifier. Freeze must reopen canary evidence and validate predicates, configuration and source equality. The run must validate the entire persisted attempt/receipt prefix against the frozen ordered schedule before dispatch, including duplicates, unexpected slots, missing consumed receipts and prior failure states. It must refuse drift rather than find another slot to run. Existing valid slots are skipped only after full evidence verification; study failure blocks continuation and never creates a retry.

For each study receipt, require exact freeze digest, schedule slot, scientific map/digest, admitted CLI/configuration, requested alias/effort, complete prompt/input map, reservation relationship and count/cap validity. Verify actual terminal process state, no timeout/forced cleanup, Job ActiveProcesses=0 and judge cleanup true for a valid grade. Replay classification from the bound raw stream locally and require equality of status, verdict, reason/projection and backend facts. Establish the first exposed backend identity and stop on a conflicting exposed identity, including across resumed holdout calls; report unexposed identities honestly. Do not use arbitrary receipt directory iteration to choose an expected identity. Preserve missing/unattempted planned cells as explicit operational unknowns in analysis.

In `analysis.py:load_receipts/reconcile/analyze`, require an explicit verified evidence bundle rather than loose syntactically plausible dictionaries. Remove silent skipping of malformed/unreadable JSON. Bundle-level custody failure yields an explicit BLOCKED analysis with diagnostics; trustworthy known failed/missing study cells still enter the existing missingness accounting. Duplicate/contradictory cell records cannot produce valid grades. Keep the statistical calculations and practical thresholds untouched.

### Step 6: Export deterministic safe public replay

In `evidence.py`, build public projections with an allowlist of event type, safe item lifecycle identifiers normalized to local ordinals, exposed safe backend identity, allowed final structured content and sanitized lifecycle/failure metadata. Drop account/thread IDs, paths, arbitrary event metadata, raw stderr and auth information. Apply deterministic path/identifier sanitization to final reasons and bounded public failure codes. Reject forbidden sensitive content rather than broadly publishing unrecognized fields. Record original raw SHA/byte counts as commitments, projection SHA and a private verification record tying the deterministic transform to the retained raw bytes. Export no private absolute paths.

The public bundle contains the scientific freeze/map, exact schedule/protocol, admission manifests, reservation/receipt projections, event/final projections and their hash manifest. Public analysis reopens those files, verifies their exact hashes/joins, and replays lifecycle/classification from the sanitized producer-derived projection. It does not require the operator's installed CLI or private paths. Its output states `public_projection_replay` verification scope; private execution uses `private_raw_verified` and refuses missing raw bytes. Neither scope may be silently substituted for the other. Explain that raw-byte equality is independently auditable only by an authorized private verifier; public hash commitments alone are not that proof.

### Step 7: Review one unchanged successor and complete QA

Run the full offline matrix and lint before independent review; fix a consolidated report as one batch. Require review PASS on the same source/tests/spec identity used by native inert QA. The root then runs only the two existing authentic outcome-blind predicates during QA, retaining full private captures and generating sanitized producer-derived fixtures. Replay those exact captures and projections through production reader, runner receipt writer and reducer. Reconcile authentic event shape with the admitted parser contract; if unsupported, retain the failed attempt, repair offline, and obtain fresh review/native QA before explicitly changed-premise readmission within budget. Do not silently tune the parser around grader outcomes.

Final QA binds both offline/native and authentic admission evidence. Freeze only after it passes. No model turn is needed to implement or run inert tests, and no study case is added. No commit/push is part of this architecture-only task.

## 4. Existing patterns and conventions to retain

Confirmed from source: the package uses standard-library modules, frozen dataclasses in `codex_cli.py`, `Path` paths, `canonical_json` and SHA-256 in `protocol.py`, UTC-aware `runner.utc_now`, create-only JSON writes, deterministic `ordered_schedule`, and `unittest` with bounded temporary directories under `TASK_TMP`. Retain these patterns. Keep all model transport serial and all judged inputs confined to the existing prompt builder. Existing Wilson, within-family paired bootstrap and missingness logic in `analysis.py` remain authoritative.

The current tests predominantly patch `subprocess.run` or call helpers; they do not prove the caller composition. Extend tests through `run_canaries`, `run_split`, the CLI entrypoint and the real native supervisor using the inert helper. Mocks may inject faults at explicit boundaries but must not bypass the verifier whose behavior is being tested.

Two valid custody approaches exist: native suspended creation followed by Job assignment/resume, or the blocked wrapper assigned before payload release. Recommend the blocked wrapper: it works with Python's ordinary subprocess API, avoids private subprocess thread-handle reliance, and is simple to inspect. Both require equivalent native Job and descendant evidence. Post-launch assignment of an already-running CLI and PID polling are insufficient substitutes because descendants can escape the assignment race.

## 5. Risk assessment and defect-ledger exposure

**Breaking change risk: medium.** Internal receipt schemas and analyze arguments intentionally become stricter; old synthetic dictionaries will fail. No real outcomes currently need migration. Preserve RED artifacts rather than converting them into admitted evidence. New receipts must carry a schema version and unknown versions must refuse.

**Performance:** model calls remain serial and unchanged in count. File-backed streams and incremental hashes bound memory. Supervisor waits, CLI inspection and cleanup all have finite deadlines. A create-only lock prevents concurrency races. Do not add generic resource monitoring, framework infrastructure or a polling process census.

**Security:** only the subscribed route is allowed; no API key fallback. Private raw output stays outside Git and judge cwd. Child environment and handles are minimized. Parent Job containment addresses task process cleanup, not complete OS data isolation. Review sanitized exports for private identifiers and judge-inaccessible oracle material. Live transport is Windows-only; replay stays portable through lazy imports.

The operator's local defect ledger was read. Applicable classes and prevention are:

| Class | Prevention required by this plan |
| --- | --- |
| LEDGER-01 leakage | Unchanged held-out cases/prompts; no grading outcomes used for repair; judge context and tool/marker predicates remain mandatory. |
| LEDGER-02 undefined names | Ruff F rules plus actual canary/study caller composition catches `identity_before` and runtime-only errors. |
| LEDGER-03 timezone | Preserve UTC-aware receipt times; reject naive timestamps; use monotonic deadlines. |
| LEDGER-04 silent external failure | Durable finite failure step/class, complete private capture custody, CLI return code, timeout precedence, strict terminal lifecycle and authentic canary proof. |
| LEDGER-05 contextual constants | Derive allowance/config values from protocol; name fixed diagnostic/cleanup bounds once with units, never conflate inference deadline and cleanup budget. |
| LEDGER-06 source of truth | One scientific closure/freeze and exact source maps; no copied CLI/config/schedule identity declarations trusted without equality joins. |
| LEDGER-07 moving gates | Preserve A1-A12 scientific predicates/thresholds and RED evidence; review unchanged consolidated candidate. |
| LEDGER-08 Windows traps | Real Job-assigned wrapper/helper/native paths with spaces, child/descendant cleanup and unrelated sentinel preserved. |
| LEDGER-10 cross-file signature drift | Search every `_execute_reserved_call`, `ProcessResult`, parser and `analyze` caller; exercise production compositions and documented entrypoints. |
| LEDGER-11 doc/code drift | Update commands and two-phase QA wording; execute documented offline commands through real clean subprocess entrypoints. |
| LEDGER-12 cwd | All commands and generated files anchored to this repo/task root; worker absolute-path clean launch tested. |
| LEDGER-13 unreadable versus absent | Corrupt/unreadable reservations, receipts, freeze and captures block loudly; they never become an empty ledger. |
| LEDGER-14 provenance | Exact candidate/freeze/CLI/config/schedule/evidence joins, complete reviewed file inventory and stable hashed checkout bytes. |
| LEDGER-15 boundary acceptance | Archived actual-caller RED versus successor GREEN, native inert composition, authentic producer canary/replay and tamper matrix; helper-only green tests do not admit execution. |

LEDGER-09 hook bypass is avoided by normal patch/edit tooling and explicit lint; this task does not change hooks or global prompts. No broker-connected code is touched.

## 6. Testing strategy

Use existing `unittest` plus native inert integration tests. Before review run `python -m ruff check --select F study tests` with the already available Ruff; if the module entrypoint is unavailable use the installed Ruff executable, without installing a dependency. Run `python -m unittest discover -v` from the repository root, preserving each command's exit before continuing.

Required regressions:

1. Hash-pinned archived candidate actual `_execute_reserved_call` and `run_split` paths reproduce the NameError/keyword TypeError with inert transport; repaired same-boundary calls retain one reservation and one terminal receipt. Exercise `run_canaries` too.
2. Wrong structured verdict/reason, wrong marker verdict, marker echo, tool event, stale summary, changed source/config/predicate, failed then changed-premise canary admission, unchanged-premise refusal, cap exhaustion, post-freeze refusal, missing receipt and concurrent lock refusal.
3. Orphan/duplicate/reordered lifecycle events, duplicate final, unknown/tool items, missing completion, invalid final schema, malformed JSON, terminal error, mixed model identities, nonzero exit, and timeout plus malformed partial stdout. Assert finite statuses and no grade on every failure.
4. Native helper child/descendant: clean normal exit, normal root exit with lingering descendant, inference timeout, wrapper launch/assignment/release fault, capture read/write fault and cleanup fault. Require bounded return, correct phase receipt, Job zero on accepted success, task-owned absence after termination, and unrelated sentinel still alive. Cleanup only test-owned sentinel in test finally. Include paths with spaces and inherited handle stress.
5. Long stderr/stdout with terminal-only sentinel: full byte count/SHA retained, independently capped head/tail and truncation; private diagnostic present, public sentinel/private fields absent as applicable.
6. Mutation of every exact identity/hash/join: freeze, candidate map, CLI binary/version/config, schedule/slot, requested/exposed model, input hashes, reservation, cleanup boolean/active count, terminal status, raw stream, public projection and export manifest. Both resume and reducer refuse the same contradictions. Corrupt/unreadable files must not disappear.
7. Portable public replay in a clean non-installed checkout with PYTHONPATH scrubbed: no private paths/CLI/auth needed; missing public file or tampering blocks. Private verification with missing raw bytes blocks. README-only edits preserve scientific freeze equality; any scientific source/config/prompt/case edit invalidates it.
8. Existing deterministic oracle, report parity, thresholds, missingness and statistical tests retain their original expectations. Final authentic QA binds exact producer capture hashes and tests the installed CLI boundary; consumer-authored JSONL alone cannot satisfy that gate.

Native tests may be explicitly skipped on other OSes, but Windows final QA cannot pass with them skipped. Authentic tests may be pending during offline development only; final QA cannot label them PASS without retained root-operated canary evidence. No tests make model calls automatically.

## 7. Definition of done

- [ ] All six review blockers fixed as one coherent candidate; RED archive/review unchanged.
- [ ] Full source/test inventory passes Ruff F rules and offline suite, with original actual-caller RED and successor GREEN evidence.
- [ ] Native inert Windows composition proves bounded Job lifecycle and task-only cleanup on normal/failure paths, including descendants and unrelated sentinel preservation.
- [ ] Every reserved attempt is retained; failures have durable finite cause/step and diagnostic custody; caps derive from unchanged protocol.
- [ ] Exact scientific/freeze/CLI/config/predicate/schedule/raw/projection identity checks govern dispatch, resume and reducer through one implementation.
- [ ] No failure/cleanup contradiction becomes a grade; timeout precedence survives truncated JSON.
- [ ] Independent review PASS binds unchanged successor; native offline QA and root authentic two-predicate admission complete before final QA/freeze.
- [ ] Producer-derived private-to-public replay is hash-bound and privacy-reviewed; public verification scope is explicit and portable, with no silent fallback.
- [ ] Scientific design, case/report pair, 104/16/120 allowance, statistics and thresholds remain unchanged; zero study calls occur during repair.
- [ ] Exact documented operator commands work from the intended clean checkout; tasks and correction lesson reflect actual evidence and remaining gates.

If any item fails, stop with a finite BLOCKED state and retained evidence. Do not erase an attempt, add cases/calls, substitute paid resources, weaken predicates, or describe a pending authentic gate as passed.
