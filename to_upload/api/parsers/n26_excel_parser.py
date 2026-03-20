import pandas as pd
import re
from .base_parser import BaseParser
from .finclassifier import FinClassifier

class N26ExcelParser(BaseParser):
    """
    Парсер для Excel выписок N26
    """
    
    def __init__(self):
        super().__init__()
        self.bank_name = "N26"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит Excel выписку N26
        """
        transactions = []
        
        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path)
            print(f"Прочитано строк: {len(df)}")
            print(f"Колонки: {df.columns.tolist()}")
            
            for _, row in df.iterrows():
                transaction = self._parse_row(row)
                if transaction:
                    transactions.append(transaction)
                    
        except Exception as e:
            print(f"Ошибка чтения Excel: {e}")
        
        return transactions
    
    def _parse_row(self, row):
        """
        Парсит строку Excel
        """
        try:
            # Определяем дату
            date_val = None
            for col in ['Date', 'Дата', 'Fecha', 'Booking date']:
                if col in row and pd.notna(row[col]):
                    date_val = row[col]
                    break
            
            if date_val is None:
                return None
            
            # Преобразуем дату
            date_str = str(date_val)
            if ' ' in date_str:
                date_str = date_str.split()[0]
            
            # Парсим дату в формате YYYY-MM-DD
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                date = date_str
            else:
                # Пробуем другие форматы
                date = self._parse_date(date_str)
            
            # Определяем сумму
            amount = 0
            currency = 'EUR'
            
            for col in ['Amount', 'Сумма', 'Importe', 'Amount (EUR)']:
                if col in row and pd.notna(row[col]):
                    amount = float(row[col])
                    break
            
            if 'Currency' in row and pd.notna(row['Currency']):
                currency = str(row['Currency'])
            elif 'Валюта' in row and pd.notna(row['Валюта']):
                currency = str(row['Валюта'])
            
            # Определяем описание
            description = ''
            for col in ['Description', 'Описание', 'Concepto', 'Payment details']:
                if col in row and pd.notna(row[col]):
                    description = str(row[col])
                    break
            
            # Определяем тип транзакции
            transaction_type = 'unknown'
            if amount < 0:
                transaction_type = 'expense'
            else:
                transaction_type = 'income'
            
            # Определяем статью
            article_code = self._extract_article_code(description)
            
            return {
                'date': date,
                'amount': amount,
                'currency': currency,
                'description': description,
                'bank': self.bank_name,
                'article_code': article_code,
                'type': transaction_type
            }
            
        except Exception as e:
            print(f"Ошибка парсинга строки: {e}")
            return None
    
    def _parse_date(self, date_str):
        """Парсит дату в разных форматах"""
        try:
            # Формат ДД.ММ.ГГГГ
            if '.' in date_str:
                parts = date_str.split('.')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[1]}-{parts[0]}"
            # Формат ДД/ММ/ГГГГ
            elif '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[1]}-{parts[0]}"
        except:
            pass
        return date_str
    
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