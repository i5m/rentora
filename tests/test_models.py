"""Tests for input model validation."""

import pytest
from pydantic import ValidationError

from models import HelocInput, HouseInput, InvestmentInput, RentInput


class TestRentInputValidation:
    def test_rejects_negative_rent(self):
        with pytest.raises(ValidationError):
            RentInput(
                monthly_rent=-100.0,
                monthly_utilities=150.0,
                yoy_increase_percentage=3.0,
                annual_insurance_amount=300.0,
            )

    def test_rejects_negative_utilities(self):
        with pytest.raises(ValidationError):
            RentInput(
                monthly_rent=2000.0,
                monthly_utilities=-1.0,
                yoy_increase_percentage=3.0,
                annual_insurance_amount=300.0,
            )

    def test_accepts_zero_rent(self):
        RentInput(
            monthly_rent=0.0,
            monthly_utilities=0.0,
            yoy_increase_percentage=0.0,
            annual_insurance_amount=0.0,
        )


class TestHouseInputValidation:
    def test_rejects_down_payment_over_100(self):
        with pytest.raises(ValidationError):
            HouseInput(
                total_cost=400000.0,
                mortgage_interest_rate=6.5,
                mortgage_years=30,
                monthly_utilities=250.0,
                yoy_appreciation_percentage=3.0,
                closing_cost=8000.0,
                down_payment_percentage=120.0,
                annual_insurance=1200.0,
                property_tax_percentage=1.2,
                pmi=0.5,
            )

    def test_rejects_zero_or_negative_mortgage_years(self):
        with pytest.raises(ValidationError):
            HouseInput(
                total_cost=400000.0,
                mortgage_interest_rate=6.5,
                mortgage_years=0,
                monthly_utilities=250.0,
                yoy_appreciation_percentage=3.0,
                closing_cost=8000.0,
                down_payment_percentage=20.0,
                annual_insurance=1200.0,
                property_tax_percentage=1.2,
                pmi=0.5,
            )

    def test_rejects_negative_total_cost(self):
        with pytest.raises(ValidationError):
            HouseInput(
                total_cost=-1.0,
                mortgage_interest_rate=6.5,
                mortgage_years=30,
                monthly_utilities=250.0,
                yoy_appreciation_percentage=3.0,
                closing_cost=8000.0,
                down_payment_percentage=20.0,
                annual_insurance=1200.0,
                property_tax_percentage=1.2,
                pmi=0.5,
            )


class TestInvestmentInputValidation:
    def test_accepts_negative_returns(self):
        InvestmentInput(annual_increase_percentage=-5.0)


class TestHelocInputValidation:
    def test_uses_loan_length_years_field(self):
        heloc = HelocInput(
            interest_rate_percentage=8.0,
            loan_length_years=15,
            after_years=10,
            ltv_cap=0.80,
        )
        assert heloc.loan_length_years == 15

    def test_default_ltv_cap(self):
        heloc = HelocInput(
            interest_rate_percentage=8.0,
            loan_length_years=15,
            after_years=10,
        )
        assert heloc.ltv_cap == 0.80

    def test_rejects_ltv_cap_over_one(self):
        with pytest.raises(ValidationError):
            HelocInput(
                interest_rate_percentage=8.0,
                loan_length_years=15,
                after_years=10,
                ltv_cap=1.5,
            )
