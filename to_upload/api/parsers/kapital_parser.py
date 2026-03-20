import pandas as pd
import re
from datetime import datetime
from .finclassifier import FinClassifier

class KapitalParser:
    def __init__(self):
        self.classifier = FinClassifier()
        self.bank_name = 'Kapital Bank'
        self.currency = 'AZN'
    
    def parse(self, file_path, filename):
        """
        Парсит выписку Kapital Bank
        """
        transactions = []
        
        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path, sheet_name='Sheet0', header=None)
            
            # Ищем строку с заголовками (Дата, Расход, Доход, Баланс, Комментарии)
            header_row = None
            for idx, row in df.iterrows():
                row_str = ' '.join([str(x).lower() for x in row if pd.notna(x)])
                if 'дата' in row_str and 'расход' in row_str and 'доход' in row_str:
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
            print(f"Ошибка парсинга Kapital Bank: {e}")
        
        return transactions
    
    def _parse_row(self, row):
        """Парсит одну строку транзакции"""
        try:
            # Дата (колонка 0)
            date_val = row[0] if len(row) > 0 and pd.notna(row[0]) else None
            if date_val is None:
                return None
            
            date = self._parse_date(str(date_val))
            
            # Расход (колонка 1)
            debit = 0
            if len(row) > 1 and pd.notna(row[1]):
                try:
                    debit = float(str(row[1]).replace(',', ''))
                except:
                    pass
            
            # Доход (колонка 2)
            credit = 0
            if len(row) > 2 and pd.notna(row[2]):
                try:
                    credit = float(str(row[2]).replace(',', ''))
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
            
            # Описание (колонка 4)
            description = str(row[4]) if len(row) > 4 and pd.notna(row[4]) else ''
            
            # Баланс (колонка 3) - необязательно
            balance = None
            if len(row) > 3 and pd.notna(row[3]):
                try:
                    balance = float(str(row[3]).replace(',', ''))
                except:
                    pass
            
            # Определяем статью
            article_code = self._extract_article_code(description)
            
            return {
                'date': date,
                'amount': amount,
                'currency': self.currency,
                'description': description,
                'payee': '',
                'bank': self.bank_name,
                'article_code': article_code,
                'balance': balance
            }
            
        except Exception as e:
            print(f"Ошибка парсинга строки Kapital: {e}")
            return None
    
    def _parse_date(self, date_str):
        """Парсит дату в формате ДД-ММ-ГГГГ"""
        try:
            # Пробуем формат ДД-ММ-ГГГГ
            if '-' in date_str:
                parts = date_str.split('-')
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
        
        # По ключевым словам
        if 'p2p' in desc_lower or 'перевод' in desc_lower:
            return 'Перевод между счетами'
        elif 'fee' in desc_lower or 'комиссия' in desc_lower:
            return '1.2.17 РКО'
        elif 'transfer_from_zeus' in desc_lower:
            return '1.1.1.3 Арендная плата (счёт)'
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """Определяет направление"""
        desc_lower = transaction['description'].lower()
        
        if 'baku' in desc_lower or 'баку' in desc_lower:
            return 'East-Восток', None
        elif 'aze' in desc_lower:
            return 'East-Восток', None
        
        return 'East-Восток', None
    
    def enrich_transaction(self, transaction):
        """Обогащает транзакцию"""
        return transaction