from dataclasses import dataclass
from datetime import date
from typing import List, Optional

@dataclass(frozen=True)
class Transaction:
    date: date
    amount: float  # Negative for deposits/subscriptions, Positive for withdrawals
    description: str

@dataclass
class Portfolio:
    name: str
    transactions: List[Transaction]
    current_value: float
    current_date: date
