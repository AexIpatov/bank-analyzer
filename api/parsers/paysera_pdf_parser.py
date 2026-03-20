import re
import fitz  # PyMuPDF
from .base_pdf_parser import BasePDFParser
from .finclassifier import FinClassifier

class PayseraPDFParser(BasePDFParser):
    """
    Универсальный парсер для PDF выписок Paysera (все форматы)
    """
    
    def __init__(self, bank_type='property'):
        super().__init__()
        self.bank_type = bank_type
        self.classifier = FinClassifier()
        
        # Настройка имени банка в зависимости от типа
        if bank_type == 'property':
            self.bank_name = "Paysera BS Property"
        elif bank_type == 'rerum':
            self.bank_name = "Paysera BS Rerum"
        elif bank_type == 'sveciy':
            self.bank_name = "Paysera Sveciy Namai"
        else:
            self.bank_name = "Paysera"
    
    def parse(self, file_path, filename):
        """
        Парсит PDF выписку Paysera
        """
        transactions = []
        
        try:
            # Открываем PDF с помощью PyMuPDF
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Определяем язык/формат страницы
                if 'Pārskaitījums' in text:
                    # Латышский формат
                    page_transactions = self._parse_latvian_text(text)
                elif 'Transfer' in text or 'Payment' in text:
                    # Английский формат
                    page_transactions = self._parse_english_text(text)
                else:
                    # Универсальный формат
                    page_transactions = self._parse_universal_text(text)
                
                transactions.extend(page_transactions)
            
            doc.close()
            
        except Exception as e:
            print(f"Ошибка при парсинге Paysera PDF: {e}")
        
        return transactions
    
    def _parse_latvian_text(self, text):
        """Парсит латышский формат (с Pārskaitījums)"""
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if 'Pārskaitījums' in line and self._contains_date(line):
                # Парсим транзакцию
                transaction = self._parse_latvian_transaction(lines, i)
                if transaction:
                    transactions.append(transaction)
                    i += transaction.get('lines_used', 1)
                    continue
            i += 1
        
        return transactions
    
    def _parse_english_text(self, text):
        """Парсит английский формат"""
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ищем строки с датой и суммой
            if self._contains_date(line) and ('EUR' in line or '€' in line):
                transaction = self._parse_english_transaction(lines, i)
                if transaction:
                    transactions.append(transaction)
                    i += transaction.get('lines_used', 1)
                    continue
            i += 1
        
        return transactions
    
    def _parse_universal_text(self, text):
        """Универсальный парсер для любого формата"""
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ищем любые строки, похожие на транзакции
            if self._contains_date(line) and self._contains_amount(line):
                transaction = self._parse_universal_transaction(lines, i)
                if transaction:
                    transactions.append(transaction)
                    i += transaction.get('lines_used', 1)
                    continue
            i += 1
        
        return transactions
    
    def _contains_date(self, text):
        """Проверяет наличие даты в формате YYYY-MM-DD"""
        return bool(re.search(r'\d{4}-\d{2}-\d{2}', text))
    
    def _contains_amount(self, text):
        """Проверяет наличие суммы"""
        return bool(re.search(r'\d+[.,]?\d*\s*(EUR|€)', text))
    
    def _parse_latvian_transaction(self, lines, start_idx):
        """Парсит транзакцию в латышском формате"""
        try:
            line = lines[start_idx].strip()
            
            # Дата
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if not date_match:
                return None
            date = date_match.group(1)
            
            # Сумма
            amount_match = re.search(r'([-+]?\s*\d+[.,]?\d*[.,]?\d*)\s*EUR', line)
            if not amount_match:
                return None
            amount = float(amount_match.group(1).replace(',', '.').replace(' ', ''))
            if '-' in amount_match.group(0):
                amount = -amount
            
            # Собираем информацию
            payee = ""
            description = ""
            lines_used = 1
            
            j = start_idx + 1
            while j < len(lines) and j < start_idx + 5:
                current = lines[j].strip()
                if not current:
                    j += 1
                    continue
                
                if 'Maksājuma mērķis' in current:
                    desc_parts = current.split(':', 1)
                    if len(desc_parts) > 1:
                        description = desc_parts[1].strip()
                elif not payee and current and not current.startswith('Maksājuma'):
                    payee = current
                
                lines_used = j - start_idx + 1
                j += 1
            
            return {
                'date': date,
                'amount': amount,
                'currency': 'EUR',
                'description': description,
                'payee': payee,
                'bank': self.bank_name,
                'article_code': self._extract_article_code(description),
                'direction': self._determine_direction(payee + " " + description),
                'lines_used': lines_used
            }
            
        except Exception as e:
            return None
    
    def _parse_english_transaction(self, lines, start_idx):
        """Парсит транзакцию в английском формате"""
        try:
            line = lines[start_idx].strip()
            
            # Дата
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if not date_match:
                return None
            date = date_match.group(1)
            
            # Сумма
            amount_match = re.search(r'([-+]?\s*\d+[.,]?\d*[.,]?\d*)\s*(EUR|€)', line)
            if not amount_match:
                return None
            amount = float(amount_match.group(1).replace(',', '.').replace(' ', ''))
            
            # Определяем знак (обычно расходы идут с минусом)
            if 'Expenses' in line or 'Payment' in line or 'Debit' in line:
                amount = -amount
            
            # Описание - всё остальное
            description = line.replace(date_match.group(0), '').replace(amount_match.group(0), '').strip()
            
            return {
                'date': date,
                'amount': amount,
                'currency': 'EUR',
                'description': description,
                'payee': '',
                'bank': self.bank_name,
                'article_code': self._extract_article_code(description),
                'direction': self._determine_direction(description),
                'lines_used': 1
            }
            
        except Exception as e:
            return None
    
    def _parse_universal_transaction(self, lines, start_idx):
        """Универсальный парсер транзакции"""
        try:
            line = lines[start_idx].strip()
            
            # Дата
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if not date_match:
                return None
            date = date_match.group(1)
            
            # Сумма
            amount_match = re.search(r'([-+]?\s*\d+[.,]?\d*[.,]?\d*)\s*(EUR|€)', line)
            if not amount_match:
                return None
            
            amount_str = amount_match.group(1).replace(',', '.').replace(' ', '')
            amount = float(amount_str)
            
            # Определяем знак
            if '-' in amount_match.group(0) or 'Debit' in line or 'Expenses' in line:
                amount = -amount
            
            # Описание
            description = line.replace(date_match.group(0), '').replace(amount_match.group(0), '').strip()
            
            return {
                'date': date,
                'amount': amount,
                'currency': 'EUR',
                'description': description,
                'payee': '',
                'bank': self.bank_name,
                'article_code': self._extract_article_code(description),
                'direction': self._determine_direction(description),
                'lines_used': 1
            }
            
        except Exception as e:
            return None
    
    def _extract_article_code(self, description):
        """Извлекает код статьи из описания"""
        if not description:
            return None
        
        desc_lower = description.lower()
        
        keywords = {
            '1.2.17 РКО': ['fee', 'komisijas maksa', 'maintenance fee', 'service'],
            '1.2.10.3 Вода': ['ūdens', 'water', 'rigas ūdens'],
            '1.2.10.5 Электричество': ['elektriba', 'electricity', 'latvenergo', 'elektro'],
            '1.2.10.1 Мусор': ['atkritumi', 'waste', 'clean r', 'eco baltia'],
            '1.2.9.1 Связь , интернет': ['internets', 'internet', 'tele', 'bite', 'tele2'],
            '1.1.1.3 Арендная плата (счёт)': ['rent', 'īre', 'apmaksa', 'payment', 'rekina'],
            '1.2.8.1 Обслуживание объектов': ['maintenance', 'remonts', 'uzturēšana'],
            '1.2.21.2 Административные расходы': ['office', 'administrative', 'biroja']
        }
        
        for article, words in keywords.items():
            for word in words:
                if word in desc_lower:
                    return article
        
        return None
    
    def _determine_direction(self, text):
        """Определяет направление"""
        text_lower = text.lower()
        
        if 'latvia' in text_lower or 'riga' in text_lower or 'lv' in text_lower:
            return 'Latvia'
        elif 'lithuania' in text_lower or 'vilnius' in text_lower or 'lt' in text_lower:
            return 'Europe'
        elif 'čaka' in text_lower or 'caka' in text_lower:
            return 'Latvia'
        elif 'matisa' in text_lower:
            return 'Latvia'
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """Определяет направление"""
        if transaction.get('direction'):
            return transaction['direction'], None
        return 'Latvia' if 'property' in self.bank_name.lower() else 'Europe', None
    
    def enrich_transaction(self, transaction):
        """Обогащает транзакцию"""
        return transaction