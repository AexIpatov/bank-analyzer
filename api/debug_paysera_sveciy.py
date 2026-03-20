import pandas as pd

def debug_paysera_sveciy():
    file_path = r"C:\Users\Александр\Desktop\bank-analyzer\api\parsers\Paysera Sveciy Namai Lithuania EUR.xls"
    
    print("="*60)
    print("ОТЛАДКА PAYSERA SVECIY NAMAI")
    print("="*60)
    
    try:
        # Читаем файл
        df = pd.read_excel(file_path, sheet_name='Sheet1', header=None)
        
        print(f"\n📄 Всего строк: {len(df)}")
        print(f"📄 Всего колонок: {len(df.columns)}")
        
        print("\n📊 Первые 15 строк:")
        print("-" * 60)
        
        for i in range(min(15, len(df))):
            row = df.iloc[i]
            row_text = ' | '.join([str(x) for x in row if pd.notna(x)])
            print(f"Строка {i}: {row_text[:150]}")
        
        print("\n" + "="*60)
        print("🔍 Поиск транзакций...")
        print("-" * 60)
        
        # Ищем строки с транзакциями
        transaction_count = 0
        for i, row in df.iterrows():
            row_text = ' '.join([str(x) for x in row if pd.notna(x)])
            
            # Ищем признаки транзакции
            if ('Transfer' in row_text or 'Commission fee' in row_text) and 'EUR' in row_text:
                transaction_count += 1
                print(f"\n✅ Найдена транзакция в строке {i}:")
                print(f"   {row_text[:200]}...")
        
        print(f"\n📊 Найдено потенциальных транзакций: {transaction_count}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_paysera_sveciy()