import csv

def debug_unicredit_v2():
    files = [
        "parsers/Garpiz UniCredit Bank CZK_0226.csv",
        "parsers/Koruna UniCredit- CZK_0226.csv",
        "parsers/TwoHills_Molly_Unicredit_CZK_0226.csv"
    ]
    
    for file_path in files:
        print("="*60)
        print(f"ОТЛАДКА: {file_path}")
        print("="*60)
        
        try:
            # Читаем файл построчно
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"\n📄 Всего строк: {len(lines)}")
            
            print("\n📊 Первые 10 строк:")
            print("-" * 60)
            for i, line in enumerate(lines[:10]):
                print(f"Строка {i}: {line.strip()[:150]}")
            
            # Ищем строки с транзакциями (содержат дату и сумму)
            print("\n🔍 Поиск транзакций:")
            print("-" * 60)
            
            transaction_count = 0
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Ищем дату в формате YYYY-MM-DD
                if '2026-02' in line or '2026-01' in line:
                    # Ищем сумму
                    import re
                    amounts = re.findall(r'[-+]?\d+[.,]?\d*', line)
                    if amounts:
                        # Пытаемся найти сумму в CZK
                        for a in amounts:
                            try:
                                amount = float(a.replace(',', '.'))
                                if amount != 0 and abs(amount) < 1000000:
                                    transaction_count += 1
                                    print(f"\n✅ Транзакция {transaction_count} (строка {i}):")
                                    print(f"   Строка: {line[:150]}")
                                    print(f"   Сумма: {amount}")
                                    break
                            except:
                                pass
            
            print(f"\n📊 Найдено транзакций: {transaction_count}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print()

if __name__ == "__main__":
    debug_unicredit_v2()