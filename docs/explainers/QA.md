# QA Report

Candidate binding: `docs/explainers/candidate.json` SHA-256 `86abbf3395354dae72e73a34c9a2d76acfa6875ff511d0798365e8e78c26a4ae`; reviewer verdict APPROVED for the same bytes. Independent SHA-256 comparison passed for all 11 listed payload files.

## Acceptance criteria

| # | Status | Evidence or gap |
|---|---|---|
| 1 | PASS | Root reports offline local Chrome reload, H16 interaction, playback, caption option, 16 chapters and transcript. Root subsequently keyboard-edited values 7/9 using Tab and toggled the checkbox with Space; focus and updated outputs were visible. The accessibility tree exposed both labeled spin buttons, checkbox and updated live-region text. Static inspection confirms native controls, focus styling and a common chapter handler. File-URL VTT raised a CORS error; root observed inline English fallback. No audible screen-reader test is claimed. |
| 2 | PASS | Actual subprocess probe: H.264/AAC, 1280x720, 24 fps, 474.091 s, 6,952,260 bytes; renderer check passed cue timing. Root saw playback and burned captions. Within-line timing is approximate; no human listening audit was performed. |
| 3 | PASS | Reviewer checked source claims; inspection of content and transcript confirms Codex admission closure, separately preregistered Qwen, repairs, study, amendment and no provider comparison. |
| 4 | PASS | Content and transcript state 2/12, 3/12, 4/12, 3/12, six correct controls, primary +1 versus +2 screen and one-case mitigation reduction versus two-case target. Reviewer checked against sources. |
| 5 | PASS | Content/transcript explain first versus last record and four H16 decisions; root reports interactive 1/2 and 7/9 duplicate and distinct-key tests. |
| 6 | PASS | Content, transcript and companion state the 300-to-305 redaction amendment and exactly three CRLF-to-LF presentation changes with scientific closure unchanged; reviewer checked sources. |
| 7 | PASS | Inspected all six required glossary definitions and four explicit five-minute activities; plan covers tracing, replay, amendment and explanation. Root observed four headings. |
| 8 | PASS | Reviewer checked originality and sources. Independent `verify_git_closure.py HEAD` reports 426 canonical protected blobs PASS; tracked diff is only `tasks/todo.md`, plus the additive explainer bundle. |

## Test results and static checks

- `python docs/explainers/render_explainer.py --check`: exit 0, `Schema, cue timing, source identity, and manifest hashes pass.` Python startup emitted `pip_system_certs` truststore permission warning.
- `python -S C:/Users/leste/Downloads/Repos/_tmp/completion-report-grading/check_explainer_artifact.py`: exit 0; output confirmed above media metadata, mean loudness -16.8 dB, peak -0.1 dB and `text_crlf_files: []`.
- Extracted inline script piped to `node --check`: exit 0. HTML has one inline script and one local JS dependency. Source roles identify Morgan as founder and Casey as engineer; generated transcript agrees. Exact CRLF-to-LF statement appears in both content and companion.
- `python -m unittest discover -v`: 105 tests OK in 19.759s with local loopback access. Earlier sandboxed run had six `tests.test_ollama_worker.NativeHTTPTests` failures caused by `PermissionError` on loopback; the same six passed in the rerun. No inference ran.
- `python -m ruff check --no-cache --select F study tests publication docs/explainers/render_explainer.py`: all checks passed.
- Public replay documented in README, run as the exact `python -S -B -m study analyze ...` subprocess with PYTHONPATH removed: exit 0, 72/72 valid cells, status PASS, primary +1 against threshold 2, mitigation target not met.
- Independent Git closure: `python -S C:/Users/leste/Downloads/Repos/_tmp/completion-report-grading/verify_git_closure.py HEAD` produced `{"blobs": 426, "ref": "HEAD", "status": "PASS"}`.

## Edge cases and browser evidence

Root separately reports Chrome `file://` with offline emulation and reload; H16 with duplicate on/off and 1/2 and 7/9 values; actual video progression and burned captions; local English caption fallback despite VTT file-CORS error; transcript, 16 chapters and 960px layout. Root reports network restored with GoOnline. On the regenerated candidate root reloaded the guide, saw four five-minute headings, played at 0:07 and sought to 5:52 to see the corrected CRLF-to-LF card. These are supplied observations, not this QA agent's browser observations. This QA did not control the browser; another helper request was in flight.

Imported actual renderer `run()` with a child exiting 17 and stderr `forced-sentinel`: it raised RuntimeError containing both. Actual `validate()` rejected empty narration, invalid speaker and empty scenes with AssertionError. Static inspection shows empty/noninteger H16 values receive an error announcement; runtime empty-input interaction and audible screen-reader announcements were not exercised. Root separately verified keyboard input, tab focus and space toggle, and the accessibility tree labels and live-region text. No model or new inference ran.

## Defect-ledger verification

Ledger read from `C:/Users/leste/.Codex/defect-ledger.md`. The final reviewer audit identifies applicability and evidence per class; evidence is distinguished below from independent QA executions.

| Class | Detector and evidence | Status |
|---|---|---|
| 02/09 | QA Ruff F, renderer `--check` exit 0, JS syntax check and root Chrome interaction; reviewer does not claim hook firing. | CLEAN |
| 04 | QA forced external subprocess exit 17; actual `run()` raised with exit and stderr. | CLEAN |
| 06/07 | Reviewer compared source numbers and thresholds; QA checked content and executed public replay. | CLEAN |
| 08/38 | Root-supplied real Windows renderer build; QA renderer check and MP4 probe; reviewer inspected temp creation before media commands. | CLEAN |
| 10 | No existing signature/key rename; generated contract checked by renderer. | N/A to rename detector |
| 11 | QA grep found corrected three CRLF-to-LF statement and four five-minute labels; renderer check and documented public replay passed. | CLEAN |
| 12 | Review and QA commands used explicit repository working directory; no cleanup or stash. | CLEAN |
| 14 | No configured Git ref or irreversible dispatch in renderer. | N/A |
| 15 | Frozen matrix, hash/media checks and root-supplied offline, keyboard and accessibility-tree observations; no audible screen-reader claim. | CLEAN |
| 20/27 | No release-contract transition or changed-path scope manifest in additive bundle; reviewer inspected inventory. | N/A |
| 34 | QA retained command exit and final summary, including initial sandbox failures and successful rerun. | CLEAN |
| 44/45 | No project-wide packaging/attributes or frozen scientific closure change; no governed embedded Python program. QA verified 426 Git blobs. | N/A |
| 01/03/05 | No signal, broker clock or sizing logic added. | N/A |

Root additionally confirmed that the three manifest-bound source-document hashes equal actual HEAD Git blob hashes. Root's successful renderer build and browser observations are supplied evidence rather than this agent's direct executions.

## Build, lint and guards

| Guard | Status | Evidence |
|---|---|---|
| Pre-existing tests | PASS | 105 tests OK after local-loopback access; initial sandbox failure documented above. |
| Build | PASS (supplied evidence) | Root supplied successful renderer build for the frozen candidate; independent renderer `--check` and media probe pass. No separate project build system. |
| Lint | PASS | README F checks plus renderer passed. |
| Hook availability | PASS | `ruff --version`: 0.15.15; both required hook script paths exist. |
| Security regressions | PASS (scoped) | Additive HTML/JS/content/renderer scan found no external asset, secret or eval; subprocess uses argument lists, fixed PowerShell script and stdin narration. |
| Scientific files | PASS | 426 canonical protected Git blobs match; tracked diff limited to `tasks/todo.md`. |

## Final verdict

**SHIP IT** — all acceptance criteria and scoped guards pass on the bound candidate. The initial sandbox loopback failures resolved on rerun; the truststore startup warning and file-CORS fallback are recorded above. No human audio assessment, audible screen-reader test or word-perfect caption claim is made.