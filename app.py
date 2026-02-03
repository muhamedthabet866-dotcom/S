import streamlit as st
import pandas as pd
from docx import Document
import re

def extract_spss_mapping(doc_file):
    doc = Document(doc_file)
    mapping = {}
    # البحث عن الأسطر التي تبدأ بـ X متبوعة برقم (مثل X1, X2)
    pattern = r"X(\d+)\s*=\s*(.*)"
    
    for p in doc.paragraphs:
        text = p.text.strip()
        match = re.search(pattern, text)
        if match:
            var_num = f"X{match.group(1)}" # سيعطي X1
            var_label = match.group(2).strip() # سيعطي نص السؤال
            
            # محاولة استخراج القيم (Value Labels) إذا وجدت في نفس السطر مثل (1 = yes)
            values = re.findall(r"(\d+)\s*=\s*([a-zA-Zأ-ي]+)", var_label)
            mapping[var_num] = {
                "label": var_label,
                "values": values
            }
    return mapping

st.set_page_config(page_title="SPSS Syntax Pro - Eng. Mohamed", layout="wide")
st.title("📊 محول البيانات الذكي لسينتاكس SPSS")

col1, col2 = st.columns(2)
with col1:
    up_excel = st.file_uploader("ارفع ملف الإكسيل (Data Set)", type=['xlsx', 'xls', 'csv'])
with col2:
    up_word = st.file_uploader("ارفع ملف الوورد (Questions)", type=['docx', 'doc'])

if up_excel and up_word:
    # قراءة الإكسيل
    df = pd.read_excel(up_excel)
    # استخراج التعريفات من الوورد
    word_mapping = extract_spss_mapping(up_word)
    
    st.subheader("📋 نتيجة مطابقة المتغيرات")
    
    if not word_mapping:
        st.error("لم يتم العثور على تعريفات تبدأ بـ X1, X2 في ملف الوورد. تأكد من وجود قسم 'Where' في نهاية الملف.")
    else:
        preview_data = []
        syntax_lines = ["* SPSS Syntax Generated based on Variable Definitions.\n"]
        
        for col in df.columns:
            # تنظيف اسم العمود (تحويله لـ uppercase ليطابق X1 بدلاً من x1)
            clean_col = col.strip().upper()
            if clean_col in word_mapping:
                label = word_mapping[clean_col]["label"]
                vals = word_mapping[clean_col]["values"]
                
                preview_data.append({"العمود": col, "الوصف المستخرج": label, "عدد القيم": len(vals)})
                
                # إضافة VARIABLE LABELS
                syntax_lines.append(f"VARIABLE LABELS {col} '{label}'.")
                
                # إضافة VALUE LABELS
                if vals:
                    syntax_lines.append(f"VALUE LABELS {col}")
                    for val_num, val_text in vals:
                        syntax_lines.append(f"  {val_num} '{val_text}'")
                    syntax_lines.append(".")

        st.table(preview_data)
        
        if st.button("توليد ملف السينتاكس 🚀"):
            syntax_lines.append("\nEXECUTE.")
            final_code = "\n".join(syntax_lines)
            st.code(final_code, language='spss')
            st.download_button("تحميل .sps", final_code, "SPSS_Analysis.sps")
