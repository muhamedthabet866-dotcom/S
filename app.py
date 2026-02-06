import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

st.set_page_config(page_title="MBA SPSS Solver Pro", layout="wide")
st.title("🎓 المحرك الذكي النهائي - المهندس محمد")

# دالة تنظيف عدوانية للنصوص لضمان المطابقة
def ultra_clean(text):
    if not text or pd.isna(text): return ""
    # تحويل لصغير + إزالة أي رموز وترقيم + توحيد المسافات
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

# --- جلب المنهج من GitHub ---
GITHUB_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/spss_rules.csv"

@st.cache_data
def load_rules(url):
    try:
        # قراءة ملف CSV المرفوع (نظراً لأن الملف المرفق CSV)
        res = requests.get(url, timeout=15)
        return pd.read_csv(BytesIO(res.content))
    except: return None

rules_df = load_rules(GITHUB_URL)

with st.sidebar:
    st.header("⚙️ الإعدادات")
    mapping_input = st.text_area("تعريف المتغيرات (X1=name):", 
        value="X1=account balance\nX2=ATM transactions\nX4=debit card\nX5=interest\nX6
