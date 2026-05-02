from models import HouseInput


class BuyCalculator:
    def __init__(self, house_input: HouseInput, inflation_rate: float):
        self.total_cost = house_input.total_cost
        self.down_payment = self.total_cost * (house_input.down_payment_percentage / 100.0)
        self.closing_cost = house_input.closing_cost
        self.loan_amount = self.total_cost - self.down_payment

        self.interest_rate = house_input.mortgage_interest_rate / 100.0
        self.mortgage_years = house_input.mortgage_years

        # Monthly mortgage payment formula: P * (r(1+r)^n) / ((1+r)^n - 1)
        if self.interest_rate > 0:
            r = self.interest_rate / 12
            n = self.mortgage_years * 12
            self.monthly_mortgage = self.loan_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        else:
            self.monthly_mortgage = self.loan_amount / (self.mortgage_years * 12)

        self.current_home_value = self.total_cost
        self.remaining_loan = self.loan_amount
        self.monthly_utilities = house_input.monthly_utilities
        self.appreciation = house_input.yoy_appreciation_percentage / 100.0
        self.annual_insurance = house_input.annual_insurance
        self.property_tax_rate = house_input.property_tax_percentage / 100.0
        self.pmi_rate = house_input.pmi / 100.0  # assume it's annual % of original loan
        self.inflation_rate = inflation_rate
        self.assessed_home_value = self.total_cost

    def get_initial_out_of_pocket(self) -> float:
        return self.down_payment + self.closing_cost

    def calculate_year(self, year: int) -> dict:
        """Calculates total buy cost for the given year (0-indexed)."""
        is_mortgage_active = year < self.mortgage_years

        yearly_mortgage_payment = self.monthly_mortgage * 12 if is_mortgage_active else 0

        # Calculate interest vs principal for the year
        interest_paid = 0
        principal_paid = 0

        if is_mortgage_active:
            for _ in range(12):
                if self.remaining_loan > 0:
                    monthly_interest = self.remaining_loan * (self.interest_rate / 12)
                    monthly_principal = self.monthly_mortgage - monthly_interest
                    interest_paid += monthly_interest
                    principal_paid += monthly_principal
                    self.remaining_loan -= monthly_principal

        # Prevent negative loan
        if self.remaining_loan < 0:
            self.remaining_loan = 0

        utilities_cost = self.monthly_utilities * 12
        property_tax = self.assessed_home_value * self.property_tax_rate
        insurance_cost = self.annual_insurance

        # Calculate PMI (drops off at 80% LTV of ORIGINAL purchase price usually)
        ltv = self.remaining_loan / self.total_cost
        pmi_cost = 0
        if ltv > 0.80 and is_mortgage_active:
            pmi_cost = self.loan_amount * self.pmi_rate

        total_yearly_cost = (
            yearly_mortgage_payment + utilities_cost + property_tax + insurance_cost + pmi_cost
        )

        # Record stats before appreciating for the next year
        year_home_value = self.current_home_value

        # Appreciate home and costs for next year
        self.current_home_value *= 1 + self.appreciation
        self.assessed_home_value *= 1 + self.inflation_rate
        self.monthly_utilities *= 1 + self.inflation_rate  # assume utilities inflate
        self.annual_insurance *= 1 + self.inflation_rate  # assume insurance inflates

        return {
            "year": year,
            "home_value": year_home_value,
            "remaining_loan": self.remaining_loan,
            "yearly_mortgage": yearly_mortgage_payment,
            "principal_paid": principal_paid,
            "interest_paid": interest_paid,
            "utilities_cost": utilities_cost,
            "property_tax": property_tax,
            "insurance_cost": insurance_cost,
            "pmi_cost": pmi_cost,
            "total_buy_cost": total_yearly_cost,
            "ltv": ltv,
        }
