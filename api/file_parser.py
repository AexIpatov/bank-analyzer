import PyPDF2
import pandas as pd
import io
import csv
import tempfile
import os
from typing import Optional

class FileParser:
    @staticmethod
    async def parse_pdf(file_path: str) -> str:
        """Извлекает текст из PDF файла"""
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    @staticmethod
    async def parse_csv(file_path: str) -> str:
        """Извлекает текст из CSV файла"""
        text = ""
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                text += " | ".join(row) + "\n"
        return text
    
    @staticmethod
    async def parse_excel(file_path: str) -> str:
        """Извлекает текст из Excel файла"""
        df = pd.read_excel(file_path)
        return df.to_string()
    
    @staticmethod
    async def parse_txt(file_path: str) -> str:
        """Извлекает текст из TXT файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def parse_file(self, file_path: str, filename: str) -> Optional[str]:
        """Определяет тип файла и парсит его по пути"""
        if filename.endswith('.pdf'):
            return await self.parse_pdf(file_path)
        elif filename.endswith('.csv'):
            return await self.parse_csv(file_path)
        elif filename.endswith(('.xlsx', '.xls')):
            return await self.parse_excel(file_path)
        elif filename.endswith('.txt'):
            return await self.parse_txt(file_path)
        else:
            return None
    
    async def parse_file_content(self, content_bytes: bytes, filename: str) -> Optional[str]:
        """Парсит файл из байтового содержимого (для загрузки через API)"""
        # Сохраняем во временный файл
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content_bytes)
            tmp_path = tmp.name
        
        try:
            # Парсим файл
            text = await self.parse_file(tmp_path, filename)
            return text
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)