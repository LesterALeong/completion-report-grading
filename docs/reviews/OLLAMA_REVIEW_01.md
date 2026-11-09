## Verdict: APPROVED

Offline candidate only. Reviewed against `docs/SPEC.md` and `docs/OLLAMA_ARCHITECTURE.md`; authentic inference compatibility is deliberately pending. This review permits the QA stage, not study dispatch or publication.

Candidate SHA-256: `0424be7750a715f632ef700df04d35cc5e393715ac19c81d5c9aa45b134beafd`.

Scientific SHA-256 recorded in preflight: `d2c2572ebcf506a162687a318e1410df11c37547f09363ec4d217891ee7f4027`.

Independently reopened all 56 candidate file hashes from the saved preflight map: zero differences. Independently reproduced the canonical candidate digest and archive SHA-256 `9b6b9e333dcb895c00f3a5d5620202c5a370f95287606ecee59fc639745bd87e`; every mapped file also matches the retained ZIP. This review file is outside that closure.

## Issues Found

- No blocking issue found in the reviewed offline candidate.
- [SUGGESTION] `study/__main__.py:24`: preflight help still describes “offline ... CLI checks”, although v2 performs local HTTP metadata inspection. In a subsequent coherent candidate, describe protocol checks and local runtime metadata inspection. The README accurately explains the live metadata boundary, so this wording does not invalidate admission or replay.

## Defect-Ledger Classes Checked

The local authoritative ledger was consulted, including the Ollama missing-`done` recurrence and authentic producer requirements. “Clean” below means source and available offline evidence inspected; it does not claim execution of pending native/authentic QA detectors.

- LEDGER-01: clean — fixed scientific inputs, separate oracle, one-message requests, marker commitment and explicit absence from exact request; no grading outcome used for transport selection.
- LEDGER-02: clean — request, parser, projection and adapter paths execute in the independent pure checks; actual runner/export/analysis caller tests and native tests are present in the retained suite.
- LEDGER-03: clean — UTC-aware saved timestamps and strict replay time checks; no exchange/broker clock involved.
- LEDGER-04: clean — native/HTTP/completion uncertainty wins over content; `done is True`, HTTP 200, complete body, exact model and custody are required; failures never supply verdict/reason. Partial or missing capture evidence blocks replay.
- LEDGER-05: clean — fixed controls and bounds match the approved protocol; request integer controls reject Boolean substitutes. No financial instrument units.
- LEDGER-06: clean — canonical reservations determine counts; retained historical bytes and create-only manifest are reopened. Budget arithmetic is 32 + 72 = 104 study cells; two historical attempts leave 14 of 16 canary slots; 104 + 16 = 120 total.
- LEDGER-07 / LEDGER-20: clean — frozen spec thresholds and scientific mathematics retained; provider change is explicitly pre-outcome and separately documented.
- LEDGER-08: clean for source/offline scope — isolated absolute worker path, real native Job composition tests, finite inference/cleanup bounds and no daemon ownership claim. Final native QA must execute these tests on this unchanged candidate. No strict external pacing rule applies here.
- LEDGER-09: clean — source read directly; retained full suite inspected; root reports Ruff F clean. No Bash source-write path introduced by this review.
- LEDGER-10 / LEDGER-11 / LEDGER-12: clean apart from the help suggestion — explicit v1/v2 contracts, composed runner/export/public reducer test, clean subprocess replay, absolute worker path and anchored task paths.
- LEDGER-13: clean — missing, corrupt, mixed-version or incomplete inventories refuse; no private-to-public fallback.
- LEDGER-14 / LEDGER-21 / LEDGER-23 / LEDGER-27 / LEDGER-35: clean — exact candidate map and archived bytes independently reopened; source/config/request/runtime/history/capture/admission/freeze joins inspected; canonical JSON reproduces the candidate hash.
- LEDGER-15: clean for the offline stage — actual producer-worker and caller composition tests exist; authentic producer compatibility is not inferred from consumer fixtures. Authentic retained canary bytes and production private/public replay remain mandatory after native QA.
- LEDGER-16 / LEDGER-29: n/a to CLI admission/cold tool installation — active inference uses the fixed standard-library HTTP worker, without CLI discovery or bootstrap.
- LEDGER-17 / LEDGER-18 / LEDGER-19 / LEDGER-22 / LEDGER-24 / LEDGER-25 / LEDGER-26 / LEDGER-28: n/a — no extracted native runtime deletion, broker execution/calendar/order policy, test-created Git commit or mutable canonical release fixture introduced.
- LEDGER-30: clean — public canary/study entrypoints require explicit authorization before their operator-locked dispatch paths; no externally reachable tool or alternate network route added.
- LEDGER-31: clean within declared limit — pre/post observed model/server/client identity is bound; artifact identity is expressly not atomic daemon identity or deterministic GPU arithmetic.
- LEDGER-32 / LEDGER-39 / LEDGER-47 / LEDGER-49: unchanged native supervisor inspected with new HTTP caller; Job assignment precedes worker release, timeout and forced cleanup cannot grade, and the pre-existing daemon is outside task ownership. Native fault/descendant tests remain QA responsibility.
- LEDGER-33: clean — transport truth predicates, status precedence, strict typed receipts and private/public replay comparisons inspected; a non-valid study receipt terminates the accepted prefix.
- LEDGER-34: clean — independent command below returned terminal exit 0 and `Ran 7 tests ... OK`; retained full-suite log ends `Ran 101 tests in 20.130s` and `OK`. The latter was inspected, not independently rerun here.
- LEDGER-36 / LEDGER-37 / LEDGER-38 / LEDGER-40 / LEDGER-41 / LEDGER-42 / LEDGER-43 / LEDGER-44 / LEDGER-45 / LEDGER-46 / LEDGER-48: no new applicable mechanism — no untracked scientific dependency, platform spoofing, external renderer, synthetic production identity claim, cache workload substitution, release gate rewrite, embedded executable generator or broker callback adapter.

## Positive Notes

- Literal loopback HTTP transport has no proxy, redirect, auth, tool dispatcher or provider fallback. Raw body custody remains separate from native and HTTP metadata.
- Private replay verifies raw captures; public replay verifies sanitized projections and explicitly limits its claim. Export integration deletes private evidence before the clean standard-library subprocess replay.
- Historical failures remain charged and cannot satisfy v2 admission. Reservation precedes dispatch; study prefix validation prevents retries and continuation after failure.
- No scientific estimator or missingness denominator change was found. The final model, canary and study evidence is not confused with inert fixture results.

## Evidence and Resource Limits

Independent read-only command: `python -S -B -m unittest tests.test_ollama tests.test_ollama_worker.RequestTests -v`; terminal exit 0, seven tests passed in 0.009 seconds. No HTTP server, daemon query, model call, auth, Git operation or source/test modification was performed by this review.

Read the retained 101-test terminal summary and relevant test/source bodies, including native HTTP timeout/incomplete/oversize custody, v2 runner failures, historical integrity, evidence mutations, and portable export. Root reports full-suite exit 0 and Ruff F exit 0; this review does not substitute that report for the required independent native QA.

The response bound is 8 MiB per serial call plus one overflow-detection byte; 104 study bodies would therefore consume at most 832 MiB, or 960 MiB for 120 capped bodies, excluding small metadata/diagnostics. Replay streams raw captures one at a time rather than loading a corpus. The spec inventory reports a 6,594,474,711-byte model (about 6.14 GiB) on 16 GiB VRAM with about 15 GiB free at inventory time. Actual latency, KV/runtime overhead and current capacity are not established by this code review; finite outcome-blind admission remains the approved feasibility gate. The 180-second inference bound gives 104 × 180 = 18,720 seconds (5.2 hours) of maximum client inference waiting, excluding metadata/cleanup. No inference throughput claim is made.

Known limits: incomplete captures safely refuse replay/export; public commitments do not prove unpublished raw equality; native client cleanup does not establish daemon-side completion; pre/post identity observations are not atomic execution attestation. These limits are disclosed and do not permit a grade on uncertainty.

## Gate Decision

PASS → QA agent may proceed on the unchanged candidate. After native inert QA passes, root may perform the already-authorized outcome-blind authentic admission canaries as the next QA boundary. Retain and replay their exact raw body/HTTP metadata and sanitized projections through production readers; stop and charge any failed attempt. This review does not approve study freeze, study calls, publication, or claims that authentic compatibility has already passed.
