"""Explicit command-line entry points; importing this module makes no calls."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .analysis import analyze, load_verified_bundle
from .export import export_public_bundle
from .runner import freeze_protocol, preflight, run_canaries, run_split


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m study")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("preflight", help="run offline protocol, oracle, tokenizer, and CLI checks")

    canary = commands.add_parser("canary", help="run two outcome-blind local-model canaries")
    canary.add_argument("--authorize-local-model-calls", action="store_true")
    canary.add_argument("--confirm-offline-review-and-native-qa", action="store_true")
    canary.add_argument("--changed-premise", help="required repair explanation for changed-source/configuration readmission")

    commands.add_parser("freeze", help="freeze the protocol and randomized schedule")

    run = commands.add_parser("run", help="execute only unattempted cells in a frozen split")
    run.add_argument("--split", choices=("development", "holdout"), required=True)
    run.add_argument("--authorize-local-model-calls", action="store_true")

    reduce = commands.add_parser("analyze", help="verify an explicit evidence bundle and reduce it without model calls")
    reduce.add_argument("--split", choices=("development", "holdout"), required=True)
    reduce.add_argument("--bundle", type=Path, required=True)
    reduce.add_argument("--scope", choices=("private_raw_verified", "public_projection_replay"), required=True)
    reduce.add_argument("--manifest-sha256", help="independently recorded public manifest byte hash")

    export = commands.add_parser("export", help="create a sanitized public replay bundle from verified private evidence")
    export.add_argument("--private-root", type=Path, required=True)
    export.add_argument("--target", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "preflight":
            result = preflight()
        elif args.command == "canary":
            result = run_canaries(
                args.authorize_local_model_calls,
                args.confirm_offline_review_and_native_qa,
                changed_premise=args.changed_premise,
            )
        elif args.command == "freeze":
            result = freeze_protocol()
        elif args.command == "run":
            result = run_split(args.split, args.authorize_local_model_calls)
        elif args.command == "export":
            result = export_public_bundle(args.private_root, args.target)
        else:
            verified = load_verified_bundle(
                args.bundle, scope=args.scope, manifest_sha256=args.manifest_sha256,
            )
            result = analyze(args.split, verified)
        _print_json(result)
        return 0 if result.get("status") in {None, "PASS", "PARTIAL"} else 2
    except Exception as error:
        print(f"study command blocked: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
