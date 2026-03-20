class BaseParser:
    """
    Базовый класс для всех парсеров (без PDF зависимостей)
    """
    
    def __init__(self):
        self.bank_name = "Unknown"
    
    def parse(self, file_path, filename):
        """
        Основной метод парсинга (должен быть переопределен)
        """
        raise NotImplementedError("Метод parse должен быть реализован в дочернем классе")
    
    def determine_direction(self, transaction, dictionaries):
        """
        Определяет направление (может быть переопределен)
        """
        return None, None
    
    def enrich_transaction(self, transaction):
        """
        Обогащает транзакцию (может быть переопределен)
        """
        return transaction