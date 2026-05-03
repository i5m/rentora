# Simulation semantics (explaining outputs)

Summarized from repo [`README.md`](../../../README.md) and [`src/calculators/simulation.py`](../../../src/calculators/simulation.py).

Per simulated year (order matters):

1. Compute the renter’s annual cash outflow.
2. Compute the buyer’s annual cash outflow (mortgage, taxes, insurance, utilities, PMI).
3. If the HELOC trigger year matches, borrow maximum equity capped by **`ltv_cap`** and add proceeds to the buyer’s investments at the **start** of that year.
4. Compound both sides’ existing investments for the year.
5. Add the **cash-flow surplus** (whoever spent less) as **new principal** to the other side’s investments. New principal lands at **year-end** and earns returns starting the **next** year.
6. **Net worth:** `renter_net_worth` = invested capital; `buyer_net_worth` = `home_value - mortgage_balance - heloc_balance + invested capital`. The first year buyer exceeds renter is **`break_even_year`**.

**Smart renter:** The renter starts with seed capital equal to the buyer’s initial out-of-pocket (`down_payment + closing_cost`) so the comparison is like-for-like.

Use this only to **explain** tool output—do **not** substitute hand-calculated numbers for **`yearly_breakdown`**.
