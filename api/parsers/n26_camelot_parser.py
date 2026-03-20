import camelot
import pandas as pd
import re
from .base_pdf_parser import BasePDFParser
from .finclassifier import FinClassifier

class N26CamelotParser(BasePDFParser):
    """
    Парсер для PDF выписок N26 с использованием Camelot
    """
    
    def __init__(self):
        super().__init__()
        self.bank_name = "N26"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит PDF выписку N26 используя Camelot
        """
        transactions = []
        
        try:
            # Извлекаем таблицы из PDF
            tables = camelot.read_pdf(file_path, pages='all', flavor='stream')
            
            print(f"Найдено таблиц: {len(tables)}")
            
            for table_num, table in enumerate(tables):
                df = table.df
                print(f"\nТаблица {table_num + 1}: {df.shape}")
                
                # Парсим каждую строку таблицы
                for _, row in df.iterrows():
                    transaction = self._parse_row(row)
                    if transaction:
                        transactions.append(transaction)
            
        except Exception as e:
            print(f"Ошибка Camelot: {e}")
            # Если Camelot не сработал, пробуем другой подход
            return self._fallback_parse(file_path)
        
        return transactions
    
    def _parse_row(self, row):
        """
        Парсит строку таблицы
        """
        try:
            # Объединяем все ячейки в строку
            line = ' '.join([str(cell) for cell in row if cell and str(cell).strip()])
            
            # Ищем дату в формате ДД.ММ.ГГГГ
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', line)
            if not date_match:
                return None
            
            date_str = date_match.group(1)
            date = f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"
            
            # Ищем сумму с €
            amount_match = re.search(r'([+-]?\s*\d+[.,]?\d*[.,]?\d*)\s*[€]', line)
            if not amount_match:
                return None
            
            amount_str = amount_match.group(1).replace('.', '').replace(',', '.').replace('+', '').strip()
            amount = float(amount_str)
            
            # Определяем знак
            if '-' in amount_match.group(0):
                amount = -amount
            
            # Описание
            description = line.replace(date_match.group(0), '').replace(amount_match.group(0), '').strip()
            description = re.sub(r'\s+', ' ', description)
            
            # Определяем статью
            article_code = self._extract_article_code(description)
            
            return {
                'date': date,
                'amount': amount,
                'currency': 'EUR',
                'description': description,
                'bank': self.bank_name,
                'article_code': article_code,
                'type': 'expense' if amount < 0 else 'income'
            }
            
        except Exception as e:
            return None
    
    def _fallback_parse(self, file_path):
        """
        Запасной метод парсинга
        """
        transactions = []
        
        try:
            import pdfplumber
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            if re.search(r'\d{2}\.\d{2}\.\d{4}', line) and '€' in line:
                                # Простой парсинг строки
                                parts = line.split()
                                if len(parts) >= 3:
                                    date_str = parts[0]
                                    if re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
                                        date = f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"
                                        
                                        # Ищем сумму
                                        for part in parts:
                                            if '€' in part:
                                                amount_str = part.replace('€', '').replace('.', '').replace(',', '.').replace('+', '')
                                                try:
                                                    amount = float(amount_str)
                                                    if '-' in part:
                                                        amount = -amount
                                                    
                                                    description = ' '.join(parts[1:parts.index(part)])
                                                    
                                                    transactions.append({
                                                        'date': date,
                                                        'amount': amount,
                                                        'currency': 'EUR',
                                                        'description': description,
                                                        'bank': self.bank_name,
                                                        'article_code': self._extract_article_code(description)
                                                    })
                                                except:
                                                    pass
        except Exception as e:
            print(f"Ошибка fallback: {e}")
        
        return transactions
    
    def _extract_article_code(self, description):
        """Извлекает код статьи из описания"""
        if not description:
            return None
        
        desc_lower = description.lower()
        
        keywords = {
            '1.2.2 Командировочные расходы': ['air india', 'transport', 'vuelo', 'fly', 'flixbus', 'hotel', 'booking', 'airbnb'],
            '1.2.17 РКО': ['metal membership', 'cuota', 'fee', 'comisión', 'membership'],
            '1.2.9.3 IT сервисы': ['google', 'openai', 'chatgpt', 'adobe', 'lovable'],
            '1.2.1.1 Бытовое оборудование': ['supermercado', 'supermarket', 'mercado', 'productos'],
            'Перевод между счетами': ['instant savings', 'ahorro', 'transfer', 'ingresos']
        }
        
        for article, words in keywords.items():
            for word in words:
                if word in desc_lower:
                    return article
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """Определяет направление"""
        return 'UK Estate', None
    
    def enrich_transaction(self, transaction):
        """Обогащает транзакцию"""
        return transaction