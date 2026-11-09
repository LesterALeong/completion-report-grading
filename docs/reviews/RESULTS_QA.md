## QA Report

### Acceptance Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Approved, unchanged publication candidate and scientific closure | PASS | `freeze_final_candidate.py`: 423 files, candidate `5317c46dd208f231a37b8a2f168f2c4d25db29e392001e57cb5ea8755167b48c`; scientific `d2c2572ebcf506a162687a318e1410df11c37547f09363ec4d217891ee7f4027`, freeze `832bec41d955390f189fcd51d379f8299315cf6a10172f7e93487cc441a82e61`. |
| Amendment preserves evidence and changes display only | PASS | Actual production `prepare` reconstructed every successor byte and provenance, including publisher `3c20df4b3dd1be6c700a85589df0f1f91e111ff8b7a18d746bd139188ecfd04a`; retained producer red-to-green and grade/model refusal tests pass. Original manifest remains `ef3369c61e24c4b5a6c0417ee5eb8f25b77c4bbde39b86359d12b12c1750f94b`. |
| Public replay and private analysis agree | PASS | Cold subprocesses, absent private root, empty PATH, scrubbed PYTHONPATH and forbidden network/live adapters: holdout 72/72 and development 32/32 PASS. Cold JSON equals saved JSON; reconstruction verifies all private analysis fields equal except scope. Successor manifest `64c1ed196bbadcf02180463910ff47ae9db7f938efa8c86a5c2f8f9c64b33114`. |
| Report accurately distinguishes results and limitations | PASS | README and report checked against saved and private analysis: primary 4/12 versus 3/12 below two-case screen; mitigation 3/12 below target; controls 6/6; H16 flip and mitigation PASS; secondary 4 versus 2. AI assistance and public projection limits disclosed. 104 cells plus four canaries = 108/120. |

### Test Results and Edge Cases

- `python -m unittest discover -v`: **105 passed, no skips**, exit 0, 21.385s with authorized inert loopback. Initial sandbox run: 99 passed, six native HTTP failures at `tests/test_ollama_worker.py:110` because connection raised `PermissionError`; the same six passed with loopback access.
- `python -S -B -m unittest publication.tests.test_amend -v`, also with a fresh task-owned temporary root: **4 passed**. Exercises actual retained producer RED/GREEN, 299/300 boundaries, Unicode, redaction expansion, malformed input and grade/model refusal.
- Both documented analysis commands ran successfully; publisher `--help` succeeded without mutation. Cold subprocesses and actual publication reconstruction exercise real paths without model calls. The portable detector shows the predecessor rejection and repaired acceptance; missing/corrupt and custody failure tests fail closed.

### Defect-Ledger Verification

| Classes | Detector and observed output |
|---|---|
| 01/07/44 | Frozen closure and schedule tests passed; candidate reconstruction printed the exact source and freeze identities above. |
| 02/04/10/13/15/33 | Ruff F clean; actual producer RED/GREEN and refusal tests passed; cold subprocesses returned PASS; six sandbox connection errors surfaced explicitly. |
| 06/11 | Report and README checked against both replayed analyses and frozen thresholds; figures above match. |
| 08/09/12/34 | Native Windows suite reached terminal `OK`; explicit repository cwd and native subprocesses used. No pacing change. |
| 14/23/35/36/42/43 | Full publisher reconstruction and 423-file digest passed; four portable tests and full consumer replay passed. Git publication is outside this gate. |
| 03/05/16–22/24–32/37–41/45–50 | N/A to this publication-only amendment; no broker, clock, execution sizing, binary-offset or new transport change. |

### Build, Lint and Guards

- No separate build command is defined for this Python project. Documented `python -m ruff check --no-cache --select F study tests publication` exited 0, `All checks passed!`; Ruff 0.15.15 and both required hook scripts resolve. The host printed a `pip_system_certs` truststore injection `Permission denied` diagnostic during some ordinary Python invocations; offline checks completed successfully and the elevated full suite had no such diagnostic.
- Security: public-bundle scan found no local Windows user paths, obvious key patterns or private-key markers; publisher scan found no `eval`, `exec`, or hardcoded password/API-key assignment. This is a targeted check, not a security certification.
- Integrity and contracts: exact source/freeze/candidate identities, complete output reconstruction, strict reader, and full saved/private analysis equality passed. No performance limit was specified. Public replay cannot independently expose unpublished raw captures.

### Final Verdict

**FINAL_PASS / SHIP IT** for the reviewed code and results publication candidate. This is an independent QA gate, not human peer review, a course credential, or authorization for new inference. Package installation, tokenizer download and the create-only publisher were not executed; those operations mutate external or retained state.
