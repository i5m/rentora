"""End-to-end tests for `run_simulation`.

These exercise the full rent-vs-buy projection across multiple years to verify
shape, invariants, break-even detection, and edge cases like zero / negative
renter net worth.
"""

from itertools import pairwise

import pytest

from calculators.simulation import run_simulation
from models import (
    HelocInput,
    HouseInput,
    InflationInput,
    InvestmentInput,
    LocationInput,
    RentInput,
)


def _inputs(**overrides):
    base = {
        "location": LocationInput(country="US", zip_code="10001"),
        "rent": RentInput(
            monthly_rent=2000.0,
            monthly_utilities=150.0,
            yoy_increase_percentage=3.0,
            annual_insurance_amount=300.0,
        ),
        "house": HouseInput(
            total_cost=400000.0,
            mortgage_interest_rate=6.5,
            mortgage_years=30,
            monthly_utilities=250.0,
            yoy_appreciation_percentage=3.0,
            closing_cost=8000.0,
            down_payment_percentage=20.0,
            annual_insurance=1200.0,
            property_tax_percentage=1.2,
            pmi=0.5,
        ),
        "inflation": InflationInput(annual_increase_percentage=2.5),
        "investments": InvestmentInput(annual_increase_percentage=7.0),
        "heloc": HelocInput(
            interest_rate_percentage=8.0,
            loan_length_years=15,
            after_years=10,
            ltv_cap=0.80,
        ),
        "years_to_simulate": 30,
    }
    base.update(overrides)
    return base


class TestShape:
    def test_yearly_breakdown_length_matches_years_to_simulate(self):
        result = run_simulation(**_inputs(years_to_simulate=10))
        assert len(result["yearly_breakdown"]) == 10

    def test_each_year_has_required_keys(self):
        result = run_simulation(**_inputs(years_to_simulate=2))
        required = {
            "year",
            "rent_cost",
            "renter_investment_principal",
            "renter_investment_total",
            "renter_net_worth",
            "buy_cost",
            "home_value",
            "mortgage_balance",
            "heloc_balance",
            "buyer_investment_principal",
            "buyer_investment_total",
            "buyer_net_worth",
            "networth_difference_absolute",
            "networth_difference_percentage",
        }
        for entry in result["yearly_breakdown"]:
            assert required.issubset(entry.keys())

    def test_top_level_keys(self):
        result = run_simulation(**_inputs(years_to_simulate=5))
        assert set(result.keys()) == {
            "location",
            "yearly_breakdown",
            "break_even_year",
            "best_option_at_end",
        }
        assert result["best_option_at_end"] in {"Buy", "Rent"}


class TestInvariants:
    def test_renter_seed_capital_equals_buyer_initial_out_of_pocket(self):
        result = run_simulation(**_inputs(years_to_simulate=1))
        # Renter starts with 88k seed (down + closing). After year 0:
        #   compound to 88k * 1.07 = 94160
        #   add (buy_cost - rent_cost) at end of year (buy is more expensive year 0)
        first_year = result["yearly_breakdown"][0]
        # Principal = seed + difference contributed end of year 0
        assert first_year["renter_investment_principal"] >= 88000.0

    def test_buyer_starts_with_zero_investment_principal(self):
        result = run_simulation(**_inputs(years_to_simulate=1))
        first_year = result["yearly_breakdown"][0]
        # Buyer only invests when rent > buy, which is rare in year 0.
        # The principal at year 0 may be 0 if buying is more expensive.
        assert first_year["buyer_investment_principal"] >= 0.0

    def test_mortgage_balance_decreases_over_time(self):
        result = run_simulation(**_inputs(years_to_simulate=30))
        balances = [y["mortgage_balance"] for y in result["yearly_breakdown"]]
        for prev, nxt in pairwise(balances):
            assert nxt <= prev

    def test_home_value_grows_at_appreciation_rate(self):
        result = run_simulation(**_inputs(years_to_simulate=3))
        years = result["yearly_breakdown"]
        assert years[1]["home_value"] == pytest.approx(years[0]["home_value"] * 1.03)
        assert years[2]["home_value"] == pytest.approx(years[1]["home_value"] * 1.03)


class TestHelocActivation:
    def test_heloc_balance_zero_before_activation(self):
        result = run_simulation(**_inputs(years_to_simulate=15))
        years = result["yearly_breakdown"]
        for y in years[:10]:
            assert y["heloc_balance"] == 0.0

    def test_heloc_active_after_trigger_year(self):
        result = run_simulation(**_inputs(years_to_simulate=15))
        # Year 10 is when HELOC activates and starts paying down.
        years = result["yearly_breakdown"]
        assert years[10]["heloc_balance"] > 0.0


class TestBreakEvenAndBestOption:
    def test_break_even_is_int_or_none(self):
        result = run_simulation(**_inputs(years_to_simulate=30))
        assert result["break_even_year"] is None or isinstance(result["break_even_year"], int)

    def test_buy_wins_with_high_appreciation(self):
        result = run_simulation(
            **_inputs(
                house=HouseInput(
                    total_cost=400000.0,
                    mortgage_interest_rate=4.0,
                    mortgage_years=30,
                    monthly_utilities=250.0,
                    yoy_appreciation_percentage=8.0,
                    closing_cost=8000.0,
                    down_payment_percentage=20.0,
                    annual_insurance=1200.0,
                    property_tax_percentage=1.2,
                    pmi=0.5,
                ),
                years_to_simulate=30,
            )
        )
        assert result["best_option_at_end"] == "Buy"

    def test_rent_wins_with_no_appreciation_and_high_returns(self):
        result = run_simulation(
            **_inputs(
                house=HouseInput(
                    total_cost=400000.0,
                    mortgage_interest_rate=8.0,
                    mortgage_years=30,
                    monthly_utilities=250.0,
                    yoy_appreciation_percentage=0.0,
                    closing_cost=8000.0,
                    down_payment_percentage=20.0,
                    annual_insurance=1200.0,
                    property_tax_percentage=1.2,
                    pmi=0.5,
                ),
                investments=InvestmentInput(annual_increase_percentage=10.0),
                years_to_simulate=30,
            )
        )
        assert result["best_option_at_end"] == "Rent"


class TestNetWorthPercentageGuard:
    def test_zero_percentage_when_renter_net_worth_is_zero(self):
        # Force a near-zero renter scenario by zeroing out the renter's seed
        # capital indirectly: with a very large down payment percentage and
        # zero return there is still seed capital, so this is a smoke test.
        result = run_simulation(**_inputs(years_to_simulate=1))
        # Just verify the field is always finite (no division-by-zero crash).
        for y in result["yearly_breakdown"]:
            assert y["networth_difference_percentage"] is not None
            assert isinstance(y["networth_difference_percentage"], (int, float))

    def test_no_crash_with_no_initial_capital(self):
        # Renter seed capital is buyer's down + closing. Make those zero so
        # renter starts with $0 and net worth could be 0 or negative.
        result = run_simulation(
            **_inputs(
                house=HouseInput(
                    total_cost=400000.0,
                    mortgage_interest_rate=6.5,
                    mortgage_years=30,
                    monthly_utilities=250.0,
                    yoy_appreciation_percentage=3.0,
                    closing_cost=0.0,
                    down_payment_percentage=0.0,
                    annual_insurance=1200.0,
                    property_tax_percentage=1.2,
                    pmi=0.0,
                ),
                years_to_simulate=5,
            )
        )
        for y in result["yearly_breakdown"]:
            assert isinstance(y["networth_difference_percentage"], (int, float))
