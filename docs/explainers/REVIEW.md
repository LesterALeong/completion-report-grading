# Explainer candidate review

## Verdict: APPROVED

Frozen successor candidate: `docs/explainers/candidate.json` SHA-256 `86abbf3395354dae72e73a34c9a2d76acfa6875ff511d0798365e8e78c26a4ae`. This review applies only to those bytes. All 11 candidate payload hashes and all build-manifest source hashes matched. Relative to the archived first candidate, changes are confined to content, HTML, architecture, and their generated derivatives; the renderer, poster, spec and protected source documents retain their hashes.

## Issues Found

None blocking. The prior batch is resolved: scene `s13`, generated captions and browser data now say exactly three **CRLF-to-LF** changes in presentation files, while the HTML states the same; all four companion learning steps explicitly allocate five minutes; the fictional character roles now agree across assets.

## Defect-Ledger Classes Checked

- **LEDGER-02 — clean:** QA's Ruff `--select F` includes `render_explainer.py`; the unchanged renderer's `--check` executed with exit 0. Root exercised the HTML script in Chrome, including edited H16 controls; QA separately checked JavaScript syntax. This is evidence for changed executable paths, not a claim that lint alone catches JavaScript key errors.
- **LEDGER-04 — clean:** The renderer's subprocess wrapper checks nonzero return codes and raises with bounded stderr. QA forced an exit-17 command and observed that failure, and separately rejected invalid narration. No model, API or broker call occurs in this bundle.
- **LEDGER-06/07 — clean:** The 2/3/4/3 counts, six controls, +1 primary result, +2 preregistered screen, mitigation target, 104/108/120 attempt counts, H16 values and 300/305 publication figures match `REPORT.md`, `INTERVIEW_GUIDE.md`, `README.md` and the frozen `SPEC.md`. The 105-test claim is supported by `docs/reviews/RESULTS_QA.md` and `tasks/todo.md`. No acceptance threshold moved after the result.
- **LEDGER-08 — clean for this scope:** The actual Windows SAPI/PowerShell/Pillow/FFmpeg render produced the frozen MP4; `ffprobe`, renderer `--check` and the local-file Chrome exercise worked on Windows. Native pacing, MSYS path conversion and HTTP TLS detectors are N/A because this bundle has no such clock, Git Bash native-tool call or new HTTP path.
- **LEDGER-09 — independently covered:** The source-edit mechanism is not established by this review, so hook firing is not claimed. QA ran Ruff F over the new Python file and executed its `--check` path; generated text and hashes were reopened. This addresses the ledger's unlinted-output risk for the reviewed bytes.
- **LEDGER-10 — N/A to rename detector:** No existing signature, key or caller was renamed. The new `content.json` → `media-data.js`/caption/transcript contract was checked by `render_explainer.py --check` and hash equality.
- **LEDGER-11 — clean:** Spoken, browser, transcript and source-document claims were compared; the earlier missing CRLF direction and five-minute labels were corrected. QA executed the documented renderer `--check` and public replay command from the repository root.
- **LEDGER-12 — clean:** Review Git and verification commands used the explicit repository workdir. No stash, reset, checkout or cleanup command was used.
- **LEDGER-14 — N/A:** The explainer renderer has no configured Git ref or irreversible remote dispatch; candidate and protected-source hashes were still compared against the declared baseline.
- **LEDGER-15 — clean at this bundle boundary:** The frozen `SPEC.md` section 4 matrix was exercised through source/hash checks, actual MP4 probe and supplied local-file Chrome evidence. Root's successor keyboard check used numeric edits 7/9, Tab and Space to toggle duplicate on/off, observed matching and mismatching outputs, visible focus, accessible labels and changing `aria-live` text. This proves labels and keyboard operation; it is not a full audible screen-reader-client test.
- **LEDGER-20/27 — N/A:** No release-contract transition or `scope.changed_paths` manifest exists in this additive bundle. The exact new-file inventory and tracked diff from `43cda33` were inspected; only `tasks/todo.md` is a tracked change.
- **LEDGER-34 — clean:** Verification claims use terminal exit 0 and final output: renderer `--check`, `ffprobe`, Ruff F, QA's 105-test `OK` summary and 72/72 public replay. The earlier sandbox loopback failures are disclosed in `QA.md` rather than folded into a false pass.
- **LEDGER-38 — clean:** `TEMP.mkdir(parents=True, exist_ok=True)` precedes external media commands. The real render produced the MP4 and sibling outputs; no assumption that FFmpeg creates the temp directory is needed.
- **LEDGER-44/45 — N/A:** No repository-wide attributes/workflow/packaging metadata or predecessor scientific closure was changed; QA independently verified 426 protected Git blobs. There is no governed embedded Python program or generated `python -c` payload. The fixed PowerShell speech script is part of the inspected renderer and was exercised by the actual Windows build.
- **LEDGER-01/03/05 — N/A:** No signal, broker clock, order sizing or trading logic is added by this documentation/media bundle.

## Positive Notes

- The film and companion keep the primary +1/12 comparison below its +2-case screen, report the mitigation miss and all correct controls, and explain H16 and study limits without claiming production safety, personal mastery or a hiring outcome. Generated text reaches the DOM through text nodes rather than HTML injection.
- The successor MP4 probes as H.264/AAC, 1280×720, 24 fps, 474.091 seconds and 6,952,260 bytes. Schema, cue timing, source identity and manifest hashes pass. Root reopened the successor in local-file Chrome and observed the revised plan and chapter metadata; the earlier offline Chrome exercise covered playback, burned captions, selectable English fallback, H16 controls and transcript. Human listening and word-perfect within-line synchronization are not established by this review.

## Gate Decision

**PASS → QA agent may proceed** on successor candidate `86abbf3395354dae72e73a34c9a2d76acfa6875ff511d0798365e8e78c26a4ae`.
