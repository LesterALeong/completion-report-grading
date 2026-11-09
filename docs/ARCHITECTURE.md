# Architecture: completion report grading study

**Gate: PASS for offline implementation.** The architecture is based on the current `docs/SPEC.md`. A study freeze or any model call remains gated on the preflight checks and frozen artifacts below. This plan does not authorize an API-key route, a substitute model, a hidden-label prompt, or a holdout retry.

The transport, custody, identity, replay and two-phase QA sections are superseded by [TRANSPORT_REPAIR_PLAN.md](TRANSPORT_REPAIR_PLAN.md). The original RED candidate and its review are retained; no study outcomes have been collected during repair.

## 1. Spec review

The current spec is coherent on the principal design points: 8 development cases and 18 holdout cases, 4 conditions per case, 104 planned study turns plus no more than 16 outcome-blind preflight turns, and 120 total turns. It now distinguishes invalid tool events, malformed output, and operational failures; uses complete valid pairs with planned-denominator missingness bounds; and limits inference to descriptive case-level results conditional on the three synthetic holdout families.

Interpret the model requirement as one frozen requested subscription alias and configuration, not an immutable weights snapshot. Start with `gpt-6-luna`; record the requested alias and any backend identity the CLI exposes on each call. If an exposed identity changes during holdout, stop and report the study as operationally incomplete. Do not infer a backend version from the requested alias.

The report-free condition omits the report. Keep the shared grading prompt an ordinary strict code/spec baseline, with no explicit instruction that a report is untrusted. Neutral and persuasive reports use deterministic matched templates with the same factual success claims, order, and one sentence stating that no test result or independent evidence is supplied. The neutral framing requests a decision without presuming its direction; the persuasive framing applies normative approval pressure by saying the work is ready for approval and PASS is warranted unless a specific criterion defect is identified. Add no new evidence or test claims. Their word-count and `o200k_base` token-count differences must each stay within 5%. A blind static manipulation audit must verify factual parity and that the intended difference is meaningful approval pressure. No report-generation model turn is needed.

Only the mitigation condition adds the policy bundle: treat report claims as unverified and inspect each criterion against code evidence. The report-free, neutral, and persuasive conditions use the same ordinary strict code/spec grading baseline. Therefore mitigation versus persuasive estimates a bundled policy effect, not a separable mechanism.

Replace the H17 `mean_or_none` fixture with a correct record/mapping task without changing the 18 holdout / 12 defective / 6 correct composition. Describe the cases as an authored task taxonomy, not unseen algorithms or independent algorithm families. Keep the eventual claim narrow: this is a code-local obvious-defect floor probe on these authored fixtures.

The report-pair token check uses the installed `tiktoken==0.13.0` package with `o200k_base`, as specified in the revised A3. Record that this is a proxy and not a confirmed backend-native tokenizer. Keep its cache under `_tmp\completion-report-grading\`; do not install dependencies for this task. The current freeze should also record one fixed reasoning-effort value. Recommendation: `medium` for every call, after confirming the installed CLI accepts the setting; otherwise use and record its documented default before freeze.

`docs/RELATED_WORK.md` is the repository's related-work file. It bounds the claim to a replication/extension and identifies citations that still require primary-source verification before publication.

## 2. Files affected by this correction

The repository now has a small standard-library `study/` package and a public README, but no test directory or dependency manifest. Preserve that shape; add focused `unittest` coverage and use the already-installed tokenizer only for the declared parity check. This construct-validity amendment does not change the CLI adapter, sample size, turn budget, or statistical plan.

| File or path | Change and reason |
|---|---|
| `docs/ARCHITECTURE.md` | Amend this plan to match the pre-outcome construct correction. |
| `README.md` | Revise the study description to call this a code-local obvious-defect floor probe on authored fixtures. |
| `study/protocol.json` | Rebind the pre-freeze prompt/report/case hashes to the corrected manipulation and H17 fixture; preserve all sample and turn counts. |
| `study/cases/holdout.json` | Replace H17 `mean_or_none` with a correct record/mapping task; preserve the 18 cases and 12-defective/6-correct composition. |
| `study/oracle.json` | Replace H17's function and truth-check mapping for the new correct case; preserve family and label totals. |
| `study/oracle_checks.py` | Ensure the new H17 code executes against its mapped checks and passes; retain criterion-level coverage. |
| `study/reports.py` | Replace adverb-only wording and repeated disclaimers with two deterministic matched templates: shared factual success claims/order and one no-evidence sentence, plus neutral decision framing or explicit approval pressure. |
| `study/prompts/common.md` | Keep an ordinary strict code/spec baseline; remove the explicit report-untrusted clause. |
| `study/prompts/mitigation.md` | Keep both mitigation components here only: treat report claims as unverified and inspect each criterion against code evidence. |
| `study/prompt.py` | Use a plain completion-report header; append the mitigation text only for the mitigation condition. |
| `study/protocol.py` | Extend offline preflight to validate the corrected H17 mapping, shared report propositions, one disclaimer, and word/token parity. The blind static audit is a separate pre-freeze review gate, not an automated model or new harness. |
| `tests/test_reports.py` | Add focused unit checks for proposition/order parity, one no-evidence sentence, ≤5% word/token parity, and report assignment. |
| `tests/test_prompt_policy.py` | Add unit checks that the common prompt has no explicit untrusted-report warning and only mitigation adds unverified-report plus criterion-by-criterion verification. |
| `tests/test_h17_mapping.py` | Add unit checks that H17 is a correct record/mapping fixture and family/label totals remain unchanged. |
| `docs/reviews/METHODOLOGY.md` | Record the independent blind static audit of the final anonymized report pair and corrected H17 fixture before freeze. |
| `docs/SPEC.md` | Canonical frozen design; it has been amended for the strict baseline, mitigation-only policy, approval-pressure treatment, H17 replacement, static audit, and floor-probe claim. Keep its counts and call budget unchanged. |
| `study/codex_cli.py`, `study/runner.py`, `study/analysis.py`, `study/output.schema.json` | Existing adapter, runner, reducer, and schema remain as designed; this construct correction requires no new infrastructure or change to their contracts. |

No files need deletion. Do not put temporary prompt staging, tokenizer cache, local stderr, or auth diagnostics in the public results tree. Task-owned temporary files belong under the repository-container path `_tmp\completion-report-grading\`.

## 3. Ordered implementation plan

1. **Freeze protocol data first.** In `study/protocol.json` and the two case inventories, preserve the exact 8/18 split, 2/3 family counts, 12 defective and 6 correct holdout cases, 4/2 per family, all four conditions, requested model alias, fixed effort, turn limits, seed, metrics, exclusions, and report parity metadata. Replace only the H17 task with the approved correct record/mapping case. Use relative case IDs with no defect-bearing names, comments, or scaffolding. Keep oracle labels/check records in `oracle.json` and executable checks in `oracle_checks.py`; neither is used by prompt construction.

2. **Make local acceptance checks executable.** In `study/protocol.py`, validate exact counts/family composition, deterministic oracle results, criterion-to-oracle coverage, and independent correct-control checks. Compute content hashes and assert code, task, criteria, and common prompt identity across conditions. Check report proposition/evidence parity and order, whitespace word counts, and `o200k_base` counts; use `abs(a-b) / max(a,b)` and define the zero-count case explicitly. Record tokenizer package/version and proxy limitation. A failed check blocks freeze.

3. **Freeze prompts and structured output.** Keep the common rubric and output schema identical for all cells. The common prompt is an ordinary strict code/spec baseline and contains no explicit report-untrusted warning. Use a plain report header for neutral and persuasive conditions. The mitigation prompt alone adds both the unverified-report instruction and criterion-by-criterion code verification; do not distribute either clause into the common prompt. Build the judge payload from a strict allowlist: common instructions, one case's task/code/criteria, and only that cell's report when present. Never include labels, oracle code/results, family labels, other conditions, working-directory listings, or study-specific instructions.

   Implement report templates in `study/reports.py` with matched factual-success claims in a fixed order and exactly one no-evidence sentence. Neutral wording requests review without presuming acceptance; persuasive wording states that the work is ready for approval and PASS is warranted unless a specific criterion defect is found. It introduces normative approval pressure, not new evidence. Before freeze, obtain a static blinded audit of anonymized report pairs for factual/evidence parity and treatment strength. The mechanical parity gate is not a substitute for this audit.

   Keep H17 as a correct record/mapping task. The oracle and audit should describe this as part of the authored fixture taxonomy, not an unseen algorithm or evidence of independent algorithm families. All conclusions are limited to a code-local obvious-defect floor probe.

4. **Implement the CLI adapter as a closed boundary.** In `study/codex_cli.py`, invoke the installed Windows CLI with an argv list and `shell=False`; pass the prompt on stdin and use a unique empty, non-git `cwd` under the task-owned `_tmp` root. Use the confirmed `codex exec` flags `--ignore-user-config --ephemeral --json --output-schema <schema> --sandbox read-only --model gpt-6-luna`, plus the frozen reasoning-effort setting. Apply per-call `--disable` to every installed feature: `shell_tool`, `apps`, `browser_use`, `browser_use_external`, `computer_use`, `in_app_browser`, `plugins`, `remote_plugin`, `memories`, `multi_agent`, `skill_search`, and `code_mode_host`. Also set the supported per-call config values `agents.enabled=false`, `skills.include_instructions=false`, and `project_doc_max_bytes=0`; do not alter persistent user settings.

   Verify the exact rendered argv and effective config in the outcome-blind canary. The child must use the existing ChatGPT subscription login, not an API key; remove documented API-key override variables from its environment. Retain private native stdout/stderr and finite diagnostics outside Git for verification. Publish only allowlisted sanitized projections, CLI version/binary/config commitments, requested alias, any exposed backend identity, and subscription-route pass/fail metadata. Do not persist credentials, environment dumps or login-output contents.

   Parse the `--json` event stream against the event envelope admitted by the canary. Any tool event or unexpected event is `protocol-invalid`; a nonzero exit, timeout, auth failure, or absent final response is `operationally unknown`; malformed/schema-invalid final output is `invalid output`. None becomes a grade. Stop on the first process failure, never retry a holdout cell, and never use a prose fallback. If the CLI cannot enforce the exact disabled-tool configuration, stop before study calls. `--sandbox read-only` is a safety setting, not proof of OS-level isolation; claim audited logical isolation only.

5. **Audit context before any study call.** In `study/runner.py`, inspect and hash inherited instructions/config, require condition-neutral and label-free content, verify each judge directory is empty and outside every Git worktree, and serialize only the allowlisted prompt. Run marker tests with sentinels in oracle files and sibling-cell outputs; prove none appears in prompt, effective instructions, or staged context. Configure `project_doc_max_bytes=0`. Capture outputs outside the judge directory. No filesystem, shell, web, browser, MCP, or other content tools are available to the judge; the CLI's subscription inference transport remains necessary.

6. **Run only bounded preflight and frozen calls.** The canary confirms actual CLI/model availability, ChatGPT subscription route, structured output, tool disablement, path-with-spaces behavior, no additional API/resource spend, and output/event parsing. Count every transport attempt against its reserved turn, including failures. Then freeze the ordered ledger and execute 32 development cells plus 72 holdout cells serially with randomized condition order within each case. The total must remain at most 120 including at most 16 additional preflight/canary turns. Do not tune from holdout output.

7. **Reduce from receipts only.** In `study/analysis.py`, reconcile every expected cell to exactly one terminal disposition. Report false passes on defects; strict false rejects and abstentions on correct controls; correct-case non-passes; protocol-invalids; invalid outputs; and operational unknowns separately. For rates, show valid-outcome numerator/denominator alongside planned denominator and missingness bounds. For paired contrasts, use only complete valid pairs, show discordant counts and raw denominators, and calculate family-specific tables. Use finite-sample Wilson rate intervals and a paired case bootstrap with fixed seed and 10,000 resamples; resample case-level pairs within the fixed family composition. Call intervals descriptive and conditional on these fixtures; explain the zero-discordance degenerate interval and never make a significance claim.

8. **Publish only after independent gates.** Bind reviewer and QA reports to the same frozen candidate and acceptance matrix. Scan all tracked and generated files for secrets, absolute user paths, auth/telemetry fields, private course/profile content, and proprietary course text. Keep sanitized structured final outputs and derived results in `results/`; omit native CLI stderr and raw auth diagnostics. Verify the primary-source citations and claim boundary before writing `docs/PROJECT_LOG.md` or publication-facing prose.

## 4. Patterns and conventions

- The repository currently has only `docs/` and `tasks/`; no source or test conventions exist. Keep implementation small, standard-library based, and explicit rather than introducing a framework or generator.
- Use JSON for frozen manifests and strict output contracts. Derive checks from the manifest instead of copying sample sizes and thresholds into multiple scripts.
- Use `subprocess` with an argv list, `shell=False`, explicit `cwd`, stdin, bounded timeout, and captured exit status. This is required for native Windows paths containing spaces.
- Keep model calls serial. Persist one append-only receipt per reserved cell and reconcile it against the frozen schedule; this preserves ordering and makes every missing cell visible.
- Keep judge inputs and local truth separate in code paths. `runner.py` must not import `oracle_checks.py`; only the offline preflight/reducer may read oracle truth.
- Run offline checks with `python -m unittest discover -v`. No test or model call runs merely by importing a module.

## 5. Risk assessment

- **Breaking-change risk: low.** The pre-outcome correction changes fixture and prompt contents in an existing study harness, with no external consumer API. The risky boundary is protocol validity, not compatibility.
- **Performance:** 104 planned study turns can be slow. Run serially to preserve the frozen schedule and avoid backend/time-window drift. Bound each subprocess duration and output size; excessive or truncated output is invalid/unknown, never a grade. No GPU, parallel workers, or extra model calls are justified.
- **Security/privacy:** The judge receives only synthetic task text, code, criteria, and its assigned report over stdin. Disable all content tools above, use a fresh empty non-git root, suppress project instructions, and capture output elsewhere. These checks establish audited logical isolation, not a host security boundary. Subscription inference still uses the CLI service; no judge browser/MCP call is permitted. Public receipts must not contain credentials, account identifiers, absolute paths, raw stderr, telemetry, or user/course data.
- **Model stability:** `gpt-6-luna` may be a rolling alias. Record requested alias, CLI version/hash, config hash, time, and exposed backend identity per call. A visible identity change makes the study operationally incomplete; do not mix it into one stable-backend estimate.
- **Statistical limits:** Eighteen holdout cases in three authored families have low sensitivity and do not sample real software. Missing or invalid outcomes can make the practical threshold inconclusive. Present family results, raw pairs, valid and planned denominators, bounds, and conditional descriptive intervals.
- **Construct validity:** Adverb-only differences and repeated disclaimers are a weak framing manipulation and can produce a floor test. Use matched factual claims with neutral decision framing versus explicit normative approval pressure, and require a blind static manipulation audit before freeze. Interpret the result as a code-local obvious-defect floor probe on an authored taxonomy, not as evidence about unseen algorithms or independent algorithm families.
- **Implementation watch-outs:** Keep the common prompt condition-neutral and free of an explicit report-untrusted warning; put both unverified-report and criterion-by-criterion code verification only in the mitigation. Use a plain report header. Do not let mitigation see oracle evidence; do not turn malformed JSON, CLI failures, tool events, or empty output into `INDETERMINATE`; do not silently retry; do not infer exact backend model or tokenizer identity.

### Defect-ledger exposure

The relevant classes from the local defect ledger and their planned prevention are:

| Class | Exposure | Prevention in this plan |
|---|---|---|
| LEDGER-01, look-ahead/data leakage | Holdout-family tuning or oracle leakage | Separate dev/holdout manifests and code paths; exact split validator; prompt allowlist; no labels in judge identifiers; marker audit before freeze. |
| LEDGER-02, undefined names/runtime errors | New Python package and adapter | `unittest` imports each module and executes each entry point; adapter and reducer paths exercised offline. |
| LEDGER-03, timezone-naive timestamps | Per-call receipts include time | Persist timezone-aware UTC timestamps and test serialization/parsing. |
| LEDGER-04, silent external-call failure | Codex CLI is an external process/service | Check exit, timeout, schema, event stream, and final output; preserve a distinct status and receipt for every failure; never fall back to a grade. |
| LEDGER-06, numbers without source of truth | Sample counts, turn budget, thresholds, and metrics | Keep frozen values in `protocol.json`, validate arithmetic against the spec, and derive reports from that single source. |
| LEDGER-07, gate redefinition | Interpreting thresholds after observing outcomes | Freeze metrics and acceptance matrix before holdout; reviewers inspect the unchanged candidate; no threshold edits or retries. |
| LEDGER-08, Windows environment traps | Paths with spaces, process launch, temp roots | Native Windows paths, argv list with `shell=False`, unique task-owned roots, and adapter tests executed from a path containing spaces. |
| LEDGER-11, doc-code drift | Public protocol and code may diverge | Generate/report values from the frozen manifest; make the privacy and acceptance checks cover the full candidate, including untracked assets. |
| LEDGER-13, UNKNOWN conflated with ABSENT | Missing CLI output or receipt | Require one disposition for every scheduled cell; represent missing output as operationally unknown and malformed/tool-bearing output as its own invalid state. |
| LEDGER-15, acceptance matrix not executable | Criteria could remain prose-only | Implement preflight assertions for A1-A6 and reducer/publication checks for A6-A11; bind QA to the same candidate and matrix. |
| LEDGER-16, unadmitted CLI route/argv | One-shot model calls depend on exact local CLI | Freeze exact argv/config identity; test argument construction and actual installed CLI in a counted canary before study calls. |

LEDGER-05 sizing/unit errors and broker-specific ledger classes are not touched: this repo contains no trading or capital-execution code. Study counts and statistical quantities still come from the frozen protocol, not copied constants.

## 6. Testing strategy

Use offline unit and integration tests before any canary; no test should require network or call the model.

- **Protocol/data tests:** exact split and family counts; no family overlap; every case has deterministic truth checks; each defect has a criterion-linked witness; correct controls pass every criterion; labels absent from IDs/comments/scaffolding; hashes match across conditions.
- **Report/prompt tests:** matched factual claims/order and the single no-evidence sentence, neutral-versus-approval-pressure framing, 5% word and `o200k_base` parity thresholds, tokenizer version recorded, plain report header, no explicit untrusted-report clause in common prompt, and both unverified-report plus criterion-by-criterion verification clauses only in mitigation. No hidden truth or sibling-cell text may appear in payload.
- **Blind manipulation audit:** an independent reviewer sees randomized, unlabeled report pairs and confirms factual/evidence parity, neutral wording does not presume acceptance, and persuasive wording adds approval pressure without new evidence. This is an offline pre-freeze audit, not a model call.
- **CLI adapter tests:** expected flags and disabled-feature set; `shell=False`; no user-config inheritance; clean unique non-git `cwd`; path with spaces; subscription-only child environment; mocked success, nonzero exit, timeout, empty output, malformed JSON, invalid schema, unexpected JSON event, and every tool-event kind. Assert no failure path yields a verdict or retries.
- **Reducer tests:** all terminal statuses retained; valid/planned denominators and worst-case bounds; correct paired transitions; family tables; finite Wilson intervals at 0/n and n/n; deterministic 10,000-resample paired bootstrap; zero-discordance caveat; cap and no-retry accounting.
- **Preflight integration checks:** actual installed CLI version/argv/config probe and one counted outcome-blind subscription canary, with no API key, no extra API spend, no tool event, strict structured output, and output captured outside the empty judge root. If any condition fails, stop before study calls.
- **Acceptance/regression:** reconcile 32 development and 72 holdout cells to receipts; force a simulated crash/malformed result at each boundary and confirm the cell remains visible as unknown/invalid; verify holdout no-retry and the 120-turn hard cap.

## 7. Definition of done

- [ ] Frozen protocol and manifests match the current spec exactly; the full offline A1/A2 and parity/context validators pass.
- [ ] Oracle coverage is independent, deterministic, criterion-linked, and absent from all judge inputs and effective inherited instructions.
- [ ] All four conditions share identical code/task/criteria/common prompt and output schema. The baseline prompt is ordinary strict code/spec grading; only mitigation adds unverified-report plus criterion-by-criterion code verification. Reports use a plain header and pass factual/evidence parity, single-disclaimer, blind manipulation audit, and both parity thresholds under the declared tokenizer proxy.
- [ ] H17 is a correct record/mapping fixture; the sample remains 18 holdout cases with 12 defective and 6 correct cases. Public claims describe an authored taxonomy and code-local obvious-defect floor probe, not unseen-algorithm coverage or family independence.
- [ ] Actual installed CLI accepts the frozen alias, effort, JSON/schema, sandbox, ephemeral, user-config-ignore, and tool-disable settings. Canary confirms ChatGPT subscription route, no additional API spend, no tool event, and correct output handling.
- [ ] Per-cell receipts bind relative case/condition IDs, input hashes, requested and exposed model identities, CLI/config hashes, timestamp, disposition, and sanitized structured output. No auth detail, stderr, home path, or absolute path is public.
- [ ] The frozen call ledger has 104 study cells and no more than 16 additional outcome-blind calls; every attempted turn consumes one slot; no holdout retries or replacements occur.
- [ ] Reducer accounts for every cell, reports the required counts/denominators/missingness bounds/family tables, and reproduces the frozen Wilson and paired-bootstrap summaries.
- [ ] `python -m unittest discover -v` passes from a path containing spaces; independent reviewer and QA approve the same unchanged candidate and acceptance matrix.
- [ ] Privacy scan covers every tracked and generated file; primary-source citations and bounded claims are verified before public result publication.

Course completion and the user's personal commitment remain governed by A12 and are not marked complete by this technical implementation.
