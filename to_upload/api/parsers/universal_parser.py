import csv
import re
import pandas as pd
from datetime import datetime
from .finclassifier import FinClassifier
from .bank_configs import BANK_CONFIGS, ARTICLE_KEYWORDS, DIRECTION_KEYWORDS

class UniversalParser:
    def __init__(self):
        self.classifier = FinClassifier()
        self.configs = BANK_CONFIGS
    
    def identify_bank(self, filename):
        """
        Определяет банк по имени файла
        """
        filename_lower = filename.lower()
        
        # Проверяем, что файл не PDF
        if filename_lower.endswith('.pdf'):
            return None, None
        
        for bank_key, config in self.configs.items():
            for pattern in config['patterns']:
                if re.search(pattern, filename_lower):
                    return bank_key, config
        
        return None, None
    
    def parse_file(self, file_path, filename):
        """
        Парсит файл используя конфигурацию банка
        """
        bank_key, config = self.identify_bank(filename)
        
        if not bank_key:
            raise ValueError(f"Неизвестный тип банка для файла {filename}")
        
        print(f"Определен банк: {config['name']} (ключ: {bank_key})")
        
        # Выбираем метод парсинга в зависимости от типа файла
        if config['file_type'] == 'csv':
            transactions = self._parse_csv(file_path, config)
        elif config['file_type'] == 'excel':
            transactions = self._parse_excel(file_path, config)
        else:
            print(f"  ⚠️ Формат {config['file_type']} не поддерживается. Используйте Excel или CSV.")
            return []
        
        # Обогащаем транзакции
        enriched = []
        for t in transactions:
            t['bank'] = config['name']
            t['bank_key'] = bank_key
            enriched.append(self._enrich_transaction(t, config))
        
        return enriched
    
    def _parse_csv(self, file_path, config):
        """Парсит CSV файл"""
        transactions = []
        encoding = config.get('encoding', 'utf-8')
        delimiter = config.get('delimiter', ',')
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Пропускаем строки, если нужно
                for _ in range(config.get('skip_rows', 0)):
                    next(f)
                
                # Читаем CSV
                reader = csv.reader(f, delimiter=delimiter)
                
                # Ищем заголовки
                headers = None
                if config.get('has_header', True):
                    try:
                        headers = next(reader)
                    except:
                        pass
                
                if not headers:
                    # Используем позиционные заголовки из конфига
                    header_map = config['headers']
                    for row in reader:
                        if not row or all(not cell.strip() for cell in row):
                            continue
                        t = self._extract_from_row(row, header_map, config)
                        if t:
                            transactions.append(t)
                else:
                    # Заголовки есть, создаем маппинг
                    header_map = {}
                    for key, value in config['headers'].items():
                        if isinstance(value, int):
                            header_map[key] = value
                        else:
                            try:
                                header_map[key] = headers.index(value)
                            except ValueError:
                                pass
                    
                    for row in reader:
                        if not row or all(not cell.strip() for cell in row):
                            continue
                        t = self._extract_from_row(row, header_map, config)
                        if t:
                            transactions.append(t)
        except Exception as e:
            print(f"Ошибка чтения CSV: {e}")
        
        return transactions
    
    def _parse_excel(self, file_path, config):
        """Парсит Excel файл"""
        transactions = []
        
        sheet_name = config.get('sheet_name', 0)
        
        try:
            # Пробуем разные движки для чтения Excel
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='openpyxl')
            except:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='xlrd')
                except:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            # Пропускаем строки
            start_row = config.get('skip_rows', 0)
            if start_row > 0:
                df = df.iloc[start_row:].reset_index(drop=True)
            
            # Ищем строку с данными
            data_start = 0
            for idx, row in df.iterrows():
                if any(pd.notna(x) for x in row):
                    data_start = idx
                    break
            
            df = df.iloc[data_start:].reset_index(drop=True)
            
            # Пробуем найти заголовки
            header_map = {}
            for attempt in range(min(5, len(df))):
                row = df.iloc[attempt]
                row_str = ' '.join([str(x).lower() for x in row if pd.notna(x)])
                
                # Проверяем наличие признаков заголовка
                has_date = any(word in row_str for word in ['date', 'дата', 'tarix', 'datum'])
                has_amount = any(word in row_str for word in ['amount', 'сумма', 'məbləğ', 'summa'])
                
                if has_date and has_amount:
                    headers = [str(x).strip() if pd.notna(x) else '' for x in row]
                    
                    for key, value in config['headers'].items():
                        if isinstance(value, str):
                            for idx, header in enumerate(headers):
                                if value.lower() in header.lower():
                                    header_map[key] = idx
                                    break
                        elif isinstance(value, int):
                            header_map[key] = value
                    
                    df = df.iloc[attempt+1:].reset_index(drop=True)
                    break
            
            # Если заголовки не найдены, используем позиционный маппинг
            if not header_map:
                header_map = config['headers']
            
            # Парсим строки
            for _, row in df.iterrows():
                if all(pd.isna(x) for x in row):
                    continue
                
                t = self._extract_from_row(row.tolist(), header_map, config)
                if t and t.get('amount', 0) != 0:
                    transactions.append(t)
                    
        except Exception as e:
            print(f"Ошибка чтения Excel: {e}")
            import traceback
            traceback.print_exc()
        
        return transactions
    
    def _extract_from_row(self, row, header_map, config):
        """Извлекает транзакцию из строки"""
        try:
            transaction = {}
            
            # Определяем сумму
            amount = 0
            currency = 'EUR'
            
            if config['amount_sign'] == 'debit_credit':
                debit_idx = header_map.get('debit')
                credit_idx = header_map.get('credit')
                credit_debit_idx = header_map.get('credit_debit')
                
                # Сначала проверяем колонку Credit/Debit (C/D)
                if credit_debit_idx is not None and credit_debit_idx < len(row):
                    cd_val = str(row[credit_debit_idx]) if pd.notna(row[credit_debit_idx]) else ''
                    if cd_val.upper() == 'D':
                        # Это дебет (расход) - ищем сумму в колонке amount
                        amount_idx = header_map.get('amount')
                        if amount_idx is not None and amount_idx < len(row):
                            amount_val = row[amount_idx]
                            if amount_val and str(amount_val).strip() and str(amount_val).strip() != 'nan':
                                try:
                                    amount = -float(str(amount_val).replace(',', '.').replace(' ', ''))
                                except:
                                    pass
                    elif cd_val.upper() == 'C':
                        # Это кредит (доход)
                        amount_idx = header_map.get('amount')
                        if amount_idx is not None and amount_idx < len(row):
                            amount_val = row[amount_idx]
                            if amount_val and str(amount_val).strip() and str(amount_val).strip() != 'nan':
                                try:
                                    amount = float(str(amount_val).replace(',', '.').replace(' ', ''))
                                except:
                                    pass
                
                # Если не нашли через credit_debit, пробуем через debit/credit колонки
                if amount == 0 and debit_idx is not None and debit_idx < len(row):
                    debit_val = row[debit_idx]
                    if debit_val and str(debit_val).strip() and str(debit_val).strip() != 'nan':
                        try:
                            amount = -float(str(debit_val).replace(',', '.').replace(' ', ''))
                        except:
                            pass
                
                if amount == 0 and credit_idx is not None and credit_idx < len(row):
                    credit_val = row[credit_idx]
                    if credit_val and str(credit_val).strip() and str(credit_val).strip() != 'nan':
                        try:
                            amount = float(str(credit_val).replace(',', '.').replace(' ', ''))
                        except:
                            pass
            else:
                amount_idx = header_map.get('amount')
                if amount_idx is not None and amount_idx < len(row):
                    amount_val = row[amount_idx]
                    if amount_val and str(amount_val).strip() and str(amount_val).strip() != 'nan':
                        try:
                            amount = float(str(amount_val).replace(',', '.'))
                        except:
                            pass
            
            if amount == 0:
                return None
            
            transaction['amount'] = amount
            
            # Дата
            date_idx = header_map.get('date')
            if date_idx is not None and date_idx < len(row):
                date_val = row[date_idx]
                if pd.notna(date_val) and str(date_val).strip():
                    transaction['date'] = self._parse_date(str(date_val), config.get('date_format'))
            
            # Дата и время
            date_time_idx = header_map.get('date_time')
            if date_time_idx is not None and date_time_idx < len(row):
                dt_val = row[date_time_idx]
                if pd.notna(dt_val) and str(dt_val).strip():
                    dt_str = str(dt_val).split()[0]  # Берем только дату
                    transaction['date'] = self._parse_date(dt_str, config.get('date_format'))
            
            # Валюта
            currency_idx = header_map.get('currency')
            if currency_idx is not None and currency_idx < len(row):
                currency_val = row[currency_idx]
                if pd.notna(currency_val) and str(currency_val).strip():
                    transaction['currency'] = str(currency_val).strip()
            
            # Описание
            desc_idx = header_map.get('description')
            if desc_idx is not None and desc_idx < len(row):
                desc_val = row[desc_idx]
                if pd.notna(desc_val) and str(desc_val).strip():
                    transaction['description'] = str(desc_val).strip()
            
            # Плательщик/получатель
            payee_idx = header_map.get('payee')
            if payee_idx is not None and payee_idx < len(row):
                payee_val = row[payee_idx]
                if pd.notna(payee_val) and str(payee_val).strip():
                    transaction['payee'] = str(payee_val).strip()
            
            return transaction
            
        except Exception as e:
            return None
    
    def _parse_date(self, date_str, date_format):
        """Парсит дату в разных форматах"""
        if not date_str:
            return ''
        
        date_str = str(date_str).strip()
        
        if date_format:
            try:
                dt = datetime.strptime(date_str, date_format)
                return dt.strftime('%Y-%m-%d')
            except:
                pass
        
        formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d %b %Y',
            '%Y%m%d'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return date_str
    
    def _extract_article_code(self, description, config):
        """Извлекает код статьи из описания"""
        if not description:
            return None
        
        pattern = config.get('article_pattern')
        if pattern:
            match = re.search(pattern, description)
            if match:
                return match.group(1)
        
        desc_lower = description.lower()
        for article, keywords in ARTICLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return article
        
        return None
    
    def _determine_direction(self, description):
        """Определяет направление по ключевым словам"""
        if not description:
            return None, None
        
        desc_lower = description.lower()
        
        for direction, keywords in DIRECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return direction, None
        
        return None, None
    
    def _enrich_transaction(self, transaction, config):
        """Обогащает транзакцию данными"""
        if 'article_code' not in transaction:
            transaction['article_code'] = self._extract_article_code(
                transaction.get('description', ''), config
            )
        
        direction, subdirection = self._determine_direction(
            transaction.get('description', '')
        )
        transaction['direction'] = direction
        transaction['subdirection'] = subdirection
        
        return transaction