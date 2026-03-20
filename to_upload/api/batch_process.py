import os
from datetime import datetime
from parsers.bank_parser import BankParser
import pandas as pd

def list_available_files():
    """Показывает все доступные файлы в папке parsers"""
    parsers_dir = "parsers"
    files = []
    
    print("\n📁 Доступные файлы в папке parsers:")
    print("-" * 60)
    
    for i, filename in enumerate(sorted(os.listdir(parsers_dir)), 1):
        if filename.endswith(('.csv', '.xlsx', '.xls', '.pdf')):
            file_path = os.path.join(parsers_dir, filename)
            size = os.path.getsize(file_path)
            size_kb = size / 1024
            print(f"{i:2}. {filename} ({size_kb:.1f} KB)")
            files.append(filename)
    
    return files

def select_files(files):
    """Позволяет пользователю выбрать файлы для обработки"""
    print("\n🔍 Выберите файлы для обработки:")
    print("-" * 60)
    print("Варианты ввода:")
    print("  • 1,3,5-8  - выбрать файлы по номерам")
    print("  • 1-5       - выбрать диапазон")
    print("  • all       - выбрать все файлы")
    print("  • q         - выход")
    print("-" * 60)
    
    choice = input("Введите номера файлов: ").strip()
    
    if choice.lower() == 'q':
        return []
    
    if choice.lower() == 'all':
        return files
    
    selected = []
    parts = choice.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Диапазон вида 5-10
            start, end = map(int, part.split('-'))
            for num in range(start, end + 1):
                if 1 <= num <= len(files):
                    selected.append(files[num - 1])
        else:
            # Отдельный номер
            try:
                num = int(part)
                if 1 <= num <= len(files):
                    selected.append(files[num - 1])
            except:
                print(f"⚠️ Неверный формат: {part}")
    
    return selected

def process_files(selected_files):
    """Обрабатывает выбранные файлы"""
    if not selected_files:
        print("\n❌ Файлы не выбраны")
        return None, None
    
    print(f"\n🔄 Выбрано файлов: {len(selected_files)}")
    
    parser = BankParser()
    all_transactions = []
    results = []
    
    for filename in selected_files:
        print(f"\n📄 Обработка: {filename}")
        file_path = os.path.join("parsers", filename)
        
        try:
            # Определяем банк
            bank_key, parser_type = parser.identify_bank(filename, file_path)
            print(f"   Банк: {bank_key} (тип: {parser_type})")
            
            # Парсим файл
            transactions = parser.parse_file(file_path, filename)
            
            if transactions:
                print(f"   ✅ Найдено транзакций: {len(transactions)}")
                
                # Добавляем имя файла к каждой транзакции
                for t in transactions:
                    t['source_file'] = filename
                    t['source_bank'] = bank_key
                
                all_transactions.extend(transactions)
                results.append({
                    'file': filename,
                    'bank': bank_key,
                    'count': len(transactions),
                    'status': 'OK'
                })
            else:
                print(f"   ⚠️ Нет транзакций")
                results.append({
                    'file': filename,
                    'bank': bank_key,
                    'count': 0,
                    'status': 'NO TRANSACTIONS'
                })
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results.append({
                'file': filename,
                'bank': 'unknown',
                'count': 0,
                'status': f'ERROR'
            })
    
    return all_transactions, results

def save_to_excel(transactions, results):
    """Сохраняет все транзакции в один Excel файл"""
    if not transactions:
        print("\n❌ Нет транзакций для сохранения")
        return
    
    # Создаем DataFrame
    data = []
    for t in transactions:
        data.append({
            'Дата': t.get('date', ''),
            'Сумма': t.get('amount', 0),
            'Валюта': t.get('currency', 'EUR'),
            'Банк': t.get('bank', ''),
            'Исходный файл': t.get('source_file', ''),
            'Статья код': t.get('article_code', ''),
            'Статья название': t.get('article_name', ''),
            'Направление': t.get('direction', ''),
            'Субнаправление': t.get('subdirection', ''),
            'Описание': t.get('description', ''),
            'Контрагент': t.get('payee', ''),
            'Тип': t.get('type', ''),
            'Парсер': t.get('parser', '')
        })
    
    df = pd.DataFrame(data)
    
    # Генерируем имя файла с датой
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'batch_export_{timestamp}.xlsx'
    output_path = os.path.join('exports', output_filename)
    
    # Создаем папку exports если её нет
    os.makedirs('exports', exist_ok=True)
    
    # Сохраняем в Excel
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    print(f"\n✅ Все транзакции сохранены в: {output_path}")
    return output_path

def print_summary(results, transactions):
    """Печатает сводку по обработке"""
    print("\n" + "=" * 60)
    print("📊 СВОДКА ПО ОБРАБОТКЕ")
    print("=" * 60)
    
    total_success = sum(1 for r in results if r['status'] == 'OK')
    total_transactions = sum(r['count'] for r in results)
    
    print(f"\nВсего файлов: {len(results)}")
    print(f"Успешно обработано: {total_success}")
    print(f"Всего транзакций: {total_transactions}")
    
    print("\n📁 Детали по файлам:")
    for r in results:
        if r['status'] == 'OK':
            print(f"  ✅ {r['file']}: {r['bank']} - {r['count']} транзакций")
        else:
            print(f"  ❌ {r['file']}: {r['status']}")
    
    if transactions:
        # Статистика по банкам
        print("\n🏦 Статистика по банкам:")
        bank_stats = {}
        for t in transactions:
            bank = t.get('bank', 'Неизвестно')
            if bank not in bank_stats:
                bank_stats[bank] = {'count': 0, 'amount': 0}
            bank_stats[bank]['count'] += 1
            bank_stats[bank]['amount'] += t.get('amount', 0)
        
        for bank, stats in bank_stats.items():
            print(f"  • {bank}: {stats['count']} транзакций, сумма: {stats['amount']:.2f}")

def main():
    """Основная функция"""
    print("=" * 60)
    print("🚀 ПАКЕТНАЯ ОБРАБОТКА ВЫПИСОК")
    print("=" * 60)
    
    # Показываем доступные файлы
    files = list_available_files()
    
    if not files:
        print("\n❌ В папке parsers нет файлов для обработки")
        return
    
    # Выбираем файлы
    selected = select_files(files)
    
    if not selected:
        print("\n❌ Файлы не выбраны. Выход.")
        return
    
    # Обрабатываем файлы
    transactions, results = process_files(selected)
    
    if transactions:
        # Сохраняем результаты
        save_to_excel(transactions, results)
        
        # Печатаем сводку
        print_summary(results, transactions)
    
    print("\n✅ Обработка завершена!")

if __name__ == "__main__":
    main()