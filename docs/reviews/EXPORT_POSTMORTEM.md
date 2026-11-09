# Publication escape: redaction expands a valid reason beyond the public schema

## Diagnosis: proven

This is an escaped publication defect after a passed review/QA pipeline. The original study source, protocol, raw evidence, reservations, receipts, labels and metrics must remain unchanged. No new inference or scientific retry is required or authorized by this plan.

An independent read-only traversal of all 104 generated public receipts found exactly one affected attempt:

- Attempt: `e01782c4184246ab94325e2cab896dd7`.
- Slot: `study:holdout:H03:mitigation`.
- Original receipt: `valid`, verdict `FAIL`, reason length 300 characters.
- Original reason SHA-256: `e6b369c5547ad08ba41707cd26b656e01148124b0ea5a22c898190d00d688ab6`.
- Frozen `_public_reason` result: 305 characters; exactly equal to the persisted public projection reason.
- Persisted projection SHA-256: `771e5b1606a9970ea7855c70848bfa0779666abbdf05a6942a5d91d3fb8917c0`.
- Frozen `parse_projection`: `operational_unknown`, null reason.
- Generated public receipt: original `valid` status retained, reason replaced with null.

The exact failed bundle manifest SHA-256 is `ef3369c61e24c4b5a6c0417ee5eb8f25b77c4bbde39b86359d12b12c1750f94b`. Calling the production `verify_v2_public_bundle` on it independently reproduces `EvidenceError: V2_VALID_CUSTODY`. Raw reason text was not printed or copied into this report.

## Root cause and escaped gate

`study/evidence.py:311` replaces sensitive-looking strings with explanatory placeholders. A replacement can be longer than its input. `study/ollama.py:176` stores that transformed reason without bounding its length. `study/ollama.py:183` then applies the unchanged maximum-300-character schema to the transformed display text. `study/export.py:30` copies the original receipt but substitutes the parsed projection reason without requiring successful projection parsing first. Thus sanitization can invalidate a valid response and create an internally inconsistent public receipt. The final public verifier correctly refuses it; no scientific grade was silently accepted or relabeled by that verifier.

The process gap was a missing composition invariant: every valid original reason up to 300 characters must produce a privacy-safe, schema-valid public reason. The short email-redaction test and the rejection of native 301-character reasons did not test redaction expansion at the valid boundary. The successful authentic admission reasons and zero-study publication smoke also did not represent this boundary. The earlier review approved that inadequate boundary coverage; this report supersedes its publication-completeness implication, not its frozen scientific evidence.

Applicable ledger classes: LEDGER-04 (external/publication failure must be explicit), LEDGER-07 (no outcome-informed gate changes), LEDGER-10 (producer/consumer contract drift), LEDGER-14 (exact provenance), LEDGER-15 (real producer-to-writer-to-reader regression), LEDGER-23 (complete production artifact boundary), LEDGER-33 (inconsistent status/reason cross-product), LEDGER-34 (terminal test evidence), and LEDGER-44 (preserve predecessor closure). The local ledger was read. A `/postmortem` command was not found in the probed local command directory; this document supplies the required process-level diagnosis and mechanical-detector plan. After the portable original-RED/successor-GREEN detector and full 105-test matrix passed, root appended this recurrence and detector to the authoritative defect ledger under the user's standing postmortem instruction, verifying every prior byte was preserved. Memory files were not changed.

## Architecture: PASS for a separate publication-only amendment

1. Preserve `results/study` and its failed manifest byte for byte. Preserve the archived candidate and scientific closure `d2c2572ebcf506a162687a318e1410df11c37547f09363ec4d217891ee7f4027`. Add new publisher/test files outside `study/`, `tests/` and the existing frozen candidate inventories, for example `publication/`. Do not edit the frozen sanitizer, parser, exporter, protocol, thresholds or response schema.
2. Implement a deterministic, explicitly versioned publication amendment command. Inputs must include the exact failed manifest hash and the verified private evidence root. Reopen the full private bundle with the frozen production loader. Reconstruct each original public attempt using the frozen production `_v2_public_attempt`, comparing its receipt/projection/HTTP/attestation bytes to the failed bundle before repair. This establishes that the amendment starts from the authentic retained producer outputs and not invented receipts.
3. Amend only display reasons: apply the frozen sanitizer, then, only when its result exceeds 300 characters, retain the first 299 Unicode characters and append one ellipsis character. Require the result to be nonblank, at most 300 characters, and a fixed point of the frozen sanitizer. Parse each corrected projection with the frozen strict parser and require unchanged original status, verdict and reported model. Fail loudly before publishing if any invariant fails. Do not change `content_valid`, native validity, private reasons, raw commitments, identity, custody, reservations, timestamps or study accounting.
4. Create a fresh output leaf such as `results/study-publication-v2`. Preserve every unaffected file byte for byte. Change affected projection display reasons and public receipt display reasons, recompute their projection attestations and the manifest using existing canonical serialization. Use the existing strict bundle inventory and unchanged public reader. Put an amendment/provenance record beside the bundle, not inside its strict inventory: exact original and successor manifest hashes, frozen scientific/candidate identities, publisher code hash/version, changed attempt IDs, reason-length/hash commitments, and the explicit statement that display sanitization alone changed.
5. Freeze one amendment candidate for independent review and QA. Add a public-project regression detector that runs original frozen producer RED and amended producer GREEN on the exact retained failing case, with no mutation of the retained response. Add boundary fixtures for 299/300-character reasons, expansion by every replacement class, Unicode truncation, unchanged already-safe reasons, sanitizer fixed-point/privacy checks, malformed originals, wrong hashes and unchanged status/verdict/model requirements. Assert every full-run cell and all statistical outputs match private analysis; compare presentation/provenance fields separately.
6. Run the complete 104-receipt export through the unchanged production public reader, then run both documented analysis commands in clean `-S -B` subprocesses with private paths unavailable and no model/auth/network inspection. Retain individual terminal exits, original RED, successor GREEN, source hashes and final bundle hash. Explain the amendment transparently in the result report. Only after independent review/QA may the new publication artifact replace the failed export as the release candidate.

This is the smallest semantic repair: the already-established scientific reason schema and strict reader remain intact; only a sanitized, explicitly abbreviated public display string changes. It neither changes an observation nor creates a new study attempt. The substantive result and thresholds play no role in selecting or validating this repair.

## Gate decision

Architecture PASS to implement the separate publication amendment under the above frozen invariants. Publication remains BLOCKED until its independent reviewer and QA gates pass. Do not modify the failed bundle or frozen study files, weaken custody/length validation, relabel the affected grade, drop a cell, retry inference, or report the failed export as a success.
