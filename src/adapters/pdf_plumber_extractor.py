import pdfplumber
from typing import List
from src.ports.pdf_extractor import PDFExtractor

class PdfPlumberExtractor(PDFExtractor):
    def extract_tables(self, file_path: str) -> List[List[List[str]]]:
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_tables()
                if extracted:
                    tables.extend(extracted)
        return tables

    def extract_text(self, file_path: str) -> str:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text
