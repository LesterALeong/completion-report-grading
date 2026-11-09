# Codex run: operationally incomplete

The original subscription-backed run stopped before grading any study case. Two outcome-blind structured canaries returned the requested constant JSON, but each also emitted a provider startup error because the Code Mode host was disabled. Neither response was admitted as a valid grade. The marker predicate was not reached.

The first attempt used the scalar Code Mode feature flag. A reviewed, separately recorded configuration repair used the documented nested setting while keeping the host disabled. It produced the same bootstrap failure. Both consumed reservations, raw captures, source/configuration identities and diagnostic sidecars were retained unchanged. Native transport exited cleanly, with zero remaining Job processes and successful judge-directory cleanup.

## Why this route closed

The installed model catalog declares a Code Mode-only tool mode. A version-matched source audit found an important distinction: the executor uses explicit runtime bindings and rejects imports, while the CLI's [JSONL item mapper](https://github.com/openai/codex/blob/rust-v0.166.0-alpha.5.1/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L311) emits selected item types and drops unmatched payloads. An empty observed tool trace therefore cannot establish the original zero-executor-invocation condition. Enabling the host without completing that audit would not satisfy the declared gate.

The retained producer error also exposed a taxonomy issue: a provider error item is an operational failure, rather than evidence that the model called a content tool. A producer-derived regression now enforces failure-only handling, including when a later final says PASS. The first receipt preserves its original conservative classification under its original source identity; it was not rewritten after the parser repair.

## Interpretation and next run

This is evidence about this installed transport/configuration, not a result about completion-report persuasion or Codex grading accuracy. There are zero Codex study observations, so no false-pass rate or provider comparison is reported.

The original [specification](protocols/CODEX_V1.md), [configuration](protocols/codex-v1.json), review reports and sanitized producer fixture preserve the development record. A separate local-model preregistration follows this operational failure. It retains the same authored fixtures, report pair, contrasts and thresholds; model selection precedes all case-grading outcomes. The two consumed canaries continue to count toward the original project-wide 120-attempt cap.
