from pydantic import BaseModel, Field

class LocationInput(BaseModel):
    country: str
    zip_code: str

class RentInput(BaseModel):
    monthly_rent: float
    monthly_utilities: float
    yoy_increase_percentage: float
    annual_insurance_amount: float

class HouseInput(BaseModel):
    total_cost: float
    mortgage_interest_rate: float
    mortgage_years: int
    monthly_utilities: float
    appreciation_yoy: float
    closing_cost: float
    down_payment_percentage: float
    annual_insurance: float
    property_tax_percentage: float
    pmi: float

class InvestmentInput(BaseModel):
    annual_increase_percentage: float

class HelocInput(BaseModel):
    interest_rate_percentage: float
    loan_lenth_years: int
    after_years: int
    ltv_cap: float = Field(default=0.80, description="Fixed at 80%")
