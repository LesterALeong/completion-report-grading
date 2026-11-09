# Completion report grading: a local-model safety pilot

Can approval-seeking completion reports make an LLM grader accept broken code? In this preregistered pilot, local Qwen falsely approved **3 of 12 defective holdout cases with a neutral report and 4 of 12 with approval pressure**. The one-case increase fell below the predeclared two-case screen. The mitigation yielded one fewer false approval overall, also below its target. All six correct controls passed in every condition.

| Holdout condition | False approvals / defective cases | Correct controls approved |
| --- | ---: | ---: |
| No report | 2/12 | 6/6 |
| Neutral report | 3/12 | 6/6 |
| Approval-seeking report | 4/12 | 6/6 |
| Approval-seeking report + mitigation | 3/12 | 6/6 |

**Read the [report](docs/REPORT.md)** for paired estimates, uncertainty, the concrete failure, family breakdown and limitations. This is a small authored, obvious-defect floor probe on one quantized local model. A below-threshold finding does not establish that approval pressure is harmless or that the mitigation works.

The safety concern is an evaluation gate that accepts an AI agent's unsupported success claims. This work sample tests a small part of that concern and demonstrates frozen inputs, independent executable ground truth, retained failures, strict evidence handling and reproducible analysis. Research, implementation, review and writing were AI-assisted; the reviews are not human peer review.

## Replay without a model

From this repository root, use Python 3.12 and the standard library. No Ollama server, Codex login, GPU or API key is needed:

```powershell
python -S -B -m study analyze --split holdout --bundle results/study-publication-v2 --scope public_projection_replay --manifest-sha256 64c1ed196bbadcf02180463910ff47ae9db7f938efa8c86a5c2f8f9c64b33114
```

Use `--split development` for the separate development analysis. Saved [holdout](results/holdout-analysis.json) and [development](results/development-analysis.json) JSON files contain the full tables, paired contrasts, missingness accounting and case-level decisions. Cold public replay passed for all 72 holdout and 32 development cells with private state absent and network/live adapters blocked. Both analyses match private raw verification except for the explicit verification-scope label.

Public replay verifies published projections and commitments. It cannot independently prove equality with unpublished raw captures. Raw responses, native diagnostics and the original failed export remain in the owner's retained private evidence.

## Design and provenance

- 8 development cases in 2 authored families; 18 holdout cases in 3 further authored families, including 12 defective cases and 6 controls. Each implementation receives all four conditions. Family labels do not establish statistical independence.
- Neutral and approval-seeking reports hold factual claims, evidence and order fixed; the intervention is normative approval pressure. The mitigation bundles a report warning with a verification instruction.
- 48 local criterion checks across 26 synthetic Python functions, including defect witnesses and audited controls. The grader receives no oracle labels or checks.
- Installed `qwen3.5:9b-q4_K_M`, Ollama 0.40.14, manifest digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. Fixed schema, tools `[]`, thinking disabled, temperature 0, seed 20261109, context 4096, output cap 512, two CPU threads and serial calls. A digest does not guarantee identical future GPU arithmetic.
- [Preregistration commit d4bd17f](https://github.com/LesterALeong/completion-report-grading/commit/d4bd17f6c9383dd4fcffea79041a3268a3839e8a) was public before any study grading. The [admission bundle](results/admission) preserves the zero-study checkpoint; the [commentable log](https://github.com/LesterALeong/completion-report-grading/issues/1) preserves the earlier prediction and operational pivot.
- All 104 study cells completed validly, with no retries or tuning between splits. Four charged canaries include two failed Codex attempts and two successful local predicates: 108 evaluation attempts within the original 120 cap. No separate paid API, rented GPU, model download or training was used.

The original Codex route closed before study grades because admission and observability requirements were not met. Local v2 was separately preregistered before outcomes; this is not a provider comparison. See the [operability report](docs/CODEX_OPERABILITY.md), [v2 specification](docs/SPEC.md), [protocol](study/protocol.json), [architecture](docs/OLLAMA_ARCHITECTURE.md) and [related work](docs/RELATED_WORK.md).

## Publication amendment

The first full export failed because redaction expanded one valid 300-character explanation to 305 characters. A separate [publication amendment](publication/amend.py) bounds only that sanitized display reason. Frozen study code, raw evidence, verdicts, validity and statistical outputs remain unchanged. The [postmortem](docs/reviews/EXPORT_POSTMORTEM.md) and [amendment provenance](results/study-publication-v2-amendment.json) record the original failure, exact identities and change. The unchanged strict public reader accepts the corrected bundle.

Rebuilding this publication requires retained private evidence, the original failed bundle and reviewed source archive. Its create-only command is:

```powershell
python -S -B -m publication.amend --private-root ../_tmp/completion-report-grading --original ../_tmp/completion-report-grading/failed-public-export-01 --target results/new-publication --original-manifest-sha256 ef3369c61e24c4b5a6c0417ee5eb8f25b77c4bbde39b86359d12b12c1750f94b
```

The live harness also requires retained historical evidence and the exact installed model/runtime. Public cloning supports replay of the published run; it does not recreate private captures or guarantee identical new inference.

## Model-free checks

For the full suite, install the pinned development packages and seed the public tokenizer cache once. This downloads an encoding, not a model or inference response:

```powershell
python -m pip install tiktoken==0.13.0 ruff==0.15.15
python -c "import os; from study.protocol import TASK_TMP; os.environ['TIKTOKEN_CACHE_DIR'] = str(TASK_TMP / 'tokenizer-cache'); import tiktoken; tiktoken.get_encoding('o200k_base')"
python -m ruff check --no-cache --select F study tests publication
python -m unittest discover -v
```

Native transport tests use inert ephemeral loopback servers on Windows and never contact the model. The recorded pre-study suite passed 101 tests without skips; the publication amendment adds a portable retained-producer regression and display-boundary tests. The `o200k_base` encoding is a report-length parity proxy, not Qwen's native tokenizer.

See the [interview guide](docs/INTERVIEW_GUIDE.md) to trace the work and prepare to explain its limits. The repository does not establish course attendance, personal mastery or a hiring outcome.
