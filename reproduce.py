#!/usr/bin/env python3
"""Reproduce the bounded tests and complete frozen finite campaign.

The controller runs exactly one scientific child at a time, records each child's
stdout/stderr in the requested output directory, applies per-child and whole-run
time limits, and rejects any deterministic count drift before writing the final
summary.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
WHOLE_TIMEOUT_SECONDS = 180.0
CHILD_TIMEOUT_SECONDS = 20.0

EXPECTED_TOTALS = {
    "total_verdict_cases": 244_828,
    "total_summary_oracle_checks": 310_463,
    "total_whole_graph_oracle_checks": 244_824,
    "total_whole_graph_oracle_exclusions": 4,
    "total_raw_semantics_oracle_checks": 2_500,
    "exhaustive_binding_cases": 65_635,
    "refinement_checks": 1,
    "transfer_relation_candidates": 22_186,
    "accepted_transfer_relations": 1_358,
    "transfer_implication_checks": 2_116,
    "mismatches": 0,
}

EXPECTED_SUITE_CASES = {
    "core-2-0-625": 2_500,
    "core-3-0-2000": 24_000,
    "core-3-2000-4000": 24_000,
    "core-3-4000-6000": 24_000,
    "core-3-6000-8000": 24_000,
    "core-3-8000-10000": 24_000,
    "core-3-10000-12000": 24_000,
    "core-3-12000-14000": 24_000,
    "core-3-14000-16000": 24_000,
    "core-3-16000-18000": 24_000,
    "core-3-18000-19683": 20_196,
    "closed": 1_024,
    "modules": 512,
    "binding": 65_635,
    "refinement": 2,
    "transfer": 22_186,
    "raw": 2_500,
    "named": 26,
    "scaling": 30,
}


def _portable_command(argv: list[str], output: Path) -> list[str]:
    """Remove machine-private paths from the retained command record."""
    result: list[str] = []
    for index, value in enumerate(argv):
        if index == 0:
            result.append("python3")
        elif value == str(output):
            result.append("<output>")
        else:
            result.append(value)
    return result


def _validate_result(result: dict[str, Any], output: Path) -> None:
    suites = result["suites"]
    observed_suite_cases = {entry["suite"]: entry["cases"] for entry in suites}
    if observed_suite_cases != EXPECTED_SUITE_CASES:
        raise RuntimeError(
            "suite inventory/count drift: "
            f"observed={observed_suite_cases!r}, expected={EXPECTED_SUITE_CASES!r}"
        )

    for key, expected in EXPECTED_TOTALS.items():
        observed = result.get(key)
        if observed != expected:
            raise RuntimeError(
                f"deterministic total drift for {key}: {observed!r} != {expected!r}"
            )

    test_log = (output / "tests.stderr.txt").read_text()
    methods = len(re.findall(r"^test_.* \.\.\. ok$", test_log, re.MULTILINE))
    if methods != 22 or not re.search(r"^OK$", test_log, re.MULTILINE):
        raise RuntimeError(
            f"unit-test receipt drift: found {methods} passing methods and "
            f"OK={bool(re.search(r'^OK$', test_log, re.MULTILINE))}"
        )

    if len(result["commands_executed"]) != 20:
        raise RuntimeError("expected exactly 20 sequential commands")
    if any(command["exit_code"] != 0 for command in result["commands_executed"]):
        raise RuntimeError("a retained command has a nonzero exit code")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "reproduced", help="new result directory"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="resume an incomplete output created by this exact source",
    )
    args = parser.parse_args()
    output = args.output.resolve()

    if output.exists() and not args.resume:
        raise ValueError("output already exists; use a new directory or explicit --resume")
    output.mkdir(parents=True, exist_ok=True)

    start = time.monotonic()
    commands: list[dict[str, Any]] = []

    def run(argv: list[str], tag: str) -> None:
        remaining = WHOLE_TIMEOUT_SECONDS - (time.monotonic() - start)
        if remaining <= 0:
            raise TimeoutError("whole reproduction time limit reached")

        command_start = time.monotonic()
        stdout_path = output / f"{tag}.stdout.txt"
        stderr_path = output / f"{tag}.stderr.txt"
        print(f"[reproduce] {tag}", file=sys.stderr, flush=True)

        with stdout_path.open("w") as stdout_handle, stderr_path.open("w") as stderr_handle:
            # Files rather than pipes prevent a child from blocking the controller
            # on captured output. A process group lets a timeout terminate any
            # accidental descendants as well as the immediate child.
            process = subprocess.Popen(
                argv,
                cwd=ROOT,
                text=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
                start_new_session=True,
            )
            try:
                process.wait(timeout=min(CHILD_TIMEOUT_SECONDS, remaining))
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise TimeoutError(f"bounded command timed out: {tag}") from None

        commands.append(
            {
                "command": _portable_command(argv, output),
                "exit_code": process.returncode,
                "wall_seconds": time.monotonic() - command_start,
            }
        )
        if process.returncode != 0:
            raise RuntimeError(f"failed bounded command: {tag}")

    run([sys.executable, "tests/test_core.py"], "tests")

    jobs: list[tuple[str, int, int, int]] = [("core", 2, 0, 625)]
    jobs.extend(
        ("core", 3, begin, min(begin + 2_000, 19_683))
        for begin in range(0, 19_683, 2_000)
    )
    jobs.extend(
        (kind, 0, 0, 0)
        for kind in (
            "closed",
            "modules",
            "binding",
            "refinement",
            "transfer",
            "raw",
            "named",
            "scaling",
        )
    )

    for kind, states, begin, end in jobs:
        tag = f"core-{states}-{begin}-{end}" if kind == "core" else kind
        if args.resume and (output / f"{tag}.json").exists():
            continue
        argv = [sys.executable, "src/campaign.py", kind, "--out", str(output)]
        if kind == "core":
            argv.extend(
                ["--n", str(states), "--start", str(begin), "--stop", str(end)]
            )
        run(argv, tag)

    suites: list[dict[str, Any]] = []
    for kind, states, begin, end in jobs:
        tag = f"core-{states}-{begin}-{end}" if kind == "core" else kind
        suites.append(json.loads((output / f"{tag}.json").read_text()))

    result: dict[str, Any] = {
        "suites": suites,
        "total_verdict_cases": sum(suite["verdict_cases"] for suite in suites),
        "total_summary_oracle_checks": sum(
            suite["summary_oracle_checks"] for suite in suites
        ),
        "total_whole_graph_oracle_checks": sum(
            suite["whole_graph_oracle_checks"] for suite in suites
        ),
        "total_whole_graph_oracle_exclusions": sum(
            suite["whole_graph_oracle_exclusions"] for suite in suites
        ),
        "total_raw_semantics_oracle_checks": sum(
            suite.get("raw_semantics_oracle_checks", 0) for suite in suites
        ),
        "exhaustive_binding_cases": next(
            suite["cases"] for suite in suites if suite["suite"] == "binding"
        ),
        "refinement_checks": next(
            suite.get("refinement_checks", 0)
            for suite in suites
            if suite["suite"] == "refinement"
        ),
        "transfer_relation_candidates": next(
            suite.get("transfer_relation_candidates", 0)
            for suite in suites
            if suite["suite"] == "transfer"
        ),
        "accepted_transfer_relations": next(
            suite.get("accepted_transfer_relations", 0)
            for suite in suites
            if suite["suite"] == "transfer"
        ),
        "transfer_implication_checks": next(
            suite.get("transfer_implication_checks", 0)
            for suite in suites
            if suite["suite"] == "transfer"
        ),
        "mismatches": sum(suite["mismatches"] for suite in suites),
        "wall_seconds": time.monotonic() - start,
        "measured_child_cpu_seconds": (
            resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
            + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
        ),
        "parent_cpu_seconds": time.process_time(),
        "peak_child_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "peak_parent_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "max_concurrent_scientific_workers": 1,
        "commands_executed": commands,
        "resume_note": (
            "Existing completion markers are trusted only when --resume is explicitly "
            "selected; clean evidence uses a new output directory."
        ),
    }

    _validate_result(result, output)
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    concise = {
        key: value
        for key, value in result.items()
        if key not in {"suites", "commands_executed"}
    }
    print(json.dumps(concise, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as exc:
        print(f"REPRODUCTION FAILED: {exc}", file=sys.stderr)
        sys.exit(2)
