# Offline / Native QA 02

**Verdict: OFFLINE_PASS** for one changed-premise structured falsifier. This does not admit authentic transport, host Code Mode, freeze, or study calls.

## Candidate and evidence

- Recomputed the complete 40-file candidate map and 22-file scientific map: exact match to approved roots `b9085e29a799d820156d67d35c7fc22fad4ebf28effc9d0cd7026dbb065904c7` and `a5301b34f40510dd1ba3853b5647c05243077e88e91c9c09335abdc25cbdc4ec`.
- Full suite: `python -B -m unittest discover -v` → exit 0, **69 passed, 0 failed, 0 skipped**, including all 8 native Win32 Job tests. Ruff F: `python -B -m ruff check --no-cache --select F study tests` → exit 0, all checks passed. Ruff 0.15.15 resolves; both required hook scripts exist.
- Amendment-specific regressions passed: nested `features.code_mode.enabled=false` is rendered; `code_mode_host` remains in the disabled-feature list; provider `item.error` refuses a grade without falsely reporting a tool; operational failure takes precedence while tool/protocol flags are preserved; raw-to-projection provenance is bound.
- Reopened retained original attempt `2a22e64d73ff4fc6826545dd436ae518`: receipt SHA `791e68c26518fd97743039bb1eab9a74898ae7de685c6a611fd17f1d90fac6aa`, sidecar SHA `eb1e814f05747dff175f4b63f4dc8c3e38674a97c824352d435a38d643e8b3a5`, raw stdout 640 bytes/SHA `71e1829d3c56918c98b150d0d6ea03588aeacedbc4fe212c53f19f330500d60b`. Its 289-byte sanitized fixture SHA is `581b93aa35a7f0d6ff435cddcd43fbdb498dda45670efecda9ba6079e383f8a3`; the full suite reopened and checked the raw binding. Original attempt remains failed, with no grade/admission.
- Current inventory remains 1 canary attempt, 0 study attempts, one retained canary run, no freeze. This QA made no model calls and did not alter the retained attempt. The host `pip_system_certs` startup diagnostic appeared, but commands completed with exit 0.

## Gate assessment

| Area | Result |
|---|---|
| Frozen scientific cases, reports, analysis, and budgets | PASS; unchanged prior acceptance evidence applies. |
| Parser, provider failure taxonomy, capture projection, and failure precedence | PASS offline; amendment regressions and full matrix pass. |
| Windows custody, cleanup, and failure paths | PASS offline; 8 native tests ran, no skips. |
| Subscription startup syntax | PENDING authentic falsifier; feature listing cannot establish that the installed host accepts this nested flag. |
| Marker predicate | Run only if the structured predicate succeeds. `run_canaries` returns immediately after structured failure. |
| Final QA, freeze, study execution | PENDING authentic producer evidence and final QA. |

The original provider bootstrap error invalidated the PASS-shaped final. The successor classifies its authentic `item.error` as `operational_unknown`, with no grade and no false tool classification. The host remains disabled (`code_mode_host`). If the same startup error recurs on the changed-premise attempt, preserve it and close this path; do not retry unchanged source/configuration or enable the host. The existing runner requires budget for the pair, but will reserve/run the marker only after structured success.

**Authorized next step:** root may execute the canary command once with an explicit `--changed-premise` explanation for the nested Code Mode configuration repair. Require the structured receipt to be `valid`, `PASS`, exact reason `structured response available`, no tool event, no marker echo, and clean custody. Only on that success may the marker predicate run; it must be `valid`, `INDETERMINATE`, tool-free, marker-free, and cleanly captured. Retain/replay both actual producer captures through parser, verifier, receipt writer, and sanitizer. A failed structured attempt consumes its slot and terminates this path. Request final QA on retained authentic evidence before freeze or any study call.

No build target is configured. This is independent AI review/QA, not human peer review or successful authentic admission.
