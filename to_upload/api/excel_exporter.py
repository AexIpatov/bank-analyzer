import pandas as pd
from datetime import datetime
import os
from parsers.bank_parser import BankParser
from data.load_dictionaries import dictionaries
from parsers.finclassifier import FinClassifier

class ExcelExporter:
    def __init__(self):
        self.dictionaries = dictionaries
        self.parser = BankParser()
        self.classifier = FinClassifier()  # Добавляем классификатор
    
    def extract_transactions(self, file_content, filename):
        """
        Извлекает транзакции из файла выписки с использованием классификатора
        """
        # Сохраняем временно файл для парсинга
        temp_dir = 'temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, filename)
        with open(temp_path, 'wb') as f:
            f.write(file_content)
        
        try:
            # Парсим файл
            transactions = self.parser.parse_file(temp_path, filename)
            
            # Обогащаем транзакции данными из классификатора
            for t in transactions:
                # Если статья не определена, используем классификатор
                if not t.get('article_code') and not t.get('article_name'):
                    article = self.classifier.classify_article(t.get('description', ''))
                    if article:
                        t['article_code'] = article
                        t['article_name'] = article
                
                # Если направление не определено, используем классификатор
                if not t.get('direction'):
                    direction, subdirection = self.classifier.classify_direction(t.get('description', ''))
                    if direction:
                        t['direction'] = direction
                    if subdirection:
                        t['subdirection'] = subdirection
            
            return transactions
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def parse_file_content(self, file_content, filename):
        """
        Извлекает текст из файла для анализа (для DeepSeek)
        """
        from file_parser import FileParser
        parser = FileParser()
        return parser.parse_file(file_content, filename)
    
    def save_to_excel(self, transactions, output_path):
        """
        Сохраняет транзакции в Excel с использованием классификатора
        """
        data = []
        for t in transactions:
            # Применяем классификатор для недостающих данных
            article_name = t.get('article_name', '')
            if not article_name:
                article = self.classifier.classify_article(t.get('description', ''))
                article_name = article if article else "Требует уточнения!!!"
            
            direction = t.get('direction', '')
            if not direction:
                dir_result, _ = self.classifier.classify_direction(t.get('description', ''))
                direction = dir_result if dir_result else "Требует уточнения!!!"
            
            data.append({
                'Дата': t.get('date', ''),
                'Сумма': t.get('amount', 0),
                'Валюта': t.get('currency', 'EUR'),
                'Счет': t.get('account_name', t.get('bank', '')),
                'Исходный файл': t.get('source_file', ''),
                'Статья код': t.get('article_code', ''),
                'Статья название': article_name,
                'Направление': direction,
                'Субнаправление': t.get('subdirection', ''),
                'Описание': t.get('description', ''),
                'Контрагент': t.get('payee', ''),
                'Тип': t.get('type', ''),
                'Парсер': t.get('parser', '')
            })
        
        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path
    
    def export_to_excel(self, transactions, filename):
        """
        Экспортирует транзакции в Excel (для одного файла)
        """
        # Генерируем имя файла с датой
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'export_{timestamp}.xlsx'
        output_path = os.path.join('exports', output_filename)
        
        # Создаем папку exports если её нет
        os.makedirs('exports', exist_ok=True)
        
        # Сохраняем в Excel
        self.save_to_excel(transactions, output_path)
        
        return output_path