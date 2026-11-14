# Can a passing test make a flawed patch look safer?

An AI agent submits a patch and recommends approval. An independent runner confirms that a real test passed. The patch still has a bug that the test never exercised. Will the reviewer treat the passing result as limited evidence, or will it make the agent’s recommendation more persuasive?

The [original pilot](../REPORT.md) found three false approvals with a neutral report and four with an approval recommendation, out of twelve flawed cases. That one-case difference fell below the pilot’s predeclared screen. The follow-up asks whether giving the reviewer independently measured but incomplete test evidence changes that difference.

Across six development pairs, both versions passed every visible check. Each flawed version failed an independent contract check that its correct counterpart passed. For a review study, the reviewer would see the task, the patch, and at most the independently captured results of the visible checks. The independent contract checks supply the evaluation labels. [Screen summary](results/screen-summary.json)

For example, suppose a function splits a list into groups of two and must retain any leftover item. Two versions can both split `[1, 2, 3, 4]` into `[[1, 2], [3, 4]]`. On `[1, 2, 3]`, the correct version returns `[[1, 2], [3]]`, while the flawed one drops `3`. The passing result on the first list is genuine, but it misses the requirement to retain the leftover item.

| What the reviewer reads | Test result withheld | Passing results shown |
| --- | --- | --- |
| Neutral report | Neutral, no result | Neutral, genuine partial result |
| Report recommending approval | Recommendation, no result | Recommendation, genuine partial result |

The question is whether the gap in false approvals between the two reports gets bigger or smaller when the results are shown. We can also compare a reviewer who never sees the report and a reviewer who verifies a limited set of checks independently. We would count correct patches rejected, patches sent for human review, and verification time as well as flaws missed.

Three relevant papers already cover report visibility in GUI auditing, test-result presentation in patch review, and executable evaluation of AI code reviewers. The proposed contribution is to measure how a genuine but incomplete pass interacts with an approval recommendation on the same patch. [GUI report leakage](https://arxiv.org/abs/2610.29609) · [Patch correctness assessment](https://doi.org/10.4230/LIPIcs.ESEM.2026.21) · [SWE-Review](https://arxiv.org/abs/2607.06065)

For the first discussion, show one pair and ask which checks a reviewer would realistically have before merging a patch. Ask someone to independently examine the requirement and the failing example. Their critique can shape a small pilot on real patches and a later preregistered study. The current exercise measures whether we can construct the test cases. Model behavior is still an open question.

The [design note](DESIGN.md) gives the proposed analysis, criteria for expanding the study, and replay command.
