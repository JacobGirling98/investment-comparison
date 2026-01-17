from abc import ABC, abstractmethod
from typing import List, Dict, Any

class PDFExtractor(ABC):
    @abstractmethod
    def extract_tables(self, file_path: str) -> List[List[List[str]]]:
        pass

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        pass
