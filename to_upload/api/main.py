from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
from excel_exporter import ExcelExporter

app = FastAPI(
    title="🤖 Анализатор банковских выписок",
    description="""
    ## Добро пожаловать в AI-агента для анализа банковских выписок!
    
    ### 📋 Что я умею:
    - 📄 Читать выписки в форматах **Excel, CSV**
    - 📦 Загружать **несколько файлов одновременно**
    - 📊 Объединять все транзакции в один Excel файл
    - 🏷️ Группировать траты по категориям (с обучением)
    - ❗ Помечать неопределенные статьи "Требует уточнения!!!"
    - 📝 Автоматически определять название счета из имени файла
    """,
    version="3.1.0"
)

# Настройка CORS для работы с браузером
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Папки для работы (используем прямые слеши)
BASE_DIR = Path("C:/Users/Александр/Desktop/bank-analyzer")
UPLOADS_DIR = BASE_DIR / "uploads"
RESULTS_DIR = UPLOADS_DIR / "results"

# Создаем папки, если их нет
UPLOADS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Инициализация экспортера
exporter = ExcelExporter()

def extract_account_name(filename: str) -> str:
    """
    Извлекает название счета из имени файла
    Пример: "ANTONIJAS NAMS 14 SIA-Industra_0226.xls" -> "ANTONIJAS NAMS 14 SIA-Industra"
    """
    # Убираем расширение
    name_without_ext = os.path.splitext(filename)[0]
    # Убираем внутреннее обозначение _0226, _0126, _0226 и т.д.
    account_name = re.sub(r'_\d{4}$', '', name_without_ext)
    return account_name

@app.get("/")
async def root():
    return {
        "message": "🤖 Анализатор банковских выписок API",
        "status": "✅ работает",
        "version": "3.1.0"
    }

@app.post("/api/process-multiple",
    summary="📦 Обработка нескольких выписок",
    description="""
    Загрузите несколько файлов с банковскими выписками.
    
    **Что произойдет:**
    1. Все файлы будут обработаны
    2. Все транзакции объединятся в один Excel файл
    3. Неопределенные статьи помечаются "Требует уточнения!!!"
    4. В столбец "Счет" попадает полное имя файла без расширения и без _0226
    5. Файл сохранится в папку C:\\Users\\Александр\\Desktop\\bank-analyzer\\uploads\\results
    6. Имя файла: выписки_ГГГГММДД_ЧЧММСС_Кол-во счетов.xlsx
    
    **Поддерживаемые форматы:** Excel (.xlsx, .xls), CSV
    **Максимум файлов:** 20
    """
)
async def process_multiple_files(
    files: List[UploadFile] = File(..., description="📄 Выберите файлы с выписками"),
    analysis_type: str = Form("full", description="🔧 Тип анализа")
):
    try:
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="❌ Слишком много файлов. Максимум 20")
        
        all_transactions = []
        results = []
        
        for file in files:
            content = await file.read()
            
            if len(content) > 10 * 1024 * 1024:
                results.append({
                    "filename": file.filename,
                    "status": "❌ error",
                    "error": "Файл слишком большой (макс. 10MB)"
                })
                continue
            
            try:
                # Парсим файл
                transactions = exporter.extract_transactions(content, file.filename)
                
                if transactions:
                    # Получаем название счета из имени файла
                    account_name = extract_account_name(file.filename)
                    
                    # Добавляем транзакции в общий список
                    for t in transactions:
                        # Проверяем, определена ли статья - используем классификатор
                        if not t.get('article_code') and not t.get('article_name'):
                            # Пробуем определить статью через классификатор
                            article = exporter.classifier.classify_article(t.get('description', ''))
                            if article:
                                t['article_name'] = article
                                t['article_code'] = article
                            else:
                                t['article_name'] = "Требует уточнения!!!"
                                t['article_code'] = "??? Требует уточнения"
                        
                        # Проверяем, определено ли направление - используем классификатор
                        if not t.get('direction'):
                            direction, subdirection = exporter.classifier.classify_direction(t.get('description', ''))
                            if direction:
                                t['direction'] = direction
                            else:
                                t['direction'] = "Требует уточнения!!!"
                            if subdirection:
                                t['subdirection'] = subdirection
                        
                        # Добавляем информацию о счете
                        t['account_name'] = account_name
                        t['source_file'] = file.filename
                        all_transactions.append(t)
                    
                    results.append({
                        "filename": file.filename,
                        "status": "✅ success",
                        "transactions": len(transactions)
                    })
                else:
                    results.append({
                        "filename": file.filename,
                        "status": "⚠️ warning",
                        "error": "Нет транзакций в файле"
                    })
                    
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "❌ error",
                    "error": str(e)
                })
        
        if all_transactions:
            # Создаем итоговый Excel файл
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            num_banks = len(set(t.get('account_name', 'Неизвестно') for t in all_transactions))
            
            # Имя файла: выписки_20250320_143022_5 счетов.xlsx
            output_filename = f"выписки_{timestamp}_{num_banks} счетов.xlsx"
            output_path = RESULTS_DIR / output_filename
            
            # Сохраняем в Excel
            data = []
            for t in all_transactions:
                # Применяем классификатор для недостающих данных
                article_name = t.get('article_name', '')
                if not article_name or article_name == "Требует уточнения!!!":
                    article = exporter.classifier.classify_article(t.get('description', ''))
                    article_name = article if article else "Требует уточнения!!!"
                
                direction = t.get('direction', '')
                if not direction or direction == "Требует уточнения!!!":
                    dir_result, _ = exporter.classifier.classify_direction(t.get('description', ''))
                    direction = dir_result if dir_result else "Требует уточнения!!!"
                
                data.append({
                    'Дата': t.get('date', ''),
                    'Сумма': t.get('amount', 0),
                    'Валюта': t.get('currency', 'EUR'),
                    'Счет': t.get('account_name', 'Неизвестно'),
                    'Исходный файл': t.get('source_file', ''),
                    'Статья код': t.get('article_code', ''),
                    'Статья название': article_name,
                    'Направление': direction,
                    'Субнаправление': t.get('subdirection', ''),
                    'Описание': t.get('description', ''),
                    'Контрагент': t.get('payee', ''),
                    'Тип': t.get('type', '')
                })
            
            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            return JSONResponse({
                "success": True,
                "total_files": len(files),
                "processed": len([r for r in results if r['status'] == '✅ success']),
                "failed": len([r for r in results if r['status'] == '❌ error']),
                "results": results,
                "output_file": str(output_path),
                "output_filename": output_filename,
                "total_transactions": len(all_transactions),
                "message": f"✅ Результат сохранен в папку uploads\\results\\{output_filename}"
            })
        else:
            return JSONResponse({
                "success": False,
                "total_files": len(files),
                "processed": 0,
                "failed": len(files),
                "results": results,
                "message": "❌ Не удалось обработать ни одного файла"
            })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Ошибка: {str(e)}")

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Скачивает обработанный файл"""
    file_path = RESULTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)