import pandas as pd
import re
import json
from collections import defaultdict
import os

class FinClassifier:
    def __init__(self):
        # Путь к обученным данным
        self.training_data_path = r"C:\Users\Александр\Desktop\bank-analyzer\api\training_data.json"
        
        # Загружаем обученные данные
        self._load_training_data()
    
    def _load_training_data(self):
        """Загружает обученные данные из JSON файла"""
        try:
            if os.path.exists(self.training_data_path):
                with open(self.training_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.description_to_article = data.get('description_to_article', {})
                self.description_to_direction = data.get('description_to_direction', {})
                self.description_to_subdirection = data.get('description_to_subdirection', {})
                self.keywords_to_article = data.get('keywords_to_article', {})
                self.keywords_to_direction = data.get('keywords_to_direction', {})
                
                print(f"✅ Загружено обученных данных:")
                print(f"   Статьи: {len(self.description_to_article)}")
                print(f"   Ключевых слов для статей: {len(self.keywords_to_article)}")
                print(f"   Ключевых слов для направлений: {len(self.keywords_to_direction)}")
            else:
                print(f"⚠️ Файл обучения не найден: {self.training_data_path}")
                self._init_empty()
        except Exception as e:
            print(f"⚠️ Ошибка загрузки обученных данных: {e}")
            self._init_empty()
    
    def _init_empty(self):
        """Инициализирует пустые данные"""
        self.description_to_article = {}
        self.description_to_direction = {}
        self.description_to_subdirection = {}
        self.keywords_to_article = {}
        self.keywords_to_direction = {}
    
    def _extract_keywords(self, text):
        """Извлекает ключевые слова из текста"""
        if not text:
            return []
        # Очищаем текст
        text = re.sub(r'[^\w\s-]', ' ', text)
        text = re.sub(r'\d+', '', text)
        
        words = text.lower().split()
        words = [w for w in words if len(w) > 2 and not w.isdigit()]
        
        # Добавляем биграммы (пары слов)
        bigrams = []
        for i in range(len(words)-1):
            bigrams.append(f"{words[i]} {words[i+1]}")
        
        return words + bigrams
    
    def classify_article(self, description):
        """
        Определяет статью по описанию операции
        """
        if not description:
            return None
        
        # 1. Ищем точное совпадение описания
        if description in self.description_to_article:
            return self.description_to_article[description]
        
        # 2. Ищем частичное совпадение
        desc_lower = description.lower()
        for known_desc, article in self.description_to_article.items():
            if known_desc.lower() in desc_lower or desc_lower in known_desc.lower():
                return article
        
        # 3. Ищем по ключевым словам
        words = self._extract_keywords(description)
        
        # Собираем кандидатов по ключевым словам
        candidates = defaultdict(int)
        for word in words:
            if word in self.keywords_to_article:
                for article, count in self.keywords_to_article[word].items():
                    candidates[article] += count
        
        if candidates:
            # Возвращаем наиболее вероятную статью
            best_article = max(candidates.items(), key=lambda x: x[1])[0]
            return best_article
        
        # 4. Если ничего не нашли, используем простые ключевые слова
        desc_lower = description.lower()
        
        if 'rent' in desc_lower or 'аренд' in desc_lower or 'apmaksa' in desc_lower:
            return '1.1.1.3 Арендная плата (счёт)'
        elif 'fee' in desc_lower or 'комиссия' in desc_lower or 'komisijas' in desc_lower:
            return '1.2.17 РКО'
        elif 'salary' in desc_lower or 'зарплат' in desc_lower or 'darba alga' in desc_lower:
            return '1.2.15.1 Зарплата'
        elif 'tax' in desc_lower or 'налог' in desc_lower or 'nodokļu' in desc_lower:
            return '1.2.16 Налоги'
        elif 'electricity' in desc_lower or 'latvenergo' in desc_lower or 'электричеств' in desc_lower:
            return '1.2.10.5 Электричество'
        elif 'water' in desc_lower or 'ūdens' in desc_lower or 'вода' in desc_lower:
            return '1.2.10.3 Вода'
        elif 'internet' in desc_lower or 'связь' in desc_lower:
            return '1.2.9.1 Связь , интернет, TV'
        elif 'google' in desc_lower or 'openai' in desc_lower:
            return '1.2.9.3 IT сервисы'
        elif 'facebook' in desc_lower or 'facbk' in desc_lower or 'реклам' in desc_lower:
            return '1.2.3 Оплата рекламных систем (бюджет)'
        
        return None
    
    def classify_direction(self, description):
        """
        Определяет направление по описанию операции
        """
        if not description:
            return None, None
        
        # 1. Ищем точное совпадение
        if description in self.description_to_direction:
            direction = self.description_to_direction[description]
            subdirection = self.description_to_subdirection.get(description)
            return direction, subdirection
        
        # 2. Ищем частичное совпадение
        desc_lower = description.lower()
        for known_desc, direction in self.description_to_direction.items():
            if known_desc.lower() in desc_lower or desc_lower in known_desc.lower():
                subdirection = self.description_to_subdirection.get(known_desc)
                return direction, subdirection
        
        # 3. Ищем по ключевым словам
        words = self._extract_keywords(description)
        
        # Собираем кандидатов для направления
        dir_candidates = defaultdict(int)
        subdir_candidates = defaultdict(int)
        
        for word in words:
            if word in self.keywords_to_direction:
                for direction, count in self.keywords_to_direction[word].items():
                    dir_candidates[direction] += count
        
        direction = None
        subdirection = None
        
        if dir_candidates:
            direction = max(dir_candidates.items(), key=lambda x: x[1])[0]
        
        # 4. По простым ключевым словам
        if not direction:
            desc_lower = description.lower()
            
            if 'latvia' in desc_lower or 'riga' in desc_lower or 'lv' in desc_lower:
                direction = 'Latvia'
            elif 'europe' in desc_lower or 'czech' in desc_lower or 'praha' in desc_lower:
                direction = 'Europe'
            elif 'nomiqa' in desc_lower or 'dubai' in desc_lower or 'baku' in desc_lower:
                direction = 'Nomiqa'
            elif 'east' in desc_lower or 'азербайджан' in desc_lower:
                direction = 'East-Восток'
            elif 'uk' in desc_lower or 'estate' in desc_lower:
                direction = 'UK Estate'
        
        return direction, subdirection
    
    def get_article_info(self, article_code):
        """Возвращает информацию о статье"""
        return None
    
    def get_direction_info(self, direction_name):
        """Возвращает информацию о направлении"""
        return None
    
    def print_stats(self):
        """Печатает статистику"""
        print(f"Загружено обучающих данных:")
        print(f"  Статьи: {len(self.description_to_article)}")
        print(f"  Ключевых слов для статей: {len(self.keywords_to_article)}")