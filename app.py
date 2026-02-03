import streamlit as st
import pandas as pd
from docx import Document

def parse_full_word_data(doc_file):
    doc = Document(doc_file)
    extracted_data = []
    current_q = None
    current_opts = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text: continue
        
        # تمييز السؤال
        if text[0].isdigit() and len(text) > 10:
            if current_q:
                extracted_data.append({"question": current_q, "options": current_opts})
            current_q = text
            current_opts = []
        # تمييز الخيارات
        elif any(char in text for char in ['-', '=', ':']) and text[0].isdigit():
            current_opts.append(text)
            
    if current_q:
        extracted_data.append({"question": current_q, "options": current_opts})
    return extracted_data

st.set_page_config(page_title="SPSS Pro Generator", layout="wide")
st.title("🚀 نظام معالجة البيانات والسينتاكس المتكامل")

# المدخلات
with st.sidebar:
    st.header("الإعدادات")
    missing_val_code = st.text_input("كود القيم المفقودة الافتراضي", "99")
    include_missing = st.checkbox("تفعيل تعريف القيم المفقودة (Missing Values)", True)

col1, col2 = st.columns(2)
with col1:
    up_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx'])
with col2:
    up_word = st.file_uploader("ارفع ملف الوورد", type=['docx'])

if up_excel and up_word:
    df = pd.read_excel(up_excel)
    word_questions = parse_full_word_data(up_word)
    
    st.subheader("📋 مراجعة الربط والبيانات")
    
    preview_list = []
    excel_cols = df.columns.tolist()
    
    for i in range(min(len(excel_cols), len(word_questions))):
        preview_list.append({
            "Variable": excel_cols[i],
            "Label (Question)": word_questions[i]['question'],
            "Values": len(word_questions[i]['options'])
        })
    
    st.table(preview_list)

    if st.button("توليد السينتاكس الكامل ✨"):
        syntax = ["* Comprehensive SPSS Syntax for Eng. Mohamed.\n"]
        
        for i in range(len(preview_list)):
            col = preview_list[i]["Variable"]
            label = preview_list[i]["Label (Question)"]
            opts = word_questions[i]['options']
            
            # 1. Variable Labels
            syntax.append(f"VARIABLE LABELS {col} '{label}'.")
            
            # 2. Value Labels
            if opts:
                syntax.append(f"VALUE LABELS {col}")
                for opt in opts:
                    parts = opt.replace('-', ' ').replace('=', ' ').split()
                    if len(parts) >= 2:
                        syntax.append(f"  {parts[0]} '{' '.join(parts[1:])}'")
                syntax.append(".")

            # 3. Missing Values
            if include_missing:
                # إذا كان أحد الخيارات يحتوي على كلمة "مفقود" أو "لا أعرف"
                syntax.append(f"MISSING VALUES {col} ({missing_val_code}).")

        syntax.append("\nEXECUTE.")
        final_syntax = "\n".join(syntax)
        
        st.subheader("السينتاكس الجاهز:")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل الملف .sps", final_syntax, "final_spss_project.sps")