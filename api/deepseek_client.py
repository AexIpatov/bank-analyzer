from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class DeepSeekClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"
    
    async def analyze_statement(self, text_content: str, analysis_type: str = "full"):
        """
        Отправляет текст выписки в DeepSeek для анализа
        """
        # Создаем промпт в зависимости от типа анализа
        prompts = {
            "full": """Ты - финансовый аналитик. Проанализируй банковскую выписку и предоставь:
1. Общий баланс и движение средств
2. Крупные расходы (>10% от среднего)
3. Категоризация трат (продукты, транспорт, развлечения и т.д.)
4. Регулярные платежи
5. Аномалии или подозрительные операции
6. Советы по оптимизации расходов

Выписка:""",
            
            "quick": "Сделай краткий анализ выписки: основные доходы, расходы и баланс. Выписка:",
            
            "categories": "Сгруппируй все расходы по категориям и покажи сумму по каждой. Выписка:"
        }
        
        system_prompt = prompts.get(analysis_type, prompts["full"])
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_content[:15000]}  # Ограничиваем длину
                ],
                temperature=0.3,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при обращении к DeepSeek: {str(e)}"
    
    async def extract_structured_data(self, text_content: str):
        """
        Извлекает структурированные данные из выписки
        """
        prompt = """Извлеки структурированные данные из банковской выписки.
        Верни ТОЛЬКО JSON в формате:
        {
            "total_income": число,
            "total_expenses": число,
            "balance": число,
            "top_categories": [{"category": "название", "amount": число}],
            "large_transactions": [{"date": "дата", "description": "описание", "amount": число}]
        }
        
        Выписка:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - AI, который извлекает данные и возвращает только JSON."},
                    {"role": "user", "content": prompt + text_content[:10000]}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка: {str(e)}"