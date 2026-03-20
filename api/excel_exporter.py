import pandas as pd
import io
import os
import tempfile
import re
from datetime import datetime
from transaction_parser import TransactionParser


class ExcelExporter:
    def __init__(self):
        self.transaction_parser = TransactionParser()
    
    def extract_transactions(self, file_content, file_name):
        """
        Извлекает транзакции из загруженного файла
        """
        transactions = []
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        try:
            # Проверяем Excel-файлы Paysera
            if file_name.lower().endswith(('.xls', '.xlsx')) and 'paysera' in file_name.lower():
                transactions = self._parse_paysera_excel(tmp_path, file_name)
                if transactions:
                    return self._enrich_transactions(transactions)
            
            # Универсальный парсер для других Excel/CSV файлов
            if file_name.lower().endswith(('.xls', '.xlsx', '.csv')):
                transactions = self._parse_generic_excel(tmp_path, file_name)
                if transactions:
                    return self._enrich_transactions(transactions)
            
            return []
            
        except Exception as e:
            print(f"Ошибка при парсинге файла {file_name}: {e}")
            return []
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _parse_paysera_excel(self, file_path, file_name):
        """
        Парсер для структурированных Excel-выписок Paysera
        """
        try:
            # Читаем Excel с заголовками (заголовки на 3-й строке, индекс 2)
            df = pd.read_excel(file_path, sheet_name=0, header=2)
            
            print(f"=== ПАРСЕР PAYSERA: Найдено столбцов: {list(df.columns)} ===")
            print(f"Всего строк с данными: {len(df)}")
            
            transactions = []
            
            # Проходим по всем строкам
            for idx, row in df.iterrows():
                # Пропускаем пустые строки
                if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
                    continue
                
                # Получаем дату (столбец 3 - Date and time)
                date_str = str(row.iloc[3]) if len(row) > 3 else ""
                date = date_str[:10] if len(date_str) >= 10 else ""
                
                # Получаем сумму (столбец 7 - Amount and currency)
                amount_str = str(row.iloc[7]) if len(row) > 7 else ""
                amount = 0
                amount_match = re.search(r'([-]?\d+[.,]?\d*)', amount_str)
                if amount_match:
                    try:
                        amount = float(amount_match.group(1).replace(',', '.'))
                    except:
                        amount = 0
                
                # Определяем знак по типу транзакции (столбец 0 - Type)
                type_val = str(row.iloc[0]).lower() if len(row) > 0 else ""
                if 'commission' in type_val or 'fee' in type_val:
                    amount = -abs(amount)
                
                # Получаем описание (столбец 4 - Recipient / Payer)
                description = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                if not description:
                    description = type_val
                
                if date and amount != 0:
                    transaction = {
                        'date': date,
                        'amount': amount,
                        'currency': 'EUR',
                        'account_name': os.path.splitext(file_name)[0],
                        'description': description[:200],
                        'article_name': '',
                        'article_code': '',
                        'direction': '',
                        'subdirection': ''
                    }
                    transactions.append(transaction)
                    print(f"Найдена транзакция: {date} | {amount} | {description[:50]}")
            
            print(f"Всего найдено транзакций в Paysera: {len(transactions)}")
            return transactions
            
        except Exception as e:
            print(f"Ошибка при парсинге Paysera Excel: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_generic_excel(self, file_path, file_name):
        """
        Универсальный парсер для Excel/CSV файлов
        """
        try:
            if file_name.lower().endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                except:
                    df = pd.read_excel(file_path)
            
            transactions = []
            
            # Пытаемся найти нужные столбцы
            date_col = None
            amount_col = None
            desc_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'дата' in col_lower or 'date' in col_lower:
                    date_col = col
                elif 'сумм' in col_lower or 'amount' in col_lower or 'сумма' in col_lower:
                    amount_col = col
                elif 'опис' in col_lower or 'description' in col_lower or 'назначени' in col_lower:
                    desc_col = col
            
            if date_col and amount_col:
                for _, row in df.iterrows():
                    try:
                        amount = float(row[amount_col]) if pd.notna(row[amount_col]) else 0
                        
                        transaction = {
                            'date': str(row[date_col])[:10] if pd.notna(row[date_col]) else '',
                            'amount': amount,
                            'currency': 'EUR',
                            'account_name': os.path.splitext(file_name)[0],
                            'description': str(row[desc_col])[:200] if desc_col and pd.notna(row[desc_col]) else '',
                            'article_name': '',
                            'article_code': '',
                            'direction': '',
                            'subdirection': ''
                        }
                        transactions.append(transaction)
                    except:
                        continue
            
            return transactions
            
        except Exception as e:
            print(f"Ошибка в универсальном парсере: {e}")
            return []
    
    def _enrich_transactions(self, transactions):
        """
        Обогащает транзакции данными из классификатора
        """
        enriched = []
        for transaction in transactions:
            # Получаем классификацию
            classification = self.transaction_parser.classify_transaction(transaction)
            
            transaction['article_name'] = classification.get('article_name', '')
            transaction['article_code'] = classification.get('article_code', '')
            transaction['direction'] = classification.get('direction', '')
            transaction['subdirection'] = classification.get('subdirection', '')
            
            enriched.append(transaction)
        
        return enriched
    
    def export_to_excel(self, transactions, output_path=None):
        """
        Экспортирует транзакции в Excel
        """
        if not transactions:
            return None
        
        df = pd.DataFrame([{
            'Дата': t.get('date', ''),
            'Сумма': t.get('amount', 0),
            'Валюта': t.get('currency', 'EUR'),
            'Счет': t.get('account_name', ''),
            'Статья': t.get('article_name', ''),
            'Направление': t.get('direction', ''),
            'Субнаправление': t.get('subdirection', ''),
            'Описание': t.get('description', '')[:100]
        } for t in transactions])
        
        if output_path:
            df.to_excel(output_path, index=False, sheet_name='Транзакции')
            return output_path
        else:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Транзакции')
            output.seek(0)
            return output
