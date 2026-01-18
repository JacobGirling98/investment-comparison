import pytest
from datetime import date
from src.adapters.interactive_investor_reader import InteractiveInvestorReader
from src.ports.pdf_extractor import PDFExtractor
from typing import List

class FakePDFExtractor(PDFExtractor):
    def __init__(self, text: str):
        self.text = text

    def extract_tables(self, file_path: str) -> List[List[List[str]]]:
        return []

    def extract_text(self, file_path: str) -> str:
        return self.text

def test_ii_reader_parsing(tmp_path):
    # Setup fake directory
    d = tmp_path / "ii"
    d.mkdir()
    # Create a dummy file with a date in the filename
    (d / "Statement 2025-09-30.pdf").write_text("dummy")
    
    # Simulate text content based on what we've seen
    # Includes Total Portfolio Value line with multiple amounts (last one is the total)
    # Includes a subscription transaction
    text = """
    Interactive Investor Statement
    
    Total Portfolio Value £ 16,001.66 £ 1,830.18 £ 17,831.84
    
    Activities - ISA
    23 Nov 2024 SUBSCRIPTION £ 1,000.00
    12 Dec 2024 Monthly Subscription £ 1,000.00
    """
    
    fake_extractor = FakePDFExtractor(text)
    reader = InteractiveInvestorReader(fake_extractor)
    
    portfolio = reader.read_all(str(d))
    
    assert portfolio.name == "Interactive Investor"
    # Should pick the last value on the line
    assert portfolio.current_value == 17831.84
    # Should parse date from filename
    assert portfolio.current_date == date(2025, 9, 30)
    
    # Check transactions
    assert len(portfolio.transactions) == 2
    
    # SUBSCRIPTION should be negative
    tx1 = next(t for t in portfolio.transactions if t.date == date(2024, 11, 23))
    assert tx1.amount == -1000.0
    assert "SUBSCRIPTION" in tx1.description
    
    tx2 = next(t for t in portfolio.transactions if t.date == date(2024, 12, 12))
    assert tx2.amount == -1000.0
    assert "Monthly Subscription" in tx2.description

def test_ii_reader_parsing_with_fees(tmp_path):
    # Setup fake directory
    d = tmp_path / "ii_fees"
    d.mkdir()
    (d / "Statement 2025-06-30.pdf").write_text("dummy")
    
    text = """
    Interactive Investor Statement
    Total Portfolio Value £ 13,273.19
    
    Activities - ISA
    12 Jun 2025 Monthly Subscription £ 1,000.00
    
    Regular Fees
    Due Date Fee Type Fee Amount Invoiced Account Status
    10 Jun 2025 Total Monthly Fee £ 4.99 3657992 PAID
    Net Amount VAT Total Amount
    Monthly Plan Fee £ 4.99 £ 0.00 £ 4.99
    Due Date Fee Type Fee Amount Invoiced Account Status
    12 May 2025 Total Monthly Fee £ 4.99 3657992 PAID
    """
    
    fake_extractor = FakePDFExtractor(text)
    reader = InteractiveInvestorReader(fake_extractor)
    
    portfolio = reader.read_all(str(d))
    
    # Check for fee transactions
    # Fees should be treated as negative cashflow (similar to deposits/subscriptions in logic, 
    # but technically it's a cost. If it's paid externally, it's a cost you pay.
    # If it's paid internally, it's a withdrawal from value.
    # The domain model XIRR calculation expects:
    # - Negative for deposits (money into the system)
    # - Positive for withdrawals (money out of the system)
    # Wait.
    # If I pay £4.99 from my bank account to cover the fee:
    # That is a DEPOSIT of £4.99 that is immediately consumed.
    # So effectively it is money I "put in" that disappeared.
    # So it should be NEGATIVE (investment).
    
    # Wait, let's trace the logic.
    # Profit = Final Value - Net Invested
    # Net Invested = Total In - Total Out
    # If I pay £4.99 fee externally:
    # My "Total In" increases by £4.99.
    # My "Final Value" does NOT increase (it was consumed by fee).
    # So Profit = V - (In + 4.99) = (V - In) - 4.99.
    # So Profit decreases. This is correct.
    
    # So External Fees should be treated as DEPOSITS (Negative amounts in Transaction).
    
    fee_tx = next(t for t in portfolio.transactions if t.date == date(2025, 6, 10))
    assert fee_tx.amount == -4.99
    assert "Total Monthly Fee" in fee_tx.description
    
    fee_tx2 = next(t for t in portfolio.transactions if t.date == date(2025, 5, 12))
    assert fee_tx2.amount == -4.99
