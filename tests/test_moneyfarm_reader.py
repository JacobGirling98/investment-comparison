from datetime import date
from typing import List
from src.domain.model import Transaction
from src.ports.pdf_extractor import PDFExtractor
from src.adapters.moneyfarm_reader import MoneyfarmReader
import os

class FakePDFExtractor(PDFExtractor):
    def __init__(self, text: str, tables: List[List[List[str]]]):
        self.text = text
        self.tables = tables

    def extract_tables(self, file_path: str) -> List[List[List[str]]]:
        return self.tables

    def extract_text(self, file_path: str) -> str:
        return self.text

def test_moneyfarm_reader_parsing(tmp_path):
    # Setup fake directory
    d = tmp_path / "moneyfarm"
    d.mkdir()
    (d / "23_q4.pdf").write_text("dummy")
    
    # Update text to include transactions in the format: YYYY-MM-DD Description £Amount
    text = """
    Total account value At 31 December 2023 £3,077.39
    
    2023-11-03 Bank input £2,000.00
    2023-11-17 Bank input £700.00
    2023-12-21 Bank input £250.00
    """
    tables = [] # Tables are now ignored by the reader for transactions
    
    fake_extractor = FakePDFExtractor(text, tables)
    reader = MoneyfarmReader(fake_extractor)
    
    portfolio = reader.read_all(str(d))
    
    assert portfolio.name == "Moneyfarm"
    assert portfolio.current_value == 3077.39
    assert portfolio.current_date == date(2023, 12, 31)
    assert len(portfolio.transactions) == 3
    # Bank input should be negative (deposit)
    assert portfolio.transactions[0].amount == -2000.0
