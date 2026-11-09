# Completion Report Grading Study: Local Ollama Preregistration

**Status:** Separate, pre-outcome v2 continuation. No grading outcome has been observed. This document does not amend or erase the Codex v1 record.

## 1. Problem Statement

The v1 Codex route is operationally closed: two outcome-blind structured canary attempts each hit the installed CLI's mandatory Code Mode bootstrap error, and its version-matched JSONL mapper drops executor payloads, so the frozen strict no-tool gate cannot be audited. The user still wants the bounded report-framing study completed. This preregisters a direct, local Ollama route before any grading outcomes, using the same fixtures and scientific question, so the project can proceed without treating provider operability as a result or claiming that this is a model comparison.

## 2. Key Assumptions

- **Direct local transport makes the frozen no-tool contract inspectable** (Risk: HIGH)
  - **Evidence:** The outcome-blind CLI attempts failed on Code Mode startup; the installed version's output mapper does not retain the executor payload needed to establish zero use. Ollama's local `/api/chat` contract accepts `tools: []` and returns native message/tool-call fields. Read-only inspection confirmed server version `0.40.14` and the installed model identity.
  - **If wrong:** Stop before study calls. Do not enable a dispatcher, add file/MCP access, or reinterpret an unobservable invocation as no tool use.
  - **Validation:** After the offline engineering pipeline passes, outcome-blind admission verifies the actual request, raw response shape, empty tool-call set, local route and bounded custody.
- **The pinned local model and runtime metadata remain the intended inference system** (Risk: HIGH)
  - **Evidence:** Read-only `/api/show`, `/api/tags`, and `/api/version` inspection matched `qwen3.5:9b-q4_K_M` to digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` on Ollama `0.40.14`.
  - **If wrong:** Do not grade. Reconcile the tag, digest, model metadata, server/client identity and request configuration, then obtain fresh review and QA before any call.
  - **Validation:** Freeze and recheck those identities and the model's system text, template, parameters, and supported options before admission and throughout the run. Record any exposed runtime/backend variation; do not imply the artifact digest pins GPU execution.
- **The existing authored cases remain a useful bounded replication across providers** (Risk: HIGH)
  - **Evidence:** The scientific protocol, prompts, cases, reports, oracle and thresholds were fixed and hash-audited before any grading output; provider selection changed solely after operational failures. The final study freeze is still pending.
  - **If wrong:** Limit interpretation to an exploratory result on this model and these fixtures, or stop if the unchanged protocol cannot be administered. Do not pool with or compare against Codex grades; v1 has none.
  - **Validation:** Bind the unchanged scientific artifacts and analysis to v2 before calls and report this as a single-model study, conditional on this local runtime.
- **The fixed decoding and context limits are operable on the available host** (Risk: MEDIUM)
  - **Evidence:** The model is a 9.7B Q4_K_M GGUF of 6,594,474,711 bytes; the host has an RTX 4070 Ti SUPER with 16 GB VRAM and approximately 15 GB free, plus 28 GB free RAM. No local inference has run.
  - **If wrong:** Record a pre-outcome operational stop. Any operability adjustment must be documented, frozen and independently reviewed before a new canary; no outcome-informed tuning is allowed.
  - **Validation:** Admission checks the exact request and finite completion behavior under the fixed settings; monitor and record resource/runtime facts without changing settings in response to grades.

## 3. Scope (In / Out)

**In scope**

- One local model only: `qwen3.5:9b-q4_K_M`, expected digest above, Ollama `0.40.14`. Freeze the complete runtime/model identity before calls: server and client versions/identity, model tag and digest, relevant `/api/show` metadata, template and system hashes, parameters, hardware/runtime facts, effective endpoint, and request configuration. The observed system text is empty; observed template SHA-256 is `b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315`; observed defaults are presence penalty `1.5`, temperature `1`, top-k `20`, and top-p `0.95`. These are recorded facts, not an immutable execution snapshot.
- Direct loopback `POST /api/chat`; no Codex CLI, subscription inference, API key, cloud route, MCP, filesystem bridge, or tool dispatcher. Each request has one fresh user message, `stream:false`, `tools:[]`, the frozen output JSON schema, `think:false`, `keep_alive:"60s"`, and options `temperature:0`, `seed:20261109`, `num_ctx:4096`, `num_predict:512`, `num_thread:2`. Thinking=false is supported by the inspected model metadata. Record effective inherited defaults as well as these explicit overrides. No further generation knobs may be selected from outcomes.
- Preserve exactly 8 development cases in 2 families; 18 holdout cases in 3 families (12 defective and 6 correct); the four existing conditions (`report_free`, `neutral`, `persuasive`, `mitigation`); authored code, prompts, reports, criteria, seeds, exclusion rules, thresholds, statistics, and analysis. Planned calls remain 32 development plus 72 holdout = 104.
- Reuse existing shared attempt accounting, native Windows Job custody for the task-owned Python HTTP worker, receipt identity, analysis/reducer and public replay boundaries. Capture the exact response body bytes as raw transport output; do not fabricate a Codex JSONL lifecycle. Extend replay only with a provider-specific decoder/projection tied to the exact raw bytes and runtime identity.
- Preserve the global cap: the two failed Codex v1 canaries remain charged. At most 14 further outcome-blind canary attempts and 104 study attempts are available, for at most 120 total across v1 and v2. Every reserved transport attempt, including failures, consumes a slot. No budget reset, study retry/replacement, unchanged-premise canary retry, or extra allowance.
- Keep Codex v1 separately documented as operationally incomplete with zero grading outcomes. Keep private raw responses/diagnostics and local runtime details private; publish only sanitized task-created artifacts and verified projections. Continue the existing public GitHub repository objective without exposing private course/profile data or proprietary BlueDot course text.

**Out of scope**

- Model/provider comparison, claims of Codex-versus-Ollama efficacy, fine-tuning, model downloads, external data, paid resources, cloud/GPU rental, new cases or conditions, rebalanced budgets, expanded benchmark claims, or changes to scientific thresholds.
- Starting, stopping, or killing the user's pre-existing Ollama daemon. The task-owned HTTP client/worker is bounded; closing it does not prove the daemon stopped generation. A timeout or uncertain daemon completion is an operational failure, is never a grade, and stops the campaign.
- Fabricating human BlueDot attendance, personal reflections or calendar actions. Current course progress is 73%; unit 3/1 has its reading complete and its technical-result reflection pending (1/2 activities). AI-assisted technical reflections may describe actual evidence. Human attendance and the daily calendar time remain unclaimed.

## 4. Acceptance Criteria

1. Before any model call, the unchanged scientific manifest and this v2 provider contract are reviewed, implemented, independently reviewed, and pass offline/native QA. No study outcome is produced during this pipeline.
2. The frozen runtime identity matches the expected model digest and Ollama version. Effective endpoint is loopback-only; server/client identity, model metadata, system/template hashes, all model defaults, explicit options, schema and exact request bytes/configuration are retained before grading.
3. Admission uses only outcome-blind canaries and no more than the remaining 14 slots. Each canary is reserved in the shared append-only ledger. The structured canary must return `PASS` with reason exactly `structured response available`. The marker canary reuses the existing marker prompt, must return `INDETERMINATE`, and must not echo the private planted marker; the marker is absent from the serialized request and inaccessible to the HTTP route. Both require no tool calls, clean client Job/directory custody and exact model identity. Any failure is retained and stops admission; further attempts require a documented changed premise, fresh review/QA and remaining budget.
4. Every grading request is direct to the frozen loopback `/api/chat`, contains exactly one user message and the fixed request controls above, and has no dispatcher or tools. The response decoder accepts a grade only when HTTP/API execution completed successfully, `done` is true, the returned model matches the frozen model, and assistant content is one JSON object with exactly `verdict` and `reason`, verdict in `PASS`/`FAIL`/`INDETERMINATE`, and a non-empty reason of at most 300 characters. `tool_calls` must be absent or empty, and task-owned process/directory custody must be clean. API errors, timeout, `done:false`, identity mismatch or uncertain daemon completion are operational unknowns; non-empty tool calls are protocol-invalid; malformed/schema-invalid assistant content is invalid output. These states never become grades.
5. The captured raw bytes are the exact unmodified response body; private replay and public projection replay use the provider-specific decoder, join each response to its reservation/config/model identities, and reproduce the recorded classification. HTTP status and transport metadata are retained separately from the response bytes. Public replay does not claim to prove unpublished raw bytes. No failure or missing observation disappears from the existing planned-cell reconciliation.
6. The ledger contains exactly 8 development and 18 holdout cases, all four frozen conditions per case, no more than 104 study attempts, and no more than 120 attempts cumulatively including both historical Codex failures and all v2 canaries. No holdout retry, replacement, prompt adjustment or threshold change occurs.
7. Analysis uses the existing paired estimands, denominators, family breakdowns, missingness bounds, fixed bootstrap seed/resamples and thresholds. It reports Codex v1 as zero-outcome operationally incomplete and v2 as a single-model local study. It makes no provider comparison, model efficacy generalization, production-code claim, or small-effect/no-effect inference.
8. Public release follows the existing independent privacy and replay gates. Only sanitized synthetic study artifacts, permitted outputs, derived results and verified citations are published. Course reporting remains truthful and separate; no human-only BlueDot task or private/proprietary content is represented as completed or released.

## 5. Technical Constraints

- Windows host; existing native Win32 Job implementation owns the task-created Python HTTP worker/client and its descendants. The pre-existing Ollama server is outside that Job and must not be killed. On timeout, close the task-owned client, mark the call operationally unknown, note that daemon-side completion is uncertain, and stop the campaign.
- Serial requests only, fresh one-message history, loopback-only route, no authentication, no external network/data bridge. Use the existing transport deadline unless architecture documents a pre-outcome operability reason to adjust it; `num_predict:512` remains fixed absent a separately reviewed pre-outcome change.
- Ollama response bytes are a native HTTP response, not a synthetic CLI event stream. Freeze and test provider-specific decoding, failure precedence, raw capture, receipt binding and sanitized replay before any call.
- Local metadata and hardware are point-in-time evidence. The model digest identifies the installed artifact but does not prove bitwise-identical inference across runtime, driver, GPU or scheduling changes. Record exposed variation and stop on a material identity mismatch.
- Existing limits on sample size, small-effect sensitivity, authored family dependence, synthetic code scope and descriptive uncertainty remain unchanged.

## 6. Open Questions

- **Blocker before freeze/canaries:** Architecture must bind the exact active loopback endpoint and HTTP client/runtime identity, confirm effective request defaults and response/error shapes, and show that no dispatcher or external route is reachable through the grader path. The read-only inventory verified `/api/show`, `/api/tags`, and `/api/version`; it did not make an inference call.
- **Blocker before study calls:** The provider-specific decoder and evidence/replay path must pass independent review and QA against model-free fixtures before any canary. Authentic canaries may run only after that pipeline PASS; study calls require successful admission and a new frozen protocol.
- **Nice to know:** Actual latency, GPU residency and thermal behavior are unknown until outcome-blind admission. Record them; do not change fixed generation settings based on grading outcomes.
- **No user-owned decision remains open.** The provider choice is already authorized and was made before seeing any grade. Course reflection and human attendance/calendar actions remain the user's own activities, outside this transport spec.

## 7. Success Metrics

- **Admission:** Exact model/runtime/config identity, local-only routing, no-tool predicates, response decoding and bounded task-owned custody pass before the protocol is frozen for grading.
- **Study validity:** All 104 planned cells have explicit valid or missing/invalid/operational dispositions, every reserved attempt remains charged, cumulative calls do not exceed 120, and existing analysis/publication checks pass.
- **Scientific interpretation:** Report the preregistered framing and mitigation estimates with the same thresholds and caveats as v1; observed direction or size does not determine whether results are retained or published.
- **Project completion:** A public, privacy-reviewed GitHub repository and truthful BlueDot progress record remain project deliverables. They are not evidence of scientific success and do not authorize claiming pending human activities complete.

## Architecture Handoff

**PASS to architecture** for a provider-specific local transport plan under these constraints. This is an offline specification handoff only: it admits no inference call, freeze, commit, push, or study result. Architecture must preserve the frozen science and cumulative ledger, define the provider decoder and replay binding, and return a reviewable candidate for the required implementer → reviewer → QA gates before any canary.
