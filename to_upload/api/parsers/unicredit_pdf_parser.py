import re
from .base_pdf_parser import BasePDFParser
from .finclassifier import FinClassifier

class UniCreditPDFParser(BasePDFParser):
    """
    Парсер для PDF выписок UniCredit (чешский формат)
    """
    
    def __init__(self):
        super().__init__()
        self.bank_name = "UniCredit"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит PDF выписку UniCredit
        """
        # Извлекаем текст из PDF
        text = self.extract_text_from_pdf(file_path)
        if not text:
            return []
        
        transactions = []
        
        # Разбиваем на строки
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ищем строки с датой (формат ДД.ММ.ГГГГ)
            if re.search(r'\d{2}\.\d{2}\.\d{4}', line):
                # Проверяем, содержит ли строка признаки транзакции
                if any(keyword in line for keyword in ['POPLATEK', 'TUZEMSKÁ', 'TRVALÝ', 'PŘÍCHOZÍ', 'úrok', 'účet']):
                    transaction = self._parse_transaction_line(line)
                    if transaction:
                        transactions.append(transaction)
            i += 1
        
        return transactions
    
    def _parse_transaction_line(self, line):
        """
        Парсит строку транзакции UniCredit
        """
        try:
            # Ищем дату (формат: 02.01.2026)
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', line)
            if not date_match:
                return None
            
            date_str = date_match.group(1)
            date = f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"
            
            # Ищем сумму (формат: -5.613,00 или +44,98 или просто число)
            # Сначала ищем числа с разделителями
            amount_pattern = r'([-+]?\s*\d+[.,]?\d*[.,]?\d*)'
            amounts = re.findall(amount_pattern, line)
            
            amount = 0
            for a in amounts:
                # Очищаем от пробелов и заменяем запятую на точку
                clean_a = a.replace(' ', '').replace(',', '.').replace('+', '')
                try:
                    val = float(clean_a)
                    # Выбираем наибольшее число (обычно это сумма транзакции)
                    if abs(val) > abs(amount):
                        amount = val
                except:
                    continue
            
            if amount == 0:
                return None
            
            # Определяем тип транзакции
            transaction_type = 'unknown'
            if 'POPLATEK' in line:
                transaction_type = 'fee'
            elif 'PŘÍCHOZÍ' in line or 'příchozí' in line.lower():
                transaction_type = 'incoming'
            elif 'TRVALÝ' in line:
                transaction_type = 'standing_order'
            elif 'úrok' in line.lower():
                transaction_type = 'interest'
            
            # Определяем статью
            article_code = None
            if transaction_type == 'fee':
                article_code = '1.2.17 РКО'
            elif transaction_type == 'interest':
                article_code = '1.1.2.4 Прочие мелкие поступления'
            
            return {
                'date': date,
                'amount': -amount if 'POPLATEK' in line or 'TRVALÝ' in line else amount,
                'currency': 'CZK',
                'description': line.strip(),
                'bank': self.bank_name,
                'article_code': article_code,
                'type': transaction_type
            }
            
        except Exception as e:
            print(f"Ошибка парсинга строки UniCredit: {e}")
            return None
    
    def determine_direction(self, transaction, dictionaries):
        """
        Определяет направление
        """
        desc_lower = transaction['description'].lower()
        
        if 'karlovy' in desc_lower or 'karlš' in desc_lower or 'karlovy vary' in desc_lower:
            return 'Europe', None
        elif 'praha' in desc_lower or 'prague' in desc_lower:
            return 'Europe', None
        else:
            return 'Europe', None
    
    def enrich_transaction(self, transaction):
        """
        Обогащает транзакцию
        """
        return transaction