import fitz  # PyMuPDF
import re
from .base_pdf_parser import BasePDFParser
from .finclassifier import FinClassifier

class N26PyMuPDFParser(BasePDFParser):
    """
    Парсер для PDF выписок N26 с использованием PyMuPDF
    """
    
    def __init__(self):
        super().__init__()
        self.bank_name = "N26"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит PDF выписку N26 используя PyMuPDF
        """
        transactions = []
        
        try:
            # Открываем PDF
            doc = fitz.open(file_path)
            
            full_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                full_text += f"\n--- Страница {page_num+1} ---\n{text}\n"
                
                # Парсим транзакции со страницы
                page_transactions = self._parse_text(text)
                transactions.extend(page_transactions)
            
            # Сохраняем для отладки
            with open("n26_pymupdf_output.txt", "w", encoding="utf-8") as f:
                f.write(full_text)
            
            doc.close()
            
        except Exception as e:
            print(f"Ошибка PyMuPDF: {e}")
        
        return transactions
    
    def _parse_text(self, text):
        """
        Парсит текст, извлеченный PyMuPDF
        """
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Пропускаем пустые строки
            if not line:
                i += 1
                continue
            
            # Ищем дату в формате ДД.ММ.ГГГГ
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', line)
            if not date_match:
                i += 1
                continue
            
            date_str = date_match.group(1)
            
            # Ищем сумму с €
            amount_match = re.search(r'([+-]?\s*\d+[.,]?\d*[.,]?\d*)\s*[€]', line)
            
            # Если не нашли в текущей строке, смотрим следующую
            if not amount_match and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                combined = line + " " + next_line
                amount_match = re.search(r'([+-]?\s*\d+[.,]?\d*[.,]?\d*)\s*[€]', combined)
                if amount_match:
                    line = combined
                    i += 1
            
            if not amount_match:
                i += 1
                continue
            
            try:
                amount_str = amount_match.group(1).replace('.', '').replace(',', '.').replace('+', '').strip()
                amount = float(amount_str)
                
                # Определяем знак (если есть минус)
                if '-' in amount_match.group(0) or 'pago' in line.lower() or 'debe' in line.lower():
                    amount = -amount
                
                # Описание (всё между датой и суммой)
                desc_start = line.find(date_str) + len(date_str)
                desc_end = line.find(amount_match.group(0))
                if desc_end > desc_start:
                    description = line[desc_start:desc_end].strip()
                else:
                    description = line.replace(date_str, '').replace(amount_match.group(0), '').strip()
                
                description = re.sub(r'\s+', ' ', description)
                
                # Определяем статью
                article_code = self._extract_article_code(description)
                
                transactions.append({
                    'date': f"{date_str[6:10]}-{date_str[3:5]}-{date_str[0:2]}",
                    'amount': amount,
                    'currency': 'EUR',
                    'description': description,
                    'bank': self.bank_name,
                    'article_code': article_code,
                    'type': 'expense' if amount < 0 else 'income'
                })
                
            except Exception as e:
                print(f"Ошибка парсинга строки: {e}")
            
            i += 1
        
        return transactions
    
    def _extract_article_code(self, description):
        """
        Извлекает код статьи из описания
        """
        if not description:
            return None
        
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['air india', 'transport', 'vuelo', 'fly', 'flixbus', 'hotel', 'booking']):
            return '1.2.2 Командировочные расходы'
        elif any(word in desc_lower for word in ['metal membership', 'cuota', 'fee', 'comisión']):
            return '1.2.17 РКО'
        elif any(word in desc_lower for word in ['google', 'openai', 'chatgpt', 'adobe', 'lovable']):
            return '1.2.9.3 IT сервисы'
        elif any(word in desc_lower for word in ['supermercado', 'supermarket', 'mercado']):
            return '1.2.1.1 Бытовое оборудование, инвентарь'
        elif any(word in desc_lower for word in ['instant savings', 'ahorro', 'transfer', 'ingresos']):
            return 'Перевод между счетами'
        
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