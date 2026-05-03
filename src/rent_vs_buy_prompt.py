"""MCP prompt body for the `rent_vs_buy_guide` workflow.

Hosts inject this text so the model knows how to gather inputs, call the tool,
and present results without inventing numbers.
"""

from __future__ import annotations

import json

from models import RentVsBuyPromptPrefill

# ruff: noqa: E501 — MCP prompt is intentionally long-form prose for agents.

RENT_VS_BUY_WORKFLOW_GUIDE = """## Rentora: rent vs buy workflow

You are helping someone compare **renting vs buying** using the Rentora MCP tool `rent_vs_buy`. The tool runs a **purely mathematical simulation** over a chosen horizon. It is **not financial advice**.

---

### A. How to use the MCP tool

1. **Tool name:** call MCP tool **`rent_vs_buy`** exactly (no aliases).
2. **Arguments:** Pass **one structured object** with these **top-level keys**:
   `location`, `rent`, `house`, `inflation`, `investments`, `heloc`, `years_to_simulate`.
   Nested objects must match the field names below (same shape as the JSON template).
3. **Units (critical):**
   - Almost all rates and percentages are **plain percent numbers** (e.g. `6.5` = 6.5% annual mortgage rate; `20` = 20% down payment).
   - **Exception:** `heloc.ltv_cap` is a **ratio from 0 to 1** (e.g. `0.8` for 80% max LTV), **not** a percent like `80`.
   - Confirm ambiguous answers with the user (e.g. “6.5” vs “0.065”) before calling the tool.
4. **Reading the response:**
   - Parse the tool result **as JSON** from the MCP tool response text (same payload shape hosts already receive from `call_tool`).
   - Use **`yearly_breakdown`**, **`break_even_year`**, **`best_option_at_end`**, and **`location`** **only** from that parsed JSON—not from memory, estimation, or prior turns unless this JSON is present again.
5. **Optional MCP `prefill`:** The host may supply prompt argument **`prefill`** (partial JSON matching `RentVsBuyPromptPrefill`: nested `location`, `rent`, `house`, etc.). **Merge** those values into the eventual `rent_vs_buy` payload; **still** collect every missing field from the user (or template). **Do not call `rent_vs_buy` until the full tool payload is complete.**
6. **Show inputs before calling the tool:** Immediately **before** invoking `rent_vs_buy`, present the **complete** scenario in a **user-friendly** way (short labeled sections or a readable table)—**plain-language headings** (e.g. “Rent”, “Home purchase”, “HELOC”), not raw JSON paths only. Include **every** value you will send: from **user replies**, merged **`prefill`**, and any **defaults** (explicitly flag defaults, e.g. “HELOC max LTV: 0.80 (default)”). If the host allows interaction, pause for confirmation or corrections; if not, still print this summary **once** before the tool call so the user can see what was assumed.

---

### B. How to ask the user for inputs

**If you can ask questions:** Use an **ordered questionnaire**, grouped like the payload:

1. **Location:** `location.country`, `location.zip_code`
2. **Rent:** `rent.monthly_rent`, `rent.monthly_utilities`, `rent.yoy_increase_percentage`, `rent.annual_insurance_amount`
3. **House:** `house.total_cost`, `house.mortgage_interest_rate`, `house.mortgage_years`, `house.monthly_utilities`, `house.yoy_appreciation_percentage`, `house.closing_cost`, `house.down_payment_percentage`, `house.annual_insurance`, `house.property_tax_percentage`, `house.pmi`
4. **Inflation:** `inflation.annual_increase_percentage`
5. **Investments:** `investments.annual_increase_percentage`
6. **HELOC:** `heloc.interest_rate_percentage`, `heloc.loan_length_years`, `heloc.after_years`, `heloc.ltv_cap`
7. **Horizon:** `years_to_simulate`

For **each** answer, tie it to the **exact JSON path** above. Prefer **one block at a time** (or one field at a time if the user wants). Maintain a **mental checklist**: **if any required field is missing, do not call `rent_vs_buy`.**

**If you cannot ask follow-up questions:** Give the user the **JSON template** below. Ask them to **fill every placeholder** and paste the completed JSON back. **Validate completeness**, then call `rent_vs_buy` with that object.

---

### Required inputs catalog (all must be provided before calling the tool)

| Path | Meaning |
|------|---------|
| `location.country` | Country label (tagged on response; required string) |
| `location.zip_code` | Postal/ZIP code (tagged on response; required string) |
| `rent.monthly_rent` | Monthly rent (≥ 0) |
| `rent.monthly_utilities` | Monthly utilities while renting (≥ 0) |
| `rent.yoy_increase_percentage` | YoY rent change (**percent**, can be negative) |
| `rent.annual_insurance_amount` | Renter insurance per year (≥ 0) |
| `house.total_cost` | Purchase price / total cost (> 0) |
| `house.mortgage_interest_rate` | Annual mortgage rate (**percent**, ≥ 0) |
| `house.mortgage_years` | Mortgage term in years (integer > 0) |
| `house.monthly_utilities` | Monthly utilities as owner (≥ 0) |
| `house.yoy_appreciation_percentage` | Annual home appreciation (**percent**, can be negative) |
| `house.closing_cost` | Closing costs (≥ 0) |
| `house.down_payment_percentage` | Down payment (**percent** 0-100) |
| `house.annual_insurance` | Owner annual insurance (≥ 0) |
| `house.property_tax_percentage` | Property tax as **percent** of home value per year (≥ 0) |
| `house.pmi` | PMI as **annual percent of original loan** (≥ 0); applies when LTV > 80% |
| `inflation.annual_increase_percentage` | General inflation (**percent**, can be negative) |
| `investments.annual_increase_percentage` | Expected portfolio return (**percent**, can be negative) |
| `heloc.interest_rate_percentage` | HELOC annual rate (**percent**, ≥ 0) |
| `heloc.loan_length_years` | HELOC amortization term (integer > 0) |
| `heloc.after_years` | Simulation year index (0-based) when HELOC is taken (≥ 0) |
| `heloc.ltv_cap` | Max combined LTV as **ratio** in (0, 1], typically `0.8` |
| `years_to_simulate` | Number of years to simulate (integer); ask explicitly—do not silently assume |

---

### JSON template (fill all fields, then call `rent_vs_buy`)

```json
{
  "location": { "country": "", "zip_code": "" },
  "rent": {
    "monthly_rent": 0,
    "monthly_utilities": 0,
    "yoy_increase_percentage": 0,
    "annual_insurance_amount": 0
  },
  "house": {
    "total_cost": 0,
    "mortgage_interest_rate": 0,
    "mortgage_years": 0,
    "monthly_utilities": 0,
    "yoy_appreciation_percentage": 0,
    "closing_cost": 0,
    "down_payment_percentage": 0,
    "annual_insurance": 0,
    "property_tax_percentage": 0,
    "pmi": 0
  },
  "inflation": { "annual_increase_percentage": 0 },
  "investments": { "annual_increase_percentage": 0 },
  "heloc": {
    "interest_rate_percentage": 0,
    "loan_length_years": 0,
    "after_years": 0,
    "ltv_cap": 0.8
  },
  "years_to_simulate": 30
}
```

---

### C. Accuracy guardrails (tables, charts, narrative)

**Anti-hallucination:** If any number or conclusion cannot be traced to the **latest** `rent_vs_buy` tool JSON response, **do not state it**. Re-run the tool or collect missing inputs instead.

**Tables:**
- Every numeric cell must match **`yearly_breakdown`** from that JSON **verbatim** (same floats/integers as returned).
- Before showing the table, **spot-check** at least the **first row**, **last row**, and **one middle row** against the raw JSON (`year`, `renter_net_worth`, `buyer_net_worth`, `networth_difference_absolute`, etc.).

**Charts:**
- Only plot **`renter_net_worth`** and **`buyer_net_worth`** versus **`year`** from `yearly_breakdown`.
- Do **not** extrapolate, smooth, interpolate extra years, or add points not returned.
- If you cannot plot faithfully from the JSON, **omit the chart** and keep the table.

**Summary:**
- State **`break_even_year`** and **`best_option_at_end`** **exactly** as in the JSON (if `break_even_year` is null/absent, say so—not invented).
- “Better” at the horizon means **higher modeled net worth** per `best_option_at_end`; do not contradict `best_option_at_end` unless you have identified a parsing error—in that case, fix parsing and re-read the JSON.

---

### Presenting results (after a successful tool call)

1. **Table first:** Year-by-year breakdown with at minimum: `year`, `renter_net_worth`, `buyer_net_worth`, `networth_difference_absolute`. Optionally add `rent_cost`, `buy_cost`, `home_value` for context—all still sourced only from `yearly_breakdown`.
2. **Charts (optional):** Line chart of renter vs buyer net worth over `year`, only if your environment supports faithful plotting from the JSON series (see section C).
3. **Short explanation:** Interpret `break_even_year`, final net worths, and `best_option_at_end` in plain language, grounded **only** in that JSON.
4. **Closing:** Offer qualitative follow-ups the tool does **not** cover (neighborhood research, builder reputation, local market sentiment, regulatory risks, personal cash-flow preferences). Make clear those are outside this simulation.

"""


def rent_vs_buy_guide_messages(
    prefill: RentVsBuyPromptPrefill | None = None,
) -> list[dict]:
    """Prompt messages for FastMCP (`assistant` role).

    Avoid importing ``mcp`` at module scope here: Workers/Pyodide imports ``worker``
    before ``setup_server()`` runs, and pulling in ``mcp`` triggers jsonschema/rpds
    entropy calls that Pyodide forbids during global import.
    """
    sections: list[str] = [
        "Treat everything below as mandatory workflow instructions you must follow.\n\n",
        RENT_VS_BUY_WORKFLOW_GUIDE,
    ]
    if prefill is not None:
        merged = prefill.model_dump(mode="python", exclude_none=True)
        if merged:
            sections.append(
                "\n\n---\n\n### Known inputs from MCP (`prefill`)\n\n"
                "Merge these into the eventual `rent_vs_buy` tool call. Still collect any "
                "missing fields from the user (or filled JSON); do not call the tool until "
                "every required field is present.\n\n```json\n"
                f"{json.dumps(merged, indent=2)}\n```"
            )
    body = "".join(sections)
    return [
        {
            "role": "assistant",
            "content": {"type": "text", "text": body},
        }
    ]
