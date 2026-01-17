import os
import re
from datetime import datetime, date
from typing import List, Set
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
        
        for file in files:
            path = os.path.join(directory_path, file)
            text = self.extractor.extract_text(path)
            
            # Date Fallback from filename: YY_qX.pdf
            file_date = latest_date
            date_match = re.search(r"(\d{2})_q(\d)", file)
            if date_match:
                yy, q = date_match.groups()
                year = 2000 + int(yy)
                month_map = {"1": (3, 31), "2": (6, 30), "3": (9, 30), "4": (12, 31)}
                m, d = month_map[q]
                file_date = date(year, m, d)

            # Extract Value
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if "Total account value" in line or "Total investments value" in line:
                    chunk = " ".join(lines[i:i+5])
                    val_match = re.search(r"£?\s*([\d,]+\.\d{2})", chunk)
                    if val_match:
                        val = float(val_match.group(1).replace(",", ""))
                        if file_date >= latest_date:
                            latest_date = file_date
                            latest_value = val

            # Transactions
            tx_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(.*?)\s+£\s*([\d,]+(?:\.\d{2})?)")
            for match in tx_pattern.finditer(text):
                dt_str, desc, amount_str = match.groups()
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
                    amount = float(amount_str.replace(",", ""))
                    if any(x in desc.lower() for x in ["bank input", "subscription", "withdrawal"]):
                        final_amt = -amount if "input" in desc.lower() or "subscription" in desc.lower() else amount
                        tx_key = (dt, round(final_amt, 2))
                        if tx_key not in seen_txs:
                            all_transactions.append(Transaction(dt, final_amt, desc))
                            seen_txs.add(tx_key)
                except ValueError:
                    continue

        return Portfolio("Moneyfarm", all_transactions, latest_value, latest_date)
