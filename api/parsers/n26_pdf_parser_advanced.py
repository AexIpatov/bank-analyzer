import pdfplumber
import re
from .base_pdf_parser import BasePDFParser
from .finclassifier import FinClassifier

class N26PDFParserAdvanced(BasePDFParser):
    """
    Продвинутый парсер для PDF выписок N26 с использованием pdfplumber
    """
    
    def __init__(self):
        super().__init__()
        self.bank_name = "N26"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит PDF выписку N26 используя pdfplumber
        """
        transactions = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Извлекаем таблицы
                    tables = page.extract_tables()
                    
                    for table in tables:
                        for row in table:
                            if row and any(cell for cell in row if cell):
                                transaction = self._parse_row(row)
                                if transaction:
                                    transactions.append(transaction)
                    
                    # Если таблиц нет, пробуем извлечь текст
                    if not tables:
                        text = page.extract_text()
                        if text:
                            page_transactions = self._parse_text(text)
                            transactions.extend(page_transactions)
        
        except Exception as e:
            print(f"Ошибка при парсинге N26 PDF: {e}")
        
        return transactions
    
    def _parse_row(self, row):
        """
        Парсит строку таблицы
        """
        try:
            # Объединяем все ячейки в одну строку
            line = ' '.join([str(cell) for cell in row if cell]).strip()
            
            # Ищем дату
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', line)
            if not date_match:
                return None
            
            date_str = date_match.group(1)
            date = f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"
            
            # Ищем сумму
            amount_match = re.search(r'([+-]?\s*\d+[.,]?\d*[.,]?\d*)\s*[€]', line)
            if not amount_match:
                return None
            
            amount_str = amount_match.group(1).replace('.', '').replace(',', '.').replace('+', '').strip()
            amount = float(amount_str)
            
            # Определяем знак
            if '-' in amount_match.group(0) or 'Debe' in line or 'pago' in line.lower():
                amount = -amount
            
            # Описание - всё остальное
            description = line.replace(date_match.group(0), '').replace(amount_match.group(0), '').strip()
            description = re.sub(r'\s+', ' ', description)
            
            # Определяем тип
            transaction_type = 'unknown'
            if amount > 0:
                transaction_type = 'income'
            elif 'Mastercard' in description or 'Tarjeta' in description:
                transaction_type = 'card_payment'
            
            # Определяем статью
            article_code = self._extract_article_code(description)
            
            return {
                'date': date,
                'amount': amount,
                'currency': 'EUR',
                'description': description,
                'bank': self.bank_name,
                'article_code': article_code,
                'type': transaction_type
            }
            
        except Exception as e:
            return None
    
    def _parse_text(self, text):
        """
        Парсит текст страницы
        """
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if re.search(r'\d{2}\.\d{2}\.\d{4}', line) and '€' in line:
                # Собираем многострочную транзакцию
                desc_lines = [line]
                j = i + 1
                while j < len(lines) and not re.search(r'\d{2}\.\d{2}\.\d{4}', lines[j]):
                    if lines[j].strip():
                        desc_lines.append(lines[j].strip())
                    j += 1
                
                full_text = ' '.join(desc_lines)
                
                # Парсим дату
                date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', full_text)
                if not date_match:
                    i = j
                    continue
                
                date_str = date_match.group(1)
                date = f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"
                
                # Парсим сумму
                amount_match = re.search(r'([+-]?\s*\d+[.,]?\d*[.,]?\d*)\s*[€]', full_text)
                if not amount_match:
                    i = j
                    continue
                
                amount_str = amount_match.group(1).replace('.', '').replace(',', '.').replace('+', '').strip()
                amount = float(amount_str)
                
                if '-' in amount_match.group(0):
                    amount = -amount
                
                # Описание
                description = full_text.replace(date_match.group(0), '').replace(amount_match.group(0), '').strip()
                description = re.sub(r'\s+', ' ', description)
                
                article_code = self._extract_article_code(description)
                
                transactions.append({
                    'date': date,
                    'amount': amount,
                    'currency': 'EUR',
                    'description': description,
                    'bank': self.bank_name,
                    'article_code': article_code,
                    'type': 'card_payment' if 'Mastercard' in description else 'unknown'
                })
                
                i = j
            else:
                i += 1
        
        return transactions
    
    def _extract_article_code(self, description):
        """
        Извлекает код статьи из описания
        """
        if not description:
            return None
        
        desc_lower = description.lower()
        
        keywords = {
            '1.2.2 Командировочные расходы': ['air india', 'transport', 'vuelo', 'fly', 'flixbus', 'hotel', 'booking', 'airbnb'],
            '1.2.17 РКО': ['metal membership', 'cuota', 'fee', 'comisión'],
            '1.2.9.3 IT сервисы': ['google', 'openai', 'chatgpt', 'adobe'],
            '1.2.1.1 Бытовое оборудование': ['supermercado', 'supermarket', 'mercado'],
            'Перевод между счетами': ['instant savings', 'ahorro', 'transfer']
        }
        
        for article, words in keywords.items():
            for word in words:
                if word in desc_lower:
                    return article
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """
        Определяет направление
        """
        return 'UK Estate', None
    
    def enrich_transaction(self, transaction):
        """
        Обогащает транзакцию
        """
        return transaction