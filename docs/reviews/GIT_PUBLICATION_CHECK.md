## Git publication check

**GIT_PUBLICATION_PASS** for commit `32f837754a4470e8a1e34cf3b6c9bbbb6246c08c` and the 425 reviewed candidate and gate-report blobs. The canonical Git blob map SHA-256 is `c67c98742b5c430e7a917d44aa2af22e2c2f046abfca97fe37786a35759d6d75`; the original reviewed 423-file map remains `5317c46dd208f231a37b8a2f168f2c4d25db29e392001e57cb5ea8755167b48c`. The commit also tracks `tasks/lessons.md` and `tasks/todo.md`, which are excluded task bookkeeping.

The publication sequence continued after a staging blob check detected a line-ending mismatch: the commit and push occurred before that failure stopped further mutations. This was a verification-ordering failure. Future blocking checks must throw or stop before any subsequent mutation. No history rewrite is implied by this attestation.

An independent rerun of `verify_published_git.py` compared each actual committed blob to the reviewed candidate and two gate reports. Exactly three differed, each solely through CRLF-to-LF normalization:

- `results/development-analysis.json`
- `results/holdout-analysis.json`
- `docs/reviews/RESULTS_REVIEW.md`

The two JSON objects are semantically identical. All other 422 checked blobs, including frozen scientific source and the strict public bundle, are byte-identical. The manifest remains `64c1ed196bbadcf02180463910ff47ae9db7f938efa8c86a5c2f8f9c64b33114`.

Cold subprocess replay from the actual Git archive, with private state absent, PATH empty, PYTHONPATH scrubbed and network/live adapters forbidden, returned PASS for all 32 development and 72 holdout cells. Each replay equals the committed JSON and the full private analysis apart from the explicit scope label. This check ran no inference and authorizes no future inference. It does not replace the original review or QA.
