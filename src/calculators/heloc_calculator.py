from models import HelocInput


class HelocCalculator:
    def __init__(self, heloc_input: HelocInput):
        self.interest_rate = heloc_input.interest_rate_percentage / 100.0
        self.loan_length_years = heloc_input.loan_length_years
        self.after_years = heloc_input.after_years
        self.ltv_cap = heloc_input.ltv_cap

        self.heloc_amount = 0.0
        self.remaining_balance = 0.0
        self.monthly_payment = 0.0
        self.is_active = False

    def check_and_activate(
        self, year: int, current_home_value: float, remaining_mortgage: float
    ) -> float:
        """
        Checks if it's the year to activate HELOC.
        Returns the borrowed amount (which can be added to investments).
        """
        if year == self.after_years and not self.is_active:
            max_heloc = (current_home_value * self.ltv_cap) - remaining_mortgage
            if max_heloc > 0:
                self.heloc_amount = max_heloc
                self.remaining_balance = max_heloc
                self.is_active = True

                # Calculate monthly payment
                if self.interest_rate > 0:
                    r = self.interest_rate / 12
                    n = self.loan_length_years * 12
                    self.monthly_payment = (
                        self.heloc_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
                    )
                else:
                    self.monthly_payment = self.heloc_amount / (self.loan_length_years * 12)

                return self.heloc_amount
        return 0.0

    def calculate_year(self) -> dict:
        """Calculates yearly cost and remaining balance of HELOC."""
        if not self.is_active or self.remaining_balance <= 0:
            return {
                "yearly_payment": 0.0,
                "remaining_balance": 0.0,
                "principal_paid": 0.0,
                "interest_paid": 0.0,
            }

        yearly_payment = 0.0
        interest_paid = 0.0
        principal_paid = 0.0

        for _ in range(12):
            if self.remaining_balance > 0:
                monthly_interest = self.remaining_balance * (self.interest_rate / 12)
                monthly_principal = self.monthly_payment - monthly_interest

                # If the remaining balance is less than the principal to pay, adjust it
                if self.remaining_balance < monthly_principal:
                    monthly_principal = self.remaining_balance

                interest_paid += monthly_interest
                principal_paid += monthly_principal
                self.remaining_balance -= monthly_principal
                yearly_payment += monthly_principal + monthly_interest

        if self.remaining_balance < 0:
            self.remaining_balance = 0.0

        return {
            "yearly_payment": yearly_payment,
            "remaining_balance": self.remaining_balance,
            "principal_paid": principal_paid,
            "interest_paid": interest_paid,
        }
