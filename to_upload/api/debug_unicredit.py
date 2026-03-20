import pandas as pd

def debug_unicredit():
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
            # Читаем файл
            df = pd.read_csv(file_path, encoding='utf-8')
            
            print(f"\n📄 Всего строк: {len(df)}")
            print(f"📄 Колонки: {df.columns.tolist()}")
            
            print("\n📊 Первые 5 строк:")
            print("-" * 60)
            print(df.head())
            
            # Ищем транзакции с суммой
            print("\n🔍 Поиск транзакций с суммой:")
            print("-" * 60)
            
            transaction_count = 0
            for i, row in df.iterrows():
                amount = row.get('Amount', 0)
                if amount != 0:
                    transaction_count += 1
                    print(f"\n✅ Транзакция {transaction_count}:")
                    print(f"   Дата: {row.get('Booking Date', 'Нет')}")
                    print(f"   Сумма: {amount} {row.get('Currency', 'CZK')}")
                    print(f"   Описание: {row.get('Transaction Details', 'Нет')[:100]}")
            
            print(f"\n📊 Найдено транзакций с суммой: {transaction_count}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print()

if __name__ == "__main__":
    debug_unicredit()