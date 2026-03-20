import re
from .base_pdf_parser import BasePDFParser
from .finclassifier import FinClassifier

class N26PDFParser(BasePDFParser):
    """
    Парсер для PDF выписок N26 (испанский формат)
    """
    
    def __init__(self):
        super().__init__()
        self.bank_name = "N26"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит PDF выписку N26
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
            
            # Ищем строки с датой в формате ДД.ММ.ГГГГ
            if re.search(r'\d{2}\.\d{2}\.\d{4}', line):
                # Проверяем наличие суммы с €
                if '€' in line or 'EUR' in line:
                    transaction = self._parse_transaction(lines, i)
                    if transaction:
                        transactions.append(transaction)
                        # Пропускаем обработанные строки
                        i += transaction.get('lines_used', 1)
                        continue
            i += 1
        
        return transactions
    
    def _parse_transaction(self, lines, start_idx):
        """
        Парсит транзакцию, которая может занимать несколько строк
        """
        try:
            line = lines[start_idx].strip()
            
            # Ищем дату
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', line)
            if not date_match:
                return None
            
            date_str = date_match.group(1)
            date = f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}"
            
            # Собираем описание из текущей и следующих строк
            description = line.replace(date_str, '').strip()
            lines_used = 1
            
            # Проверяем следующие строки на наличие суммы
            amount = None
            amount_line_idx = start_idx
            
            # Ищем строку с суммой (может быть на той же строке или на следующих)
            for j in range(5):  # проверяем до 5 строк вперед
                check_idx = start_idx + j
                if check_idx >= len(lines):
                    break
                
                check_line = lines[check_idx].strip()
                
                # Ищем сумму с €
                amount_match = re.search(r'([+-]?\s*\d+[.,]?\d*[.,]?\d*)\s*[€]', check_line)
                if amount_match:
                    amount_str = amount_match.group(1).replace('.', '').replace(',', '.').replace('+', '').strip()
                    try:
                        amount = float(amount_str)
                        # Определяем знак
                        if '-' in amount_match.group(0) or 'Debe' in check_line or 'pago' in check_line.lower():
                            amount = -amount
                        amount_line_idx = check_idx
                        lines_used = j + 1
                        break
                    except:
                        continue
                
                # Если это не строка с суммой, добавляем к описанию
                if j > 0 and not re.search(r'\d{2}\.\d{2}\.\d{4}', check_line):
                    description += " " + check_line
            
            if amount is None:
                return None
            
            # Очищаем описание
            description = re.sub(r'\s+', ' ', description).strip()
            
            # Определяем тип транзакции
            transaction_type = 'unknown'
            if amount > 0 or 'Ingresos' in description:
                transaction_type = 'income'
            elif 'Mastercard' in description or 'Tarjeta' in description:
                transaction_type = 'card_payment'
            elif 'comisión' in description.lower() or 'fee' in description.lower():
                transaction_type = 'fee'
            
            # Определяем статью
            article_code = self._extract_article_code(description, transaction_type)
            
            return {
                'date': date,
                'amount': amount,
                'currency': 'EUR',
                'description': description,
                'bank': self.bank_name,
                'article_code': article_code,
                'type': transaction_type,
                'lines_used': lines_used
            }
            
        except Exception as e:
            print(f"Ошибка парсинга транзакции N26: {e}")
            return None
    
    def _extract_article_code(self, description, transaction_type):
        """
        Извлекает код статьи из описания
        """
        if not description:
            return None
        
        desc_lower = description.lower()
        
        # По ключевым словам
        if 'air india' in desc_lower or 'transport' in desc_lower or 'vuelo' in desc_lower or 'fly' in desc_lower:
            return '1.2.2 Командировочные расходы'
        elif 'booking.com' in desc_lower or 'hotel' in desc_lower or 'alojamiento' in desc_lower:
            return '1.2.2 Командировочные расходы'
        elif 'metal membership' in desc_lower or 'cuota' in desc_lower:
            return '1.2.17 РКО'
        elif 'instant savings' in desc_lower or 'ahorro' in desc_lower:
            return 'Перевод между счетами'
        elif 'supermercado' in desc_lower or 'supermarket' in desc_lower:
            return '1.2.1.1 Бытовое оборудование, инвентарь'
        elif 'flixbus' in desc_lower:
            return '1.2.2 Командировочные расходы'
        elif 'google' in desc_lower:
            return '1.2.9.3 IT сервисы'
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """
        Определяет направление
        """
        desc_lower = transaction['description'].lower()
        
        if 'malaga' in desc_lower or 'spain' in desc_lower or 'españa' in desc_lower:
            return 'UK Estate', None
        elif 'booking' in desc_lower or 'hotel' in desc_lower:
            return 'UK Estate', None
        else:
            return 'UK Estate', None
    
    def enrich_transaction(self, transaction):
        """
        Обогащает транзакцию
        """
        return transaction