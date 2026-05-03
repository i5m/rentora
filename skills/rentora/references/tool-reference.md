# `rent_vs_buy` tool reference

Canonical definitions live in repo [`src/models.py`](../../../src/models.py) and [`README.md`](../../../README.md).

## Invocation

Single MCP tool call named **`rent_vs_buy`** with one structured argument object.

Top-level keys (all required):

| Key | Type | Notes |
| --- | --- | --- |
| `location` | object | Tagged on response; not used in math today. |
| `rent` | object | Rental cash flows and growth. |
| `house` | object | Purchase, mortgage, taxes, PMI, appreciation. |
| `inflation` | object | General inflation rate (percent). |
| `investments` | object | Expected portfolio return (percent). |
| `heloc` | object | HELOC timing and caps. |
| `years_to_simulate` | integer | Simulation horizon (confirm with user). |

## Units

- Nearly all rates are **percent numbers** (e.g. `6.5` means 6.5% annually).
- **`heloc.ltv_cap`** is a **ratio from 0 to 1** (e.g. `0.8` for 80% max LTV), **not** `80`.

## Required fields by group

### `location`

| Field | Constraints |
| --- | --- |
| `country` | Non-empty string |
| `zip_code` | Non-empty string |

### `rent`

| Field | Constraints |
| --- | --- |
| `monthly_rent` | ≥ 0 |
| `monthly_utilities` | ≥ 0 |
| `yoy_increase_percentage` | Percent; ≥ -100 |
| `annual_insurance_amount` | ≥ 0 |

### `house`

| Field | Constraints |
| --- | --- |
| `total_cost` | > 0 |
| `mortgage_interest_rate` | Percent; ≥ 0 |
| `mortgage_years` | Integer > 0 |
| `monthly_utilities` | ≥ 0 |
| `yoy_appreciation_percentage` | Percent; ≥ -100 |
| `closing_cost` | ≥ 0 |
| `down_payment_percentage` | Percent; 0–100 |
| `annual_insurance` | ≥ 0 |
| `property_tax_percentage` | Percent of home value per year; ≥ 0 |
| `pmi` | Percent of original loan annually; ≥ 0; applies when LTV > 80% |

### `inflation`

| Field | Constraints |
| --- | --- |
| `annual_increase_percentage` | Percent; ≥ -100 |

### `investments`

| Field | Constraints |
| --- | --- |
| `annual_increase_percentage` | Percent; ≥ -100 |

### `heloc`

| Field | Constraints |
| --- | --- |
| `interest_rate_percentage` | Percent; ≥ 0 |
| `loan_length_years` | Integer > 0 |
| `after_years` | Integer ≥ 0 (0-based simulation year when HELOC starts) |
| `ltv_cap` | Ratio in (0, 1]; often `0.8` |

### Top-level

| Field | Constraints |
| --- | --- |
| `years_to_simulate` | Integer ≥ 1 (must still be explicitly collected or confirmed) |

## Response (high level)

| Field | Meaning |
| --- | --- |
| `location` | Echo of input |
| `yearly_breakdown` | Array of per-year objects |
| `break_even_year` | First year buyer net worth exceeds renter, or null |
| `best_option_at_end` | `"Buy"` or `"Rent"` by modeled net worth at horizon |

Per-year rows include at least: `year`, `rent_cost`, `renter_net_worth`, `buy_cost`, `home_value`, `mortgage_balance`, `heloc_balance`, `buyer_net_worth`, `networth_difference_absolute`, `networth_difference_percentage`.

## JSON template (fill all fields)

Use the same shape as [assets/sample-request.json](../assets/sample-request.json).

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
