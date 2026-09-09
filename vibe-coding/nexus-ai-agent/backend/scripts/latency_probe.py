from __future__ import annotations

import argparse
import asyncio
import time

import httpx

PROMPTS = ["hey", "What is recursion?", "change the accent color to red"]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Probe NEXUS /api/chat latency. Backend logs contain the phase breakdown.")
    parser.add_argument("--url", default="http://localhost:8000/api/chat")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    async with httpx.AsyncClient(timeout=90) as client:
        for _ in range(max(1, args.repeat)):
            for prompt in PROMPTS:
                request_id = f"latency-probe-{time.time_ns()}"
                started = time.perf_counter()
                response = await client.post(
                    args.url,
                    headers={"X-Nexus-Request-Id": request_id},
                    json={"message": prompt, "history": [], "ui_context": {"model": "nexus", "accent": "lime", "visible_widgets": {}, "analytics_range": "7D", "analytics_filter": "ALL", "generated_section": None}},
                )
                elapsed = time.perf_counter() - started
                print(f"PROMPT={prompt!r} frontend_to_backend={elapsed:.3f}s status={response.status_code} body={response.text[:500]}")
                print("  See backend [CHAT PERF] log line for context_build/agent/nvidia_calls/tools/response_build and each NVIDIA call.")


if __name__ == "__main__":
    asyncio.run(main())
