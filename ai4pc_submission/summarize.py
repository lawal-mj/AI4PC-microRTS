#!/usr/bin/env python3
"""
Aggregate AI4PC submission metrics from logs into one report.

Reads:
  bot/results/decisions.jsonl    (per-LLM-call: latency, tokens) -- written by proxy.py
  bot/results/games.jsonl        (per-game: winner, ticks, units) -- written by AI4PC.gameOver()
  benchmark_results/benchmark_<latest>.json (official win/loss + score)

Writes:
  bot/results/summary.json
  bot/results/summary.md         (human-readable report for the submission ZIP)

Usage: python3 bot/summarize.py
"""

import json
import statistics
from pathlib import Path


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def latest_benchmark():
    files = sorted(Path("benchmark_results").glob("benchmark_*.json"))
    return json.loads(files[-1].read_text()) if files else {}


def stat(values):
    if not values:
        return {"avg": 0, "min": 0, "max": 0, "count": 0}
    return {
        "avg": round(statistics.mean(values), 2),
        "min": min(values),
        "max": max(values),
        "count": len(values),
    }


def main():
    decisions = [d for d in load_jsonl("bot/results/decisions.jsonl") if d.get("type") == "decision"]
    games = [g for g in load_jsonl("bot/results/games.jsonl") if g.get("type") == "game_summary"]
    bench = latest_benchmark()

    latencies = [d["elapsed_ms"] for d in decisions if d.get("elapsed_ms") is not None]
    prompt_toks = [d["prompt_tokens"] for d in decisions if d.get("prompt_tokens") is not None]
    completion_toks = [d["completion_tokens"] for d in decisions if d.get("completion_tokens") is not None]

    wins = sum(1 for g in games if g["winner"] == g["player"])
    draws = sum(1 for g in games if g["winner"] == -1)
    losses = sum(1 for g in games if g["winner"] != g["player"] and g["winner"] != -1)
    total = len(games)

    ticks = [g["final_tick"] for g in games]

    summary = {
        "agent": "ai.abstraction.submissions.ai4pc.AI4PC",
        "total_games": total,
        "win_rate": round(wins / total, 3) if total else 0,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "moves_per_game": stat(ticks),
        "latency_ms_per_llm_call": stat(latencies),
        "tokens_prompt_per_call": stat(prompt_toks),
        "tokens_completion_per_call": stat(completion_toks),
        "tokens_total": {
            "prompt": sum(prompt_toks),
            "completion": sum(completion_toks),
        },
        "units_created_per_game": [g["units_created"] for g in games],
        "benchmark_score": bench.get("benchmark_scores", {}),
        "eliminated_at": bench.get("eliminated_at", {}),
        "benchmark_file": str(sorted(Path("benchmark_results").glob("benchmark_*.json"))[-1])
            if list(Path("benchmark_results").glob("benchmark_*.json")) else None,
    }

    out_dir = Path("bot/results")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    md = []
    md.append("# AI4PC Submission Summary\n")
    md.append(f"- **Total games:** {total}")
    md.append(f"- **Win rate:** {summary['win_rate']:.1%}  ({wins}W / {draws}D / {losses}L)")
    if summary["benchmark_score"]:
        for name, score in summary["benchmark_score"].items():
            elim = summary["eliminated_at"].get(name, "cleared all")
            md.append(f"- **Benchmark score:** {score}  (eliminated at: {elim})")
    md.append("")
    md.append("## Moves per game (ticks)")
    md.append(f"avg={summary['moves_per_game']['avg']}, min={summary['moves_per_game']['min']}, max={summary['moves_per_game']['max']}\n")
    md.append("## LLM latency (ms per call)")
    lat = summary["latency_ms_per_llm_call"]
    md.append(f"avg={lat['avg']}, min={lat['min']}, max={lat['max']}, calls={lat['count']}\n")
    md.append("## Tokens per LLM call")
    pt = summary["tokens_prompt_per_call"]
    ct = summary["tokens_completion_per_call"]
    md.append(f"prompt:     avg={pt['avg']}, min={pt['min']}, max={pt['max']}")
    md.append(f"completion: avg={ct['avg']}, min={ct['min']}, max={ct['max']}")
    md.append(f"total:      prompt={summary['tokens_total']['prompt']}, completion={summary['tokens_total']['completion']}\n")
    md.append("## Units created per game")
    for i, u in enumerate(summary["units_created_per_game"], 1):
        md.append(f"  Game {i}: " + ", ".join(f"{k}={v}" for k, v in u.items()))

    (out_dir / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nWrote {out_dir / 'summary.json'} and {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
