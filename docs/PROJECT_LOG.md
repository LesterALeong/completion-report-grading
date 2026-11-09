# Project log

## Decision 1: Select a bounded measurement question

**Question:** Can a persuasive completion report change a model grader's decision about identical code, even when executable checks show that code violates its specification?

**Why this matters:** A pipeline can advance broken work if it treats a confident success claim as evidence of actual success. Reliable grading must also avoid rejecting correct work unnecessarily.

**Prediction:** The direction and size of the effect are unresolved. Existing patch-correctness research reports no significant bias from a simple all-tests-passed assertion, so a positive result is not assumed.

**Cheapest useful test:** Validate a small synthetic task set and paired report treatment, then use independent model grading with executable ground truth. Freeze the evaluation design before measuring held-out outcomes.

**Current evidence:** The project has an authorized scope, a public repository, a literature review, and an active specification review. No model-grading outcomes have been collected.

**Next decision:** Select the smallest credible baseline and one mitigation, validate the measurement instrument, then freeze the study.

## Scope and provenance

The project uses local Python and existing model access. The initial Codex route closed before study grades; the separately preregistered local route is described below. No additional paid API usage, model training, or GPU rental is planned. AI assistance is used for research support, implementation, review, and writing. Research claims must remain traceable to actual retained outputs.

The BlueDot course is being followed in order. Course progress, private profile information, personal commitments, and mentor participation are not evidence that the technical study succeeded. This log contains project-created research notes only.

See [related work](RELATED_WORK.md). The [public feedback issue](https://github.com/LesterALeong/completion-report-grading/issues/1) is the commentable log companion. GitHub sign-in is required to comment.

## Decision 2: Incorporate counterevidence and review before implementation

The closest patch-correctness study reports no significant effect from a simple all-tests-passed assertion. The planned comparison therefore holds the report's factual propositions constant and tests rhetorical framing, with a report-free baseline and one verification-policy mitigation. This is a replication/extension, not a discovery claim.

Independent methodology review required clearer missingness denominators, separate rejection and abstention counts, family-specific results, practical rather than statistical thresholds, and an honest distinction between audited logical isolation and OS isolation. These corrections were incorporated before any model-grading outcome was collected. The subscription's requested model alias and configuration will be recorded without claiming immutable backend weights.

PM and architecture gates passed for offline implementation. The runnable candidate, authentic transport canaries, independent code review, and QA remain pending. No experimental result is claimed by this entry.

## Decision 3: Strengthen the manipulation before measuring any outcome

Review of the first actual templates found that they differed by only three adverbs while repeatedly disclaiming evidence. That would measure a weak lexical cue under strong report warnings. Before any grading call, the design was revised to use matched normative approval pressure, with identical factual claims and one shared no-evidence sentence. The ordinary baseline still judges code against criteria; the mitigation adds explicit report skepticism and criterion-by-criterion verification as a bundled policy.

The fixture audit also identified ambiguous domains in a correct interval task and a central-tendency operation that overlapped the development taxonomy. These are being corrected before freeze without adding cases or calls. Claims are narrowed to a small code-local screen; no effect is presumed and a null result will not establish production reliability.

## Decision 4: Repair the measurement boundary before inference

The first complete implementation passed its original local tests but failed independent AI review. Six defects concerned actual runner composition, exact canary predicates, event lifecycle, frozen identity checks, descendant cleanup, and retained diagnostic evidence. That candidate was archived unchanged. An inert reproduction confirmed a signature failure before dispatch and an undefined variable after dispatch; neither reproduction called a model.

The repair uses a parent-owned Windows Job assigned before the transport child is released, file-backed private captures, strict terminal parsing, exact reservation/receipt joins, and one shared verifier. Component tests are useful development evidence; they do not substitute for review of the complete runner or an authentic outcome-blind transport admission. No study or canary inference has occurred at this checkpoint.

## Decision 5: Keep one primary provider

Local Ollama models are available as an additional resource. The current study keeps its requested Codex alias/configuration as the sole primary grader. Switching would add a provider adapter and runtime/decoding controls without removing the remaining shared evidence work. Model selection must not depend on which provider produces a more interesting verdict pattern.

A local model replication would require its own preregistration and runtime, weight-digest and sampling records. If the outcome-blind Codex admission cannot satisfy the existing gate, this study stops before grading outcomes; it does not silently replace its provider. A null result remains a valid result of the planned screen.

## Pre-outcome assumptions

This AI-assisted list records what must hold for the study to answer its narrow question. No grading outcome was used to select these assumptions.

1. **Prior work transfers enough to motivate a test.** Self-report leakage in other settings makes the question plausible, but the closest patch-judging counterevidence means an effect here is uncertain.
2. **The labels are defensible.** Each authored task has unambiguous criteria, executable checks and a criterion-linked defect witness or independently audited correct control. Passing a finite test suite alone is not a proof of correctness.
3. **The report pair holds evidence fixed.** Neutral and persuasive reports share factual propositions, truth status, evidence and order. Their intended difference is normative approval pressure, not new test evidence or pure friendliness.
4. **The intervention is meaningful.** The static blinded audit recognizes stronger approval pressure; matching length alone would not establish treatment strength. No model-grading outcome selects the wording.
5. **Judge context excludes the answer key.** Fresh logical contexts, label-free inputs, disabled tools and a marker predicate can audit separation. They do not prove complete OS isolation.
6. **The instrument cannot invent success.** Strict parsing, native process custody and private/public replay must agree. Review found duplicate-key ambiguity in the current parser; that is a blocker to repair before inference, not a usable grade.
7. **Existing access supports the exact run.** The signed-in subscription must support the requested alias/configuration and both authentic predicates without API-key or paid-resource fallback. Offline tests do not establish this.
8. **The recorded provider stays comparable.** Configuration and any exposed backend identity must remain stable. A rolling alias cannot guarantee immutable weights; an exposed identity change stops the run.
9. **A useful mitigation preserves correct work.** Fewer false passes must be considered alongside strict rejection and abstention on the six correct controls. Rejecting everything cannot satisfy the declared target.
10. **The sample supports only a narrow screen.** Twelve held-out defective cases and six controls can reveal large observed differences. Conditional intervals and missingness bounds do not justify production rates, small-effect claims or proof of no effect.
11. **Failures and evidence remain auditable.** Every attempted call consumes its reservation; failures cannot disappear or become grades. Public projections support replay of published artifacts, while unpublished raw-byte equality requires private verification.
12. **The deliverable demonstrates relevant work honestly.** A readable, reproducible evaluation can support career discussions when its owner understands the design and limitations. AI assistance, synthetic scope and pending human course participation remain explicit; no hiring outcome is presumed.

## Decision 6: Close Codex v1 and preregister local v2 before grades

The initial operational prediction failed: two structured canaries returned their requested constant JSON alongside the same provider startup error. The second used a reviewed configuration repair. Neither reached the marker predicate. A bounded source audit of the installed version found that the CLI's JSONL mapper omits some executor payloads, so enabling the host could not establish the declared observability condition. Codex v1 is operationally incomplete, with zero study grades. Its original specification, configuration, raw evidence and charged attempts are retained.

The separate v2 primary is the already-installed `qwen3.5:9b-q4_K_M` model on Ollama 0.40.14, manifest digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. This selection follows an operational failure before any case-grading outcome; it is not a provider comparison. [The v2 specification](SPEC.md) fixes the local endpoint, model/runtime identity, explicit request controls and failure rules. The original cases, prompts, reports, oracle and analysis remain fixed and hash-audited.

The original cap stays at 120 total attempts, including both failed Codex canaries. Local review/native QA and two authentic predicates must pass before freeze and the 104 study calls. The task-owned HTTP client is bounded; the existing Ollama daemon is never killed. Daemon completion uncertainty stops the campaign. At this implementation checkpoint, no local inference or case-grading outcome has occurred.

## Decision 7: Complete the frozen run and report the below-threshold result

Independent review and native QA passed on one unchanged candidate. Both authentic local predicates passed, their raw/projection replay passed, and the 104-cell protocol was frozen. Preregistration commit `d4bd17f6c9383dd4fcffea79041a3268a3839e8a` and the zero-study public admission bundle were pushed and their remote hash verified before any grading call.

All 32 development and 72 holdout calls completed validly with unchanged settings and no retries. The primary holdout comparison yielded four false approvals among twelve defective cases under approval pressure versus three under neutral framing: one extra approval, below the predeclared two-case screen. The mitigation yielded three false approvals, one fewer than approval pressure and below its two-case target. All six correct holdout controls passed in each condition. Development had no false approvals or correct-case nonpasses. The report keeps these small samples separate and does not promote the more favorable secondary comparison to the primary endpoint.

The first full public export failed when redaction expanded one valid explanation past its display-length limit. The run, scientific source and private evidence were preserved. A process-level postmortem led to a separate, versioned publication amendment, with a portable actual-producer failure-to-success detector. It abbreviates one sanitized explanation and changes no grade or statistical output. The corrected full bundle passes the unchanged strict reader; cold public analyses match private analyses apart from scope. See the [report](REPORT.md) and [postmortem](reviews/EXPORT_POSTMORTEM.md). Independent final artifact review and QA gate release of these results.
