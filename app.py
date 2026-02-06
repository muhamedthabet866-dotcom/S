import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

st.set_page_config(page_title="MBA SPSS Master Solver v3.1", layout="wide")
st.title("🎓 المحرك الذكي المطور (نسخة البيانات الضخمة)")

# --- إعدادات جلب المنهج ---
GITHUB_RAW_URL = "https://github.com/muhamedthabet866-dotcom/S/raw/refs/heads/main/spss_rules.xlsx"

@st.cache_data
def load_rules(url):
    try:
        response = requests.get(url, timeout=15)
        return pd.read_excel(BytesIO(response.content))
    except: return None

rules_df = load_rules(GITHUB_RAW_URL)

col1, col2 = st.columns(2)

with col1:
    st.subheader("⚙️ تعريف المتغيرات (Mapping)")
    mapping_input = st.text_area("أدخل المتغيرات:", 
        value="X1=account balance\nX2=ATM transactions\nX4=debit card\nX5=interest\nX6=city", height=250)

with col2:
    st.subheader("📝 أسئلة الامتحان")
    questions_input = st.text_area("الصق الأسئلة هنا كما هي:", height=250)

if st.button("🚀 توليد كود Syntax المنهج"):
    if rules_df is not None and questions_input:
        # 1. بناء قاموس المتغيرات وتنظيفه
        mapping_dict = {}
        for line in mapping_input.split('\n'):
            if '=' in line:
                parts = line.split('=')
                mapping_dict[parts[1].strip().lower()] = parts[0].strip().upper()
        
        sorted_vars = sorted(mapping_dict.keys(), key=len, reverse=True)

        # 2. تقسيم الأسئلة بشكل ذكي (حسب السطر فقط)
        # تجنب التقسيم العشوائي عند الأرقام داخل الجملة
        questions = [q.strip() for q in questions_input.split('\n') if len(q.strip()) > 10]

        final_syntax = ["* Generated for Eng. Mohamed.\nSET DECIMALS=DOT.\n"]

        for q in questions:
            clean_q = q.lower()
            matched = False
            
            # ترتيب القواعد من الأطول للأقصر لضمان أفضل مطابقة
            rules_df['key_len'] = rules_df['Keyword'].str.len()
            sorted_rules = rules_df.sort_values('key_len', ascending=False)

            for _, rule in sorted_rules.iterrows():
                keyword = str(rule['Keyword']).lower().strip()
                
                if keyword in clean_q:
                    template = str(rule['Syntax_Template'])
                    
                    # استخراج كافة المتغيرات المذكورة في هذا السؤال (مثل السؤال 1 و 4)
                    found_codes = []
                    for var_name in sorted_vars:
                        if var_name in clean_q:
                            found_codes.append(mapping_dict[var_name])
                    
                    if found_codes:
                        # إزالة التكرار مع الحفاظ على الترتيب
                        unique_codes = list(dict.fromkeys(found_codes))
                        var_str = " ".join(unique_codes)
                        
                        # تعويض الكود بالمتغيرات
                        current_syntax = template.replace("{var}", var_str)
                        
                        # منطق الرسوم البيانية (متغير التجميع)
                        if "{group}" in current_syntax:
                            group_var = unique_codes[-1] if len(unique_codes) > 1 else unique_codes[0]
                            current_syntax = current_syntax.replace("{group}", group_var)

                        final_syntax.append(f"* Question: {q}")
                        final_syntax.append(f"{current_syntax}\nEXECUTE.")
                        matched = True
                        break
            
            if not matched:
                final_syntax.append(f"* Question: {q}\n* [!] No matching rule found in Excel.")

        st.code("\n".join(final_syntax), language="spss")
    else:
        st.error("يرجى التأكد من رفع ملف المنهج وإدخال الأسئلة.")
