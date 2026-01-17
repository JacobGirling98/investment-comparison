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
