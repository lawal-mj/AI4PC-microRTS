# AI4PC

An LLM-based MicroRTS agent. The Java client (`AI4PC.java`) talks to a Python proxy
(`proxy.py`) that wraps each LLM call with a strategy-selection prompt and forwards
to a local Ollama instance. The LLM picks one of four scripted rush strategies
each LLM tick; AI4PC delegates execution to that strategy's bot.

Architecture: Java thin client + Python proxy + local Ollama.

## Prerequisites

- Java 8+ (project targets 1.8)
- Python 3.9+
- [Ollama](https://ollama.ai/) running locally with `llama3.1:8b` pulled

## Run

```bash
# 1. Pull and serve the model (separate terminal, leave running)
ollama pull llama3.1:8b
ollama serve

# 2. Start the AI4PC proxy on port 11435 (separate terminal)
python3 bot/proxy.py

# 3. Compile (if not using prebuilt microrts.jar)
ant build

# 4a. Run a single game (uses resources/config.properties)
java -cp "lib/*:lib/bots/*:bin" rts.MicroRTS -f resources/config.properties

# 4b. Or run the full benchmark
OLLAMA_HOST=http://localhost:11435 python3 benchmark_arena.py --games 10

# 5. Aggregate metrics for the submission
python3 bot/summarize.py
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Where AI4PC's Java side sends HTTP. Set to `http://localhost:11435` to go through the proxy. |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model name passed to Ollama. |

## Logs

- `bot/results/decisions.jsonl` — per-LLM-call: state, label, latency, prompt/completion tokens.
- `bot/results/games.jsonl` — per-game: winner, ticks, units created (worker/light/heavy/ranged/base/barracks).
- `benchmark_results/benchmark_<timestamp>.json` — official `benchmark_arena.py` output.
- `bot/results/summary.json` + `summary.md` — combined report (run `bot/summarize.py`).

## Files

- `src/ai/abstraction/submissions/ai4pc/AI4PC.java` — the agent.
- `bot/proxy.py` — strategy-selection prompt wrapper, forwards to Ollama.
- `bot/router.py` — the prompt template used by the proxy.
- `bot/summarize.py` — merges logs into the submission report.
- `bot/requirements.txt` — Python deps (stdlib only).
