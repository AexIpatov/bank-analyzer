import pandas as pd
import os
import re
import json
from datetime import datetime
from collections import defaultdict

def extract_keywords(text):
    """Извлекает ключевые слова из текста"""
    if not text:
        return []
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\d+', '', text)
    
    words = text.lower().split()
    words = [w for w in words if len(w) > 2 and not w.isdigit()]
    
    bigrams = []
    for i in range(len(words)-1):
        bigrams.append(f"{words[i]} {words[i+1]}")
    
    return words + bigrams

def train_classifier():
    """
    Обучает классификатор на основе эталонных данных из Финтабло
    """
    print("="*60)
    print("🚀 ОБУЧЕНИЕ КЛАССИФИКАТОРА (УЛУЧШЕННАЯ ВЕРСИЯ)")
    print("="*60)
    
    # Путь к файлу с эталонной разноской
    training_file = r"C:\Users\Александр\Desktop\bank-analyzer\training_data\Деньги-операции - 20.03.2026.xlsx"
    
    try:
        # Читаем эталонный файл
        print("\n📖 Чтение эталонного файла...")
        df = pd.read_excel(training_file, sheet_name='Деньги-операции')
        print(f"   Найдено записей: {len(df)}")
        
        # Собираем обучающие данные
        training_data = {
            'description_to_article': {},
            'description_to_direction': {},
            'description_to_subdirection': {},
            'bank_to_account': {}
        }
        
        # Для извлечения ключевых слов
        keywords_to_article = defaultdict(lambda: defaultdict(int))
        keywords_to_direction = defaultdict(lambda: defaultdict(int))
        
        print("\n🔍 Анализ эталонных данных...")
        
        for _, row in df.iterrows():
            # Описание операции
            description = str(row.get('Описание', '')).strip()
            if not description or pd.isna(description) or description == 'nan' or description == '':
                continue
            
            # Очищаем описание от лишних символов
            clean_desc = re.sub(r'\s+', ' ', description)
            clean_desc = clean_desc.strip()
            
            # Статья
            article = str(row.get('Статья', '')).strip()
            if article and article != 'nan':
                training_data['description_to_article'][clean_desc] = article
                # Извлекаем ключевые слова
                words = extract_keywords(clean_desc)
                for word in words:
                    keywords_to_article[word][article] += 1
            
            # Направление
            direction = str(row.get('Направление', '')).strip()
            if direction and direction != 'nan':
                training_data['description_to_direction'][clean_desc] = direction
                words = extract_keywords(clean_desc)
                for word in words:
                    keywords_to_direction[word][direction] += 1
            
            # Субнаправление
            subdirection = str(row.get('Субнаправление', '')).strip()
            if subdirection and subdirection != 'nan':
                training_data['description_to_subdirection'][clean_desc] = subdirection
            
            # Банк/Счет
            account = str(row.get('Счет', '')).strip()
            if account and account != 'nan':
                training_data['bank_to_account'][clean_desc] = account
        
        # ДОБАВЛЯЕМ ВРУЧНУЮ НЕДОСТАЮЩИЕ ПРИМЕРЫ
        manual_examples = [
            # Такси и транспорт (командировочные расходы)
            ("Cars Taxi", "1.2.2 Командировочные расходы", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("Careem", "1.2.2 Командировочные расходы", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("Uber", "1.2.2 Командировочные расходы", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("taxi", "1.2.2 Командировочные расходы", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("Dubai Taxi", "1.2.2 Командировочные расходы", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("Parkonic", "1.2.2 Командировочные расходы", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("Flydubai", "1.2.2 Командировочные расходы", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            
            # IT сервисы (правильные)
            ("Google One", "1.2.9.3 IT сервисы", "UK Estate", None),
            ("Openai *Chatgpt", "1.2.9.3 IT сервисы", "UK Estate", None),
            ("Lovable LOVABLE.DEV", "1.2.9.3 IT сервисы", "UK Estate", None),
            ("Lovable", "1.2.9.3 IT сервисы", "UK Estate", None),
            ("Adobe", "1.2.9.3 IT сервисы", "UK Estate", None),
            ("Albato", "1.2.9.3 IT сервисы", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("Asana com", "1.2.9.3 IT сервисы", "Nomiqa", "DNQ_Dubai-Nomiqa"),
            ("Chatgpt", "1.2.9.3 IT сервисы", "UK Estate", None),
            ("Openai", "1.2.9.3 IT сервисы", "UK Estate", None),
            
            # Коммунальные платежи
            ("RIGAS UDENS", "1.2.10.3 Вода", "Latvia", None),
            ("Rīgas Ūdens", "1.2.10.3 Вода", "Latvia", None),
            ("LATVENERGO", "1.2.10.5 Электричество", "Latvia", None),
            ("Clean R", "1.2.10.1 Мусор", "Latvia", None),
            ("Eco Baltia", "1.2.10.1 Мусор", "Latvia", None),
            ("BITE LATVIJA", "1.2.9.1 Связь , интернет, TV", "Latvia", None),
            ("TELE2", "1.2.9.1 Связь , интернет, TV", "Latvia", None),
            
            # Аренда
            ("Money added from", "1.1.1.3 Арендная плата (счёт)", "Latvia", None),
            ("Rent", "1.1.1.3 Арендная плата (счёт)", "Latvia", None),
            ("ire", "1.1.1.3 Арендная плата (счёт)", "Latvia", None),
            
            # Комиссии
            ("Charge for", "1.2.17 РКО", "Nomiqa", None),
            ("Fee", "1.2.17 РКО", "Nomiqa", None),
            ("Komisijas maksa", "1.2.17 РКО", "Latvia", None),
            ("Commission", "1.2.17 РКО", "Nomiqa", None),
            
            # Реклама
            ("FACEBK", "1.2.3 Оплата рекламных систем (бюджет)", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("Facebook", "1.2.3 Оплата рекламных систем (бюджет)", "Nomiqa", "BNQ_BAKU-Nomiqa"),
            ("Instagram", "1.2.3 Оплата рекламных систем (бюджет)", "Nomiqa", "BNQ_BAKU-Nomiqa"),
        ]
        
        print(f"\n📝 Добавляем вручную {len(manual_examples)} примеров...")
        
        for desc, article, direction, subdirection in manual_examples:
            clean_desc = desc.strip()
            training_data['description_to_article'][clean_desc] = article
            if direction:
                training_data['description_to_direction'][clean_desc] = direction
            if subdirection:
                training_data['description_to_subdirection'][clean_desc] = subdirection
            
            # Добавляем ключевые слова
            words = extract_keywords(clean_desc)
            for word in words:
                keywords_to_article[word][article] += 1
                if direction:
                    keywords_to_direction[word][direction] += 1
        
        print(f"\n📊 Собрано обучающих примеров:")
        print(f"   Статьи: {len(training_data['description_to_article'])}")
        print(f"   Направления: {len(training_data['description_to_direction'])}")
        print(f"   Субнаправления: {len(training_data['description_to_subdirection'])}")
        print(f"   Ключевых слов для статей: {len(keywords_to_article)}")
        print(f"   Ключевых слов для направлений: {len(keywords_to_direction)}")
        
        # Сохраняем обученные данные
        output_file = r"C:\Users\Александр\Desktop\bank-analyzer\api\training_data.json"
        
        # Преобразуем ключевые слова для сохранения
        keywords_article_serializable = {}
        for word, articles in keywords_to_article.items():
            keywords_article_serializable[word] = dict(articles)
        
        keywords_direction_serializable = {}
        for word, directions in keywords_to_direction.items():
            keywords_direction_serializable[word] = dict(directions)
        
        output_data = {
            'description_to_article': training_data['description_to_article'],
            'description_to_direction': training_data['description_to_direction'],
            'description_to_subdirection': training_data['description_to_subdirection'],
            'bank_to_account': training_data['bank_to_account'],
            'keywords_to_article': keywords_article_serializable,
            'keywords_to_direction': keywords_direction_serializable
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Обученные данные сохранены в: {output_file}")
        
        # Статистика по статьям
        print("\n📈 Статистика по статьям (топ-15):")
        articles = {}
        for desc, article in training_data['description_to_article'].items():
            if article not in articles:
                articles[article] = 0
            articles[article] += 1
        
        sorted_articles = sorted(articles.items(), key=lambda x: x[1], reverse=True)[:15]
        for article, count in sorted_articles:
            print(f"   {article}: {count} примеров")
        
        return training_data
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    train_classifier()