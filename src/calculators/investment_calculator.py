from models import InvestmentInput


class InvestmentCalculator:
    def __init__(self, investment_input: InvestmentInput, initial_principal: float):
        self.annual_increase = investment_input.annual_increase_percentage / 100.0
        self.total_value = initial_principal
        self.total_principal = initial_principal

    def add_capital(self, amount: float):
        """Adds capital to the investment pool."""
        if amount > 0:
            self.total_principal += amount
            self.total_value += amount

    def compound_year(self):
        """Compounds the investment for one year."""
        self.total_value *= 1 + self.annual_increase

    def get_stats(self) -> dict:
        return {"investment_principal": self.total_principal, "investment_total": self.total_value}
