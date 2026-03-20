import pandas as pd
import re
from datetime import datetime
from .finclassifier import FinClassifier

class MashreqParser:
    def __init__(self):
        self.classifier = FinClassifier()
        self.bank_name = 'Mashreq Bank'
        self.currency = 'AED'
    
    def parse(self, file_path, filename):
        """
        Парсит выписку Mashreq Bank
        """
        transactions = []
        
        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path, sheet_name='Account transactions Statement', header=None)
            
            # Ищем строку с заголовками
            header_row = None
            for idx, row in df.iterrows():
                row_str = ' '.join([str(x).lower() for x in row if pd.notna(x)])
                if 'date' in row_str and 'value date' in row_str and 'description' in row_str:
                    header_row = idx
                    break
            
            if header_row is not None:
                # Пропускаем строки до данных
                df = df.iloc[header_row + 1:].reset_index(drop=True)
                
                for _, row in df.iterrows():
                    # Проверяем, есть ли данные в строке
                    if all(pd.isna(x) for x in row):
                        continue
                    
                    t = self._parse_row(row)
                    if t:
                        transactions.append(t)
            
        except Exception as e:
            print(f"Ошибка парсинга Mashreq Bank: {e}")
        
        return transactions
    
    def _parse_row(self, row):
        """Парсит одну строку транзакции"""
        try:
            # Дата (колонка 0)
            date_val = row[0] if len(row) > 0 and pd.notna(row[0]) else None
            if date_val is None:
                return None
            
            date = self._parse_date(str(date_val))
            
            # Value Date (колонка 1)
            value_date = None
            if len(row) > 1 and pd.notna(row[1]):
                value_date = self._parse_date(str(row[1]))
            
            # Reference (колонка 2)
            reference = str(row[2]) if len(row) > 2 and pd.notna(row[2]) else ''
            
            # Описание (колонка 3)
            description = str(row[3]) if len(row) > 3 and pd.notna(row[3]) else ''
            
            # Credit (колонка 5)
            credit = 0
            if len(row) > 5 and pd.notna(row[5]):
                try:
                    credit = float(str(row[5]).replace(',', ''))
                except:
                    pass
            
            # Debit (колонка 6)
            debit = 0
            if len(row) > 6 and pd.notna(row[6]):
                try:
                    debit = float(str(row[6]).replace(',', ''))
                except:
                    pass
            
            # Определяем сумму (доход или расход)
            amount = 0
            if credit > 0:
                amount = credit
            elif debit > 0:
                amount = -debit
            else:
                return None
            
            # Баланс (колонка 7)
            balance = None
            if len(row) > 7 and pd.notna(row[7]):
                try:
                    balance = float(str(row[7]).replace(',', ''))
                except:
                    pass
            
            # Определяем статью
            article_code = self._extract_article_code(description)
            
            # Определяем комментарий (есть ли в описании пометки)
            comment = ''
            if 'нДС' in description or 'НДС' in description:
                comment = 'НДС'
            
            return {
                'date': date,
                'value_date': value_date,
                'amount': amount,
                'currency': self.currency,
                'description': description,
                'reference': reference,
                'bank': self.bank_name,
                'article_code': article_code,
                'balance': balance,
                'comment': comment
            }
            
        except Exception as e:
            print(f"Ошибка парсинга строки Mashreq: {e}")
            return None
    
    def _parse_date(self, date_str):
        """Парсит дату в формате 'DD Mon YYYY'"""
        try:
            # Пробуем формат "02 Jan 2026"
            months = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            
            parts = date_str.split()
            if len(parts) == 3:
                day = parts[0].zfill(2)
                month = months.get(parts[1].lower()[:3], '01')
                year = parts[2]
                return f"{year}-{month}-{day}"
        except:
            pass
        return date_str
    
    def _extract_article_code(self, description):
        """Извлекает код статьи из описания"""
        if not description:
            return None
        
        desc_lower = description.lower()
        
        # По ключевым словам
        if 'vat' in desc_lower or 'ндс' in desc_lower:
            return '1.2.38 НДС в составе комиссий'
        elif 'commission' in desc_lower or 'комиссия' in desc_lower:
            return '1.1.4.1 Комиссия за продажу недвижимости'
        elif 'transfer' in desc_lower or 'перевод' in desc_lower:
            return '4.1 Перевод'
        elif 'charge' in desc_lower and 'bank' in desc_lower:
            return '1.2.17 РКО'
        elif 'fee' in desc_lower:
            return '1.2.17 РКО'
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """Определяет направление"""
        desc_lower = transaction['description'].lower()
        
        if 'nomiqa' in desc_lower:
            return 'Nomiqa', None
        elif 'baku' in desc_lower or 'баку' in desc_lower:
            return 'Nomiqa', 'BNQ_BAKU-Nomiqa'
        elif 'dubai' in desc_lower or 'дубай' in desc_lower:
            return 'Nomiqa', 'DNQ_Dubai-Nomiqa'
        
        return 'Nomiqa', None
    
    def enrich_transaction(self, transaction):
        """Обогащает транзакцию"""
        return transaction