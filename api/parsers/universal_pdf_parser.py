import re
from .base_pdf_parser import BasePDFParser
from .finclassifier import FinClassifier
from .bank_configs import BANK_CONFIGS

class UniversalPDFParser(BasePDFParser):
    """
    Универсальный парсер для PDF выписок всех банков
    """
    
    def __init__(self):
        super().__init__()
        self.classifier = FinClassifier()
        self.bank_templates = self._load_templates()
    
    def _load_templates(self):
        """
        Загружает шаблоны для разных банков из конфигурации
        """
        templates = {}
        
        # Добавляем шаблоны для банков, которые могут присылать PDF
        pdf_banks = ['revolut', 'n26', 'paysera_property', 'paysera_rerum', 
                     'paysera_sveciy', 'unicredit_czk']
        
        for bank_key in pdf_banks:
            if bank_key in BANK_CONFIGS:
                templates[bank_key] = {
                    'name': BANK_CONFIGS[bank_key]['name'],
                    'patterns': BANK_CONFIGS[bank_key]['patterns'],
                    'date_formats': self._get_date_formats(bank_key),
                    'amount_patterns': self._get_amount_patterns(bank_key)
                }
        
        return templates
    
    def _get_date_formats(self, bank_key):
        """
        Возвращает форматы дат для конкретного банка
        """
        formats = {
            'revolut': [r'\d{1,2}\s+[A-Za-z]+\s+\d{4}'],  # 14 Mar 2026
            'n26': [r'\d{2}\.\d{2}\.\d{4}'],  # 08.01.2026
            'paysera_property': [r'\d{4}-\d{2}-\d{2}'],  # 2026-01-02
            'paysera_rerum': [r'\d{4}-\d{2}-\d{2}'],
            'paysera_sveciy': [r'\d{4}-\d{2}-\d{2}'],
            'unicredit_czk': [r'\d{2}\.\d{2}\.\d{4}']  # 02.01.2026
        }
        return formats.get(bank_key, [r'\d{2}\.\d{2}\.\d{4}'])
    
    def _get_amount_patterns(self, bank_key):
        """
        Возвращает паттерны для сумм конкретного банка
        """
        patterns = {
            'revolut': r'([-+]?\d+[.,]?\d*)\s*([€$£]|EUR|USD|GBP)',
            'n26': r'([-+]?\d+[.,]?\d*)\s*[€]',
            'paysera': r'([-+]?\d+[.,]?\d*)\s*EUR',
            'unicredit': r'([-+]?\d+[.,]?\d*)\s*CZK'
        }
        return patterns
    
    def parse(self, file_path, filename):
        """
        Парсит PDF выписку, автоматически определяя банк
        """
        # Извлекаем текст из PDF
        text = self.extract_text_from_pdf(file_path)
        if not text:
            return []
        
        # Определяем банк
        bank_key = self._detect_bank(text, filename)
        if not bank_key:
            print(f"Не удалось определить банк для файла {filename}")
            return []
        
        print(f"Определен банк: {self.bank_name} (ключ: {bank_key})")
        
        # Парсим транзакции
        transactions = self._parse_by_bank(text, bank_key)
        
        return transactions
    
    def _detect_bank(self, text, filename):
        """
        Определяет банк по тексту PDF и имени файла
        """
        filename_lower = filename.lower()
        text_lower = text.lower()
        
        for bank_key, template in self.bank_templates.items():
            # Проверяем по паттернам из конфига
            for pattern in template['patterns']:
                if re.search(pattern, filename_lower) or re.search(pattern, text_lower):
                    self.bank_name = template['name']
                    return bank_key
        
        return None
    
    def _parse_by_bank(self, text, bank_key):
        """
        Парсит транзакции в зависимости от банка
        """
        if bank_key == 'revolut':
            return self._parse_revolut(text)
        elif bank_key == 'n26':
            return self._parse_n26(text)
        elif bank_key.startswith('paysera'):
            return self._parse_paysera(text, bank_key)
        elif bank_key == 'unicredit_czk':
            return self._parse_unicredit(text)
        else:
            return self._parse_generic(text)
    
    def _parse_revolut(self, text):
        """
        Парсит Revolut PDF
        """
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            # Ищем строки с транзакциями
            if re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', line):
                transaction = self._parse_revolut_line(line)
                if transaction:
                    transactions.append(transaction)
        
        return transactions
    
    def _parse_revolut_line(self, line):
        """
        Парсит одну строку Revolut
        """
        # Дата
        date_match = re.search(r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})', line)
        if not date_match:
            return None
        
        date_str = date_match.group(1)
        date = self._parse_revolut_date(date_str)
        
        # Сумма
        amount_match = re.search(r'([-+]?\d+[.,]?\d*)\s*([€$£]|EUR)', line)
        if not amount_match:
            return None
        
        amount = self._clean_amount(amount_match.group(1))
        
        # Описание (всё между датой и суммой)
        desc_match = re.search(rf'{date_str}\s+(.+?)\s+{amount_match.group(1)}', line)
        description = desc_match.group(1).strip() if desc_match else ''
        
        return {
            'date': date,
            'amount': amount,
            'currency': 'EUR',
            'description': description,
            'bank': 'Revolut',
            'article_code': self._extract_article_code(description)
        }
    
    def _parse_n26(self, text):
        """
        Парсит N26 PDF (испанский формат)
        """
        transactions = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Ищем строки с датой и суммой
            if re.search(r'\d{2}\.\d{2}\.\d{4}', line):
                # Парсим транзакцию N26
                transaction = self._parse_n26_line(line, lines[i+1] if i+1 < len(lines) else '')
                if transaction:
                    transactions.append(transaction)
        
        return transactions
    
    def _parse_n26_line(self, line, next_line):
        """
        Парсит одну строку N26
        """
        # Дата
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', line)
        if not date_match:
            return None
        
        date_str = date_match.group(1)
        date = f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"
        
        # Сумма
        amount_match = re.search(r'([-+]?\d+[.,]?\d*)€', line + ' ' + next_line)
        if not amount_match:
            return None
        
        amount = self._clean_amount(amount_match.group(1))
        
        # Описание
        description = line.replace(date_str, '').strip()
        if not description and next_line:
            description = next_line.strip()
        
        return {
            'date': date,
            'amount': amount,
            'currency': 'EUR',
            'description': description,
            'bank': 'N26',
            'article_code': self._extract_article_code(description)
        }
    
    def _parse_paysera(self, text, bank_key):
        """
        Парсит Paysera PDF
        """
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            # Ищем строки с транзакциями Paysera
            if 'Pārskaitījums' in line or 'Komisijas maksa' in line:
                transaction = self._parse_paysera_line(line, bank_key)
                if transaction:
                    transactions.append(transaction)
        
        return transactions
    
    def _parse_paysera_line(self, line, bank_key):
        """
        Парсит одну строку Paysera
        """
        # Дата (в формате YYYY-MM-DD)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
        if not date_match:
            return None
        
        date = date_match.group(1)
        
        # Сумма
        amount_match = re.search(r'([-+]?\d+[.,]?\d*)\s*EUR', line)
        if not amount_match:
            return None
        
        amount = self._clean_amount(amount_match.group(1))
        
        # Определяем направление по ключу банка
        direction = 'Latvia'
        if 'sveciy' in bank_key:
            direction = 'Europe'
        
        return {
            'date': date,
            'amount': amount,
            'currency': 'EUR',
            'description': line.strip(),
            'bank': self.bank_name,
            'article_code': None,
            'direction': direction
        }
    
    def _parse_unicredit(self, text):
        """
        Парсит UniCredit PDF (чешский)
        """
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            # Ищем строки с транзакциями
            if re.search(r'\d{2}\.\d{2}\.\d{4}', line) and ('POPLATEK' in line or 'TUZEMSKÁ' in line):
                transaction = self._parse_unicredit_line(line)
                if transaction:
                    transactions.append(transaction)
        
        return transactions
    
    def _parse_unicredit_line(self, line):
        """
        Парсит одну строку UniCredit
        """
        # Дата
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', line)
        if not date_match:
            return None
        
        date_str = date_match.group(1)
        date = f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"
        
        # Сумма
        amount_match = re.search(r'([-+]?\d+[.,]?\d*)\s*CZK', line)
        if not amount_match:
            return None
        
        amount = self._clean_amount(amount_match.group(1))
        
        # Тип транзакции
        transaction_type = 'unknown'
        if 'POPLATEK' in line:
            transaction_type = 'fee'
        elif 'PŘÍCHOZÍ' in line:
            transaction_type = 'incoming'
        
        return {
            'date': date,
            'amount': amount,
            'currency': 'CZK',
            'description': line.strip(),
            'bank': 'UniCredit',
            'article_code': '1.2.17 РКО' if transaction_type == 'fee' else None,
            'type': transaction_type
        }
    
    def _parse_generic(self, text):
        """
        Универсальный парсер для любых PDF
        """
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            # Ищем любые строки, похожие на транзакции
            if self._looks_like_transaction(line):
                transaction = self._parse_generic_line(line)
                if transaction:
                    transactions.append(transaction)
        
        return transactions
    
    def _looks_like_transaction(self, line):
        """
        Проверяет, похожа ли строка на транзакцию
        """
        # Должна содержать дату и сумму
        has_date = bool(re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', line))
        has_amount = bool(re.search(r'[-+]?\d+[.,]?\d*\s*[€$£]|EUR|USD|CZK', line))
        
        return has_date and has_amount
    
    def _parse_generic_line(self, line):
        """
        Универсальный парсер строки
        """
        # Дата
        date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', line)
        if not date_match:
            return None
        
        date_str = date_match.group(1)
        date = self._parse_date(date_str)
        
        # Сумма
        amount_match = re.search(r'([-+]?\d+[.,]?\d*)\s*([€$£]|EUR|USD|CZK)', line)
        if not amount_match:
            return None
        
        amount = self._clean_amount(amount_match.group(1))
        currency = amount_match.group(2)
        
        # Описание (остаток строки)
        description = line.replace(date_str, '').replace(amount_match.group(0), '').strip()
        
        return {
            'date': date,
            'amount': amount,
            'currency': currency if len(currency) <= 3 else 'EUR',
            'description': description,
            'bank': 'Unknown',
            'article_code': self._extract_article_code(description)
        }
    
    def _parse_revolut_date(self, date_str):
        """
        Парсит дату в формате Revolut
        """
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
        
        return date_str
    
    def _extract_article_code(self, description):
        """
        Извлекает код статьи из описания
        """
        if not description:
            return None
        
        # Ищем паттерн вида (1.2.10.3)
        match = re.search(r'\((\d+\.\d+\.\d+\.?\d*)\)', description)
        if match:
            return match.group(1)
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """
        Определяет направление
        """
        # Используем классификатор
        direction, subdirection = self.classifier.classify_direction(
            transaction.get('description', '')
        )
        
        if direction:
            return direction, subdirection
        
        return transaction.get('direction'), None
    
    def enrich_transaction(self, transaction):
        """
        Обогащает транзакцию
        """
        return transaction