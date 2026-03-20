import pandas as pd
import os

class DictionaryLoader:
    def __init__(self):
        self.base_path = os.path.dirname(__file__)
        self.directions = self.load_directions()
        self.accounts = self.load_accounts()
        self.articles = self.load_articles()
    
    def load_directions(self):
        """Загрузка справочника направлений"""
        file_path = os.path.join(self.base_path, 'Справочник направлений_для_агента.xlsx')
        try:
            df = pd.read_excel(file_path, sheet_name='Для_агента')
            directions = {}
            for _, row in df.iterrows():
                if pd.notna(row['Направление']):
                    direction = row['Направление']
                    subdirection = row['Субнаправление'] if pd.notna(row['Субнаправление']) else None
                    
                    if direction not in directions:
                        directions[direction] = []
                    
                    if subdirection and subdirection != direction:
                        directions[direction].append(subdirection)
            return directions
        except Exception as e:
            print(f"Ошибка загрузки направлений: {e}")
            return {}
    
    def load_accounts(self):
        """Загрузка справочника банковских счетов"""
        file_path = os.path.join(self.base_path, 'Справочник банковских счетов_для_агента.xlsx')
        try:
            df = pd.read_excel(file_path, sheet_name='Для_агента')
            accounts = []
            for _, row in df.iterrows():
                if pd.notna(row['Название']):
                    account = {
                        'name': row['Название'],
                        'number': str(row['Номер']) if pd.notna(row['Номер']) else '',
                        'currency': row['Валюта'] if pd.notna(row['Валюта']) else '',
                        'direction': row['Направление'] if pd.notna(row['Направление']) else '',
                        'subdirection': row['Субнаправление (Объект аренды)'] if pd.notna(row['Субнаправление (Объект аренды)']) else ''
                    }
                    accounts.append(account)
            return accounts
        except Exception as e:
            print(f"Ошибка загрузки счетов: {e}")
            return []
    
    def load_articles(self):
        """Загрузка справочника статей"""
        file_path = os.path.join(self.base_path, 'Справочник статей_для_агента.xlsx')
        try:
            df = pd.read_excel(file_path, sheet_name='Для_агента')
            articles = []
            for _, row in df.iterrows():
                if pd.notna(row['Группа статей']):
                    article = {
                        'group': row['Группа статей'],
                        'name': row['Название родительской статьи'] if pd.notna(row['Название родительской статьи']) else '',
                        'subarticle': row['Название субстатьи'] if pd.notna(row['Название субстатьи']) else None,
                    }
                    articles.append(article)
            return articles
        except Exception as e:
            print(f"Ошибка загрузки статей: {e}")
            return []

# Создаем глобальный экземпляр
dictionaries = DictionaryLoader()