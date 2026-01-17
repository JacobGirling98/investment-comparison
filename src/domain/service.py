from datetime import date
from typing import List
from src.domain.model import Transaction, Portfolio
from scipy.optimize import newton

class PerformanceService:
    def calculate_xirr(self, portfolio: Portfolio) -> float:
        cash_flows = []
        for tx in portfolio.transactions:
            cash_flows.append((tx.date, tx.amount))
        
        cash_flows.append((portfolio.current_date, portfolio.current_value))
        
        if not cash_flows or len(cash_flows) < 2:
            return 0.0

        print(f"DEBUG: XIRR Cashflows for {portfolio.name}: {cash_flows}")

        def xnpv(rate, flows):
            d0 = flows[0][0]
            return sum([f / (1 + rate)**((d - d0).days / 365.25) for d, f in flows])

        try:
            # We want to find the rate where XNPV = 0
            return newton(lambda r: xnpv(r, cash_flows), 0.1)
        except (RuntimeError, OverflowError):
            return 0.0

    def calculate_total_return(self, portfolio: Portfolio) -> float:
        """
        Calculates the Simple Return (Total Profit / Net Invested).
        This ignores the timing of deposits.
        Returns decimal (e.g. 0.10 for 10%).
        """
        total_invested = 0.0
        total_withdrawn = 0.0
        
        for tx in portfolio.transactions:
            if tx.amount < 0:
                total_invested += abs(tx.amount)
            else:
                total_withdrawn += tx.amount
        
        net_invested = total_invested - total_withdrawn
        
        if net_invested == 0:
            return 0.0
            
        profit = portfolio.current_value - net_invested
        return profit / net_invested
