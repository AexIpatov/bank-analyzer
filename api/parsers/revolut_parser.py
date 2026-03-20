import csv
from datetime import datetime
import re
from .finclassifier import FinClassifier

class RevolutParser:
    def __init__(self):
        self.bank_name = "Revolut"
        self.classifier = FinClassifier()
    
    def parse(self, file_path, filename):
        """
        Парсит CSV выписку Revolut и возвращает список транзакций
        """
        transactions = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Пропускаем если нет даты или суммы
                if not row.get('Date completed (UTC)') or not row.get('Amount'):
                    continue
                
                # Определяем тип транзакции и сумму
                amount = float(row['Amount'])
                
                # Извлекаем статью из описания, если есть
                article_code = self._extract_article_code(row['Description'])
                
                transaction = {
                    'date': row['Date completed (UTC)'],
                    'amount': amount,
                    'currency': row.get('Payment currency', 'EUR'),
                    'description': row['Description'],
                    'type': row.get('Type', ''),
                    'bank': self.bank_name,
                    'article_code': article_code,
                    'reference': row.get('Reference', ''),
                    'balance': row.get('Balance', '')
                }
                transactions.append(transaction)
        
        return transactions
    
    def _extract_article_code(self, description):
        """Извлекает код статьи из описания"""
        # Ищем паттерн вида (1.2.10.3)
        match = re.search(r'\((\d+\.\d+\.\d+\.?\d*)\)', description)
        if match:
            return match.group(1)
        
        # Ищем другие паттерны
        patterns = ['1.2.15.1', '1.2.10.1', '1.2.10.3', '1.2.10.5', '1.2.9.1', '1.2.8.1']
        for pattern in patterns:
            if pattern in description:
                return pattern
        
        return None
    
    def determine_direction(self, transaction, dictionaries):
        """Определяет направление по справочнику и классификатору"""
        
        # Сначала пробуем найти по коду статьи
        if transaction.get('article_code'):
            # Ищем в данных Финтабло
            article_info = self.classifier.get_article_info(transaction['article_code'])
            if article_info and article_info['examples']:
                # По примерам пытаемся понять направление
                for example in article_info['examples']:
                    direction, subdirection = self.classifier.classify_direction(example)
                    if direction:
                        return direction, subdirection
        
        # Затем пробуем по описанию
        direction, subdirection = self.classifier.classify_direction(transaction['description'])
        if direction:
            return direction, subdirection
        
        # Если ничего не нашли, возвращаем значения по умолчанию
        return 'Latvia', 'AN14_Antonijas14'
    
    def enrich_transaction(self, transaction):
        """
        Обогащает транзакцию данными из классификатора
        """
        # Определяем статью
        if not transaction.get('article_code'):
            transaction['article_code'] = self.classifier.classify_article(transaction['description'])
        
        # Получаем информацию о статье
        if transaction.get('article_code'):
            article_info = self.classifier.get_article_info(transaction['article_code'])
            if article_info:
                transaction['article_name'] = transaction['article_code']
                transaction['article_examples'] = article_info['examples'][:2]
        
        return transaction