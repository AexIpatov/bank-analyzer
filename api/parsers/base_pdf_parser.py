import PyPDF2
import re
from datetime import datetime
import io

class BasePDFParser:
    """
    Базовый класс для всех PDF парсеров
    """
    
    def __init__(self):
        self.bank_name = "Unknown"
        self.encoding = 'utf-8'
        self.page_delimiter = '===== Page '
    
    def extract_text_from_pdf(self, file_path):
        """
        Извлекает текст из PDF файла
        """
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    # Добавляем разделитель страниц
                    text += f"\n{self.page_delimiter}{page_num + 1}\n\n"
                    text += page_text
        except Exception as e:
            print(f"Ошибка чтения PDF: {e}")
            return None
        
        return text
    
    def extract_text_from_bytes(self, content_bytes):
        """
        Извлекает текст из PDF в виде байтов
        """
        text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
        except Exception as e:
            print(f"Ошибка чтения PDF из байтов: {e}")
            return None
        
        return text
    
    def parse(self, file_path, filename):
        """
        Основной метод парсинга (должен быть переопределен)
        """
        raise NotImplementedError("Метод parse должен быть реализован в дочернем классе")
    
    def _parse_date(self, date_str, formats=None):
        """
        Парсит дату в разных форматах
        """
        if not date_str:
            return ''
        
        date_str = str(date_str).strip()
        
        if formats is None:
            formats = [
                '%Y-%m-%d',
                '%d.%m.%Y',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%d %b %Y',
                '%d %B %Y',
                '%Y/%m/%d'
            ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return date_str
    
    def _clean_amount(self, amount_str):
        """
        Очищает строку суммы от лишних символов
        """
        if not amount_str:
            return 0
        
        # Убираем пробелы и заменяем запятую на точку
        cleaned = str(amount_str).replace(' ', '').replace(',', '.')
        
        # Оставляем только цифры, точку и минус
        cleaned = re.sub(r'[^\d.-]', '', cleaned)
        
        try:
            return float(cleaned)
        except:
            return 0
    
    def _extract_numbers(self, text):
        """
        Извлекает все числа из текста
        """
        return re.findall(r'-?\d+[.,]?\d*', text)
    
    def _find_by_pattern(self, text, pattern, group=0):
        """
        Ищет текст по регулярному выражению
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(group).strip()
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """
        Определяет направление (может быть переопределен)
        """
        return None, None
    
    def enrich_transaction(self, transaction):
        """
        Обогащает транзакцию (может быть переопределен)
        """
        return transaction
    
    def _safe_get(self, data, key, default=''):
        """
        Безопасно получает значение из словаря
        """
        return data.get(key, default) if data else default