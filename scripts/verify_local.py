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
            if "rent_vs_buy" not in tool_names:
                print(f"FAIL: expected rent_vs_buy tool, got {tool_names}")
                return 1

            prompts = await session.list_prompts()
            prompt_names = sorted(p.name for p in prompts.prompts)
            print(f"  prompts: {prompt_names}")
            if "rent_vs_buy_guide" not in prompt_names:
                print(f"FAIL: expected rent_vs_buy_guide prompt, got {prompt_names}")
                return 1

            guide = await session.get_prompt("rent_vs_buy_guide")
            if not guide.messages:
                print("FAIL: rent_vs_buy_guide returned no messages")
                return 1
            first = guide.messages[0]
            if first.role != "assistant":
                print(f"FAIL: expected assistant prompt role, got {first.role!r}")
                return 1
            if first.content.type != "text":
                print(f"FAIL: expected text prompt content, got {first.content.type!r}")
                return 1
            if "mandatory workflow instructions" not in first.content.text:
                print("FAIL: prompt body missing expected preamble")
                return 1
            print("  get_prompt(rent_vs_buy_guide) OK")

            partial = {"location": {"country": "US", "zip_code": "90210"}}
            guide_pre = await session.get_prompt(
                "rent_vs_buy_guide",
                arguments={"prefill": json.dumps(partial)},
            )
            pre_body = guide_pre.messages[0].content
            if pre_body.type != "text" or "90210" not in pre_body.text:
                print("FAIL: prefill prompt did not echo zip code")
                return 1
            print("  get_prompt with prefill OK")

            test_payload = {
                "location": {"country": "US", "zip_code": "10001"},
                "rent": {
                    "monthly_rent": 2000,
                    "monthly_utilities": 150,
                    "yoy_increase_percentage": 3.0,
                    "annual_insurance_amount": 300,
                },
                "house": {
                    "total_cost": 400000,
                    "mortgage_interest_rate": 6.5,
                    "mortgage_years": 30,
                    "monthly_utilities": 250,
                    "yoy_appreciation_percentage": 3.0,
                    "closing_cost": 8000,
                    "down_payment_percentage": 20,
                    "annual_insurance": 1200,
                    "property_tax_percentage": 1.2,
                    "pmi": 0.5,
                },
                "inflation": {"annual_increase_percentage": 2.5},
                "investments": {"annual_increase_percentage": 7.0},
                "heloc": {
                    "interest_rate_percentage": 8.0,
                    "loan_length_years": 15,
                    "after_years": 10,
                    "ltv_cap": 0.8,
                },
                "years_to_simulate": 30,
            }

            print("Calling rent_vs_buy tool...")
            result = await session.call_tool("rent_vs_buy", test_payload)
            payload = json.loads(result.content[0].text)

            if "yearly_breakdown" in payload and len(payload["yearly_breakdown"]) == 30:
                print(f"  OK. Break-even year: {payload.get('break_even_year')}")
            else:
                print(f"FAIL: Bad response payload: {payload.keys()}")
                return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8787/sse")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.url)))
