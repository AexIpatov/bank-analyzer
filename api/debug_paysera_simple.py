import fitz  # PyMuPDF
import re
import os

def analyze_paysera_file(file_name):
    print("="*60)
    print(f"АНАЛИЗ ФАЙЛА: {file_name}")
    print("="*60)
    
    file_path = os.path.join("parsers", file_name)
    
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return
    
    try:
        doc = fitz.open(file_path)
        print(f"📄 Страниц: {len(doc)}")
        
        all_transactions = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split('\n')
            
            print(f"\n--- Страница {page_num + 1} ---")
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Ищем дату
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                
                # Ищем сумму
                amount_match = re.search(r'([-+]?\s*\d+[.,]?\d*[.,]?\d*)\s*EUR', line)
                if amount_match:
                    amount_str = amount_match.group(1).replace(',', '.').replace(' ', '')
                    try:
                        amount = float(amount_str)
                        if '-' in amount_match.group(0):
                            amount = -amount
                        
                        print(f"\n✅ ТРАНЗАКЦИЯ НАЙДЕНА (строка {i+1}):")
                        print(f"   Дата: {date}")
                        print(f"   Сумма: {amount} EUR")
                        print(f"   Строка: {line[:100]}...")
                        
                        # Показываем соседние строки для контекста
                        print("   Контекст:")
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            prefix = "→" if j == i else " "
                            print(f"   {prefix} {j+1}: {lines[j][:80]}")
                        
                        all_transactions.append({
                            'page': page_num + 1,
                            'line': i + 1,
                            'date': date,
                            'amount': amount,
                            'text': line
                        })
                    except:
                        pass
        
        print(f"\n📊 ИТОГО: Найдено {len(all_transactions)} потенциальных транзакций")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    files = [
        "Paysera-BS PROPERTY, SIA_0126.pdf",
        "Paysera-BS RERUM, SIA_0126.pdf"
    ]
    
    for file_name in files:
        analyze_paysera_file(file_name)
        print("\n" + "="*60 + "\n")