# Preregistration release checks

Root release verification after independent code review, offline/native QA and authentic admission QA passed. This records the remaining public-artifact checks; it is not an independent human review or a study result.

- Reviewed candidate: `0424be7750a715f632ef700df04d35cc5e393715ac19c81d5c9aa45b134beafd`.
- Scientific source: `d2c2572ebcf506a162687a318e1410df11c37547f09363ec4d217891ee7f4027`.
- Frozen protocol: `832bec41d955390f189fcd51d379f8299315cf6a10172f7e93487cc441a82e61`.
- Public admission manifest byte hash: `c325ee032dacbbcfa92800b0f28d7d18085b00aa704191e62ac832361ec384ee`.

`python -m study export` passed private verification and public producer-projection verification. The create-only `results/admission` bundle contains four charged canaries, including the two original failures, and zero study attempts. All 104 grading cells remain unattempted at this checkpoint.

A clean `python -I -S -B` subprocess replayed holdout through the actual CLI and returned `PASS`, `public_projection_replay`, 72 planned cells and zero valid cells. Its private root did not exist; `PATH` was empty, `PYTHONPATH` and model/auth environment overrides were removed, and socket connections plus live model/CLI inspection and dispatch functions were patched to raise. No private directory was created. The public bundle is 71,780 bytes.

The root inspected the allowlisted public files and scanned the bundle and repository for local personal paths, raw capture path fields and credential-like literals; no matches were found. Published artifacts contain synthetic project inputs, safe projections and hash commitments. Private captures, native diagnostics, random marker contents, course answers and account data remain outside Git. Public commitments do not prove unpublished raw-byte equality.

PASS for initial preregistration publication and the frozen one-shot study. The independent reviews and actual 101-test/native matrix remain applicable to the unchanged scientific source. Scientific results and final report review remain pending.
