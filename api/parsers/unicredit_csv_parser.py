import pandas as pd
import re
from datetime import datetime
from .base_parser import BaseParser
from .finclassifier import FinClassifier

class UniCreditCSVParser(BaseParser):
    """
    Парсер для CSV выписок UniCredit (чешский формат)
    """
    
    def __init__(self):
        super().__init__()
        self.bank_name = "UniCredit"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит CSV выписку UniCredit
        """
        transactions = []
        
        try:
            # Читаем файл построчно
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Пропускаем заголовки
            start_row = 0
            for i, line in enumerate(lines):
                if 'From Account' in line and 'Amount' in line:
                    start_row = i + 1
                    break
            
            # Парсим каждую строку
            for i in range(start_row, len(lines)):
                line = lines[i].strip()
                if not line:
                    continue
                
                transaction = self._parse_line(line)
                if transaction:
                    transactions.append(transaction)
                    
        except Exception as e:
            print(f"Ошибка парсинга UniCredit CSV: {e}")
        
        return transactions
    
    def _parse_line(self, line):
        """
        Парсит одну строку CSV
        """
        try:
            # Разбиваем по точке с запятой
            parts = line.split(';')
            
            if len(parts) < 5:
                return None
            
            # Номер счета (первая колонка)
            account = parts[0].strip()
            
            # Сумма (вторая колонка)
            amount_str = parts[1].strip().replace(',', '.').replace(' ', '')
            try:
                amount = float(amount_str)
            except:
                return None
            
            # Валюта (третья колонка)
            currency = parts[2].strip() if len(parts) > 2 else 'CZK'
            
            # Дата (четвертая колонка)
            date_str = parts[3].strip() if len(parts) > 3 else ''
            date = self._parse_date(date_str)
            
            # Описание (последняя колонка с данными)
            description = ''
            # Ищем описание в колонках после 10-й
            for j in range(10, min(len(parts), 20)):
                if parts[j] and parts[j].strip():
                    description += parts[j].strip() + ' '
            
            if not description:
                description = ';'.join(parts[4:])[:200]
            
            # Определяем статью
            article_code = self._extract_article_code(description)
            
            # Определяем направление
            direction, subdirection = self._determine_direction(description)
            
            return {
                'date': date,
                'amount': amount,
                'currency': currency,
                'description': description,
                'bank': self.bank_name,
                'article_code': article_code,
                'direction': direction,
                'subdirection': subdirection,
                'account': account
            }
            
        except Exception as e:
            return None
    
    def _parse_date(self, date_str):
        """Парсит дату в формате YYYY-MM-DD"""
        try:
            if ' ' in date_str:
                date_str = date_str.split()[0]
            return date_str
        except:
            return ''
    
    def _extract_article_code(self, description):
        """Извлекает код статьи из описания"""
        if not description:
            return None
        
        desc_lower = description.lower()
        
        # По ключевым словам
        if 'popl' in desc_lower or 'fee' in desc_lower:
            return '1.2.17 РКО'
        elif 'urok' in desc_lower or 'interest' in desc_lower:
            return '1.1.2.4 Прочие мелкие поступления'
        elif 'najem' in desc_lower or 'rent' in desc_lower:
            return '1.1.1.3 Арендная плата (счёт)'
        elif 'cez' in desc_lower or 'elekt' in desc_lower:
            return '1.2.10.5 Электричество'
        elif 'snkv' in desc_lower:
            return '1.2.10.6 Коммунальные УК дома'
        
        return None
    
    def _determine_direction(self, description):
        """Определяет направление"""
        desc_lower = description.lower()
        
        if 'karlovy' in desc_lower or 'praha' in desc_lower:
            return 'Europe', None
        elif 'otovice' in desc_lower:
            return 'Europe', 'OT1_Otovice'
        
        return 'Europe', None
    
    def determine_direction(self, transaction, dictionaries):
        """Определяет направление"""
        return transaction.get('direction'), transaction.get('subdirection')
    
    def enrich_transaction(self, transaction):
        """Обогащает транзакцию"""
        return transaction