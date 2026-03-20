import pandas as pd
import io
import os
import tempfile
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
            # Проверяем Excel-файлы Paysera по имени файла
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
        Специальный парсер для Excel-выписок Paysera
        """
        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path, sheet_name=0, header=None)
            
            # Ищем строку с заголовками
            header_row = None
            for idx, row in df.iterrows():
                row_text = ' '.join(str(v) for v in row.values if pd.notna(v))
                if 'Date and time' in row_text and 'Amount and currency' in row_text:
                    header_row = idx
                    break
            
            if header_row is None:
                return []
            
            # Читаем данные, начиная со строки заголовков
            df_data = pd.read_excel(
                file_path, 
                sheet_name=0, 
                header=header_row,
                dtype=str
            )
            
            transactions = []
            
            for _, row in df_data.iterrows():
                # Проверяем, что строка содержит данные
                if pd.isna(row.get('Date and time', pd.NA)):
                    continue
                
                # Парсим дату
                date_str = str(row['Date and time'])
                date = date_str[:10] if len(date_str) >= 10 else date_str
                
                # Парсим сумму
                amount_str = str(row.get('Amount and currency', '0'))
                amount = 0
                try:
                    # Извлекаем число
                    import re
                    amount_match = re.search(r'([-]?\d+(?:[.,]\d+)?)', amount_str)
                    if amount_match:
                        amount = float(amount_match.group(1).replace(',', '.'))
                except:
                    amount = 0
                
                # Определяем знак суммы по столбцу Credit/Debit
                cd = str(row.get('Credit/Debit', '')).upper()
                if cd == 'D' and amount > 0:
                    amount = -amount
                
                # Описание
                description = str(row.get('Purpose of payment', ''))
                
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
            
            return transactions
            
        except Exception as e:
            print(f"Ошибка при парсинге Paysera Excel: {e}")
            return []
    
    def _parse_generic_excel(self, file_path, file_name):
        """
        Универсальный парсер для Excel/CSV файлов
        """
        try:
            if file_name.lower().endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path, engine='openpyxl')
            
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
