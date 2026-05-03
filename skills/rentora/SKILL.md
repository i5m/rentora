---
name: rentora
description: >-
  Guides AI agents through the Rentora MCP workflow: collect every input for tool rent_vs_buy,
  verify them with the user, run the simulation, then present yearly tables, optional net-worth charts,
  and a grounded interpretation (break-even, best_option_at_end). Use when the user wants rent vs buy,
  buy vs rent, mortgage comparison, HELOC reinvestment modeling, housing net-worth projections,
  or yearly_breakdown output from Rentora. Complements the server MCP prompt rent_vs_buy_guide for
  clients that do not surface MCP prompts reliably.
license: MIT
compatibility: Requires MCP tool rent_vs_buy from a Rentora server (or compatible host).
metadata:
  upstream-repo: rentora-mcp
  skill-version: "1.0"
---

# Rentora: rent vs buy (MCP `rent_vs_buy`)

This skill mirrors the **`rent_vs_buy_guide` MCP prompt** on the Rentora server. Use it **in addition** to that prompt when the client ignores MCP prompts—workflow rules are the same.

## Role and limits

- **Greet briefly** and give a simple overview: Rentora compares **renting vs buying** over a horizon using the MCP tool **`rent_vs_buy`**. Output is a **purely mathematical projection** from the inputs provided.
- State clearly: **this is not financial advice.**

## Preconditions

- **Every variable is required** for the tool to behave correctly. **All** nested fields under `location`, `rent`, `house`, `inflation`, `investments`, `heloc`, plus top-level **`years_to_simulate`**, must be present before calling the tool.
- If the user has **not provided inputs** (no scenario at all), **do not call `rent_vs_buy`**. Ask for inputs using questions or the JSON template first.

## Collect inputs

### When you can ask questions

Use an **ordered questionnaire**, grouped like the tool payload:

1. Location → `location.country`, `location.zip_code`
2. Rent → `rent.monthly_rent`, `rent.monthly_utilities`, `rent.yoy_increase_percentage`, `rent.annual_insurance_amount`
3. House → all `house.*` fields (see [references/tool-reference.md](references/tool-reference.md))
4. Inflation → `inflation.annual_increase_percentage`
5. Investments → `investments.annual_increase_percentage`
6. HELOC → `heloc.interest_rate_percentage`, `heloc.loan_length_years`, `heloc.after_years`, `heloc.ltv_cap`
7. Horizon → `years_to_simulate` (**always confirm explicitly**; do not silently assume.)

For each answer, tie it to the **exact JSON path**. Confirm ambiguous units (rates as percent vs decimals; PMI meaning).

### When you cannot ask questions

Provide the **JSON template** from [references/tool-reference.md](references/tool-reference.md). Ask the user to fill **every** field and paste the completed JSON back. Validate completeness before proceeding.

### Optional MCP `prefill`

Some hosts pass prompt argument **`prefill`** (partial scenario). **Merge** it with user answers; you still need **every** field before calling **`rent_vs_buy`**.

## Show and verify inputs (mandatory before tool call)

Immediately **before** invoking **`rent_vs_buy`**:

1. Present the **complete** payload in a **user-friendly** way (labeled sections or a readable table)—plain-language headings (e.g. “Rent”, “Home purchase”, “HELOC”), not JSON paths alone.
2. Include values from **user replies**, **`prefill`**, and any **defaults**—**explicitly flag defaults** (e.g. HELOC `ltv_cap` from schema default).
3. If interaction allows, pause for **confirmation or corrections**.

## Call the tool

- Tool name: **`rent_vs_buy`** (exact).
- Arguments: **one object** with keys `location`, `rent`, `house`, `inflation`, `investments`, `heloc`, `years_to_simulate`.
- Parse the MCP tool result body **as JSON**. Use **`yearly_breakdown`**, **`break_even_year`**, **`best_option_at_end`**, **`location`** only from that parsed object—not from memory.

See [references/tool-reference.md](references/tool-reference.md) for units (**percent** vs **`heloc.ltv_cap`** as **0..1** ratio).

## Display the output

1. **Table first:** Build a **year-by-year** table from **`yearly_breakdown`**. Minimum columns: **`year`**, **`renter_net_worth`**, **`buyer_net_worth`**, **`networth_difference_absolute`**. Optionally add `rent_cost`, `buy_cost`, `home_value` for context—all sourced **only** from `yearly_breakdown`.
2. **Charts (if supported):** Plot **`renter_net_worth`** and **`buyer_net_worth`** vs **`year`** only. Do **not** extrapolate or add points not in JSON; if unsure, **omit** the chart.
3. **Explanation:** Summarize **`break_even_year`** and **`best_option_at_end`** and what “better” means **exactly as returned**. Ground narrative **only** in that JSON.

Follow [references/presentation-rules.md](references/presentation-rules.md) for anti-hallucination spot-checks.

## Closing suggestion

Offer qualitative follow-ups **outside** this tool: neighborhood research, area outlook, builder reputation, regulatory risks, personal preferences—the simulation does **not** cover those.

## Deeper reference

- Full input/output catalog and JSON template: [references/tool-reference.md](references/tool-reference.md)
- Tables, charts, fidelity rules: [references/presentation-rules.md](references/presentation-rules.md)
- How the simulation scores net worth (smart renter, HELOC timing): [references/semantics.md](references/semantics.md)
- Golden payload example: [assets/sample-request.json](assets/sample-request.json)
