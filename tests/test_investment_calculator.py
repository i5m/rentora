"""Tests for InvestmentCalculator.

End-of-year contribution model: when a year ticks, existing capital compounds
first, and any new contribution is added at the very end (so it does not earn
returns the year it is contributed). Seed capital provided to the constructor
is treated as start-of-life money and *does* compound on year zero.
"""

import pytest

from calculators.investment_calculator import InvestmentCalculator
from models import InvestmentInput


@pytest.fixture
def investment_input() -> InvestmentInput:
    return InvestmentInput(annual_increase_percentage=7.0)


class TestSeedCapitalCompounding:
    def test_seed_capital_earns_year_zero_returns(self, investment_input: InvestmentInput):
        calc = InvestmentCalculator(investment_input, initial_principal=10000.0)
        calc.compound_year()
        stats = calc.get_stats()
        assert stats["investment_principal"] == pytest.approx(10000.0)
        assert stats["investment_total"] == pytest.approx(10700.0)


class TestEndOfYearContribution:
    def test_new_capital_does_not_compound_same_year(self, investment_input: InvestmentInput):
        calc = InvestmentCalculator(investment_input, initial_principal=0.0)
        calc.compound_year()
        calc.add_capital(1000.0)
        stats = calc.get_stats()
        # Added at year-end, no growth this year.
        assert stats["investment_principal"] == pytest.approx(1000.0)
        assert stats["investment_total"] == pytest.approx(1000.0)

    def test_added_capital_compounds_following_year(self, investment_input: InvestmentInput):
        calc = InvestmentCalculator(investment_input, initial_principal=0.0)
        calc.compound_year()
        calc.add_capital(1000.0)
        calc.compound_year()
        calc.add_capital(1000.0)
        stats = calc.get_stats()
        assert stats["investment_principal"] == pytest.approx(2000.0)
        assert stats["investment_total"] == pytest.approx(1000.0 * 1.07 + 1000.0)

    def test_zero_or_negative_capital_is_ignored(self, investment_input: InvestmentInput):
        calc = InvestmentCalculator(investment_input, initial_principal=500.0)
        calc.add_capital(0.0)
        calc.add_capital(-100.0)
        stats = calc.get_stats()
        assert stats["investment_principal"] == pytest.approx(500.0)


class TestAggregateGrowth:
    def test_principal_tracks_cumulative_contributions(self, investment_input: InvestmentInput):
        calc = InvestmentCalculator(investment_input, initial_principal=1000.0)
        for _ in range(5):
            calc.compound_year()
            calc.add_capital(500.0)
        stats = calc.get_stats()
        assert stats["investment_principal"] == pytest.approx(1000.0 + 5 * 500.0)

    def test_total_strictly_greater_than_principal_with_positive_returns(
        self, investment_input: InvestmentInput
    ):
        calc = InvestmentCalculator(investment_input, initial_principal=1000.0)
        for _ in range(10):
            calc.compound_year()
            calc.add_capital(500.0)
        stats = calc.get_stats()
        assert stats["investment_total"] > stats["investment_principal"]
