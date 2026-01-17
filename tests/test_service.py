from datetime import date
from src.domain.model import Transaction, Portfolio
from src.domain.service import PerformanceService

def test_calculate_xirr_simple_growth():
    # Scenario: Deposit 1000, value becomes 1100 after 1 year.
    # Expected XIRR: 10% (0.10)
    service = PerformanceService()
    portfolio = Portfolio(
        name="Test",
        transactions=[
            Transaction(date=date(2023, 1, 1), amount=-1000.0, description="Initial")
        ],
        current_value=1100.0,
        current_date=date(2024, 1, 1)
    )
    
    result = service.calculate_xirr(portfolio)
    assert round(result, 2) == 0.10

def test_calculate_xirr_with_mid_year_deposit():
    # Scenario: 
    # Jan 1: Deposit 1000
    # July 1: Deposit 1000
    # Jan 1 (next year): Value is 2100
    # This should be less than 10% because the second 1000 was only there for half a year.
    service = PerformanceService()
    portfolio = Portfolio(
        name="Test",
        transactions=[
            Transaction(date=date(2023, 1, 1), amount=-1000.0, description="Initial"),
            Transaction(date=date(2023, 7, 1), amount=-1000.0, description="Mid")
        ],
        current_value=2100.0,
        current_date=date(2024, 1, 1)
    )
    
    result = service.calculate_xirr(portfolio)
    # 2100 - 2000 = 100 profit. 
    # Average capital ~ 1500 (rough). 100/1500 ~ 6.6%.
    assert 0.06 < result < 0.08
