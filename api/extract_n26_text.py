import PyPDF2

def extract_text_simple():
    file_path = r"parsers\Saida N26_0126.pdf"
    
    print("="*60)
    print("ИЗВЛЕЧЕНИЕ ТЕКСТА ИЗ N26 PDF")
    print("="*60)
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"Всего страниц: {len(pdf_reader.pages)}")
            
            full_text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                full_text += text
                
                print(f"\n--- Страница {page_num + 1} ---")
                print(text)
            
            # Сохраняем в файл для анализа
            with open("n26_extracted.txt", "w", encoding="utf-8") as f:
                f.write(full_text)
            print("\n✅ Текст сохранен в файл n26_extracted.txt")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    extract_text_simple()