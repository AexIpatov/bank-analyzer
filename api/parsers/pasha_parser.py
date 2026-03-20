import pandas as pd
import re
from datetime import datetime
from .finclassifier import FinClassifier

class PashaParser:
    def __init__(self):
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит выписку Pasha Bank
        """
        transactions = []
        
        # Определяем тип счета (AZN или AED) по имени файла
        if 'azn' in filename.lower():
            bank_name = 'Pasha Bank AZN'
            currency = 'AZN'
        else:
            bank_name = 'Pasha Bank AED'
            currency = 'AED'
        
        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path, sheet_name='Statement', header=None)
            
            # Пропускаем первые 8 строк (шапка)
            df = df.iloc[8:].reset_index(drop=True)
            
            # Ищем строку с данными
            for idx, row in df.iterrows():
                # Проверяем, есть ли дата в первой колонке
                date_val = row[0] if len(row) > 0 else None
                if pd.isna(date_val) or not self._is_date(str(date_val)):
                    continue
                
                # Парсим транзакцию
                t = self._parse_row(row, bank_name, currency)
                if t:
                    transactions.append(t)
                    
        except Exception as e:
            print(f"Ошибка парсинга Pasha Bank: {e}")
        
        return transactions
    
    def _is_date(self, text):
        """Проверяет, является ли текст датой"""
        if not text or text == 'nan':
            return False
        patterns = [r'\d{2}\.\d{2}\.\d{4}', r'\d{4}-\d{2}-\d{2}']
        return any(re.match(p, text) for p in patterns)
    
    def _parse_row(self, row, bank_name, currency):
        """Парсит одну строку транзакции"""
        try:
            # Дата
            date_str = str(row[0]).strip()
            date = self._parse_date(date_str)
            
            # Плательщик/получатель (колонка 2)
            payee = str(row[2]) if len(row) > 2 and pd.notna(row[2]) else ''
            
            # Описание (колонка 3)
            description = str(row[3]) if len(row) > 3 and pd.notna(row[3]) else ''
            
            # Сумма (доход или расход)
            amount = 0
            
            # Доход (колонка 5)
            if len(row) > 5 and pd.notna(row[5]):
                try:
                    amount = float(str(row[5]).replace(',', ''))
                except:
                    pass
            
            # Расход (колонка 6)
            if amount == 0 and len(row) > 6 and pd.notna(row[6]):
                try:
                    amount = -float(str(row[6]).replace(',', ''))
                except:
                    pass
            
            if amount == 0:
                return None
            
            # Определяем статью
            article_code = self._extract_article_code(description)
            
            return {
                'date': date,
                'amount': amount,
                'currency': currency,
                'description': description,
                'payee': payee,
                'bank': bank_name,
                'article_code': article_code
            }
            
        except Exception as e:
            print(f"Ошибка парсинга строки: {e}")
            return None
    
    def _parse_date(self, date_str):
        """Парсит дату"""
        try:
            # Пробуем формат ДД.ММ.ГГГГ
            if '.' in date_str:
                parts = date_str.split('.')
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
        if 'currency exchange' in desc_lower or 'конвертация' in desc_lower:
            return 'Перевод между счетами'
        elif 'charge for' in desc_lower or 'комиссия' in desc_lower:
            return '1.2.17 РКО'
        elif 'internal payment' in desc_lower:
            return 'Перевод между счетами'
        elif 'facebook' in desc_lower or 'facbk' in desc_lower:
            return '1.2.3 Оплата рекламных систем'
        elif 'outgoing' in desc_lower:
            return '1.2.17 РКО'
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """Определяет направление"""
        desc_lower = transaction['description'].lower()
        
        if 'nomiqa' in desc_lower:
            return 'Nomiqa', None
        elif 'baku' in desc_lower or 'азербайджан' in desc_lower:
            return 'East-Восток', None
        elif 'dubai' in desc_lower or 'дубай' in desc_lower:
            return 'Nomiqa', None
        
        return 'Nomiqa', None
    
    def enrich_transaction(self, transaction):
        """Обогащает транзакцию"""
        return transaction