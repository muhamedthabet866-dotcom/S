import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# إعداد الصفحة
st.set_page_config(page_title="MBA SPSS Solver Pro", layout="wide")
st.title("🎓 المحرك الذكي النهائي - المهندس محمد")

# دالة تنظيف النصوص لضمان مطابقة الكلمات المفتاحية
def ultra_clean(text):
    if not text or pd.isna(text): return ""
    text = str(text).lower()
    # إزالة الرموز والترقيم وتوحيد المسافات
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

# --- رابط المنهج من GitHub ---
# تأكد من استخدام رابط الـ RAW للملف الذي أرفقته
GITHUB_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/spss_rules.xlsx"

@st.cache_data
def load_rules(url):
    try:
        res = requests.get(url, timeout=15)
        # قراءة الملف كـ Excel بناءً على صيغة ملفك الأصلي
        return pd.read_excel(BytesIO(res.content))
    except:
        return None

rules_df = load_rules(GITHUB_URL)

# --- الواجهة ---
with st.sidebar:
    st.header("⚙️ الإعدادات")
    # تم إصلاح الخطأ في السطر 34 هنا بإغلاق النص بشكل صحيح
    mapping_input = st.text_area("تعريف المتغيرات (X1=name):", 
        value="X1=account balance\nX2=ATM transactions\nX4=debit card\nX5=interest\nX6=city", 
        height=200)

st.header("📝 أسئلة الامتحان")
questions_input = st.text_area("الصق الأسئلة هنا:", height=300)

if st.button("🚀 توليد الحل"):
    if rules_df is not None and questions_input:
        # 1. تحضير قاموس المتغيرات
        mapping = {}
        for line in mapping_input.split('\n'):
            if '=' in line:
                parts = line.split('=')
                mapping[ultra_clean(parts[1])] = parts[0].strip().upper()
        
        sorted_keys = sorted(mapping.keys(), key=len, reverse=True)

        final_syntax = ["* Generated for Eng. Mohamed.\nSET DECIMALS=DOT.\n"]

        # 2. معالجة الأسئلة سطر بسطر
        for q in questions_input.split('\n'):
            if len(q.strip()) < 5: continue
            
            q_clean = ultra_clean(q)
            matched = False
            
            # ترتيب القواعد للأطول أولاً لضمان أدق مطابقة
            rules_df['key_len'] = rules_df['Keyword'].astype(str).str.len()
            sorted_rules = rules_df.sort_values('key_len', ascending=False)

            for _, rule in sorted_rules.iterrows():
                keyword = ultra_clean(rule['Keyword'])
                
                # البحث المرن: هل الكلمة المفتاحية موجودة في السؤال؟
                if keyword and keyword in q_clean:
                    template = str(rule['Syntax_Template'])
                    
                    # استخراج كافة المتغيرات المذكورة في السؤال
                    found = []
                    for k in sorted_keys:
                        if k in q_clean:
                            found.append(mapping[k])
                    
                    if found:
                        unique_codes = list(dict.fromkeys(found))
                        var_str = " ".join(unique_codes)
                        
                        # تعويض الكود بالمتغيرات المكتشفة
                        syntax = template.replace("{var}", var_str)
                        if "{group}" in syntax:
                            # نأخذ المتغير الأخير كمتغير تصنيف (مثل City)
                            group = unique_codes[-1] if len(unique_codes) > 1 else unique_codes[0]
                            syntax = syntax.replace("{group}", group)
                        
                        final_syntax.append(f"* Question: {q.strip()}\n{syntax}\nEXECUTE.")
                        matched = True
                        break
            
            if not matched:
                final_syntax.append(f"* Question: {q.strip()}\n* [!] لم يتم العثور على قاعدة مطابقة في المنهج.")

        st.success("تم التوليد بنجاح")
        st.code("\n".join(final_syntax), language="spss")
    else:
        st.error("تأكد من الرابط وإدخال الأسئلة")
