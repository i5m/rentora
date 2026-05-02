from calculators.buy_calculator import BuyCalculator
from calculators.heloc_calculator import HelocCalculator
from calculators.investment_calculator import InvestmentCalculator
from calculators.rent_calculator import RentCalculator
from models import (
    HelocInput,
    HouseInput,
    InflationInput,
    InvestmentInput,
    LocationInput,
    RentInput,
)


def run_simulation(
    location: LocationInput,
    rent: RentInput,
    house: HouseInput,
    inflation: InflationInput,
    investments: InvestmentInput,
    heloc: HelocInput,
    years_to_simulate: int = 30,
) -> dict:

    rent_calc = RentCalculator(rent, inflation.annual_increase_percentage / 100.0)
    buy_calc = BuyCalculator(house, inflation.annual_increase_percentage / 100.0)
    heloc_calc = HelocCalculator(heloc)

    # Renter starts with the buyer's initial out of pocket costs (down payment + closing costs)
    renter_initial_capital = buy_calc.get_initial_out_of_pocket()
    renter_investments = InvestmentCalculator(investments, renter_initial_capital)

    # Buyer starts with 0 investments
    buyer_investments = InvestmentCalculator(investments, 0.0)

    yearly_results = []
    break_even_year = None

    for year in range(years_to_simulate):
        # 1. Rent calculations
        rent_stats = rent_calc.calculate_year(year)

        # 2. Buy calculations
        buy_stats = buy_calc.calculate_year(year)

        # 3. HELOC check & activation for Buyer (HELOC borrow happens at start
        # of year, so it gets a full year of returns).
        borrowed_heloc = heloc_calc.check_and_activate(
            year, buy_stats["home_value"], buy_stats["remaining_loan"]
        )
        if borrowed_heloc > 0:
            buyer_investments.add_capital(borrowed_heloc)

        heloc_stats = heloc_calc.calculate_year()

        # Total cost for buyer this year includes HELOC payment
        total_buy_cash_outflow = buy_stats["total_buy_cost"] + heloc_stats["yearly_payment"]
        total_rent_cash_outflow = rent_stats["total_rent_cost"]

        # 4. Compound existing investments (end-of-year contribution model:
        # capital from this year's cash-flow difference is added below and
        # only starts earning returns next year).
        renter_investments.compound_year()
        buyer_investments.compound_year()

        # 5. Add this year's cash-flow surplus as new principal.
        # Renter invests the difference if renting is cheaper than buying.
        difference = total_buy_cash_outflow - total_rent_cash_outflow
        if difference > 0:
            renter_investments.add_capital(difference)
        elif difference < 0:
            buyer_investments.add_capital(abs(difference))

        renter_inv_stats = renter_investments.get_stats()
        buyer_inv_stats = buyer_investments.get_stats()

        # 6. Net worth calculation
        renter_net_worth = renter_inv_stats["investment_total"]
        buyer_net_worth = (
            buy_stats["home_value"]
            - buy_stats["remaining_loan"]
            - heloc_stats["remaining_balance"]
            + buyer_inv_stats["investment_total"]
        )

        if break_even_year is None and buyer_net_worth > renter_net_worth:
            break_even_year = year

        yearly_results.append(
            {
                "year": year,
                # Renter details
                "rent_cost": total_rent_cash_outflow,
                "renter_investment_principal": renter_inv_stats["investment_principal"],
                "renter_investment_total": renter_inv_stats["investment_total"],
                "renter_net_worth": renter_net_worth,
                # Buyer details
                "buy_cost": total_buy_cash_outflow,
                "home_value": buy_stats["home_value"],
                "mortgage_balance": buy_stats["remaining_loan"],
                "heloc_balance": heloc_stats["remaining_balance"],
                "buyer_investment_principal": buyer_inv_stats["investment_principal"],
                "buyer_investment_total": buyer_inv_stats["investment_total"],
                "buyer_net_worth": buyer_net_worth,
                # Comparison
                "networth_difference_absolute": buyer_net_worth - renter_net_worth,
                # Percentage is only meaningful with a positive baseline; otherwise
                # report 0.0 to keep the field finite/useful for downstream charts.
                "networth_difference_percentage": (
                    (buyer_net_worth - renter_net_worth) / renter_net_worth * 100
                    if renter_net_worth > 0
                    else 0.0
                ),
            }
        )

    final = yearly_results[-1]
    best_option = "Buy" if final["buyer_net_worth"] > final["renter_net_worth"] else "Rent"

    return {
        "location": location.model_dump(),
        "yearly_breakdown": yearly_results,
        "break_even_year": break_even_year,
        "best_option_at_end": best_option,
    }
