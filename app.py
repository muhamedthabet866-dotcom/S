import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from docx import Document
import io
import re

# 1. دالة استخراج النصوص من ملف الوورد (تدعم الفقرات والجداول)
def get_word_text(file):
    try:
        # قراءة الملف كـ Bytes
        doc = Document(io.BytesIO(file.read()))
        file.seek(0) # إعادة المؤشر للبداية
        
        full_text = []
        # استخراج النصوص من الفقرات
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        
        # استخراج النصوص من الجداول
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        full_text.append(cell.text.strip())
        
        return full_text
    except Exception as e:
        st.error(f"خطأ في قراءة ملف الوورد: تأكد أنه بصيغة .docx وليس .doc قديم. التفاصيل: {e}")
        return []

# 2. محرك توليد السينتاكس الذكي
def generate_spss_syntax(paragraphs, df_cols):
    # مابينج ذكي لربط الكلمات بالمسميات (تغطي Data sets 1, 2, 3, 4)
    smart_dict = {
        "salary": "x3", "balance": "x1", "wins": "x7", "area": "x3",
        "population": "x4", "age": "x9", "children": "x8", "gender": "x1",
        "race": "x2", "region": "x4", "league": "x2", "stadium": "x4"
    }
    
    syntax = [
        "* Encoding: UTF-8.",
        "* SPSS Syntax Generated for MBA Statistics Analysis.",
        "* Prepared for: Dr. Mohamed A. Salam.\n"
    ]
    
    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        # تخطي الأسطر التعريفية
        if any(x in p_low for x in ["where:", "x1 =", "dr.", "best regards"]) or len(p) < 15:
            continue
            
        syntax.append(f"* --- [Q{q_idx}] {p[:80]}... --- .")
        
        # منطق الاختبارات الإحصائية (Chapter 4, 6, 10)
        if "test the hypothesis" in p_low:
            val_match = re.search(r"(\d+)", p_low)
            test_val = val_match.group(1) if val_match else "0"
            if "equal" in p_low:
                syntax.append(f"T-TEST /TESTVAL={test_val} /VARIABLES=x3.")
            else:
                syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")
        
        elif "bar chart" in p_low:
            syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Mean Analysis'.")
            
        elif "regression" in p_low:
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN /DEPENDENT x5 /METHOD=ENTER x1 x2 x3 x4.")
            
        syntax.append("")
        q_idx += 1
        
    return "\n".join(syntax)

# --- واجهة المستخدم Streamlit ---
st.set_page_config(page_title="MBA SPSS Engine", layout="wide")
st.title("📊 محرك التحليل الإحصائي (v5 Professional)")

# رفع الملفات
u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word - .docx فقط)", type=['docx'])

if u_excel and u_word:
    try:
        # قراءة البيانات
        if u_excel.name.endswith('.csv'):
            df = pd.read_csv(u_excel)
        else:
            df = pd.read_excel(u_excel)
            
        # استخراج الأسئلة
        paragraphs = get_word_text(u_word)
        
        if paragraphs:
            # توليد الكود
            syntax_code = generate_spss_syntax(paragraphs, df.columns.tolist())
            
            st.success("✅ تم استخراج الأسئلة وتوليد الكود بنجاح!")
            st.code(syntax_code, language='spss')
            
            st.download_button("تحميل ملف الـ Syntax (.sps)", syntax_code, "Final_Analysis.sps")
            
            # عرض معاينة للبيانات
            with st.expander("معاينة البيانات المرفوعة"):
                st.write(df.head())
    except Exception as e:
        st.error(f"حدث خطأ غير متوقع: {e}")
