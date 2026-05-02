"""Tests for HelocCalculator.

The HELOC sits idle until the configured trigger year, then activates with the
maximum borrowable amount (LTV cap minus remaining mortgage), and amortizes
over its own loan term.
"""

import pytest

from calculators.heloc_calculator import HelocCalculator
from models import HelocInput


def _heloc(**overrides) -> HelocInput:
    defaults = {
        "interest_rate_percentage": 8.0,
        "loan_length_years": 15,
        "after_years": 10,
        "ltv_cap": 0.80,
    }
    defaults.update(overrides)
    return HelocInput(**defaults)


HOME_VALUE = 500000.0
REMAINING_MORTGAGE = 200000.0


class TestActivation:
    def test_returns_zero_before_trigger_year(self):
        calc = HelocCalculator(_heloc())
        borrowed = calc.check_and_activate(
            year=5, current_home_value=HOME_VALUE, remaining_mortgage=REMAINING_MORTGAGE
        )
        assert borrowed == 0.0
        assert not calc.is_active

    def test_activates_at_trigger_year(self):
        calc = HelocCalculator(_heloc())
        borrowed = calc.check_and_activate(
            year=10, current_home_value=HOME_VALUE, remaining_mortgage=REMAINING_MORTGAGE
        )
        assert borrowed == pytest.approx(HOME_VALUE * 0.80 - REMAINING_MORTGAGE)
        assert calc.is_active

    def test_no_activation_when_no_equity(self):
        calc = HelocCalculator(_heloc())
        borrowed = calc.check_and_activate(
            year=10, current_home_value=300000.0, remaining_mortgage=300000.0
        )
        assert borrowed == 0.0
        assert not calc.is_active

    def test_only_activates_once(self):
        calc = HelocCalculator(_heloc())
        calc.check_and_activate(
            year=10, current_home_value=HOME_VALUE, remaining_mortgage=REMAINING_MORTGAGE
        )
        second = calc.check_and_activate(
            year=10, current_home_value=HOME_VALUE, remaining_mortgage=REMAINING_MORTGAGE
        )
        assert second == 0.0


class TestAmortization:
    def test_zero_payment_when_inactive(self):
        calc = HelocCalculator(_heloc())
        stats = calc.calculate_year()
        assert stats == {
            "yearly_payment": 0.0,
            "remaining_balance": 0.0,
            "principal_paid": 0.0,
            "interest_paid": 0.0,
        }

    def test_payments_reduce_balance(self):
        calc = HelocCalculator(_heloc())
        calc.check_and_activate(
            year=10, current_home_value=HOME_VALUE, remaining_mortgage=REMAINING_MORTGAGE
        )
        starting_balance = calc.remaining_balance

        stats = calc.calculate_year()
        assert stats["remaining_balance"] < starting_balance
        assert stats["principal_paid"] > 0
        assert stats["interest_paid"] > 0

    def test_balance_zero_at_end_of_term(self):
        calc = HelocCalculator(_heloc(loan_length_years=5))
        calc.check_and_activate(
            year=10, current_home_value=HOME_VALUE, remaining_mortgage=REMAINING_MORTGAGE
        )
        for _ in range(5):
            calc.calculate_year()
        assert calc.remaining_balance == pytest.approx(0.0, abs=1.0)

    def test_principal_plus_interest_equals_yearly_payment(self):
        calc = HelocCalculator(_heloc())
        calc.check_and_activate(
            year=10, current_home_value=HOME_VALUE, remaining_mortgage=REMAINING_MORTGAGE
        )
        stats = calc.calculate_year()
        assert stats["principal_paid"] + stats["interest_paid"] == pytest.approx(
            stats["yearly_payment"]
        )
