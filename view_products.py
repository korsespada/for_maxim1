import os
import json
import tempfile

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Сетка товаров", layout="wide")

DATA_DIR = "data"        # папка с файлами в репо
DEFAULT_FILE = "szwego_products.csv"

# ---------- Настройки стилей ----------

st.markdown("""
<style>
    div[data-testid="column"] {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        text-align: center;
    }
    img {
        max-height: 150px;
        object-fit: cover;
        margin-bottom: 10px;
    }
    /* Описание в одну строку с троеточием */
    .one-line-desc {
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.85rem;
        color: rgba(250, 250, 250, 0.8);
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Выбор файла ----------

def get_file_path():
    st.sidebar.title("📁 Настройки файла")

    upload_method = st.sidebar.radio(
        "Способ загрузки:",
        ["Выбрать из репозитория", "Загрузить из компьютера"]
    )

    if upload_method == "Выбрать из репозитория":
        # список csv из папки data
        csv_files = [
            f for f in os.listdir(DATA_DIR)
            if f.lower().endswith(".csv")
        ]

        if not csv_files:
            st.sidebar.error("В папке data нет CSV файлов.")
            return None

        # дефолтный файл
        default_index = 0
        if DEFAULT_FILE in csv_files:
            default_index = csv_files.index(DEFAULT_FILE)

        selected = st.sidebar.selectbox(
            "Файл с товарами из GitHub:",
            csv_files,
            index=default_index
        )
        return os.path.join(DATA_DIR, selected)

    else:
        uploaded_file = st.sidebar.file_uploader(
            "Загрузите CSV файл:",
            type=["csv"]
        )
        if uploaded_file is None:
            return None

        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.sidebar.success(f"Файл загружен: {uploaded_file.name}")
        return temp_path

# ---------- Работа с CSV ----------

def load_data(file_path):
    if not file_path:
        st.error("Файл не выбран!")
        return pd.DataFrame()
    if not os.path.exists(file_path):
        st.error(f"Файл не найден: {file_path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path, sep=';')
        return df
    except Exception as e:
        st.error(f"Ошибка чтения: {e}")
        return pd.DataFrame()

def save_data(df, file_path):
    if not file_path:
        st.error("Путь к файлу не указан!")
        return
    try:
        df.to_csv(file_path, sep=';', index=False, encoding='utf-8')
        st.toast("Файл обновлен!", icon="✅")
    except Exception as e:
        st.error(f"Ошибка сохранения: {e}")

# ---------- Картинки ----------

BASE_OPTIM_PARAMS = "imageMogr2/auto-orient/thumbnail/!320x320r/quality/80/format/jpg"

def to_thumb(url: str) -> str:
    """Добавляет параметры imageMogr2 для уменьшения картинки."""
    if not url:
        return url
    if "imageMogr2" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{BASE_OPTIM_PARAMS}"

def get_first_image(photos_str):
    if pd.isna(photos_str) or photos_str == '':
        return None
    try:
        clean_str = str(photos_str).replace('""', '"')
        if clean_str.startswith('"') and clean_str.endswith('"'):
            clean_str = clean_str[1:-1]

        images = json.loads(clean_str)
        if isinstance(images, list) and len(images) > 0:
            return images[0]
    except Exception:
        return None
    return None

# ---------- Основная логика ----------

file_path = get_file_path()

if file_path:
    st.title("📦 Управление товарами")
    st.info(f"Текущий файл: `{file_path}`")

    if 'df' not in st.session_state or \
       'current_file' not in st.session_state or \
       st.session_state['current_file'] != file_path:
        st.session_state['df'] = load_data(file_path)
        st.session_state['current_file'] = file_path

    df = st.session_state['df']

    if not df.empty:
        st.write(f"Всего товаров: **{len(df)}**")

        COLS_COUNT = 6

        for i in range(0, len(df), COLS_COUNT):
            cols = st.columns(COLS_COUNT)
            batch = df.iloc[i: i + COLS_COUNT]

            for idx, (real_index, row) in enumerate(batch.iterrows()):
                with cols[idx]:
                    # 1. Картинка с оптимизацией
                    img_url = get_first_image(row.get('photos'))
                    if img_url:
                        thumb_url = to_thumb(img_url)
                        st.image(thumb_url, use_container_width=True)
                    else:
                        st.text("Нет фото")

                    # 2. Описание в одну строку с троеточием
                    full_desc = str(row.get('description', '')).strip()
                    if full_desc.lower() == 'nan' or full_desc == '':
                        display_desc = "Без описания"
                    else:
                        display_desc = full_desc

                    st.markdown(
                        f'<span class="one-line-desc">{display_desc}</span>',
                        unsafe_allow_html=True
                    )

                    # 3. Цена
                    price = row.get('price', '')
                    st.write(f"**{price}**")
    else:
        st.warning("Файл пуст или не загружен.")
else:
    st.title("📦 Управление товарами")
    st.warning("Выберите файл для начала работы.")
