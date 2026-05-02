"""Tests for BuyCalculator.

Covers the standard amortizing mortgage formula, PMI gating against the
original purchase price, property-tax/insurance/utility inflation, and home
appreciation.
"""

import pytest

from calculators.buy_calculator import BuyCalculator
from models import HouseInput


def _house(**overrides) -> HouseInput:
    defaults = {
        "total_cost": 400000.0,
        "mortgage_interest_rate": 6.5,
        "mortgage_years": 30,
        "monthly_utilities": 250.0,
        "yoy_appreciation_percentage": 3.0,
        "closing_cost": 8000.0,
        "down_payment_percentage": 20.0,
        "annual_insurance": 1200.0,
        "property_tax_percentage": 1.2,
        "pmi": 0.5,
    }
    defaults.update(overrides)
    return HouseInput(**defaults)


class TestInitialOutOfPocket:
    def test_includes_down_payment_and_closing(self):
        calc = BuyCalculator(_house(), inflation_rate=0.025)
        assert calc.get_initial_out_of_pocket() == pytest.approx(80000.0 + 8000.0)


class TestMortgagePayment:
    def test_standard_amortization_formula(self):
        calc = BuyCalculator(_house(), inflation_rate=0.0)
        # 320k loan, 6.5% APR, 30 years => ~$2022.62/mo
        assert calc.monthly_mortgage == pytest.approx(2022.62, abs=0.5)

    def test_zero_interest_uses_simple_division(self):
        calc = BuyCalculator(
            _house(mortgage_interest_rate=0.0, total_cost=120000.0, down_payment_percentage=0.0),
            inflation_rate=0.0,
        )
        assert calc.monthly_mortgage == pytest.approx(120000.0 / (30 * 12))


class TestYearZero:
    def test_yearly_mortgage_equals_12_months(self):
        calc = BuyCalculator(_house(), inflation_rate=0.0)
        result = calc.calculate_year(0)
        assert result["yearly_mortgage"] == pytest.approx(calc.monthly_mortgage * 12)

    def test_principal_plus_interest_equals_yearly_mortgage(self):
        calc = BuyCalculator(_house(), inflation_rate=0.0)
        result = calc.calculate_year(0)
        assert result["principal_paid"] + result["interest_paid"] == pytest.approx(
            result["yearly_mortgage"]
        )

    def test_property_tax_uses_purchase_price(self):
        calc = BuyCalculator(_house(), inflation_rate=0.025)
        result = calc.calculate_year(0)
        assert result["property_tax"] == pytest.approx(400000.0 * 0.012)

    def test_no_pmi_at_exactly_20_percent_down(self):
        calc = BuyCalculator(_house(down_payment_percentage=20.0), inflation_rate=0.0)
        result = calc.calculate_year(0)
        assert result["pmi_cost"] == 0.0

    def test_pmi_charged_with_low_down_payment(self):
        calc = BuyCalculator(_house(down_payment_percentage=10.0), inflation_rate=0.0)
        result = calc.calculate_year(0)
        # PMI base is the original loan amount (360k * 0.5%)
        assert result["pmi_cost"] == pytest.approx(360000.0 * 0.005)

    def test_home_value_in_year_zero_is_purchase_price(self):
        calc = BuyCalculator(_house(), inflation_rate=0.025)
        result = calc.calculate_year(0)
        assert result["home_value"] == pytest.approx(400000.0)


class TestAcrossYears:
    def test_remaining_loan_decreases(self):
        calc = BuyCalculator(_house(), inflation_rate=0.025)
        calc.calculate_year(0)
        loan_after_year_0 = calc.remaining_loan
        calc.calculate_year(1)
        loan_after_year_1 = calc.remaining_loan
        assert loan_after_year_1 < loan_after_year_0

    def test_home_appreciates(self):
        calc = BuyCalculator(_house(), inflation_rate=0.025)
        result_0 = calc.calculate_year(0)
        result_1 = calc.calculate_year(1)
        assert result_1["home_value"] == pytest.approx(result_0["home_value"] * 1.03)

    def test_property_tax_inflates(self):
        calc = BuyCalculator(_house(), inflation_rate=0.025)
        result_0 = calc.calculate_year(0)
        result_1 = calc.calculate_year(1)
        assert result_1["property_tax"] == pytest.approx(result_0["property_tax"] * 1.025)

    def test_loan_fully_paid_at_term_end(self):
        calc = BuyCalculator(_house(mortgage_years=15), inflation_rate=0.0)
        for year in range(15):
            calc.calculate_year(year)
        assert calc.remaining_loan == pytest.approx(0.0, abs=1.0)

    def test_no_mortgage_after_term(self):
        calc = BuyCalculator(_house(mortgage_years=15), inflation_rate=0.0)
        for year in range(15):
            calc.calculate_year(year)
        post_term = calc.calculate_year(15)
        assert post_term["yearly_mortgage"] == 0.0
        assert post_term["principal_paid"] == 0.0
        assert post_term["interest_paid"] == 0.0
