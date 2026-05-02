"""Smoke test the locally-running Worker via the MCP SSE transport.

Run this against `uv run pywrangler dev` to verify the deployed tool surface
matches what we expect.

Usage:
    uv run python scripts/verify_local.py
    uv run python scripts/verify_local.py --url http://localhost:8787/sse
"""

import argparse
import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.sse import sse_client


async def main(url: str) -> int:
    print(f"Connecting to {url} ...")
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("  initialized OK")

            tools = await session.list_tools()
            tool_names = sorted(t.name for t in tools.tools)
            print(f"  tools: {tool_names}")
            if tool_names != ["name_value"]:
                print(f"FAIL: expected ['name_value'], got {tool_names}")
                return 1

            cases: list[tuple[str, int]] = [
                ("Cat", 24),
                ("Hello, World!", 124),
                ("", 0),
                ("Cloudflare", 97),
            ]
            failed = False
            for name, expected_total in cases:
                result = await session.call_tool("name_value", {"name": name})
                payload = json.loads(result.content[0].text)
                got_total = payload["total"]
                marker = "OK" if got_total == expected_total else "FAIL"
                print(f"  name_value({name!r}) -> {payload}  [{marker}]")
                if got_total != expected_total:
                    failed = True

            if failed:
                return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8787/sse")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.url)))
