import PyPDF2
import pandas as pd
import io
import csv
from typing import Optional

class FileParser:
    @staticmethod
    async def parse_pdf(file_content: bytes) -> str:
        """Извлекает текст из PDF"""
        text = ""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    @staticmethod
    async def parse_csv(file_content: bytes) -> str:
        """Извлекает текст из CSV"""
        content = file_content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = []
        for row in csv_reader:
            rows.append(" | ".join(row))
        return "\n".join(rows)
    
    @staticmethod
    async def parse_excel(file_content: bytes) -> str:
        """Извлекает текст из Excel"""
        df = pd.read_excel(io.BytesIO(file_content))
        return df.to_string()
    
    @staticmethod
    async def parse_txt(file_content: bytes) -> str:
        """Извлекает текст из TXT"""
        return file_content.decode('utf-8')
    
    async def parse_file(self, file_content: bytes, filename: str) -> Optional[str]:
        """Определяет тип файла и парсит его"""
        if filename.endswith('.pdf'):
            return await self.parse_pdf(file_content)
        elif filename.endswith('.csv'):
            return await self.parse_csv(file_content)
        elif filename.endswith(('.xlsx', '.xls')):
            return await self.parse_excel(file_content)
        elif filename.endswith('.txt'):
            return await self.parse_txt(file_content)
        else:
            return None