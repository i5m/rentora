from models import RentInput

class RentCalculator:
    def __init__(self, rent_input: RentInput):
        self.current_monthly_rent = rent_input.monthly_rent
        self.monthly_utilities = rent_input.monthly_utilities
        self.yoy_increase = rent_input.yoy_increase_percentage / 100.0
        self.annual_insurance = rent_input.annual_insurance_amount
    
    def calculate_year(self, year: int) -> dict:
        """Calculates total rent cost for the given year (0-indexed)."""
        # Calculate costs for the current year
        rent_cost = self.current_monthly_rent * 12
        utilities_cost = self.monthly_utilities * 12
        insurance_cost = self.annual_insurance
        
        total_cost = rent_cost + utilities_cost + insurance_cost
        
        # Prepare for next year (increase applies to rent and utilities, let's assume insurance too)
        self.current_monthly_rent *= (1 + self.yoy_increase)
        self.monthly_utilities *= (1 + self.yoy_increase)
        self.annual_insurance *= (1 + self.yoy_increase)
        
        return {
            "year": year,
            "rent_cost": rent_cost,
            "utilities_cost": utilities_cost,
            "insurance_cost": insurance_cost,
            "total_rent_cost": total_cost,
            "monthly_rent": self.current_monthly_rent / (1 + self.yoy_increase)
        }
