#!/usr/bin/env python3
"""
Run benchmark_arena.py against AI4PC only (skip the other reference LLMs).

Usage:
    OLLAMA_HOST=http://localhost:11435 python3 bot/run_official_bench.py [games]

`games` defaults to 10 (form requires >=10).
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

os.environ.setdefault("OLLAMA_HOST", "http://localhost:11435")

import benchmark_arena as ba

games = int(sys.argv[1]) if len(sys.argv) > 1 else 10
model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

ba.LLMS = {
    "ai.abstraction.submissions.ai4pc.AI4PC": {
        "name": "ai4pc",
        "display": f"{model} (AI4PC)",
        "agent_type": "Hybrid",
        "env": {
            "OLLAMA_MODEL": model,
            "OLLAMA_HOST": os.environ["OLLAMA_HOST"],
        },
    }
}

ba.run_tournament(games_per_pair=games)
