import os
import re
from datetime import datetime, date
from typing import List, Set, Optional, Tuple
from src.domain.model import Transaction, Portfolio
from src.ports.statement_reader import StatementReader
from src.ports.pdf_extractor import PDFExtractor

class InteractiveInvestorReader(StatementReader):
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
            
            statement_date = self._get_date_from_filename(filename, fallback_date=latest_date)
            account_value = self._extract_portfolio_value(text_content)
            
            if account_value is not None:
                if statement_date >= latest_date:
                    latest_date = statement_date
                    latest_value = account_value

            new_transactions = self._extract_transactions(text_content)
            # Add fees as negative transactions
            fee_transactions = self._extract_regular_fees(text_content)
            new_transactions.extend(fee_transactions)
            
            for tx in new_transactions:
                # Deduplicate based on date and amount (rounded to 2 decimal places)
                tx_key = (tx.date, round(tx.amount, 2))
                if tx_key not in seen_txs:
                    all_transactions.append(tx)
                    seen_txs.add(tx_key)

        return Portfolio("Interactive Investor", all_transactions, latest_value, latest_date)

    def _extract_regular_fees(self, text: str) -> List[Transaction]:
        """
        Extracts 'Regular Fees' from the statement.
        Example: '10 Jun 2025 Total Monthly Fee £ 4.99 ...'
        These are typically paid externally (e.g. via direct debit) and thus should be treated
        as negative cash flows (investments/costs paid into the account).
        """
        fees = []
        # Regex: Date + "Total Monthly Fee" + Amount
        # 10 Jun 2025 Total Monthly Fee £ 4.99
        pattern = re.compile(r"(\d{1,2} [A-Za-z]{3} \d{4})\s+Total Monthly Fee\s+£\s*([\d,]+\.\d{2})")
        
        for match in pattern.finditer(text):
            date_str, amount_str = match.groups()
            try:
                tx_date = datetime.strptime(date_str, "%d %b %Y").date()
                amount = float(amount_str.replace(",", ""))
                
                # Treat fee as negative (money spent/invested)
                fees.append(Transaction(tx_date, -amount, "Total Monthly Fee"))
            except ValueError:
                pass
                
        return fees

    def _get_date_from_filename(self, filename: str, fallback_date: date) -> date:
        """Parses the date from the filename, e.g., 'Statement 2025-09-30.pdf'."""
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        match = re.search(date_pattern, filename)
        if match:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        return fallback_date

    def _extract_portfolio_value(self, text: str) -> Optional[float]:
        """
        Extracts the total account value. 
        Prioritizes the 'Total Portfolio Value' line which typically contains 
        Securities, Cash, and the Total Account Value as the last number.
        Fallbacks to 'Total Account Value' if the first pattern isn't found.
        """
        # Pattern 1: Find the last monetary value on the line starting with "Total Portfolio Value"
        # Example: "Total Portfolio Value £ 16,001.66 £ 1,830.18 £ 17,831.84"
        summary_line_pattern = r"Total Portfolio Value.*£\s*([\d,]+\.\d{2})\s*$"
        match = re.search(summary_line_pattern, text, re.MULTILINE)
        
        if match:
            return float(match.group(1).replace(",", ""))
        
        # Pattern 2: Explicit "Total Account Value" label
        fallback_pattern = r"Total Account Value\s*£?\s*([\d,]+\.\d{2})"
        match = re.search(fallback_pattern, text, re.IGNORECASE)
        
        if match:
            return float(match.group(1).replace(",", ""))
            
        return None

    def _extract_transactions(self, text: str) -> List[Transaction]:
        """Parses all lines in the text to find valid transactions."""
        transactions = []
        lines = text.split("\n")
        for line in lines:
            tx = self._parse_transaction_line(line)
            if tx:
                transactions.append(tx)
        return transactions

    def _parse_transaction_line(self, line: str) -> Optional[Transaction]:
        """
        Attempts to parse a single line of text into a Transaction.
        Expected format: 'DD Mon YYYY Description Amount'
        Example: '23 Nov 2024 SUBSCRIPTION £ 1,000.00'
        """
        # Regex breakdown:
        # (\d{1,2} [A-Za-z]{3} \d{4}) -> Date (e.g., 23 Nov 2024)
        # \s+(.*?)\s+                 -> Description (non-greedy capture)
        # £?\s*([\d,]+\.\d{2})      -> Amount (e.g., £ 1,000.00)
        tx_pattern = re.compile(r"(\d{1,2} [A-Za-z]{3} \d{4})\s+(.*?)\s+£?\s*([\d,]+\.\d{2})")
        
        match = tx_pattern.search(line)
        if not match:
            return None

        date_str, description, amount_str = match.groups()
        
        try:
            tx_date = datetime.strptime(date_str, "%d %b %Y").date()
            amount = float(amount_str.replace(",", ""))
            
            # Check if this is an external cash flow we care about
            is_subscription = "SUBSCRIPTION" in description.upper()
            is_withdrawal = "WITHDRAWAL" in description.upper()
            
            if is_subscription or is_withdrawal:
                # Subscriptions are money leaving the pocket (negative for XIRR)
                # Withdrawals are money entering the pocket (positive for XIRR)
                final_amount = -amount if is_subscription else amount
                return Transaction(tx_date, final_amount, description.strip())
                
        except ValueError:
            pass
            
        return None