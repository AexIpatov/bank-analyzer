import streamlit as st
import pandas as pd
import os
import tempfile
import io
from datetime import datetime
from excel_exporter import ExcelExporter

# Настройка страницы
st.set_page_config(
    page_title="Анализатор банковских выписок",
    page_icon="🤖",
    layout="wide"
)

# Заголовок
st.title("🤖 Анализатор банковских выписок")
st.markdown("---")

# Инициализация экспортера
@st.cache_resource
def get_exporter():
    return ExcelExporter()

exporter = get_exporter()

# Боковая панель с информацией
with st.sidebar:
    st.header("📋 Информация")
    st.markdown("""
    **Поддерживаемые форматы:**
    - Excel (.xlsx, .xls)
    - CSV

    **Что вы получите:**
    - Дата операции
    - Сумма
    - Валюта
    - Счет (из имени файла)
    - Статья
    - Направление
    - Субнаправление
    - Описание
    """)

    st.markdown("---")
    st.caption("Обучено на 299 примерах из Финтабло")

# Основной интерфейс
tab1, tab2 = st.tabs(["📁 Один файл", "📦 Несколько файлов"])

with tab1:
    st.header("Загрузите один файл")

    uploaded_file = st.file_uploader(
        "Выберите файл с выпиской",
        type=['csv', 'xlsx', 'xls'],
        key="single"
    )

    if uploaded_file is not None:
        st.success(f"✅ Файл загружен: {uploaded_file.name}")

        if st.button("🚀 Запустить анализ", key="single_btn"):
            with st.spinner("Анализируем файл..."):
                try:
                    content = uploaded_file.read()
                    transactions = exporter.extract_transactions(content, uploaded_file.name)

                    if transactions:
                        df = pd.DataFrame([{
                            'Дата': t.get('date', ''),
                            'Сумма': t.get('amount', 0),
                            'Валюта': t.get('currency', 'EUR'),
                            'Счет': os.path.splitext(uploaded_file.name)[0],
                            'Статья': t.get('article_name', t.get('article_code', 'Требует уточнения!!!')),
                            'Направление': t.get('direction', 'Требует уточнения!!!'),
                            'Субнаправление': t.get('subdirection', ''),
                            'Описание': t.get('description', '')[:100]
                        } for t in transactions])

                        st.success(f"✅ Найдено {len(transactions)} транзакций")

                        st.subheader("📊 Результат анализа")
                        st.dataframe(df, use_container_width=True)

                        # Сохраняем в Excel
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Транзакции')
                        output.seek(0)

                        st.download_button(
                            label="📥 Скачать Excel",
                            data=output,
                            file_name=f"анализ_{uploaded_file.name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("⚠️ Не найдено транзакций в файле")

                except Exception as e:
                    st.error(f"❌ Ошибка: {str(e)}")

with tab2:
    st.header("Загрузите несколько файлов")

    uploaded_files = st.file_uploader(
        "Выберите файлы с выписками",
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=True,
        key="multiple"
    )

    if uploaded_files:
        st.info(f"📄 Выбрано файлов: {len(uploaded_files)}")

        if st.button("🚀 Запустить анализ всех файлов", key="multi_btn"):
            all_transactions = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Обработка: {uploaded_file.name}")
                try:
                    content = uploaded_file.read()
                    transactions = exporter.extract_transactions(content, uploaded_file.name)
                    if transactions:
                        for t in transactions:
                            t['source_file'] = uploaded_file.name
                        all_transactions.extend(transactions)
                except Exception as e:
                    st.error(f"❌ Ошибка в файле {uploaded_file.name}: {str(e)}")

                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.text("Обработка завершена!")

            if all_transactions:
                df_all = pd.DataFrame([{
                    'Дата': t.get('date', ''),
                    'Сумма': t.get('amount', 0),
                    'Валюта': t.get('currency', 'EUR'),
                    'Счет': os.path.splitext(t.get('source_file', ''))[0],
                    'Исходный файл': t.get('source_file', ''),
                    'Статья': t.get('article_name', t.get('article_code', 'Требует уточнения!!!')),
                    'Направление': t.get('direction', 'Требует уточнения!!!'),
                    'Субнаправление': t.get('subdirection', ''),
                    'Описание': t.get('description', '')[:100]
                } for t in all_transactions])

                st.success(f"✅ Всего транзакций: {len(all_transactions)}")
                st.dataframe(df_all, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_all.to_excel(writer, index=False, sheet_name='Все транзакции')
                output.seek(0)

                st.download_button(
                    label="📥 Скачать сводный Excel",
                    data=output,
                    file_name=f"сводка_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
