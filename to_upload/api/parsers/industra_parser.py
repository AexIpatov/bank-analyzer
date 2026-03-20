import pandas as pd
import re
from datetime import datetime
from .finclassifier import FinClassifier

class IndustraParser:
    def __init__(self):
        self.bank_name = "Industra Bank"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит выписку Industra Bank (поддерживает CSV и Excel)
        """
        transactions = []
        
        # Определяем тип файла по расширению
        if filename.lower().endswith('.csv'):
            return self._parse_csv(file_path, filename)
        elif filename.lower().endswith(('.xlsx', '.xls')):
            return self._parse_excel(file_path, filename)
        else:
            print(f"❌ Неподдерживаемый формат для Industra: {filename}")
            return []
    
    def _parse_csv(self, file_path, filename):
        """Парсит CSV файл Industra"""
        transactions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                
                # Находим строку с заголовками
                header_found = False
                headers = []
                
                for line in lines:
                    if 'Дата транзакции' in line and 'Дебет(D)' in line:
                        headers = line.strip().split(',')
                        header_found = True
                        continue
                    
                    if header_found and line.strip():
                        try:
                            transaction = self._parse_csv_row(line.strip(), headers)
                            if transaction:
                                transactions.append(transaction)
                        except:
                            continue
        except Exception as e:
            print(f"Ошибка парсинга CSV: {e}")
        
        return transactions
    
    def _parse_csv_row(self, line, headers):
        """Парсит одну строку CSV"""
        fields = self._parse_csv_line(line)
        
        if len(fields) < 12:
            return None
        
        # Определяем сумму (дебет или кредит)
        amount = 0
        
        if len(fields) > 11 and fields[11] and fields[11].strip():
            try:
                amount = -float(fields[11].replace(',', '.'))
            except:
                amount = 0
        elif len(fields) > 12 and fields[12] and fields[12].strip():
            try:
                amount = float(fields[12].replace(',', '.'))
            except:
                amount = 0
        
        # Извлекаем информацию
        info = fields[10] if len(fields) > 10 else ''
        date_str = fields[0] if len(fields) > 0 else ''
        payee = fields[5] if len(fields) > 5 else ''
        
        # Парсим дату
        date = self._parse_date(date_str)
        
        # Извлекаем статью
        article_code = self._extract_article_code(info)
        
        return {
            'date': date,
            'amount': amount,
            'currency': 'EUR',
            'description': info,
            'payee': payee,
            'bank': self.bank_name,
            'article_code': article_code
        }
    
    def _parse_excel(self, file_path, filename):
        """Парсит Excel файл Industra"""
        transactions = []
        
        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path, header=None)
            
            # Ищем строку с данными
            start_row = 0
            for idx, row in df.iterrows():
                row_str = ' '.join([str(x) for x in row if pd.notna(x)])
                if 'Дата транзакции' in row_str and 'Дебет(D)' in row_str:
                    start_row = idx + 1
                    break
            
            # Парсим строки
            for idx in range(start_row, len(df)):
                row = df.iloc[idx]
                if all(pd.isna(x) for x in row):
                    continue
                
                transaction = self._parse_excel_row(row)
                if transaction:
                    transactions.append(transaction)
                    
        except Exception as e:
            print(f"Ошибка парсинга Excel: {e}")
        
        return transactions
    
    def _parse_excel_row(self, row):
        """Парсит одну строку Excel"""
        try:
            # Дата (колонка 0)
            date_str = str(row[0]) if len(row) > 0 and pd.notna(row[0]) else ''
            date = self._parse_date(date_str)
            
            # Описание (колонка 10)
            description = str(row[10]) if len(row) > 10 and pd.notna(row[10]) else ''
            
            # Плательщик (колонка 5)
            payee = str(row[5]) if len(row) > 5 and pd.notna(row[5]) else ''
            
            # Сумма (дебет или кредит)
            amount = 0
            if len(row) > 11 and pd.notna(row[11]):
                try:
                    amount = -float(str(row[11]).replace(',', '.'))
                except:
                    pass
            elif len(row) > 12 and pd.notna(row[12]):
                try:
                    amount = float(str(row[12]).replace(',', '.'))
                except:
                    pass
            
            if amount == 0:
                return None
            
            # Извлекаем статью
            article_code = self._extract_article_code(description)
            
            return {
                'date': date,
                'amount': amount,
                'currency': 'EUR',
                'description': description,
                'payee': payee,
                'bank': self.bank_name,
                'article_code': article_code
            }
            
        except Exception as e:
            return None
    
    def _parse_csv_line(self, line):
        """Парсит CSV строку с учетом кавычек"""
        result = []
        current = ''
        in_quotes = False
        
        for char in line:
            if char == '"' and not in_quotes:
                in_quotes = True
            elif char == '"' and in_quotes:
                in_quotes = False
            elif char == ',' and not in_quotes:
                result.append(current.strip())
                current = ''
            else:
                current += char
        
        if current:
            result.append(current.strip())
        
        return result
    
    def _parse_date(self, date_str):
        """Парсит дату"""
        try:
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
        
        # Ищем паттерн вида (1.2.15.1)
        match = re.search(r'\((\d+\.\d+\.\d+\.?\d*)\)', description)
        if match:
            return match.group(1)
        
        # По ключевым словам
        if '1.2.15.1' in description:
            return '1.2.15.1'
        elif '1.1.4' in description:
            return '1.1.4'
        elif '1.2.10.1' in description:
            return '1.2.10.1'
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """Определяет направление"""
        desc_lower = transaction['description'].lower()
        
        if 'matisa' in desc_lower or 'm81' in desc_lower:
            return 'Latvia', 'M81 - Matisa 81'
        elif 'antonijas' in desc_lower or 'an14' in desc_lower:
            return 'Latvia', 'AN14_Antonijas14'
        elif 'čaka' in desc_lower or 'caka' in desc_lower or 'ac89' in desc_lower:
            return 'Latvia', 'AC89_Čaka89'
        else:
            return 'Latvia', None
    
    def enrich_transaction(self, transaction):
        """Обогащает транзакцию"""
        return transaction