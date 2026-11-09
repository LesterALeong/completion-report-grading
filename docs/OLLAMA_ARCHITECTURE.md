# Local Ollama v2 architecture

Status: **PASS to bounded implementation**, subject to the gates below. This is an offline architecture handoff. It authorizes no inference, freeze, publication, model installation, daemon manipulation, or budget reset.

## 1. Spec review and interpretation

`docs/SPEC_OLLAMA.md` is coherent. Provider selection occurred before any grading output. Interpret "unchanged" as unchanged cases, reports, prompt bytes, oracle, schedule construction, statistical mathematics, seeds, exclusions and thresholds; provider configuration, transport implementation, identity and protocol version intentionally change. The final study freeze is still pending. The canonical `docs/SPEC.md` and `study/protocol.json` currently describe v1 and must become the approved v2 before admission. Preserve `docs/protocols/CODEX_V1.md` and `codex-v1.json` byte for byte. No Codex host enablement is an implementation option.

The inspected inventory records model metadata, not an inference response or an immutable execution snapshot. Authentic response compatibility remains an admission gate. Root confirmed that every prior live metadata query used `http://127.0.0.1:11434`; architecture pins that endpoint, with `/api/chat` as the sole inference route. Native preflight must verify this exact active endpoint and the known metadata before canaries. A different listener, redirect, unavailable server, identity drift or unsupported option blocks dispatch; do not silently discover/fall back to another endpoint. No user decision is needed to implement this check.

Retain the existing 180-second inference deadline and 5-second native cleanup deadline. There is no pre-outcome evidence justifying an increase. Latency/resource failures stop the campaign. Any subsequent operability adjustment needs a documented changed premise and fresh review/QA, within the existing allowance.

The global allowance is 16 canaries and 120 absolute, including the two historical Codex failures. It leaves at most 14 further canaries and exactly the existing 104 planned study slots. Reservation consumes allowance even if dispatch never happens. A failure does not buy a replacement.

## 2. Files affected

This document is the only file changed by architecture. The implementation inventory is:

| File | Change and reason |
| --- | --- |
| `study/ollama.py` (new) | Fixed configuration, local metadata inspection, pure native-response decoder, deterministic safe projection, and adapter using existing Job supervision. No provider registry or generic framework. |
| `study/ollama_worker.py` (new) | Standalone standard-library HTTP child, runnable with isolated absolute-path Python; exact body on binary stdout and separate transport facts. |
| `study/protocol.json` | v2 provider/runtime/request contract; preserve all scientific and budget values. Remove active subscription-specific model/CLI configuration rather than pretending it applies locally. |
| `study/runner.py` | Explicit active-v2 dispatch, static versus live identity checks, v2 receipts/admission/freeze, mixed historical allowance provenance, provider-bound offline replay. |
| `study/evidence.py` | Explicit schema-v2 validators and safe identity checks, provider-aware replay/projection hooks and historical budget joins; retain schema-v1 validators and Codex projection behavior. |
| `study/export.py` | Select decoder/projector by admitted evidence provider, publish safe v2 identity commitments and complete historical canary accounting. |
| `study/analysis.py` | Select frozen-provider replay instead of unconditional Codex JSONL parsing; keep calculations and scientific reconciliation unchanged. |
| `study/__main__.py` | Local-call authorization/help text and entrypoint tests; preserve legacy spelling only as a rejected/deprecated option for v2, never as Ollama authority. |
| `docs/SPEC.md` | Root installs approved v2 canonical spec before admission; no scientific changes. |
| `README.md` | Actual local preflight/admission/freeze/run/export/replay commands, daemon-custody limitation and v1 closure. |
| `tests/test_ollama.py` (new) | Pure strict request/decoder/identity/projection matrix. |
| `tests/fixtures/ollama_http_helper.py` (new) | Inert loopback producer for actual worker and native composition, never a model invocation. |
| `tests/test_runner.py`, `tests/test_evidence.py`, `tests/test_export.py`, `tests/test_analysis.py`, `tests/test_entrypoint.py`, `tests/test_protocol.py` | v2 actual-caller, provenance, portable replay and unchanged-science regressions; retain v1 cases. |
| `tests/test_windows_job.py` | Exercise the new real HTTP worker through unchanged Job supervision, including timeout and unrelated-server preservation. |
| `tasks/todo.md` | Checkable slices, acceptance matrix, candidate identity and final review/QA evidence. |
| `tasks/lessons.md` | Add only an actual correction/prevention lesson if one arises; no speculative lesson. |

No deletion is needed. `codex_cli.py`, its legacy parser/tests/fixtures, `windows_job.py` and `transport_worker.py` need no functional modification. Reuse their public supervisor interface, not CLI simulation. If a concrete integration fault requires changing them, stop that slice and document the smallest revised plan before editing. Historical protocol copies and original attempt files are immutable. `data.py`, prompts, cases, reports, schema, oracle and mathematical analysis functions remain unchanged.

## 3. Minimal contracts and ordered implementation slices

### Slice 1: Freeze the v2 configuration and historical accounting contract

Update the canonical spec/protocol and establish a regression comparison to the archived v1 protocol that permits only study/provider identity and transport fields to differ. Preserve schedule and serialized study prompt hashes independently of the broader scientific closure, which correctly changes when implementation files change.

Use `provider: "ollama_local"`, request model `qwen3.5:9b-q4_K_M`, and a transport configuration object in protocol; do not retain a fabricated reasoning-effort setting. Record `think:false` in that configuration. The immutable request object is:

- exactly one `messages` entry with role `user` and existing prompt text;
- `model` equal to the pinned tag, `stream:false`, `tools:[]`, `format` equal to the existing JSON schema, `think:false`, `keep_alive:"60s"`;
- `options` exactly `temperature:0`, `seed:20261109`, `num_ctx:4096`, `num_predict:512`, `num_thread:2`.

Record observed model defaults (presence penalty 1.5, temperature 1, top-k 20, top-p 0.95) separately from explicit overrides; effective known values override only temperature. Preserve all exposed default parameters, renderer/parser/template metadata and supported thinking options privately. Do not claim unexposed engine defaults are known or pinned. No outcome-based knob selection.

The static configuration digest is computed entirely from repository bytes: protocol transport/request controls, schema, decoder/projection version and worker/config source identity. It must never inspect a daemon, executable, login or network. Live inspection produces a separate immutable runtime identity record: endpoint; server version 0.40.14; installed model digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`; GGUF/9.7B/Q4_K_M and size; system hash `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; template hash `b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315`; full defaults/support hashes; Python version, executable binary hash and worker hash as the actual HTTP client identity. There is no Ollama CLI in the inference path. Record exposed server binary/runtime/hardware facts privately without implying that a digest fixes GPU arithmetic.

Keep reservation schema 1 and its create-only files unchanged. Add a create-only v2 historical manifest under the existing task root listing exactly the two prior canary attempt IDs and SHA-256 commitments to their reservations, receipts, sidecars and captures, with provider `codex_v1`, prior context/source/config commitments, failed disposition and `admitted:false`. Generate it from existing bytes, never copied summaries. Bind its hash into v2 preflight/admission/freeze and public manifest. Its purpose is provenance and allowance continuity, not v2 admission.

Validate every historical capture/sidecar hash and relationship through the existing legacy custody path. Do not run Codex, require current auth/config, reparse a failed old startup error with the Ollama decoder, overwrite old files, or relabel old failures as valid. Unknown historical entries, missing/corrupt old files, manifest drift or an unclassified provider block. Counts still derive from all canonical reservations, not a manifest subtotal or a fresh directory. Public historical ledger exposes safe commitments/dispositions, with no claim to replay unpublished old raw bytes. Later failed v2 canaries likewise remain charged and explicit.

### Slice 2: Implement the isolated HTTP worker and direct local adapter

`ollama_worker.py` receives one bounded serialized request on stdin and fixed command arguments for metadata path and deadline. Run `[sys.executable, "-I", "-S", "-B", absolute_worker_path, ...]` through existing `windows_job.run_native`; its blocked wrapper assigns Job membership before child dispatch. Use `http.client.HTTPConnection` to literal `127.0.0.1:11434`, no proxy environment, DNS, redirects, URL override, tool dispatcher, filesystem bridge or retry. Reject other routes/hosts before reservation and again at the worker boundary. Metadata GETs are limited to `/api/version`, `/api/tags`, `/api/show` (POST for show where required); never an inference fallback or model pull.

Write the response body chunks directly and exclusively to binary stdout; no JSONL wrapper, newline, re-encoding or diagnostic banner. Read at most the existing 8 MiB parse bound plus overflow detection, retain observed byte count/hash, and classify overflow operationally unknown. Keep stderr as bounded diagnostic custody through existing capture helpers. Persist a separate create-only `http.json` with schema version, request byte count/hash, effective endpoint/route, HTTP status, response completeness, failure step/last step/code, response body commitment, and dispatch/completion facts. Hash it into the sidecar and receipt. Native terminal/process metadata remain separate; `cli_pid` in the existing native process record means the owned child PID here, and must not be presented as a Codex CLI identity.

The adapter returns the existing immutable result shape (reuse `ParsedResponse`, `ProcessResult`, capture summaries; `event_count=0` is documented as not applicable). Add transport metadata via v2 sidecar/receipt commitments, not fabricated CLI events. Standalone worker imports only standard library because isolated Python starts outside package context. A completed HTTP exchange can have worker exit 0 and HTTP non-200; the decoder still rejects it. Socket/setup/body failures exit nonzero with finite transport facts and captured partial body.

Use the existing 180-second outer deadline; the inner HTTP deadline cannot exceed the outer remaining budget. Job cleanup owns only task-created wrapper/client/descendants. Never stop or adopt the existing daemon. A timeout, reset after possible dispatch, incomplete body or otherwise uncertain daemon completion produces `operational_unknown`, explicit `daemon_completion_uncertain:true`, and stops the campaign. Job ActiveProcesses=0 proves client custody only. No retry follows.

### Slice 3: Implement strict native decoding and safe projection

Pure interface: `parse_response(body_bytes, transport_facts, expected_model) -> ParsedResponse`. `transport_facts` includes HTTP status, complete-body fact, native exit/timeout and daemon uncertainty; offline replay gets them from reopened hash-bound artifacts. Use the existing duplicate-rejecting JSON reader for both outer response and inner assistant content, strict UTF-8, and bounded input. No markdown stripping, brace extraction, coercion or permissive second parse.

Failure precedence is explicit: failed/unknown native custody, timeout/uncertain completion, non-200 HTTP, incomplete body, API `error`, absent/nonboolean/false `done`, absent/wrong returned model or missing/wrong assistant envelope => `operational_unknown`. Preserve independent violation flags. On otherwise complete execution, nonempty `message.tool_calls` or malformed tool-call field => `protocol_invalid`. Require assistant role and string content; nonempty thinking output under `think:false` is a protocol violation. Valid assistant content is exactly one object with exactly `verdict`/`reason`, allowed verdict and nonblank reason <=300 characters. Malformed/schema-invalid content => `invalid_output`; only fully clean execution => `valid`. Every other disposition has null verdict/reason. Validate boolean types strictly (`1` is not `true`), duplicates at every level, non-object envelopes and trailing content. Native durations/token counts are optional diagnostics, never completion substitutes.

Add `project_response(raw, transport_facts)` with a versioned, allowlisted Ollama projection schema containing only safe model identity, completion/tool/thinking-presence facts, sanitized structured content or finite invalidity facts, and required transport classification facts. It is an Ollama projection, never a fabricated Codex lifecycle. A separate pure `parse_projection` reproduces status/verdict/sanitized reason/model; it must not pretend sanitized bytes are the original native HTTP envelope. Bound raw-to-projection transformation and attestations to both body and transport metadata commitments. Missing or unsupported shapes cannot become grades. Public invalid-output projections must retain enough explicit facts to reproduce invalidity without publishing arbitrary malformed response text.

### Slice 4: Integrate runner, admission, freeze and evidence versions

Replace active direct Codex calls in `runner.py` with the fixed Ollama adapter. A small explicit provider/schema branch selects Ollama v2 versus legacy Codex replay; do not add registration, discovery, dependency injection framework or cloud fallback. Keep existing lock, reservation-before-dispatch, outer finally, terminal receipt persistence and stop-on-study-failure rules.

Use schema 2 for v2 freeze, admission context/summary, canary receipts and study receipts; unchanged reservation files stay schema 1. In v2 replace `cli` with `transport` (provider, static configuration hash, safe client/runtime identity commitments); replace `reasoning_effort` with the fixed configuration binding rather than a fictitious effort value. Add `runtime_identity_sha256`, `request_sha256`, `transport_metadata_sha256` and `history_sha256` to relevant receipt/sidecar joins. Freeze/admission carry complete safe transport identity plus hashes committing private runtime metadata. `auth_route` is exactly `local_unauthenticated`; schema 1 retains exactly `chatgpt_subscription`. Enumerate allowed keys per version and reject mixed/unknown versions. Update every producer/consumer/callback signature together and exercise actual callers.

Inspect and compare live `/api/version`, `/api/tags`, `/api/show` identity before each dispatch and immediately after completed inference. Pre-dispatch mismatch stops before inference; post-dispatch mismatch invalidates the consumed observation and stops. Bind request bytes, runtime observations, schema, configuration, scientific closure, historical manifest and prompt into the sidecar. This detects observed drift but cannot prove atomic daemon identity or immutable GPU execution; disclose that limit. Stable identity fields must match exactly. Timestamp/residency/free-memory/latency facts are observations rather than equality gates unless they expose an actual execution-identity change.

Update `_require_passing_preflight`, `run_canaries`, `_canary_context`, `_verify_sidecar`, `_verified_admission`, `freeze_protocol`, `load_private_bundle` and `run_split` as one interface slice. Static private replay computes static hashes and reopens saved runtime facts; it never calls live inspection/auth. Metadata/HTTP completeness must be joined through the same shared verifier used by dispatch/resume/reducer, including non-valid receipts.

Canary predicates and prompts remain exactly as authored. Marker contents stay only in the private planted file and commitment; prove absence from exact serialized HTTP request. Require exact structured PASS/reason and marker INDETERMINATE/no echo, empty tools and clean native/directory custody. Preserve changed-premise documentation, prior attempt identity and source/config change checks. Historical failures are counted but cannot satisfy v2 predicates or force equality with the new configuration. Admission requires the two new successful predicate receipts for the same v2 identity. No readmission after freeze.

### Slice 5: Integrate portable export/reducer and operator entrypoint

Remove unconditional `codex_cli.configuration_sha256`, `parse_event_stream` and `project_stdout` from v2 private/export/analysis routes. Select only from explicit frozen schema/provider; closures supply bound transport facts to existing evidence callbacks. Keep legacy behavior accessible to v1 fixtures. Relax backend syntax only in the v2 model validator to permit `:` and require exact equality with the frozen local tag; do not weaken v1 or accept arbitrary provider names.

`evidence.verify_freeze`, `_validate_receipt`, `verify_inventory`, `verify_projection` and `verify_public_bundle` need explicit version branches; so do `_safe_cli` replacement and public identity allowlists. Public bundle schema 2 includes safe transport identity commitments, transport projections/attestations, v2 admission and complete historical charged-canary ledger. Preserve exact joins, allowed file inventory and independent manifest hash requirements. Public projection replay proves published projections, not unpublished raw equality. Private replay requires exact raw bytes plus HTTP metadata. Neither path requires Ollama, Codex, installed client binaries, auth, a GPU or external network.

Keep all Wilson/paired-bootstrap/threshold/missingness calculations intact. Report v1 zero outcomes/operationally incomplete and v2 one local model, without comparison. Rename operator flag to `--authorize-local-model-calls`, update help and execute documented entrypoints. Keep BlueDot progress/human activities separate and truthful.

### Slice 6: Consolidated review, native QA and authentic admission

Run offline tests/lint before independent review. Freeze one coherent candidate identity and acceptance matrix, obtain reviewer PASS and native inert QA on those unchanged bytes. Only then may root run the two authentic outcome-blind canaries, charged to the canonical ledger. Reopen raw HTTP bodies and metadata and replay exact captures and public projections through production reader/writer/reducer. Capture sanitizable authentic producer-derived fixtures with provenance; consumer-authored fixtures alone do not admit the transport. Any canary failure stops, remains charged and requires a material changed premise plus renewed review/QA before another attempt. Final protocol freeze and 104 case calls require successful admission and final QA; no study calls belong to implementation.

## 4. Confirmed patterns and alternatives

Source inspection confirmed standard-library Python, immutable result dataclasses, `protocol.canonical_json`/SHA-256, UTC-aware `runner.utc_now`, create-only reservations/receipts, a task-local operator lock, deterministic schedule, strict duplicate JSON parsing, evidence callbacks, `unittest`, bounded private capture paths under `TASK_TMP`, and assigned-before-release Windows Job custody. Follow these. `tasks/lessons.md` requires actual caller composition and bounded slices.

Two implementation choices are valid: extend a common transport abstraction, or add the fixed provider-specific module and explicit evidence-version branch. Recommend the latter: only two known formats exist, one closed; a provider framework would obscure finite admission rules. For HTTP, `urllib` can disable proxies/redirects with custom handlers; recommend `http.client` and literal loopback instead because it has neither automatic proxy discovery nor redirects. Do not shell out to `ollama run`: that loses native envelope and HTTP metadata custody.

## 5. Risks and defect-ledger exposure

Breaking-change risk: **medium**, concentrated in exact evidence schemas and cross-file callers. Preserve v1 branches/fixtures and reject schema mixing. No valid historical grades require migration. Performance: serial local 9.7B inference under unchanged finite deadline; no downloads/training, no broad monitoring framework. Metadata probes are finite and do not consume inference calls. Security: local literal endpoint, no dispatcher/credentials/proxies/redirects, raw/private runtime facts outside Git, public allowlists and marker/request audit. The daemon remains an external process boundary and cannot be claimed Job-contained.

The local defect ledger was read, including the prior Ollama missing-`done` escape. Applicable classes and mandatory prevention:

| Class | Mechanical prevention |
| --- | --- |
| LEDGER-01 leakage | Exact unchanged prompt/case hashes, marker absent from wire request, no grading outcomes in tuning or transport fixtures. |
| LEDGER-02 undefined names | Ruff F plus actual canary/study/CLI composition, including standalone isolated worker launch. |
| LEDGER-03 timezone | UTC-aware persisted times, monotonic deadlines, naive-time refusal tests. |
| LEDGER-04 silent external failure | Strict `done is True`, HTTP/native/error/body/custody precedence; fault at each HTTP boundary with durable finite failure diagnostics and no grade. |
| LEDGER-05 contextual constants | Generation controls and bounds derive from the single approved protocol; 180-second inference versus 5-second cleanup explicitly separate. |
| LEDGER-06 source of truth | Programmatic v1/v2 science comparison, inventory-derived identity, canonical reservation count, hash-bound history. |
| LEDGER-07 moving gates | Frozen acceptance matrix, unchanged statistical gates and all attempts retained, material-premise-only readmission. |
| LEDGER-08 Windows traps | Native absolute `-I -S -B` HTTP worker through real Job, paths with spaces, sentinel server/daemon preserved. |
| LEDGER-10 signature drift | Enumerate and test runner/evidence/export/reducer/entrypoint callers on the same candidate. |
| LEDGER-11 documentation drift | Execute documented local and portable replay commands in clean subprocesses with retained individual exits. |
| LEDGER-12 cwd | Worker absolute path; repository/task-root anchored inputs and captures; clean foreign cwd tests. |
| LEDGER-13 unreadable versus absent | Missing/corrupt historical ledger, runtime metadata, raw body, transport facts and receipts explicitly block. |
| LEDGER-14 provenance | Request/config/runtime/history/raw/metadata/freeze/schedule joins and full reviewed candidate map. |
| LEDGER-15 boundary acceptance | Real worker/inert server/native caller tests, provider-derived authentic canaries after review, tamper tests on persisted evidence and public reader. |

LEDGER-09 hook bypass is not introduced; normal tooling/lint applies. No broker code is touched.

## 6. Testing and acceptance/tamper matrix

Run `python -m ruff check --select F study tests`, then `python -m unittest discover -v`, preserving each terminal exit and stopping on failure. No test automatically invokes a model. Native tests may skip on other OSes; final Windows QA must execute them.

| Boundary | Required positive and negative proof |
| --- | --- |
| Scientific continuity | Byte-identical cases/reports/prompts/oracle/schema; same schedule prompts, 104 cells, seeds/thresholds/math; permitted protocol differences enumerated. |
| Worker request | Actual inert server sees exact one-user schema/tools/think/options/keepalive body; no marker or inherited system text; wrong host/port/path/proxy/redirect refuses. |
| Raw custody | Producer body with whitespace/non-ASCII/binary-invalid UTF-8 preserved exactly in stdout; status separate; no wrapper bytes. Empty/partial/oversized bodies never grade. |
| Completion | Missing/false/1/null `done`, HTTP errors, API errors, wrong model, malformed envelope, incomplete content length, reset/timeout => no grade; exact complete valid producer envelope => expected grade. |
| Strict JSON | Outer/inner duplicate keys, multiple objects, unknown inner keys, invalid verdict, blank/301-character reason, nonstring content, nonempty tools, malformed tool field/thinking output reject at documented precedence. |
| Native custody | Real HTTP worker clean success, delay/timeout, connection refusal, lingering descendant, metadata/capture failure, paths with spaces; bounded return, correct fault step, no daemon/helper-server kill. |
| Identity | Every model digest/tag/server/client/system/template/default/schema/request hash mutation fails before acceptance; pre/post mismatch consumes attempted call and stops. |
| Mixed history/budget | Actual two retained failures count; no rewrite/reparse under Ollama; missing/changed history blocks; exhaustion at global 16/120; historical admission cannot satisfy v2; unchanged-premise retry and postfreeze readmission refuse. |
| Runner composition | Actual `run_canaries`, `_execute_reserved_call`, `freeze_protocol`, `run_split`, CLI and resume with inert producer; setup failure consumes reservation and terminal receipt; no retry/next dispatch after failure. |
| Replay tampering | Modify/delete raw body, HTTP status/completeness, metadata hash, request, runtime, history, cleanup, provider/schema, reservation, admission, freeze, schedule, projection or public manifest; private/resume/reducer/public reader fail consistently. |
| Portable replay | Subprocess forbids network and all installed CLI/model inspection; private replay uses retained raw+metadata, public replay uses projections only; missing raw blocks private mode; missing/tampered projection blocks public mode. |
| Legacy regression | All original Codex parser/tests/fixtures and old bytes retained; failed old receipt remains failed and charged, independent of active v2 configuration/auth. |
| Authentic admission | After unchanged-candidate review/native QA: exactly existing two predicate canaries, exact native raw/metadata replay, safe projection equality and no tool/marker/custody/identity failure. |

## 7. Definition of done

- [ ] Approved v2 canonical spec/config and byte-exact v1 archives; unchanged-science comparison passes.
- [ ] Finite native local HTTP worker and strict decoder; response stdout is exact body and HTTP facts independently bound.
- [ ] Complete v2 producer/consumer contracts, static offline hashes and pre/post live identity checks; v1 remains reproducible.
- [ ] Both historical failures retained and verified, counted toward 16/120; no study outcomes or budget reset during engineering.
- [ ] Full offline/native acceptance and tamper matrix passes on one reviewed candidate; Ruff F and original suite green.
- [ ] Independent reviewer PASS and native QA precede authentic canaries; all results and exact candidate identity retained.
- [ ] Two authentic predicate canaries pass and replay from retained producer bytes; otherwise finite operational stop with charged attempts.
- [ ] Freeze only after final admission/QA; scientific cells remain 32 development +72 holdout, no retries or substitutions.
- [ ] Private/public replay works without running Ollama/Codex/auth and labels verification scope honestly; privacy review passes before release.
- [ ] Documentation commands verified; task review records evidence, remaining gates and v1/v2 interpretation without human-course completion claims.

Architecture PASS means the above blueprint is implementable without a new user decision. Any identity/response/custody incompatibility is an operational gate with retained evidence, not permission to weaken science, enable tools, change provider or erase a consumed attempt.
