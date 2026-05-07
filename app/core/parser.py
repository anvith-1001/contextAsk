from pathlib import Path
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document


class Parser:

    def parse(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()

        if ext == ".pdf":
            return self._parse_pdf(file_path)

        elif ext == ".docx":
            return self._parse_docx(file_path)

        elif ext in [".xlsx", ".xls"]:
            return self._parse_excel(file_path)

        elif ext == ".txt":
            return self._parse_txt(file_path)

        raise ValueError("Unsupported file format")

    def _parse_pdf(self, file_path):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _parse_docx(self, file_path):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    def _parse_excel(self, file_path):
        df = pd.read_excel(file_path)
        return df.to_string()

    def _parse_txt(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()