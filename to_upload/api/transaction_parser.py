import re
from datetime import datetime
from data.load_dictionaries import dictionaries

class TransactionParser:
    def __init__(self):
        self.dictionaries = dictionaries
    
    def parse_transactions(self, text_content, filename):
        """
        Парсит текст выписки и извлекает транзакции
        """
        transactions = []
        
        # ТЕСТОВЫЕ ДАННЫЕ - для демонстрации работы
        # В реальности здесь будет парсинг вашего файла
        test_transactions = [
            {
                'date': '2024-01-15',
                'amount': 1500.50,
                'currency': 'EUR',
                'description': 'Арендная плата от Oleg SIA за январь',
                'bank': self._get_bank_name(filename),
                'article': '1.1.1 Поступления за аренду',
                'direction': 'Latvia',
                'subdirection': 'M81 - Matisa 81'
            },
            {
                'date': '2024-01-14',
                'amount': -45.30,
                'currency': 'EUR',
                'description': 'Rimi Supermarket продукты',
                'bank': self._get_bank_name(filename),
                'article': '1.2.1.1 Хоз.принадлежности',
                'direction': 'Latvia',
                'subdirection': 'AN14_Antonijas14'
            },
            {
                'date': '2024-01-13',
                'amount': -120.00,
                'currency': 'EUR',
                'description': 'Коммунальные платежи электричество',
                'bank': self._get_bank_name(filename),
                'article': '1.2.10 Коммунальные платежи',
                'direction': 'Latvia',
                'subdirection': 'M81 - Matisa 81'
            },
            {
                'date': '2024-01-12',
                'amount': -250.00,
                'currency': 'EUR',
                'description': 'Зарплата сотрудникам',
                'bank': self._get_bank_name(filename),
                'article': '1.2.15.1 Зарплата',
                'direction': 'UK Estate',
                'subdirection': ''
            },
            {
                'date': '2024-01-10',
                'amount': 5000.00,
                'currency': 'EUR',
                'description': 'Поступление от собственника',
                'bank': self._get_bank_name(filename),
                'article': '1.1.5 Флиппинг. Поступления от Собственников',
                'direction': 'Unelma',
                'subdirection': 'UK_Unelma'
            },
            {
                'date': '2024-01-08',
                'amount': -89.90,
                'currency': 'EUR',
                'description': 'Ресторан LIDO обед',
                'bank': self._get_bank_name(filename),
                'article': '1.2.1.1 Хоз.принадлежности',
                'direction': 'Latvia',
                'subdirection': 'AN14_Antonijas14'
            },
            {
                'date': '2024-01-05',
                'amount': -350.00,
                'currency': 'EUR',
                'description': 'Налог на недвижимость',
                'bank': self._get_bank_name(filename),
                'article': '1.2.16.1 Налог на недвижимость',
                'direction': 'Europe',
                'subdirection': 'TGM20-Masaryka20'
            },
            {
                'date': '2024-01-03',
                'amount': -75.50,
                'currency': 'EUR',
                'description': 'Мобильная связь Tele2',
                'bank': self._get_bank_name(filename),
                'article': '1.2.5.5 Связь и интернет персонал',
                'direction': 'UK Estate',
                'subdirection': ''
            },
        ]
        
        return test_transactions
    
    def _parse_date(self, date_str):
        """Парсит дату из разных форматов"""
        formats = [
            '%d.%m.%Y', '%d.%m.%y',  # 31.12.2023, 31.12.23
            '%d/%m/%Y', '%d/%m/%y',  # 31/12/2023, 31/12/23
            '%Y-%m-%d',              # 2023-12-31
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except:
                continue
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _get_bank_name(self, filename):
        """Определяет банк по имени файла"""
        filename_lower = filename.lower()
        if 'sber' in filename_lower or 'сбер' in filename_lower:
            return 'Сбербанк'
        elif 'tinkoff' in filename_lower or 'тиньк' in filename_lower:
            return 'Тинькофф'
        elif 'vtb' in filename_lower or 'втб' in filename_lower:
            return 'ВТБ'
        elif 'alfa' in filename_lower or 'альфа' in filename_lower:
            return 'Альфа-Банк'
        elif 'raiff' in filename_lower or 'райфф' in filename_lower:
            return 'Райффайзенбанк'
        else:
            # Ищем по справочнику счетов
            for account in self.dictionaries.accounts:
                if account['name'].lower() in filename_lower:
                    return account['name']
            return 'Неизвестный банк'
    
    def _determine_article(self, description):
        """Определяет статью по описанию операции используя справочник"""
        description_lower = description.lower()
        
        # Ищем соответствие в справочнике статей
        for article in self.dictionaries.articles:
            if article['name'] and article['name'].lower() in description_lower:
                return article['name']
        
        # Если не нашли, возвращаем статью по умолчанию
        if any(word in description_lower for word in ['аренд', 'rent']):
            return '1.1.1 Поступления за аренду'
        elif any(word in description_lower for word in ['коммун', 'electricity', 'water', 'газ']):
            return '1.2.10 Коммунальные платежи'
        elif any(word in description_lower for word in ['продукт', 'food', 'rimi', 'maxima']):
            return '1.2.1.1 Хоз.принадлежности'
        elif any(word in description_lower for word in ['зарплат', 'salary']):
            return '1.2.15.1 Зарплата'
        elif any(word in description_lower for word in ['налог', 'tax']):
            return '1.2.16 Налоги'
        else:
            return '1.2.33 Непредвиденные расходы'
    
    def _determine_direction(self, description, article):
        """Определяет направление и субнаправление"""
        description_lower = description.lower()
        
        # По умолчанию
        direction = 'Latvia'
        subdirection = 'M81 - Matisa 81'
        
        # Ищем по справочнику направлений
        for dir_name, subdirs in self.dictionaries.directions.items():
            for subdir in subdirs:
                if subdir and subdir.lower() in description_lower:
                    return dir_name, subdir
        
        # Ищем по справочнику счетов
        for account in self.dictionaries.accounts:
            if account['direction'] and account['direction'] in description:
                direction = account['direction']
                subdirection = account['subdirection'] if account['subdirection'] else direction
                return direction, subdirection
        
        return direction, subdirection