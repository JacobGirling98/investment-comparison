import os
import re
from datetime import datetime, date
from typing import List, Set, Optional, Tuple
from src.domain.model import Transaction, Portfolio
from src.ports.statement_reader import StatementReader
from src.ports.pdf_extractor import PDFExtractor

class MoneyfarmReader(StatementReader):
    def __init__(self, extractor: PDFExtractor):
        self.extractor = extractor

    def read_all(self, directory_path: str) -> Portfolio:
        all_transactions: List[Transaction] = []
        latest_value = 0.0
        latest_date = date(1970, 1, 1)
        seen_txs: Set[tuple] = set()

        files = sorted([f for f in os.listdir(directory_path) if f.endswith(".pdf")])
        
        for filename in files:
            file_path = os.path.join(directory_path, filename)
            text_content = self.extractor.extract_text(file_path)
            
            # Identify the statement period end date from the filename
            statement_date = self._get_date_from_filename(filename, fallback_date=latest_date)
            
            # Extract the total value of the account (cash + investments)
            account_value = self._extract_account_value(text_content)
            
            if account_value is not None:
                # Update latest value if this file represents a newer or same date
                if statement_date >= latest_date:
                    latest_date = statement_date
                    latest_value = account_value

            # Extract new transactions found in this file
            new_transactions = self._extract_transactions(text_content)
            for tx in new_transactions:
                # Deduplicate based on date and amount (rounded to 2 decimal places)
                tx_key = (tx.date, round(tx.amount, 2))
                if tx_key not in seen_txs:
                    all_transactions.append(tx)
                    seen_txs.add(tx_key)

        return Portfolio("Moneyfarm", all_transactions, latest_value, latest_date)

    def _get_date_from_filename(self, filename: str, fallback_date: date) -> date:
        """
        Parses the date from the filename.
        Expected format: YY_qX.pdf (e.g. 23_q4.pdf) representing Year 20YY Quarter X.
        """
        match = re.search(r"(\d{2})_q(\d)", filename)
        if match:
            yy, q = match.groups()
            year = 2000 + int(yy)
            # Map Quarter to End Date (Month, Day)
            quarter_end_map = {
                "1": (3, 31),
                "2": (6, 30),
                "3": (9, 30),
                "4": (12, 31)
            }
            if q in quarter_end_map:
                m, d = quarter_end_map[q]
                return date(year, m, d)
        return fallback_date

    def _extract_account_value(self, text: str) -> Optional[float]:
        """
        Scans text for the Total Account Value.
        Looks for 'Total account value' or 'Total investments value' followed by a monetary amount.
        """
        lines = text.split("\n")
        for i, line in enumerate(lines):
            # Moneyfarm has varied wording over the years
            if "Total account value" in line or "Total investments value" in line:
                # Look in this line and the next few lines for the value
                # This handles cases where the value is on a subsequent line
                chunk = " ".join(lines[i:i+5])
                match = re.search(r"£?\s*([\d,]+\.\d{2})", chunk)
                if match:
                    return float(match.group(1).replace(",", ""))
        return None

    def _extract_transactions(self, text: str) -> List[Transaction]:
        """Finds all valid transactions in the text block."""
        transactions = []
        # Regex to find lines like: 2023-11-03 Bank input £2,000.00
        tx_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(.*?)\s+£\s*([\d,]+(?:\.\d{2})?)")
        
        for match in tx_pattern.finditer(text):
            tx = self._parse_transaction_match(match)
            if tx:
                transactions.append(tx)
        return transactions

    def _parse_transaction_match(self, match: re.Match) -> Optional[Transaction]:
        """Converts a regex match object into a Transaction domain object."""
        date_str, description, amount_str = match.groups()
        try:
            tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            amount = float(amount_str.replace(",", ""))
            desc_clean = description.strip()
            
            # We filter for specific external cash flow keywords
            is_deposit = "input" in desc_clean.lower() or "subscription" in desc_clean.lower()
            is_withdrawal = "withdrawal" in desc_clean.lower()
            
            if is_deposit or is_withdrawal:
                # Deposits are negative for XIRR, Withdrawals are positive
                final_amount = -amount if is_deposit else amount
                return Transaction(tx_date, final_amount, desc_clean)
        except ValueError:
            pass
            
        return None