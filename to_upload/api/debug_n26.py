from parsers.n26_pdf_parser import N26PDFParser
import PyPDF2

def debug_n26():
    print("="*60)
    print("ОТЛАДКА N26 PDF")
    print("="*60)
    
    file_path = r"parsers\Saida N26_0126.pdf"
    
    # Читаем PDF напрямую
    print("\n1. Чтение PDF через PyPDF2:")
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"   Всего страниц: {len(pdf_reader.pages)}")
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                print(f"\n   Страница {page_num + 1}:")
                print(f"   Первые 500 символов:")
                print("-" * 40)
                print(text[:500])
                print("-" * 40)
    except Exception as e:
        print(f"   ОШИБКА: {e}")
    
    # Пробуем парсер
    print("\n2. Попытка парсинга:")
    parser = N26PDFParser()
    transactions = parser.parse(file_path, "Saida N26_0126.pdf")
    print(f"   Найдено транзакций: {len(transactions)}")
    
    if transactions:
        print("\n3. Первые 3 транзакции:")
        for i, t in enumerate(transactions[:3]):
            print(f"\n   Транзакция {i+1}:")
            print(f"     Дата: {t['date']}")
            print(f"     Сумма: {t['amount']} {t['currency']}")
            print(f"     Описание: {t['description'][:100]}...")
    else:
        print("\n   Транзакции не найдены")

if __name__ == "__main__":
    debug_n26()