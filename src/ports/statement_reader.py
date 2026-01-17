from abc import ABC, abstractmethod
from typing import List
from src.domain.model import Portfolio

class StatementReader(ABC):
    @abstractmethod
    def read_all(self, directory_path: str) -> Portfolio:
        pass
