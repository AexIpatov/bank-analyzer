# Экспортируем основные классы для удобного импорта
from .bank_parser import BankParser
from .universal_parser import UniversalParser
from .format_detector import FormatDetector
from .finclassifier import FinClassifier

# Экспортируем парсеры банков
from .revolut_parser import RevolutParser
from .industra_parser import IndustraParser
from .pasha_parser import PashaParser
from .kapital_parser import KapitalParser
from .mashreq_parser import MashreqParser
from .n26_excel_parser import N26ExcelParser

# Список всех доступных классов
__all__ = [
    'BankParser',
    'UniversalParser',
    'FormatDetector',
    'FinClassifier',
    'RevolutParser',
    'IndustraParser',
    'PashaParser',
    'KapitalParser',
    'MashreqParser',
    'N26ExcelParser'
]