#!/usr/bin/env python3
"""Prints a Markdown table from a `claude plugin eval --json` result: score, turns, cost and time per arm."""
import json
import sys
from statistics import mean

result = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results/latest.json"))


def stats(runs):
    ok = [r for r in runs if not r.get("error")]
    if not ok:
        return None
    return dict(score=mean(r["score"] for r in ok), turns=mean(r["turns"] for r in ok),
                cost=mean(r["costUsd"] for r in ok), secs=mean(r["durationSeconds"] for r in ok),
                n=len(ok), errors=len(runs) - len(ok))


def cell(s, key, fmt):
    return fmt.format(s[key]) if s else "–"


print("| Case | Score with / without | Turns with / without | Cost with / without | Time with / without |")
print("|---|---|---|---|---|")
totals = {"with": [], "without": []}
for case in result["cases"]:
    w, wo = stats(case["arms"].get("with", [])), stats(case["arms"].get("without", []))
    totals["with"].append(w)
    totals["without"].append(wo)
    print(f"| {case['name']} | {cell(w, 'score', '{:.2f}')} / {cell(wo, 'score', '{:.2f}')} "
          f"| {cell(w, 'turns', '{:.1f}')} / {cell(wo, 'turns', '{:.1f}')} "
          f"| {cell(w, 'cost', '${:.2f}')} / {cell(wo, 'cost', '${:.2f}')} "
          f"| {cell(w, 'secs', '{:.0f}s')} / {cell(wo, 'secs', '{:.0f}s')} |")


def overall(arm, key):
    values = [s[key] for s in totals[arm] if s]
    return mean(values) if values else float("nan")


print(f"| **mean** | **{overall('with', 'score'):.2f} / {overall('without', 'score'):.2f}** "
      f"| {overall('with', 'turns'):.1f} / {overall('without', 'turns'):.1f} "
      f"| ${overall('with', 'cost'):.2f} / ${overall('without', 'cost'):.2f} "
      f"| {overall('with', 'secs'):.0f}s / {overall('without', 'secs'):.0f}s |")
runs = result["cases"][0]["runsPerCase"] if result["cases"] else 0
print(f"\n{len(result['cases'])} cases × {runs} runs per arm, Claude Code {result['claudeVersion']}, "
      f"{result['startedAt'][:10]}.")
