import pandas as pd
import io
import os
import tempfile
from datetime import datetime
import pdfplumber

# Импортируем парсеры
from parsers.paysera_pdf_parser import parse_paysera_pdf, can_parse as paysera_pdf_can_parse
from parsers.paysera_pdfplumber_parser import parse_paysera_pdfplumber, can_parse as paysera_pdfplumber_can_parse
from parsers.paysera_excel_parser import parse_paysera_excel, can_parse as paysera_excel_can_parse
from parsers.n26_parser import parse_n26, can_parse as n26_can_parse
from parsers.unicredit_parser import parse_unicredit, can_parse as unicredit_can_parse
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
            # Определяем тип файла и выбираем парсер
            
            # 1. Проверяем PDF-файлы Paysera
            if file_name.lower().endswith('.pdf'):
                if paysera_pdf_can_parse(file_name):
                    transactions = parse_paysera_pdf(tmp_path)
                    if transactions:
                        return self._enrich_transactions(transactions)
                
                if paysera_pdfplumber_can_parse(file_name):
                    transactions = parse_paysera_pdfplumber(tmp_path)
                    if transactions:
                        return self._enrich_transactions(transactions)
            
            # 2. Проверяем Excel-файлы Paysera
            if file_name.lower().endswith(('.xls', '.xlsx')):
                if paysera_excel_can_parse(file_name):
                    transactions = parse_paysera_excel(tmp_path)
                    if transactions:
                        return self._enrich_transactions(transactions)
            
            # 3. Проверяем другие банки
            if n26_can_parse(file_name):
                transactions = parse_n26(tmp_path)
                if transactions:
                    return self._enrich_transactions(transactions)
            
            if unicredit_can_parse(file_name):
                transactions = parse_unicredit(tmp_path)
                if transactions:
                    return self._enrich_transactions(transactions)
            
            # 4. Если ни один специализированный парсер не подошел,
            # пробуем универсальный парсер
            if file_name.lower().endswith(('.xls', '.xlsx', '.csv')):
                transactions = self._parse_generic_excel(tmp_path, file_name)
                if transactions:
                    return self._enrich_transactions(transactions)
            
            return []
            
        except Exception as e:
            print(f"Ошибка при парсинге файла {file_name}: {e}")
            return []
        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _parse_generic_excel(self, file_path, file_name):
        """
        Универсальный парсер для Excel/CSV файлов
        """
        try:
            # Определяем расширение
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
        
        # Создаем DataFrame
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
            # Возвращаем BytesIO объект
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Транзакции')
            output.seek(0)
            return output
