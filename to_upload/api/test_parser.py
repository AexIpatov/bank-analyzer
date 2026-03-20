from parsers.bank_parser import BankParser
import json
from datetime import datetime

def test_revolut_parser():
    """Тестирует парсер Revolut"""
    print("="*50)
    print("Тестирование парсера Revolut")
    print("="*50)
    
    parser = BankParser()
    
    # Путь к файлу
    file_path = r"parsers\Antonijas nams 14-Revolut International_0126.csv"
    filename = "Antonijas nams 14-Revolut International_0126.csv"
    
    try:
        transactions = parser.parse_file(file_path, filename)
        
        print(f"Найдено транзакций: {len(transactions)}")
        print("\nПервые 5 транзакций:")
        print("-"*50)
        
        for i, t in enumerate(transactions[:5]):
            print(f"\nТранзакция {i+1}:")
            print(f"  Дата: {t['date']}")
            print(f"  Сумма: {t['amount']} {t['currency']}")
            print(f"  Банк: {t['bank']}")
            print(f"  Статья код: {t['article_code']}")
            print(f"  Статья название: {t['article_name']}")
            print(f"  Направление: {t['direction']}")
            print(f"  Субнаправление: {t['subdirection']}")
            print(f"  Описание: {t['description'][:100]}...")
            print(f"  Номер счета: {t.get('account_ref', 'Нет')}")
        
        return transactions
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def test_industra_parser():
    """Тестирует парсер Industra Bank"""
    print("\n" + "="*50)
    print("Тестирование парсера Industra Bank")
    print("="*50)
    
    parser = BankParser()
    
    # Путь к файлу
    file_path = r"parsers\ANTONIJAS NAMS 14 SIA-Industra_0126.csv"
    filename = "ANTONIJAS NAMS 14 SIA-Industra_0126.csv"
    
    try:
        transactions = parser.parse_file(file_path, filename)
        
        print(f"Найдено транзакций: {len(transactions)}")
        print("\nПервые 5 транзакций:")
        print("-"*50)
        
        for i, t in enumerate(transactions[:5]):
            print(f"\nТранзакция {i+1}:")
            print(f"  Дата: {t['date']}")
            print(f"  Сумма: {t['amount']} {t['currency']}")
            print(f"  Банк: {t['bank']}")
            print(f"  Статья код: {t['article_code']}")
            print(f"  Статья название: {t['article_name']}")
            print(f"  Направление: {t['direction']}")
            print(f"  Субнаправление: {t['subdirection']}")
            print(f"  Описание: {t['description'][:100]}...")
        
        return transactions
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def save_to_excel(transactions, bank_name):
    """Сохраняет транзакции в Excel"""
    from excel_exporter import ExcelExporter
    
    exporter = ExcelExporter()
    
    # Создаем временный файл с содержимым (для теста)
    temp_content = b"test"
    
    # Экспортируем
    output_path = exporter.export_to_excel(transactions, f"{bank_name}_test.csv")
    
    print(f"\nExcel файл сохранен: {output_path}")
    return output_path

if __name__ == "__main__":
    print("Запуск тестирования парсеров...")
    print("="*50)
    
    # Тестируем Revolut
    revolut_trans = test_revolut_parser()
    if revolut_trans:
        save_to_excel(revolut_trans, "Revolut")
    
    # Тестируем Industra
    industra_trans = test_industra_parser()
    if industra_trans:
        save_to_excel(industra_trans, "Industra")
    
    print("\n" + "="*50)
    print("Тестирование завершено!")