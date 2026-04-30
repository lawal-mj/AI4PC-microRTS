#!/usr/bin/env python3
"""
Proxy server for MicroRTS AI4PC bot.

Java sends an Ollama-format request with the bare state block as the prompt.
We wrap it with our strategy-selection instructions, forward to real Ollama,
and return the response unchanged.

Usage:
    python3 bot/proxy.py [--port 11435] [--ollama-url http://localhost:11434]

Then set: OLLAMA_HOST=http://localhost:11435
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from argparse import ArgumentParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from router import build_prompt

OLLAMA_URL = "http://localhost:11434"


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        if self.path in ("/api/generate", "/api/chat"):
            self._handle_generate()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == "/api/tags":
            self._forward_get("/api/tags")
        elif self.path == "/":
            self._send_json({"status": "AI4PC proxy running"})
        else:
            self.send_error(404)

    def _handle_generate(self):
        body = self._read_body()
        request = json.loads(body)
        state_block = request.get("prompt", "")

        request["prompt"] = build_prompt(state_block)
        options = request.get("options", {}) or {}
        options["temperature"] = 0
        options["seed"] = 42
        request["options"] = options
        modified_body = json.dumps(request).encode()

        start = time.time()
        response = self._forward_to_ollama(modified_body)
        elapsed_ms = int((time.time() - start) * 1000)

        if response is None:
            self.send_error(502, "Ollama unreachable")
            return

        prompt_tokens = completion_tokens = None
        try:
            parsed = json.loads(response)
            label = parsed.get("response", "").strip().split()[0]
            prompt_tokens = parsed.get("prompt_eval_count")
            completion_tokens = parsed.get("eval_count")
        except Exception:
            label = "?"
        print(f"[proxy] {elapsed_ms}ms -> {label} (in={prompt_tokens} out={completion_tokens})", flush=True)
        self._log_decision(state_block, label, elapsed_ms, prompt_tokens, completion_tokens)
        self._send_bytes(response)

    def _log_decision(self, state, label, elapsed_ms, prompt_tokens, completion_tokens):
        try:
            os.makedirs("bot/results", exist_ok=True)
            with open("bot/results/decisions.jsonl", "a") as f:
                f.write(json.dumps({
                    "type": "decision",
                    "ts": time.time(),
                    "state": state,
                    "label": label,
                    "elapsed_ms": elapsed_ms,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                }) + "\n")
        except Exception:
            pass

    def _forward_to_ollama(self, body):
        try:
            req = urllib.request.Request(
                f"{OLLAMA_URL}{self.path}",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0",
                    "ngrok-skip-browser-warning": "true",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"[proxy] Ollama error: {e}", flush=True)
            return None

    def _forward_get(self, path):
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}{path}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                self._send_bytes(resp.read())
        except Exception as e:
            print(f"[proxy] GET error: {e}", flush=True)
            self.send_error(502)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def _send_json(self, data):
        self._send_bytes(json.dumps(data).encode())

    def _send_bytes(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    global OLLAMA_URL

    parser = ArgumentParser(description="AI4PC proxy for MicroRTS")
    parser.add_argument("--port", type=int, default=11435)
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    args = parser.parse_args()

    OLLAMA_URL = args.ollama_url

    server = HTTPServer(("127.0.0.1", args.port), ProxyHandler)
    print(f"AI4PC proxy on http://127.0.0.1:{args.port}")
    print(f"Forwarding to Ollama at {OLLAMA_URL}")
    print(f"Set OLLAMA_HOST=http://localhost:{args.port}")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
