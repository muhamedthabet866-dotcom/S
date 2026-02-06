import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

st.set_page_config(page_title="MBA SPSS Solver v2.0", layout="wide")
st.title("🎓 المحرك المطور لحل امتحانات SPSS")

# --- جلب المنهج من GitHub ---
GITHUB_RAW_URL = "https://github.com/muhamedthabet866-dotcom/S/raw/refs/heads/main/spss_rules.xlsx"

@st.cache_data
def load_rules(url):
    try:
        response = requests.get(url, timeout=10)
        return pd.read_excel(BytesIO(response.content))
    except: return None

rules_df = load_rules(GITHUB_RAW_URL)

col1, col2 = st.columns(2)

with col1:
    st.subheader("⚙️ تعريف المتغيرات (Mapping)")
    # بناءً على ملفك Data set 1
    mapping_input = st.text_area("أدخل المتغيرات:", 
        value="X1=account balance\nX2=ATM transactions\nX4=debit card\nX5=interest\nX6=city", height=250)

with col2:
    st.subheader("📝 أسئلة الامتحان")
    questions_input = st.text_area("الصق الأسئلة هنا:", height=250)

if st.button("🚀 توليد كود Syntax خالي من الأخطاء"):
    if rules_df is not None and questions_input:
        # 1. تحويل المابينج لقاموس وتجهيز قائمة كلمات مفتاحية
        mapping_dict = {}
        for line in mapping_input.split('\n'):
            if '=' in line:
                parts = line.split('=')
                mapping_dict[parts[1].strip().lower()] = parts[0].strip().upper()
        
        # ترتيب المتغيرات من الأطول للأقصر لتجنب تداخل الأسماء
        sorted_var_names = sorted(mapping_dict.keys(), key=len, reverse=True)

        final_syntax = ["* SPSS Syntax Generated for Data Set 1.\nSET DECIMALS=DOT.\n"]

        # 2. تنظيف الأسئلة من الأرقام في البداية (1. 2. 3.)
        questions = re.split(r'\d+[\.\)\s]+', questions_input)
        
        for q in questions:
            q = q.strip()
            if not q: continue
            
            matched = False
            # البحث عن القاعدة المناسبة في ملف الإكسيل
            for _, rule in rules_df.iterrows():
                keyword = str(rule['Keyword']).lower()
                if keyword in q.lower():
                    template = str(rule['Syntax_Template'])
                    
                    # --- منطق الاستبدال المتعدد (حل مشكلة السؤال رقم 1 و 4) ---
                    found_vars = []
                    for var_name in sorted_var_names:
                        if var_name in q.lower():
                            found_vars.append(mapping_dict[var_name])
                    
                    if found_vars:
                        # إذا وجدنا أكثر من متغير في السؤال (مثل السؤال 1 و 4)
                        var_string = " ".join(list(dict.fromkeys(found_vars))) # إزالة التكرار
                        current_syntax = template.replace("{var}", var_string)
                        
                        final_syntax.append(f"* Question: {q}")
                        final_syntax.append(f"{current_syntax}\nEXECUTE.")
                        matched = True
                        break
            
            if not matched:
                final_syntax.append(f"* Question: {q}\n* [!] No matching rule found.")

        st.success("تم التوليد!")
        st.code("\n".join(final_syntax), language="spss")
    else:
        st.error("تأكد من الرابط وإدخال الأسئلة")
