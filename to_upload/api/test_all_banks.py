from parsers.bank_parser import BankParser
import os
from datetime import datetime

def test_bank_parsers():
    """
    Тестирует парсеры на всех доступных выписках
    """
    print("="*60)
    print("ТЕСТИРОВАНИЕ ПАРСЕРОВ ДЛЯ ВСЕХ БАНКОВ")
    print("="*60)
    
    parser = BankParser()
    
    # Папка с выписками
    parsers_dir = r"parsers"
    
    # Список файлов для тестирования
    test_files = [
        # Revolut
        ("Antonijas nams 14-Revolut International_0126.csv", "Revolut"),
        
        # Industra
        ("ANTONIJAS NAMS 14 SIA-Industra_0126.csv", "Industra Bank"),
        ("Industra Bank-Plavas 1_0126.csv", "Industra Bank"),
        
        # Wise
        ("Saida_Wise_0126.xlsx", "Wise"),
        
        # N26
        ("Saida N26_0126.pdf", "N26 PDF"),
        ("Saida_N26_0126.xlsx", "N26 Excel"),  # Добавлен Excel файл N26
        
        # Pasha Bank
        ("BUNDA LLC-Pasha Bank - AED-дирхам_0126.xlsx", "Pasha Bank AED"),
        ("BUNDA LLC-Pasha Bank-AZN_0126.xlsx", "Pasha Bank AZN"),
        
        # Kapital Bank
        ("Kapital bank_Saida_AZN_0126.xlsx", "Kapital Bank"),
        
        # Mashreq
        ("MASHREQ BANK-AED-NOMIQA_0126.xlsx", "Mashreq Bank"),
        
        # Paysera
        ("Paysera Sveciy Namai Lithuania EUR_0126.pdf", "Paysera"),
        ("Paysera-BS PROPERTY, SIA_0126.pdf", "Paysera"),
        ("Paysera-BS RERUM, SIA_0126.pdf", "Paysera"),
        
        # UniCredit
        ("Garpiz UniCredit Bank CZK_0126.pdf", "UniCredit"),
        ("Koruna UniCredit- CZK_0126.pdf", "UniCredit"),
        ("TwoHills_Molly_Unicredit_CZK_0126.pdf", "UniCredit"),
        
        # CSOB
        ("DŽIBIK Main CSOB CZK_0126.CSV", "CSOB"),
        
        # Budapest
        ("Budapest EUR-MKB_0126.xls", "Budapest Bank"),
        ("Budapest HUF-MKB_0126.xls", "Budapest Bank"),
    ]
    
    results = []
    
    for filename, expected_bank in test_files:
        file_path = os.path.join(parsers_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"\n❌ Файл не найден: {filename}")
            continue
        
        print(f"\n{'='*50}")
        print(f"Тестирование: {filename}")
        print(f"Ожидаемый банк: {expected_bank}")
        print(f"{'='*50}")
        
        try:
            # Определяем банк
            bank_key, parser_type = parser.identify_bank(filename, file_path)
            print(f"Определен банк: {bank_key} (тип парсера: {parser_type})")
            
            # Парсим файл
            transactions = parser.parse_file(file_path, filename)
            
            if transactions:
                print(f"✅ Найдено транзакций: {len(transactions)}")
                
                # Показываем первые 3 транзакции
                print("\nПервые 3 транзакции:")
                for i, t in enumerate(transactions[:3]):
                    print(f"\n  Транзакция {i+1}:")
                    print(f"    Дата: {t['date']}")
                    print(f"    Сумма: {t['amount']:.2f} {t['currency']}")
                    print(f"    Статья: {t['article_code']}")
                    print(f"    Направление: {t['direction']}")
                    print(f"    Описание: {t['description'][:80]}...")
                
                # Сохраняем в Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = filename.replace('.', '_').replace(' ', '_')
                output_path = f"exports/test_{safe_filename}_{timestamp}.xlsx"
                
                os.makedirs('exports', exist_ok=True)
                parser.save_to_excel(transactions, output_path)
                print(f"\n✅ Excel сохранен: {output_path}")
                
                results.append({
                    'file': filename,
                    'bank': bank_key,
                    'transactions': len(transactions),
                    'status': 'OK'
                })
            else:
                print(f"❌ Нет транзакций")
                results.append({
                    'file': filename,
                    'bank': bank_key if 'bank_key' in locals() else 'unknown',
                    'transactions': 0,
                    'status': 'NO TRANSACTIONS'
                })
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            results.append({
                'file': filename,
                'bank': bank_key if 'bank_key' in locals() else 'unknown',
                'transactions': 0,
                'status': f'ERROR: {str(e)[:50]}'
            })
    
    # Итоговая статистика
    print("\n" + "="*60)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    
    success = [r for r in results if r['status'] == 'OK']
    total_transactions = sum(r['transactions'] for r in success)
    
    print(f"\nВсего файлов: {len(results)}")
    print(f"Успешно обработано: {len(success)}")
    print(f"Всего транзакций: {total_transactions}")
    
    print("\nДетали по файлам:")
    for r in results:
        status_icon = "✅" if r['status'] == 'OK' else "❌"
        print(f"  {status_icon} {r['file']}: {r['bank']} - {r['transactions']} транзакций ({r['status']})")

if __name__ == "__main__":
    test_bank_parsers()