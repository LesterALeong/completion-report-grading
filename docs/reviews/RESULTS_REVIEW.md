## Verdict: APPROVED

Reviewed the coherent 423-file candidate with SHA-256 `5317c46dd208f231a37b8a2f168f2c4d25db29e392001e57cb5ea8755167b48c`. Task bookkeeping and the two final gate reports are excluded from that identity. This approves progression to final QA; it does not attest a later commit, push, or new inference run.

## Issues Found

None blocking. No source or artifact edits are requested.

## Evidence and conclusions

Read the actual publisher, portable regressions, frozen protocol/specification, postmortem, public provenance, report, README, interview guide and project log. Independently hashed all 423 candidate members. The current 25-file scientific closure reproduces `d2c2572ebcf506a162687a318e1410df11c37547f09363ec4d217891ee7f4027`; the freeze remains `832bec41d955390f189fcd51d379f8299315cf6a10172f7e93487cc441a82e61`.

Executed `publication.amend.prepare` read-only against the retained private bundle and archived failed public export. Its production loader and archived 56-file candidate checks passed. Every reconstructed successor byte and the entire sibling provenance object match the actual release candidate. The publisher identity reproduces `3c20df4b3dd1be6c700a85589df0f1f91e111ff8b7a18d746bd139188ecfd04a`.

The unchanged production public reader rejects the original manifest `ef3369c61e24c4b5a6c0417ee5eb8f25b77c4bbde39b86359d12b12c1750f94b` with `V2_VALID_CUSTODY` and accepts successor `64c1ed196bbadcf02180463910ff47ae9db7f938efa8c86a5c2f8f9c64b33114`. Exactly four bundle members change: receipts, the affected projection, its attestation, and the manifest. The amendment bounds one already-redacted display reason to 299 Unicode characters plus an ellipsis, requires a sanitizer fixed point, and preserves status, verdict and model. Transport records, raw commitments and unaffected files remain identical. Missing/corrupt inputs raise; the create-only publisher verifies its full output before returning success.

Ran separate clean `-I -S -B` subprocesses for both public analyses, with an absent private root, empty PATH and network/model/auth entry points forbidden. Both terminal exits were zero. All 32 development and 72 holdout cells reproduce; complete analysis objects match private verification after removing only the explicit scope label. Public artifacts were checked for local user paths and obvious credential patterns; none matched. Public commitments are correctly distinguished from independent access to private raw evidence.

The results remain honest: primary false approvals are 4/12 versus 3/12, a one-case increase below the frozen two-case screen. Mitigation is 3/12, a one-case reduction below its target. All six controls pass under every condition. H16 is the documented neutral FAIL to persuasive PASS flip; mitigation also passes H16. The secondary 4-versus-2 result does not replace the primary endpoint. Development is separate, and 104 grading calls plus four charged canaries equals 108, leaving 12 within the 120 cap. The documents explain synthetic scope, model limitations, AI assistance and uncertainty.

Feasibility is bounded by this dedicated dataset: 2,069,770 retained input bytes and 657,404 public output bytes across 327 members. Even holding two output byte maps alongside those inputs accounts for about 3.23 MiB of payload, before small JSON-object overhead. This is orders below the declared host RAM; no training or growing-corpus workload is introduced. Reconstruction plus both cold analyses completed in about four seconds. Three non-writing portable regression methods independently passed, including exact retained original RED/successor GREEN, Unicode/redaction boundaries and classification/model refusal. Full native regression execution remains final QA's gate.

## Defect-Ledger Classes Checked

- LEDGER-01/07: clean; frozen scientific inputs, split and thresholds preserved, with no endpoint substitution.
- LEDGER-02/04/10/13/33: clean; executed reconstruction and strict consumers, reproduced the original failure, preserved classification, and found no swallowed read failures.
- LEDGER-06/11: clean; result figures and H16 claims agree with actual analysis and protocol.
- LEDGER-08/09/12: clean for this scope; native PowerShell execution, explicit repository cwd and direct source inspection; no new pacing or native-CLI route.
- LEDGER-14/15/23/35: clean for the reviewed byte candidate; exact candidate, producer-derived fixture, full artifact consumer and canonical digest checks passed. Git publication remains downstream.
- LEDGER-34/36/42/43/44: clean; observed terminal outcomes, portable committed fixtures, actual full production inventory and unchanged predecessor scientific closure.
- LEDGER-03/05/16–22/24–32/37–41/45–50: n/a to this publication-only change; no broker, exchange clock, execution sizing, new transport, process containment, native-resource or binary-offset implementation.

## Positive Notes

The repair preserves failed evidence and frozen science while making the publication boundary executable. The report leads with the below-threshold primary result and clearly states what public replay can establish.

## Gate Decision

PASS → QA agent may proceed on this unchanged candidate.
