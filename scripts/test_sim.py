import sys
sys.path.insert(0, "src")
from models import LocationInput, RentInput, HouseInput, InvestmentInput, HelocInput, InflationInput
from calculators.simulation import run_simulation

loc = LocationInput(country="US", zip_code="10001")
rent = RentInput(monthly_rent=2000, monthly_utilities=150, yoy_increase_percentage=3.0, annual_insurance_amount=300)
house = HouseInput(total_cost=400000, mortgage_interest_rate=6.5, mortgage_years=30, monthly_utilities=250, yoy_appreciation_percentage=3.0, closing_cost=8000, down_payment_percentage=20, annual_insurance=1200, property_tax_percentage=1.2, pmi=0.5)
inflation = InflationInput(annual_increase_percentage=2.5)
investments = InvestmentInput(annual_increase_percentage=7.0)
heloc = HelocInput(interest_rate_percentage=8.0, loan_lenth_years=15, after_years=10, ltv_cap=0.8)

res = run_simulation(loc, rent, house, inflation, investments, heloc, 30)

print(f"Simulation OK. Break-even year: {res['break_even_year']}")
print(f"Best option at end: {res['best_option_at_end']}")
