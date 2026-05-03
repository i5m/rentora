# Presenting results (tables, charts, narrative)

## Anti-hallucination

If any number or conclusion cannot be traced to the **latest** `rent_vs_buy` tool JSON response, **do not state it**. Re-run the tool or collect missing inputs instead.

## Tables

- Every numeric cell must match **`yearly_breakdown`** **verbatim** (same numeric values as returned).
- Before publishing the table, **spot-check** at least the **first row**, **last row**, and **one middle row** against the raw JSON (`year`, `renter_net_worth`, `buyer_net_worth`, `networth_difference_absolute`, etc.).

**Recommended minimum columns**

| Column | Source field |
| --- | --- |
| Year | `year` |
| Renter net worth | `renter_net_worth` |
| Buyer net worth | `buyer_net_worth` |
| Difference (buy − rent) | `networth_difference_absolute` |

Optional context columns (still from JSON only): `rent_cost`, `buy_cost`, `home_value`.

## Charts

- Plot **only** **`renter_net_worth`** and **`buyer_net_worth`** versus **`year`** from `yearly_breakdown`.
- Do **not** extrapolate, smooth, interpolate extra years, or add points not returned.
- If plotting would require guessing values, **omit the chart** and keep the table.

## Narrative

- **`break_even_year`** and **`best_option_at_end`** must match the JSON **exactly** (if `break_even_year` is null, say so—do not invent a year).
- “Better” at the horizon means **higher modeled net worth** per **`best_option_at_end`**.
- Do not contradict **`best_option_at_end`** unless you have verified a parsing mistake—then fix parsing and re-read the JSON.

## Inputs recap before tool call

Immediately before **`rent_vs_buy`**, show **all** inputs in plain language with defaults flagged—see main **`SKILL.md`** workflow step “Show and verify inputs.”
