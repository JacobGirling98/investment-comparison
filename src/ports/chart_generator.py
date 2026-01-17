from abc import ABC, abstractmethod
from typing import List, Dict

class ChartGenerator(ABC):
    @abstractmethod
    def generate_performance_chart(self, data: Dict[str, float], output_path: str):
        pass
