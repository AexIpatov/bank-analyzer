import pdfplumber
import re
import os

def analyze_with_pdfplumber(file_name):
    print("="*60)
    print(f"АНАЛИЗ С PDFPLUMBER: {file_name}")
    print("="*60)
    
    file_path = os.path.join("parsers", file_name)
    
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return
    
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"📄 Страниц: {len(pdf.pages)}")
            
            all_text = ""
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    all_text += f"\n--- Страница {page_num + 1} ---\n{text}\n"
            
            # Сохраняем весь текст
            with open(f"paysera_{file_name.replace('.', '_')}_text.txt", "w", encoding="utf-8") as f:
                f.write(all_text)
            
            print(f"✅ Текст сохранен в файл для анализа")
            
            # Показываем первые 1000 символов
            print(f"\nПервые 1000 символов:")
            print("-" * 40)
            print(all_text[:1000])
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def extract_transactions_with_pdfplumber(file_name):
    print("="*60)
    print(f"ИЗВЛЕЧЕНИЕ ТРАНЗАКЦИЙ ИЗ: {file_name}")
    print("="*60)
    
    file_path = os.path.join("parsers", file_name)
    
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return []
    
    transactions = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Извлекаем таблицы
                tables = page.extract_tables()
                
                for table in tables:
                    for row in table:
                        if row and any(cell for cell in row if cell):
                            # Объединяем все ячейки в строку
                            row_text = ' '.join([str(cell) for cell in row if cell])
                            
                            # Ищем дату и сумму
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', row_text)
                            amount_match = re.search(r'([-+]?\s*\d+[.,]?\d*[.,]?\d*)\s*EUR', row_text)
                            
                            if date_match and amount_match:
                                date = date_match.group(1)
                                amount_str = amount_match.group(1).replace(',', '.').replace(' ', '')
                                amount = float(amount_str)
                                
                                if '-' in amount_match.group(0):
                                    amount = -amount
                                
                                transactions.append({
                                    'date': date,
                                    'amount': amount,
                                    'currency': 'EUR',
                                    'description': row_text,
                                    'bank': file_name
                                })
                                
                                print(f"✅ Найдена транзакция: {date} | {amount} EUR")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print(f"\n📊 Всего найдено транзакций: {len(transactions)}")
    return transactions

if __name__ == "__main__":
    files = [
        "Paysera-BS PROPERTY, SIA_0126.pdf",
        "Paysera-BS RERUM, SIA_0126.pdf"
    ]
    
    for file_name in files:
        analyze_with_pdfplumber(file_name)
        print("\n" + "="*60 + "\n")
        extract_transactions_with_pdfplumber(file_name)
        print("\n" + "="*60 + "\n")