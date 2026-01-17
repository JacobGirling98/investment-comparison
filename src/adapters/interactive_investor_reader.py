import os
import re
from datetime import datetime, date
from typing import List, Set
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
        
        for file in files:
            path = os.path.join(directory_path, file)
            text = self.extractor.extract_text(path)
            
            # Date Fallback from filename: Statement YYYY-MM-DD.pdf
            file_date = latest_date
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", file)
            if date_match:
                file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()

            # Extract Value
            # We want "Total Account Value" which includes Cash + Securities.
            # In the summary table: "Total Account Value ... £17,831.84"
            # It often appears at the end of lines like "Total Portfolio Value ... £17,831.84"
            
            val_match = None
            # Regex to find the last monetary value on the line starting with "Total Portfolio Value"
            # As seen in inspection: "Total Portfolio Value £ 16,001.66 £ 1,830.18 £ 17,831.84"
            # The last number is the Total Account Value.
            summary_match = re.search(r"Total Portfolio Value.*£\s*([\d,]+\.\d{2})\s*$", text, re.MULTILINE)
            if summary_match:
                val_match = summary_match
            
            # Fallback: Look for "Total Account Value" explicitly
            if not val_match:
                val_match = re.search(r"Total Account Value\s*£?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
            
            if val_match:
                val = float(val_match.group(1).replace(",", ""))
                if file_date >= latest_date:
                    latest_date = file_date
                    latest_value = val

            # Transactions
            tx_pattern = re.compile(r"(\d{1,2} [A-Za-z]{3} \d{4})\s+(.*?)\s+£?\s*([\d,]+\.\d{2})")
            for line in text.split("\n"):
                match = tx_pattern.search(line)
                if match:
                    dt_str, desc, amount_str = match.groups()
                    try:
                        dt = datetime.strptime(dt_str, "%d %b %Y").date()
                        amount = float(amount_str.replace(",", ""))
                        if any(x in desc.upper() for x in ["SUBSCRIPTION", "WITHDRAWAL"]):
                            final_amt = -amount if "SUBSCRIPTION" in desc.upper() else amount
                            tx_key = (dt, round(final_amt, 2))
                            if tx_key not in seen_txs:
                                all_transactions.append(Transaction(dt, final_amt, desc))
                                seen_txs.add(tx_key)
                    except ValueError:
                        continue

        return Portfolio("Interactive Investor", all_transactions, latest_value, latest_date)
