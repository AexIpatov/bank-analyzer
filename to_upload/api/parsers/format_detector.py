import os
import re

class FormatDetector:
    """
    Определяет тип файла и его формат
    """
    
    def __init__(self):
        self.signatures = {
            'pdf': self._is_pdf,
            'excel': self._is_excel,
            'csv': self._is_csv,
            'text': self._is_text
        }
    
    def detect(self, file_path):
        """
        Определяет тип файла
        Возвращает: 'pdf', 'excel', 'csv', 'text' или None
        """
        # Сначала по расширению
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.csv':
            return 'csv'
        elif ext == '.txt':
            return 'text'
        
        # Если расширение не помогло, пробуем по содержимому
        return self._detect_by_content(file_path)
    
    def _detect_by_content(self, file_path):
        """
        Определяет тип файла по его содержимому
        """
        try:
            # Пробуем прочитать как текст
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(1024)  # Читаем первые 1024 байта
                
                # Проверяем сигнатуры
                for file_type, func in self.signatures.items():
                    if func(sample):
                        return file_type
        except:
            pass
        
        return None
    
    def _is_pdf(self, content):
        """Проверяет, является ли содержимое PDF"""
        return content.startswith('%PDF')
    
    def _is_excel(self, content):
        """Проверяет, является ли содержимое Excel"""
        # Проверяем сигнатуры Excel
        excel_signatures = [
            'xl/',  # Внутренняя структура xlsx
            'workbook.xml',
            'sheet.xml'
        ]
        return any(sig in content for sig in excel_signatures)
    
    def _is_csv(self, content):
        """Проверяет, является ли содержимое CSV"""
        # Ищем признаки CSV: запятые, точки с запятой, кавычки
        lines = content.strip().split('\n')
        if len(lines) < 1:
            return False
        
        first_line = lines[0]
        
        # Проверяем наличие разделителей
        delimiters = [',', ';', '\t', '|']
        delimiter_count = sum(1 for d in delimiters if d in first_line)
        
        # Проверяем, что это не HTML и не XML
        if '<' in first_line and '>' in first_line:
            return False
        
        return delimiter_count > 0
    
    def _is_text(self, content):
        """Проверяет, является ли содержимое простым текстом"""
        # Если прошли все проверки и это не бинарный файл
        return all(ord(c) < 128 or c.isprintable() for c in content[:100])
    
    def detect_encoding(self, file_path):
        """
        Пытается определить кодировку файла
        """
        import chardet
        
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(5000)
                result = chardet.detect(raw_data)
                return result['encoding']
        except:
            return 'utf-8'
    
    def detect_delimiter(self, file_path):
        """
        Определяет разделитель в CSV файле
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                
                # Пробуем разные разделители
                delimiters = [',', ';', '\t', '|']
                counts = {}
                
                for d in delimiters:
                    counts[d] = first_line.count(d)
                
                # Выбираем разделитель с максимальным количеством
                if counts:
                    return max(counts, key=counts.get)
        except:
            pass
        
        return ','  # По умолчанию
    
    def get_file_info(self, file_path):
        """
        Возвращает полную информацию о файле
        """
        info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'type': self.detect(file_path),
            'encoding': None,
            'delimiter': None
        }
        
        if info['type'] == 'csv':
            info['encoding'] = self.detect_encoding(file_path)
            info['delimiter'] = self.detect_delimiter(file_path)
        elif info['type'] == 'text':
            info['encoding'] = self.detect_encoding(file_path)
        
        return info