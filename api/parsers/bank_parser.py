import os
from .universal_parser import UniversalParser
from .revolut_parser import RevolutParser
from .industra_parser import IndustraParser
from .pasha_parser import PashaParser
from .kapital_parser import KapitalParser
from .mashreq_parser import MashreqParser
from .n26_excel_parser import N26ExcelParser
from .unicredit_csv_parser import UniCreditCSVParser
from .format_detector import FormatDetector
from data.load_dictionaries import dictionaries
from .finclassifier import FinClassifier

class BankParser:
    def __init__(self):
        # Универсальный парсер для CSV и Excel
        self.universal_parser = UniversalParser()
        
        # Специализированные парсеры для сложных форматов CSV/Excel
        self.special_parsers = {
            'revolut': RevolutParser(),
            'industra': IndustraParser(),
            'pasha_azn': PashaParser(),
            'pasha_aed': PashaParser(),
            'kapital': KapitalParser(),
            'mashreq': MashreqParser(),
            'n26_excel': N26ExcelParser(),
            'unicredit_csv': UniCreditCSVParser(),
        }
        
        # Определитель формата
        self.format_detector = FormatDetector()
        
        self.dictionaries = dictionaries
        self.classifier = FinClassifier()
    
    def identify_bank(self, filename, file_path):
        """
        Определяет банк по имени файла
        """
        filename_lower = filename.lower()
        
        # Проверяем, что файл не PDF
        if filename_lower.endswith('.pdf'):
            print(f"⚠️ PDF файлы не поддерживаются: {filename}")
            return None, None
        
        # UniCredit CSV
        if ('unicredit' in filename_lower or 'garpiz' in filename_lower or 
            'koruna' in filename_lower or 'twohills' in filename_lower or 
            'molly' in filename_lower) and filename_lower.endswith('.csv'):
            return 'unicredit_csv', 'special'
        
        # Проверяем специализированные парсеры для CSV/Excel
        if 'n26' in filename_lower and (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls')):
            return 'n26_excel', 'special'
        
        if 'mashreq' in filename_lower:
            return 'mashreq', 'special'
        
        if 'kapital' in filename_lower:
            return 'kapital', 'special'
        
        if 'pasha' in filename_lower or 'bunda' in filename_lower:
            if 'azn' in filename_lower:
                return 'pasha_azn', 'special'
            elif 'aed' in filename_lower or 'дирхам' in filename_lower:
                return 'pasha_aed', 'special'
        
        if 'revolut' in filename_lower:
            return 'revolut', 'special'
        if 'industra' in filename_lower or 'plavas' in filename_lower:
            return 'industra', 'special'
        if 'wise' in filename_lower:
            return 'wise', 'universal'
        if 'budapest' in filename_lower:
            return 'budapest', 'universal'
        if 'csob' in filename_lower or 'dzibik' in filename_lower:
            return 'csob', 'universal'
        
        # Затем пробуем универсальный
        bank_key, config = self.universal_parser.identify_bank(filename)
        if bank_key:
            return bank_key, 'universal'
        
        return None, None
    
    def parse_file(self, file_path, filename):
        """
        Парсит файл используя соответствующий парсер
        """
        # Сначала определяем формат файла
        file_info = self.format_detector.get_file_info(file_path)
        print(f"Формат файла: {file_info['type']}")
        
        # Определяем банк
        bank_key, parser_type = self.identify_bank(filename, file_path)
        
        if not bank_key:
            raise ValueError(f"Неизвестный тип банка или неподдерживаемый формат для файла {filename}")
        
        print(f"Банк: {bank_key}, тип парсера: {parser_type}")
        
        # Выбираем парсер
        if parser_type == 'special' and bank_key in self.special_parsers:
            # Используем специализированный парсер
            parser = self.special_parsers[bank_key]
            transactions = parser.parse(file_path, filename)
            parser_used = f'special_{bank_key}'
        else:
            # Используем универсальный парсер
            transactions = self.universal_parser.parse_file(file_path, filename)
            parser_used = 'universal'
        
        # Обогащаем транзакции
        enriched = self._enrich_transactions(transactions, bank_key, parser_used)
        
        return enriched
    
    def _enrich_transactions(self, transactions, bank_key, parser_used):
        """
        Обогащает транзакции данными
        """
        enriched = []
        
        for t in transactions:
            # Если транзакция уже содержит направление, используем его
            direction = t.get('direction')
            subdirection = t.get('subdirection')
            
            # Если нет, определяем через классификатор
            if not direction:
                dir_result, subdir_result = self.classifier.classify_direction(
                    t.get('description', '')
                )
                direction = dir_result
                subdirection = subdir_result
            
            # Определяем статью если её нет
            article_code = t.get('article_code')
            if not article_code:
                article_code = self.classifier.classify_article(t.get('description', ''))
            
            enriched.append({
                'date': t.get('date', ''),
                'amount': t.get('amount', 0),
                'currency': t.get('currency', 'EUR'),
                'description': t.get('description', ''),
                'bank': t.get('bank', bank_key),
                'article_code': article_code,
                'article_name': self._get_article_name(article_code),
                'direction': direction,
                'subdirection': subdirection,
                'payee': t.get('payee', ''),
                'reference': t.get('reference', ''),
                'type': t.get('type', ''),
                'parser': parser_used
            })
        
        return enriched
    
    def _get_article_name(self, article_code):
        """
        Находит название статьи по коду
        """
        if not article_code:
            return None
        
        article_info = self.classifier.get_article_info(article_code)
        if article_info:
            return article_code
        
        return article_code
    
    def save_to_excel(self, transactions, output_path):
        """
        Сохраняет транзакции в Excel
        """
        import pandas as pd
        
        data = []
        for t in transactions:
            data.append({
                'Дата': t['date'],
                'Сумма': t['amount'],
                'Валюта': t['currency'],
                'Банк': t['bank'],
                'Статья код': t['article_code'],
                'Статья название': t['article_name'],
                'Направление': t['direction'],
                'Субнаправление': t['subdirection'],
                'Описание': t['description'],
                'Контрагент': t.get('payee', ''),
                'Тип': t.get('type', ''),
                'Парсер': t.get('parser', '')
            })
        
        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path
    
    def print_statistics(self, transactions):
        """
        Печатает статистику по транзакциям
        """
        if not transactions:
            print("Нет транзакций")
            return
        
        total_amount = sum(t['amount'] for t in transactions)
        income = sum(t['amount'] for t in transactions if t['amount'] > 0)
        expenses = sum(t['amount'] for t in transactions if t['amount'] < 0)
        
        print(f"\nСтатистика по транзакциям:")
        print(f"  Всего транзакций: {len(transactions)}")
        print(f"  Общая сумма: {total_amount:.2f}")
        print(f"  Доходы: {income:.2f}")
        print(f"  Расходы: {expenses:.2f}")
        
        # Статистика по парсерам
        parsers = {}
        for t in transactions:
            parser = t.get('parser', 'unknown')
            if parser not in parsers:
                parsers[parser] = 0
            parsers[parser] += 1
        
        print("\nИспользованные парсеры:")
        for parser, count in parsers.items():
            print(f"  {parser}: {count} транзакций")