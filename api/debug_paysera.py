import fitz  # PyMuPDF
import os
from parsers.paysera_pdf_parser import PayseraPDFParser

def debug_paysera(file_name):
    print("="*60)
    print(f"ОТЛАДКА PAYSERA PDF: {file_name}")
    print("="*60)
    
    file_path = os.path.join("parsers", file_name)
    
    # 1. Проверяем существование файла
    print(f"\n1. Проверка файла:")
    if os.path.exists(file_path):
        print(f"   ✅ Файл найден: {file_path}")
        print(f"   Размер: {os.path.getsize(file_path)} байт")
    else:
        print(f"   ❌ Файл не найден: {file_path}")
        return
    
    # 2. Пробуем извлечь текст через PyMuPDF
    print(f"\n2. Извлечение текста через PyMuPDF:")
    try:
        doc = fitz.open(file_path)
        print(f"   ✅ PDF открыт, страниц: {len(doc)}")
        
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            all_text += text
            
            print(f"\n   Страница {page_num + 1}:")
            print("-" * 40)
            print(text[:500] + "..." if len(text) > 500 else text)
            print("-" * 40)
            
            # Ищем ключевые слова
            if 'Pārskaitījums' in text:
                print(f"   ✅ Найдено 'Pārskaitījums' на стр. {page_num + 1}")
            if 'Komisijas maksa' in text:
                print(f"   ✅ Найдено 'Komisijas maksa' на стр. {page_num + 1}")
        
        doc.close()
        
        # Сохраняем весь текст
        with open(f"paysera_debug_{file_name.replace('.', '_')}.txt", "w", encoding="utf-8") as f:
            f.write(all_text)
        print(f"\n   ✅ Текст сохранен в файл для анализа")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # 3. Пробуем парсер
    print(f"\n3. Тестирование парсера:")
    try:
        # Определяем тип
        if 'property' in file_name.lower():
            parser = PayseraPDFParser('property')
        elif 'rerum' in file_name.lower():
            parser = PayseraPDFParser('rerum')
        elif 'sveciy' in file_name.lower():
            parser = PayseraPDFParser('sveciy')
        else:
            parser = PayseraPDFParser('property')
        
        transactions = parser.parse(file_path, file_name)
        print(f"   ✅ Парсер вернул {len(transactions)} транзакций")
        
        if transactions:
            print(f"\n   Первые 3 транзакции:")
            for i, t in enumerate(transactions[:3]):
                print(f"\n   Транзакция {i+1}:")
                print(f"     Дата: {t.get('date', 'N/A')}")
                print(f"     Сумма: {t.get('amount', 0)} {t.get('currency', 'EUR')}")
                print(f"     Описание: {t.get('description', '')[:100]}...")
        else:
            print(f"   ❌ Транзакции не найдены")
            
    except Exception as e:
        print(f"   ❌ Ошибка парсера: {e}")

if __name__ == "__main__":
    # Тестируем каждый файл Paysera
    files = [
        "Paysera Sveciy Namai Lithuania EUR_0126.pdf",
        "Paysera-BS PROPERTY, SIA_0126.pdf",
        "Paysera-BS RERUM, SIA_0126.pdf"
    ]
    
    for file_name in files:
        debug_paysera(file_name)
        print("\n" + "="*60 + "\n")