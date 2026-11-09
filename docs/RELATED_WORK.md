# Related work and claim boundary

This project is a bounded replication and extension of established work on LLM judge reliability. It does not claim to discover that model judgments can be affected by presentation or self-reports.

## Closest studies

- Zhu et al., **Who Verifies the Agent's Success Claim? Self-Report Leakage in GUI-Agent Completion Judging**. [arXiv:2610.29609](https://arxiv.org/abs/2610.29609). The controlled intervention includes or withholds a GUI agent's self-report while keeping its task and trace fixed. Report isolation is directly relevant; the domain and ground-truth procedure differ from this coding study.
- Zhan et al., **How Reliable Is LLM-as-Judge for Patch Correctness Assessment? An Empirical Study**. [ESEM 2026](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.21). The study examines evidence presentation and patch correctness. Its reported absence of a significant bias from a simple all-tests-passed declaration is important counterevidence. A positive effect in the present study must be measured, never presumed. Reference-patch-assisted grading is a different information condition from standalone grading.

## Supporting primary literature

- Zheng et al., **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena**. [arXiv:2306.05685](https://arxiv.org/abs/2306.05685). General judge validity and presentation biases.
- Shi et al., **Optimization-based Prompt Injection Attack to LLM-as-a-Judge**. [arXiv:2403.17710](https://arxiv.org/abs/2403.17710). Deliberate adversarial manipulation of evaluated content is distinct from ordinary completion-report framing.
- Wang et al., **Is LLM-as-a-Judge Robust? Investigating Universal Adversarial Attacks on Zero-shot LLM Assessment**. [EMNLP 2024](https://aclanthology.org/2024.emnlp-main.427/). Related adversarial assessment setting, not evidence about this project's exact tasks or treatment.

## Permissible contribution

Measure a precisely specified completion-report intervention attached to byte-identical Python solutions. Ground truth comes from independent executable checks. Preserve held-out tasks, paired observations, invalid outputs, operational failures, uncertainty, and null findings. Test one predeclared mitigation and describe exactly which evidence it receives. Limit conclusions to the tested Codex product, model configuration, synthetic task population, and run.

This is a scoped work sample and learning project, not a general model leaderboard or evidence about all coding agents.
