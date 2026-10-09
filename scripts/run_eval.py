"""Run the four corpus applications and exit non-zero when the report fails."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from underwriting.eval_harness import execute, format_report
from underwriting.adapters import OllamaAdapter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "var" / "eval_report.json",
    )
    args = parser.parse_args()
    report = execute(args.output, OllamaAdapter())
    print(format_report(report), end="")
    print("Report written to", args.output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
