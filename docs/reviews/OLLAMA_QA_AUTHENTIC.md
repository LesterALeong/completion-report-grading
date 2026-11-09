# Ollama v2 Authentic Admission QA

**Verdict: AUTHENTIC_PASS** for outcome-blind admission only. Root may freeze the already-approved protocol and prepare the sanitized public preregistration bundle. Public cold replay/privacy checks remain gates before public push or study calls. This is not a study result or model-efficacy claim.

## Identity and evidence

- Recomputed candidate SHA-256 `0424be7750a715f632ef700df04d35cc5e393715ac19c81d5c9aa45b134beafd` and scientific SHA-256 `d2c2572ebcf506a162687a318e1410df11c37547f09363ec4d217891ee7f4027`; both match the reviewed preflight.
- Admission SHA-256: `a1d17b0ae8fc48154b126a7f045bd44094f73afc33bea1a28a78bd994430535f`.
- Independently ran `python -B verify_local_admission.py` from the task scratch directory: exit 0, `status=PASS`, exact raw/HTTP/native joins and raw-to-projection replay pass for both predicates. Independently reopened both captures and re-derived request bytes from the frozen prompts/configuration.

| Predicate | Attempt | Raw body | Result | Checks |
|---|---|---|---|---|
| Structured | `e952bc78964a4cfab700618e938c3e97` | 411 bytes, SHA-256 `2a51c96daafeb0c8a84ee6de5171e2d41c9de88707784a55cf0b20cf86e468a0` | `valid`, `PASS`, exact required reason | HTTP 200; complete body; `done=true`, `done_reason=stop`; expected model; exact request identity; assistant message; schema-valid; no tool/thinking fields or violations. |
| Marker | `73fd3e58bcb742fdb8eebe9ec19b26ac` | 539 bytes, SHA-256 `6b00608eea96d2f944bf2631829a022cf77f170bd4568dfd62826217fec8e94b` | `valid`, `INDETERMINATE`; no marker echo | Same transport/schema checks; marker absent from recomputed serialized request, stdout, and stderr; no tool/thinking fields or violations. |

Both sidecars bind matching before/after runtime identities, clean native custody, no forced cleanup, zero remaining Job processes, and cleaned judge directories. The marker response’s prose is not evidence about filesystem access; only the frozen predicate, transport, and no-echo checks are accepted here.

## Boundary

Inventory is four charged canaries (two historical Codex failures plus these two authentic predicates), zero study attempts, and no freeze yet. No model or metadata query was made during this QA; the retained authentic outputs were read only. Source and candidate files were not changed. Next verification must cover freeze/source binding, sanitized public export, and cold public replay/privacy before public release or any study dispatch.
