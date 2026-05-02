"""Tests for RentCalculator.

Pure-Python tests over the rent-side projection logic. Inflation is applied to
utilities and insurance for *next* year; the rent-bump (`yoy_increase`) is
applied to the rent itself for next year.
"""

import pytest

from calculators.rent_calculator import RentCalculator
from models import RentInput


@pytest.fixture
def rent_input() -> RentInput:
    return RentInput(
        monthly_rent=2000.0,
        monthly_utilities=150.0,
        yoy_increase_percentage=3.0,
        annual_insurance_amount=300.0,
    )


class TestYearZero:
    def test_costs_use_initial_values(self, rent_input: RentInput):
        calc = RentCalculator(rent_input, inflation_rate=0.025)
        result = calc.calculate_year(0)

        assert result["year"] == 0
        assert result["rent_cost"] == pytest.approx(2000.0 * 12)
        assert result["utilities_cost"] == pytest.approx(150.0 * 12)
        assert result["insurance_cost"] == pytest.approx(300.0)
        assert result["total_rent_cost"] == pytest.approx(24000.0 + 1800.0 + 300.0)

    def test_monthly_rent_reports_current_year_value(self, rent_input: RentInput):
        calc = RentCalculator(rent_input, inflation_rate=0.025)
        result = calc.calculate_year(0)
        assert result["monthly_rent"] == pytest.approx(2000.0)


class TestYearOne:
    def test_rent_uses_yoy_increase_only(self, rent_input: RentInput):
        calc = RentCalculator(rent_input, inflation_rate=0.025)
        calc.calculate_year(0)
        result = calc.calculate_year(1)

        # Rent grows by yoy_increase, NOT by inflation.
        assert result["rent_cost"] == pytest.approx(2000.0 * 1.03 * 12)
        assert result["monthly_rent"] == pytest.approx(2000.0 * 1.03)

    def test_utilities_and_insurance_use_inflation(self, rent_input: RentInput):
        calc = RentCalculator(rent_input, inflation_rate=0.025)
        calc.calculate_year(0)
        result = calc.calculate_year(1)

        assert result["utilities_cost"] == pytest.approx(150.0 * 1.025 * 12)
        assert result["insurance_cost"] == pytest.approx(300.0 * 1.025)


class TestZeroInflation:
    def test_costs_stay_constant(self, rent_input: RentInput):
        rent_input.yoy_increase_percentage = 0.0
        calc = RentCalculator(rent_input, inflation_rate=0.0)

        first = calc.calculate_year(0)
        second = calc.calculate_year(1)
        third = calc.calculate_year(2)

        assert first["total_rent_cost"] == second["total_rent_cost"] == third["total_rent_cost"]
