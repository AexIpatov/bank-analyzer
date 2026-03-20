import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
from excel_exporter import ExcelExporter

# === НАСТРОЙКА СТРАНИЦЫ ===
st.set_page_config(
    page_title="Аналитик выписок | Финансовый помощник",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === КАСТОМНЫЙ CSS ДЛЯ КРАСОТЫ ===
st.markdown("""
<style>
    /* Главный заголовок */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.5rem 0 0;
        opacity: 0.9;
    }
    /* Карточки */
    .card {
        background: white;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border: 1px solid #eef2f7;
    }
    /* Кнопки */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102,126,234,0.4);
    }
    /* Успешные сообщения */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #10b981;
    }
    /* Dataframe */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# === ШАПКА ===
st.markdown("""
<div class="main-header">
    <h1>📊 Финансовый аналитик выписок</h1>
    <p>Загрузите выписки — получите структурированные данные с автоматической категоризацией</p>
</div>
""", unsafe_allow_html=True)

# === БОКОВАЯ ПАНЕЛЬ (УЛУЧШЕННАЯ) ===
with st.sidebar:
    st.markdown("### 🧠 О программе")
    st.markdown("""
    <div class="card">
        <b>📁 Поддерживаемые форматы:</b><br>
        • Excel (.xlsx, .xls)<br>
        • CSV<br><br>
        <b>✨ Что вы получите:</b><br>
        • 📅 Дата операции<br>
        • 💰 Сумма и валюта<br>
        • 🏦 Счет (из имени файла)<br>
        • 📌 Статья расхода/дохода<br>
        • 🧭 Направление и субнаправление<br>
        • 📝 Описание<br><br>
        <b>🎓 Обучено на:</b> 299 примерах из Финтабло<br>
        <b>🤖 ИИ:</b> DeepSeek API для классификации
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888;">
        <small>⚡ Быстрый анализ финансов<br>© 2026 | Ваш финансовый помощник</small>
    </div>
    """, unsafe_allow_html=True)

# === ИНИЦИАЛИЗАЦИЯ ===
@st.cache_resource
def get_exporter():
    return ExcelExporter()

exporter = get_exporter()

# === ОСНОВНОЙ ИНТЕРФЕЙС ===
tab1, tab2 = st.tabs(["📂 **Один файл**", "📚 **Несколько файлов**"])

# ========== ВКЛАДКА 1: ОДИН ФАЙЛ ==========
with tab1:
    st.markdown("### Загрузите выписку для анализа")
    
    uploaded_file = st.file_uploader(
        "Выберите файл с банковской выпиской",
        type=['csv', 'xlsx', 'xls'],
        key="single",
        help="Поддерживаются файлы Excel и CSV до 200 МБ"
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ **Файл загружен:** `{uploaded_file.name}`")
        with col2:
            if st.button("🚀 **Запустить анализ**", key="single_btn", use_container_width=True):
                with st.spinner("🔄 Анализируем файл... Подождите немного..."):
                    try:
                        content = uploaded_file.read()
                        transactions = exporter.extract_transactions(content, uploaded_file.name)

                        if transactions:
                            df = pd.DataFrame([{
                                'Дата': t.get('date', ''),
                                'Сумма': t.get('amount', 0),
                                'Валюта': t.get('currency', 'EUR'),
                                'Счет': os.path.splitext(uploaded_file.name)[0],
                                'Статья': t.get('article_name', t.get('article_code', 'Требует уточнения')),
                                'Направление': t.get('direction', 'Требует уточнения'),
                                'Субнаправление': t.get('subdirection', ''),
                                'Описание': t.get('description', '')[:100]
                            } for t in transactions])

                            # Отображение статистики
                            st.markdown("---")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("📊 Всего операций", len(transactions))
                            with col_b:
                                доход = df[df['Сумма'] > 0]['Сумма'].sum() if len(df[df['Сумма'] > 0]) > 0 else 0
                                st.metric("📈 Доходы", f"{доход:,.2f} €")
                            with col_c:
                                расход = abs(df[df['Сумма'] < 0]['Сумма'].sum()) if len(df[df['Сумма'] < 0]) > 0 else 0
                                st.metric("📉 Расходы", f"{расход:,.2f} €")
                            
                            st.markdown("### 📋 Результат анализа")
                            st.dataframe(df, use_container_width=True)

                            # Экспорт в Excel
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False, sheet_name='Транзакции')
                            output.seek(0)

                            st.download_button(
                                label="📥 **Скачать Excel**",
                                data=output,
                                file_name=f"анализ_{uploaded_file.name}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        else:
                            st.warning("⚠️ Не найдено транзакций в файле. Проверьте формат.")
                    except Exception as e:
                        st.error(f"❌ Ошибка при обработке: {str(e)}")

# ========== ВКЛАДКА 2: НЕСКОЛЬКО ФАЙЛОВ ==========
with tab2:
    st.markdown("### Загрузите несколько выписок для сводного анализа")
    
    uploaded_files = st.file_uploader(
        "Выберите файлы с выписками",
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=True,
        key="multiple",
        help="Можно выбрать несколько файлов одновременно"
    )

    if uploaded_files:
        st.info(f"📄 **Выбрано файлов:** {len(uploaded_files)}")
        
        if st.button("🚀 **Запустить анализ всех файлов**", key="multi_btn", use_container_width=True):
            all_transactions = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"🔄 Обработка: {uploaded_file.name}")
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

            status_text.text("✅ Обработка завершена!")

            if all_transactions:
                df_all = pd.DataFrame([{
                    'Дата': t.get('date', ''),
                    'Сумма': t.get('amount', 0),
                    'Валюта': t.get('currency', 'EUR'),
                    'Счет': os.path.splitext(t.get('source_file', ''))[0],
                    'Исходный файл': t.get('source_file', ''),
                    'Статья': t.get('article_name', t.get('article_code', 'Требует уточнения')),
                    'Направление': t.get('direction', 'Требует уточнения'),
                    'Субнаправление': t.get('subdirection', ''),
                    'Описание': t.get('description', '')[:100]
                } for t in all_transactions])

                # Статистика
                st.markdown("---")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("📊 Всего операций", len(all_transactions))
                with col_b:
                    доход = df_all[df_all['Сумма'] > 0]['Сумма'].sum() if len(df_all[df_all['Сумма'] > 0]) > 0 else 0
                    st.metric("📈 Доходы", f"{доход:,.2f} €")
                with col_c:
                    расход = abs(df_all[df_all['Сумма'] < 0]['Сумма'].sum()) if len(df_all[df_all['Сумма'] < 0]) > 0 else 0
                    st.metric("📉 Расходы", f"{расход:,.2f} €")
                
                st.markdown("### 📋 Сводный результат")
                st.dataframe(df_all, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_all.to_excel(writer, index=False, sheet_name='Все транзакции')
                output.seek(0)

                st.download_button(
                    label="📥 **Скачать сводный Excel**",
                    data=output,
                    file_name=f"сводка_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
