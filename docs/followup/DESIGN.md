# Partial test evidence follow-up

## Development screen specification

The first uncertainty is whether the evidence treatment can be constructed. Use six new synthetic Python tasks involving ordinary functional behavior. Each has a stated requirement, a correct implementation, a plausible flawed implementation, common cases visible to a future reviewer, and additional contract examples for scoring. An eligible pair has identical correct outputs on every visible example, correct outputs on every additional example from the correct implementation, and an explicit wrong output on at least one additional example from the flawed implementation. Runtime errors are screen failures. The published cases and all their derivatives are development material.

The initial target is six eligible pairs. A screen with five eligible pairs establishes basic feasibility while the failed pair is retained and investigated. Below five after one documented revision, redesign how cases are sourced before attempting model grading. The screen runs locally, makes zero model calls, and records source and check identities and per-example outcomes. An independent reading should check that each disputed output really violates the written requirement. Passing the screen supplies executable witnesses for these specific contracts.

Run these commands from the repository root with Python 3.12.

```powershell
python -S -B docs/followup/screen.py --output docs/followup/results/screen-summary.json
python -S -B docs/followup/test_screen.py
```

The runner executes the project’s authored Python fixtures. Its syntax restrictions constrain these examples. The next data stage must use an isolated runner suitable for any third-party code it executes.

## Proposed model study

- Start with independently checked functional defects and correct controls on small software patches. Prefer licensed source with known issues and reproducible tests. Group candidate patches by issue and repository, record provenance, and reserve whole projects or problem families for fresh evaluation. Two investigators should adjudicate ambiguous labels before seeing judge outcomes.
- Use four conditions per patch, crossing neutral versus approval recommendation with genuine passing test results withheld versus shown. Keep task, patch, rubric, and every factual report claim fixed. Generate the visible artifact from independent execution of a fixed test subset, with named checks and accurate scope. Use the same artifact across both report conditions for the same patch, with equivalent artifact contents for its matched correct control where outcomes coincide. Keep additional contract checks and labels out of the grader input. Use fresh conversations and a preassigned, recorded order balanced across conditions. Include report-hidden and verification-enabled reviewers as diagnostic comparisons with specified inputs and budgets.
- Use the development run to compare multiple neutral and recommendation wordings before selecting fixed wording for confirmation. Match factual content and check length and tone. Generate the evidence block outside the author report. Omit paths, reference names and implementation identifiers that could reveal the labels. In the evidence-withheld condition, say that the reviewer has received no execution evidence. Record the exact prompts and consider a matched non-evidentiary block as a sensitivity check for added context.
- Compute the primary comparison on independently labeled flawed patches. Subtract the neutral approval rate from the approval rate with the recommendation, once for each evidence condition. Subtract the gap without visible evidence from the gap with visible evidence. A positive value means showing the result increased the effect of the recommendation on false approvals. Report all four cell rates to show whether high false approvals in both report conditions account for a smaller gap. Pair by patch and account for shared issue and repository when estimating uncertainty. Repeated judgments of a single patch measure repeatability.
- Record false approvals, rejection of correct controls, abstention and referral rates, and verification time or cost. Preserve invalid and missing decisions with status and reasons. Freeze the denominator and missingness sensitivity analysis before measurement. Compare verification policies at specified budgets.
- Start a small exploratory run with an available local model after an operability check. The four primary cells for twelve development implementations would require 48 decisions per judge before diagnostics or repeats. Use development runs to check the input boundary, assess case difficulty, and estimate paired variability. Set a smallest policy-relevant effect and size the confirmatory sample for useful precision before seeing confirmation outcomes. Archive a separate preregistration with frozen splits, condition construction, model IDs, decoding, run budget, error rules and analysis. A claim across model families requires evidence from those families.

## Research ledger and decision order

| Priority | Question | Cheapest check | Decision |
| --- | --- | --- | --- |
| 1 | Can a genuine passing result coexist with a clear defect? | Six matched pairs and executable witnesses | Retain qualifying development examples. Rework sourcing if the screen falls below its floor. |
| 2 | Do these evidence conditions resemble real review? | Independent critique and a small paired sample of real functional patches | Continue if labels, coverage and evidence visibility can be controlled. Revise the design if visible evidence reveals the labels or the wrong outputs are disputed. |
| 3 | Is there a measurable gap worth estimating? | Predeclared exploratory local runs on development cases | Inspect disagreement across cases, report conditions and model runs. Treat all-approve or all-reject behavior as a design diagnostic. Use variability to size the next study. |
| 4 | Does evidence availability change the effect, and what does verification cost? | Preregistered confirmation on fresh projects and additional graders | Report the estimates and uncertainty, including a precise small effect if that is what the data support. |

This release executes only the first row. The primary cost is authoring and reviewing the fixtures. The review team can use the original pilot as motivation and verify the new cases independently. The follow-up brief and development screen are AI-assisted.

## Relation to earlier work

Zhu et al. hold GUI traces fixed while showing or withholding self-reports and test a report-isolated auditor. Zhan et al. vary evidence presented to code judges, including a plain test-pass declaration and test lists. Their test-pass declaration showed no significant bias in their setting. SWE-Review evaluates review and downstream repair against executable outcomes on repository patches. Our working extension crosses a recommendation with visibility of an independently captured, deliberately incomplete result. A deeper comparison of intervention details is part of the decision to expand. [Zhu et al.](https://arxiv.org/abs/2610.29609) · [Zhan et al.](https://doi.org/10.4230/LIPIcs.ESEM.2026.21) · [Wang et al.](https://arxiv.org/abs/2607.06065)

Ye et al. curated repair candidates on Defects4J and used additional tests based on human-written patches to assess correctness. Their corpus offers a source to investigate for a real-patch feasibility sample. Before use, check redistribution rights, verify that cases exercise ordinary functional defects, and reproduce distinct visible and independent test outcomes. [Automated Patch Assessment for Program Repair at Scale](https://arxiv.org/abs/1909.13694)

Start that sample with the SWE-Review-Bench metadata. It provides candidate patches, repository revisions, issue identifiers, test lists and recorded resolution labels. Look for multiple candidates for the same ordinary functional issue and check whether a small visible subset can pass for both a resolved and an unresolved candidate. Independently reproduce the outcomes and check the expected behavior before accepting a pair. Record rejected candidate IDs and reasons, including ambiguous labels, unwieldy patches and tests that reveal the answer. The dataset card lists Apache 2.0. Check upstream files for their own terms before redistributing their contents. [SWE-Review-Bench dataset card](https://huggingface.co/datasets/Lego-X/SWE-Review-Bench)
