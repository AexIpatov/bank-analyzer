import pdfplumber
import re
from .base_pdf_parser import BasePDFParser
from .finclassifier import FinClassifier

class PayseraPDFPlumberParser(BasePDFParser):
    """
    Парсер для PDF выписок Paysera с использованием pdfplumber
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
        Парсит PDF выписку Paysera используя pdfplumber
        """
        transactions = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Извлекаем таблицы
                    tables = page.extract_tables()
                    
                    for table in tables:
                        for row in table:
                            if not row or not any(cell for cell in row if cell):
                                continue
                            
                            # Объединяем все ячейки в строку
                            row_text = ' '.join([str(cell) for cell in row if cell])
                            
                            # Ищем дату и сумму
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', row_text)
                            amount_match = re.search(r'([-+]?\s*\d+[.,]?\d*[.,]?\d*)\s*EUR', row_text)
                            
                            if date_match and amount_match:
                                date = date_match.group(1)
                                
                                amount_str = amount_match.group(1).replace(',', '.').replace(' ', '')
                                amount = float(amount_str)
                                
                                # Определяем знак (если есть минус)
                                if '-' in amount_match.group(0):
                                    amount = -amount
                                
                                # Извлекаем описание (Maksājuma mērķis)
                                description = ""
                                if 'Maksājuma mērķis' in row_text:
                                    desc_parts = row_text.split('Maksājuma mērķis')
                                    if len(desc_parts) > 1:
                                        description = desc_parts[1].replace(':', '').strip()
                                
                                if not description:
                                    # Если нет описания, используем часть с получателем
                                    parts = row_text.split('EUR')
                                    if len(parts) > 1:
                                        description = parts[1].strip()
                                
                                # Извлекаем получателя
                                payee = ""
                                for cell in row:
                                    if cell and '(' in str(cell) and ')' in str(cell):
                                        payee = str(cell)
                                        break
                                
                                # Определяем статью
                                article_code = self._extract_article_code(description)
                                
                                # Определяем направление
                                direction = self._determine_direction(description + " " + payee)
                                
                                transactions.append({
                                    'date': date,
                                    'amount': amount,
                                    'currency': 'EUR',
                                    'description': description,
                                    'payee': payee,
                                    'bank': self.bank_name,
                                    'article_code': article_code,
                                    'direction': direction,
                                    'subdirection': None
                                })
            
        except Exception as e:
            print(f"Ошибка при парсинге Paysera PDF: {e}")
        
        return transactions
    
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