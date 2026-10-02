import io
from typing import Union
import pypdf
import docx

class DocumentParser:
    @staticmethod
    def parse_file(file_bytes: bytes, filename: str) -> str:
        filename_lower = filename.lower()
        if filename_lower.endswith('.pdf'):
            return DocumentParser.parse_pdf(file_bytes)
        elif filename_lower.endswith('.docx') or filename_lower.endswith('.doc'):
            return DocumentParser.parse_docx(file_bytes)
        elif filename_lower.endswith('.txt') or filename_lower.endswith('.md'):
            return DocumentParser.parse_txt(file_bytes)
        else:
            # Fallback to UTF-8 decoding
            return DocumentParser.parse_txt(file_bytes)

    @staticmethod
    def parse_pdf(file_bytes: bytes) -> str:
        text = ""
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            raise ValueError(f"Error parsing PDF file: {str(e)}")
        return text.strip()

    @staticmethod
    def parse_docx(file_bytes: bytes) -> str:
        text = ""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            for p in doc.paragraphs:
                if p.text:
                    text += p.text + "\n"
        except Exception as e:
            raise ValueError(f"Error parsing DOCX file: {str(e)}")
        return text.strip()

    @staticmethod
    def parse_txt(file_bytes: bytes) -> str:
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return file_bytes.decode('latin-1', errors='ignore')
