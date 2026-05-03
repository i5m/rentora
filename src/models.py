"""Pydantic input models for the `rent_vs_buy` MCP tool.

All percentage fields are expressed as percent (e.g. 6.5 means 6.5%) unless the
field name explicitly says otherwise (e.g. `ltv_cap` is a 0..1 ratio).
"""

from pydantic import BaseModel, Field


class InflationInput(BaseModel):
    annual_increase_percentage: float = Field(
        ge=-100, description="Annual inflation in percent. Can be negative."
    )


class LocationInput(BaseModel):
    country: str = Field(min_length=1)
    zip_code: str = Field(min_length=1)


class RentInput(BaseModel):
    monthly_rent: float = Field(ge=0)
    monthly_utilities: float = Field(ge=0)
    yoy_increase_percentage: float = Field(
        ge=-100, description="Year-over-year rent change in percent. Can be negative."
    )
    annual_insurance_amount: float = Field(ge=0)


class HouseInput(BaseModel):
    total_cost: float = Field(gt=0)
    mortgage_interest_rate: float = Field(ge=0, description="Annual rate in percent.")
    mortgage_years: int = Field(gt=0)
    monthly_utilities: float = Field(ge=0)
    yoy_appreciation_percentage: float = Field(
        ge=-100, description="Annual home-value change in percent. Can be negative."
    )
    closing_cost: float = Field(ge=0)
    down_payment_percentage: float = Field(ge=0, le=100)
    annual_insurance: float = Field(ge=0)
    property_tax_percentage: float = Field(ge=0)
    pmi: float = Field(
        ge=0,
        description="PMI as an annual percent of the original loan. Only applied when LTV > 80%.",
    )


class InvestmentInput(BaseModel):
    annual_increase_percentage: float = Field(
        ge=-100, description="Expected annual return in percent. Can be negative."
    )


class HelocInput(BaseModel):
    interest_rate_percentage: float = Field(ge=0, description="Annual rate in percent.")
    loan_length_years: int = Field(gt=0)
    after_years: int = Field(ge=0, description="Year (0-indexed) at which to take the HELOC.")
    ltv_cap: float = Field(
        default=0.80, gt=0, le=1, description="Maximum LTV ratio (0..1). Defaults to 0.80."
    )


class RentVsBuyPromptPrefill(BaseModel):
    """Partial scenario fields for MCP prompt argument `prefill` on `rent_vs_buy_guide`.

    Hosts merge this with user answers before calling tool `rent_vs_buy`.
    """

    location: LocationInput | None = Field(default=None)
    rent: RentInput | None = Field(default=None)
    house: HouseInput | None = Field(default=None)
    inflation: InflationInput | None = Field(default=None)
    investments: InvestmentInput | None = Field(default=None)
    heloc: HelocInput | None = Field(default=None)
    years_to_simulate: int | None = Field(default=None, ge=1)
