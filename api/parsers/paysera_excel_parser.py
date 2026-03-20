import pandas as pd
import re
from datetime import datetime

def parse_paysera_excel(file_path):
    """
    Парсер для Excel-выписок Paysera
    Ожидает структуру:
    - Строки с данными начинаются после строки "Date and time"
    - Столбцы: Date and time, Amount and currency, Credit/Debit, Purpose of payment
    """
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        
        # Ищем строку с заголовками
        header_row = None
        for idx, row in df.iterrows():
            row_text = ' '.join(str(v) for v in row.values if pd.notna(v))
            if 'Date and time' in row_text and 'Amount and currency' in row_text:
                header_row = idx
                break
        
        if header_row is None:
            return []
        
        # Читаем данные, начиная со строки заголовков
        df_data = pd.read_excel(
            file_path, 
            sheet_name=0, 
            header=header_row,
            dtype=str
        )
        
        transactions = []
        
        for _, row in df_data.iterrows():
            # Проверяем, что строка содержит данные
            if pd.isna(row.get('Date and time', pd.NA)):
                continue
            
            # Парсим дату
            date_str = str(row['Date and time'])
            try:
                # Формат: 2026-02-20 08:57:48 +0100
                date_match = re.match(r'(\d{4}-\d{2}-\d{2})', date_str)
                if date_match:
                    date = date_match.group(1)
                else:
                    date = date_str[:10]
            except:
                date = ''
            
            # Парсим сумму и валюту
            amount_str = str(row.get('Amount and currency', '0'))
            amount = 0
            currency = 'EUR'
            try:
                # Извлекаем число из строки (например "6000" или "-5")
                amount_match = re.search(r'([-]?\d+(?:[.,]\d+)?)', amount_str)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', '.'))
            except:
                amount = 0
            
            # Определяем знак суммы по столбцу Credit/Debit
            cd = str(row.get('Credit/Debit', '')).upper()
            if cd == 'D' and amount > 0:
                amount = -amount
            
            # Описание
            description = str(row.get('Purpose of payment', ''))
            
            # Счет (из имени файла будет подставлен позже)
            account_name = 'Paysera'
            
            transaction = {
                'date': date,
                'amount': amount,
                'currency': currency,
                'account_name': account_name,
                'description': description,
                'article_name': '',
                'article_code': '',
                'direction': '',
                'subdirection': ''
            }
            
            transactions.append(transaction)
        
        return transactions
        
    except Exception as e:
        print(f"Ошибка при парсинге Paysera Excel: {e}")
        return []


def can_parse(file_name, file_content=None):
    """Проверяет, может ли этот парсер обработать файл"""
    if file_name:
        # Проверяем по расширению
        if file_name.lower().endswith(('.xls', '.xlsx')):
            # Проверяем по имени файла
            if 'paysera' in file_name.lower():
                return True
    return False
