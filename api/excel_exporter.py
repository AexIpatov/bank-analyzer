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
        Парсер для Excel-выписок Paysera (с отладкой)
        """
        try:
            # Пробуем прочитать Excel с разными параметрами
            try:
                df = pd.read_excel(file_path, sheet_name=0, header=None, engine='openpyxl')
                print("Файл прочитан с engine='openpyxl'")
            except Exception as e1:
                print(f"Ошибка с openpyxl: {e1}, пробуем без engine")
                df = pd.read_excel(file_path, sheet_name=0, header=None)
            
            print(f"\n=== ОТЛАДКА: Файл {file_name} ===")
            print(f"Всего строк в файле: {len(df)}")
            print(f"Всего столбцов: {len(df.columns)}")
            
            # Выводим первые 20 строк для отладки
            print("\n--- Первые 20 строк файла ---")
            for idx in range(min(20, len(df))):
                row_text = ' '.join(str(v) for v in df.iloc[idx].values if pd.notna(v))
                print(f"Строка {idx}: {row_text[:500]}")
            print("--- Конец вывода строк ---\n")
            
            transactions = []
            found_dates = 0
            found_amounts = 0
            
            for idx, row in df.iterrows():
                # Объединяем все ячейки строки
                row_text = ' '.join(str(v) for v in row.values if pd.notna(v))
                
                # Пропускаем пустые строки
                if not row_text.strip():
                    continue
                
                # Ищем дату в формате YYYY-MM-DD
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', row_text)
                
                if date_match:
                    found_dates += 1
                    date = date_match.group(1)
                    
                    # Ищем сумму (число с копейками)
                    amount_match = re.search(r'(\d+[.,]\d{2})', row_text)
                    
                    if amount_match:
                        found_amounts += 1
                        amount_str = amount_match.group(1).replace(',', '.')
                        try:
                            amount = float(amount_str)
                            
                            # Определяем знак: расход или доход
                            # Проверяем наличие меток расхода
                            if ' D ' in row_text or ' D\t' in row_text or ' D' in row_text[-3:] or 'Debit' in row_text or 'Commission fee' in row_text:
                                amount = -amount
                                sign = "РАСХОД (-)"
                            else:
                                sign = "ДОХОД (+)"
                            
                            # Описание: берем часть строки
                            description = row_text[:300]
                            
                            transaction = {
                                'date': date,
                                'amount': amount,
                                'currency': 'EUR',
                                'account_name': os.path.splitext(file_name)[0],
                                'description': description,
                                'article_name': '',
                                'article_code': '',
                                'direction': '',
                                'subdirection': ''
                            }
                            transactions.append(transaction)
                            print(f"✅ Строка {idx}: {date} | {amount} ({sign}) | {description[:80]}...")
                        except Exception as e:
                            print(f"❌ Строка {idx}: ошибка при парсинге суммы '{amount_str}': {e}")
            
            print(f"\n=== РЕЗУЛЬТАТ ===")
            print(f"Найдено строк с датами: {found_dates}")
            print(f"Найдено строк с суммами: {found_amounts}")
            print(f"Создано транзакций: {len(transactions)}")
            
            # Удаляем дубликаты
            seen = set()
            unique_transactions = []
            for t in transactions:
                key = (t['date'], t['amount'], t['description'][:50])
                if key not in seen:
                    seen.add(key)
                    unique_transactions.append(t)
            
            print(f"После удаления дубликатов: {len(unique_transactions)} транзакций")
            print("=== Конец отладки ===\n")
            
            return unique_transactions
            
        except Exception as e:
            print(f"ОШИБКА при парсинге Paysera Excel: {e}")
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
