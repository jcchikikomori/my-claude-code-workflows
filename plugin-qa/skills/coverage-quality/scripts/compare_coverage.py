#!/usr/bin/env python3
"""
compare_coverage.py — Compare two unified coverage JSONs, output delta JSON.

Usage:
  python3 compare_coverage.py \
    --baseline .coverage-snapshot/baseline.json \
    --current /tmp/coverage-current.json \
    --changed-files "src/foo.py src/bar.py" \
    --mode diff-check \
    --output /tmp/coverage-delta.json

Modes:
  diff-check   Only report files listed in --changed-files
  full-report  Report all files from current (sorted by pct ascending)
"""

import argparse
import json
import os
import sys


def collapse_ranges(lines: list) -> str:
    """Collapse sorted integers into human-readable range string.

    [12, 13, 14, 20, 21] -> "12-14, 20-21"
    """
    if not lines:
        return ""
    lines = sorted(set(lines))
    ranges = []
    start = end = lines[0]

    for n in lines[1:]:
        if n == end + 1:
            end = n
        else:
            ranges.append((start, end))
            start = end = n
    ranges.append((start, end))

    parts = []
    for s, e in ranges:
        parts.append(str(s) if s == e else f"{s}-{e}")
    return ", ".join(parts)


def file_status(current_pct: float, delta: float) -> tuple:
    if delta > 0:
        return "✅", "IMPROVED"
    if delta == 0:
        return "—", "UNCHANGED"
    if delta <= -10.0 or current_pct < 50.0:
        return "🔴", "MISSING"
    return "🟡", "DEGRADED"


def overall_status(current_pct: float, delta: float, threshold: float) -> tuple:
    if current_pct >= threshold and delta >= 0:
        return "✅", "MAINTAINED"
    if current_pct >= threshold and delta < 0:
        return "⚠️", "DEGRADED"
    return "🔴", "CRITICAL"


def compare(baseline: dict, current: dict, changed_files: list, mode: str, threshold: float) -> dict:
    baseline_files = baseline.get("files", {})
    current_files = current.get("files", {})
    baseline_overall = baseline.get("overall", {})
    current_overall = current.get("overall", {})

    overall_delta = round(
        current_overall.get("percent", 0) - baseline_overall.get("percent", 0), 2
    )
    ov_emoji, ov_status = overall_status(
        current_overall.get("percent", 0), overall_delta, threshold
    )

    if mode == "diff-check":
        candidate_paths = changed_files if changed_files else list(current_files.keys())
    else:
        candidate_paths = list(current_files.keys())

    file_reports = []

    for path in candidate_paths:
        curr = current_files.get(path)
        base = baseline_files.get(path)

        if curr is None:
            if base:
                file_reports.append({
                    "path": path,
                    "baseline_pct": base["percent"],
                    "current_pct": None,
                    "delta": None,
                    "emoji": "🔴",
                    "status": "REMOVED",
                    "missing_lines": [],
                    "missing_lines_display": "",
                })
            continue

        curr_pct = curr.get("percent", 0)
        missing = curr.get("missing_lines", [])

        if base is None:
            file_reports.append({
                "path": path,
                "baseline_pct": None,
                "current_pct": curr_pct,
                "delta": None,
                "emoji": "ℹ️",
                "status": "NEW FILE",
                "missing_lines": missing,
                "missing_lines_display": collapse_ranges(missing),
            })
            continue

        base_pct = base.get("percent", 0)
        delta = round(curr_pct - base_pct, 2)
        emoji, status_text = file_status(curr_pct, delta)

        file_reports.append({
            "path": path,
            "baseline_pct": base_pct,
            "current_pct": curr_pct,
            "delta": delta,
            "emoji": emoji,
            "status": status_text,
            "missing_lines": missing,
            "missing_lines_display": collapse_ranges(missing),
        })

    if mode == "full-report":
        file_reports.sort(key=lambda r: (r["current_pct"] is None, r["current_pct"] or 0))

    below_threshold = [
        {"path": p, "percent": info["percent"]}
        for p, info in current_files.items()
        if info["percent"] < threshold
    ]
    below_threshold.sort(key=lambda x: x["percent"])

    actions = []
    degraded_count = 0
    for fr in file_reports:
        if fr["status"] in ("MISSING", "DEGRADED") and fr["missing_lines_display"]:
            actions.append(f"Add tests for {fr['path']} lines {fr['missing_lines_display']}")
            degraded_count += 1

    if degraded_count > 0:
        actions.append(
            f"{degraded_count} file(s) degraded. Run /coverage-quality update to set new baseline."
        )
    else:
        actions.append("Coverage maintained or improved. No action required.")

    return {
        "mode": mode,
        "threshold": threshold,
        "baseline_commit": baseline.get("commit", ""),
        "current_commit": current.get("commit", ""),
        "stack": current.get("stack", ""),
        "overall": {
            "baseline_pct": baseline_overall.get("percent", 0),
            "current_pct": current_overall.get("percent", 0),
            "delta": overall_delta,
            "emoji": ov_emoji,
            "status": ov_status,
        },
        "files": file_reports,
        "below_threshold": below_threshold,
        "actions": actions,
    }


def load_threshold(config_path: str = ".coverage-snapshot/config.json") -> float:
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            return float(cfg.get("threshold", 80.0))
        except (json.JSONDecodeError, ValueError):
            pass
    return 80.0


def main():
    parser = argparse.ArgumentParser(description="Compare coverage baselines")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--changed-files", default="",
                        help="Space-separated list of changed file paths")
    parser.add_argument("--mode", choices=["diff-check", "full-report"], default="diff-check")
    parser.add_argument("--output", required=True)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    if not os.path.exists(args.baseline):
        sys.exit(f"ERROR: Baseline not found: {args.baseline}")
    if not os.path.exists(args.current):
        sys.exit(f"ERROR: Current coverage not found: {args.current}")

    with open(args.baseline) as f:
        baseline = json.load(f)
    with open(args.current) as f:
        current = json.load(f)

    threshold = args.threshold if args.threshold is not None else load_threshold()
    changed_files = [f for f in args.changed_files.split() if f] if args.changed_files else []

    delta = compare(baseline, current, changed_files, args.mode, threshold)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(delta, f, indent=2)

    ov = delta["overall"]
    sign = "+" if ov["delta"] >= 0 else ""
    print(f"Overall: {ov['baseline_pct']}% → {ov['current_pct']}% ({sign}{ov['delta']}%) "
          f"{ov['emoji']} {ov['status']}")
    print(f"Files reported: {len(delta['files'])}")
    print(f"Below threshold ({threshold}%): {len(delta['below_threshold'])}")
    print(f"Delta written to: {args.output}")


if __name__ == "__main__":
    main()
