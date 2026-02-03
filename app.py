import streamlit as st
import pandas as pd
from docx import Document
import io
import re

# 1. دالة استخراج البيانات من الوورد (تدعم الفقرات والجداول)
def extract_word_data(file):
    try:
        doc = Document(io.BytesIO(file.read()))
        file.seek(0)
        full_text = []
        for p in doc.paragraphs:
            if p.text.strip(): full_text.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip(): full_text.append(cell.text.strip())
        return full_text
    except:
        return []

# 2. محرك توليد السينتاكس (الربط الذكي بالمتغيرات)
def generate_advanced_syntax(paragraphs):
    # خريطة المتغيرات لـ Data Set 1 (بناءً على المصادر) 
    mapping = {
        "balance": "X1", "transaction": "X2", "services": "X3",
        "debit": "X4", "interest": "X5", "city": "X6"
    }
    
    syntax = [
        "* Encoding: UTF-8.",
        "* Prepared for: Dr. Mohamed A. Salam.",
        "* Scientific Justification: Based on MBA Applied Statistics Curriculum.\n",
        "VARIABLE LABELS X1 'Account Balance' X2 'ATM Transactions' X3 'Bank Services' X4 'Debit Card' X5 'Interest' X6 'City'.",
        "VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.\nEXECUTE.\n"
    ]

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "x1 =", "dr.", "best regards"]) or len(p) < 15:
            continue
            
        syntax.append(f"* --- [Q{q_idx}] {p[:80]}... --- .")
        
        # --- منطق الرسوم البيانية (تصحيح الأخطاء السابقة) ---
        if "bar chart" in p_low:
            # تحديد المتغير التابع والمستقل بذكاء
            dep = "X1" if "balance" in p_low else ("X2" if "transaction" in p_low else "X1")
            indep = "X6" if "city" in p_low else "X4"
            stat = "MEAN" if "average" in p_low else "MAX"
            syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({dep}) BY {indep} /TITLE='{stat} of {dep} by {indep}'.")

        # --- منطق التكرارات (RECODE & K-RULE) [cite: 7, 8] ---
        elif "frequency table" in p_low:
            if "categorical" in p_low:
                syntax.append("FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")
            elif "balance" in p_low:
                syntax.append("RECODE X1 (LO THRU 1000=1) (1001 THRU 2000=2) (HI=3) INTO X1_Classes.\nFREQUENCIES X1_Classes.")

        # --- المقاييس الوصفية (Mean, Median, Skewness) [cite: 5, 10] ---
        elif any(x in p_low for x in ["mean", "median", "mode", "deviation"]):
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS.")

        # --- فترات الثقة (Confidence Intervals)  ---
        elif "confidence interval" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            syntax.append("EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 99.")

        # --- تقسيم الملف (Split File)  ---
        elif "for each city" in p_low or "each gender" in p_low:
            syntax.append("SORT CASES BY X6.\nSPLIT FILE SEPARATE BY X6.\nDESCRIPTIVES X1 X2.\nSPLIT FILE OFF.")

        syntax.append("")
        q_idx += 1
        
    return "\n".join(syntax)

# --- واجهة Streamlit ---
st.title("📊 محرك الإحصاء الشامل (v6 Professional)")
u_word = st.file_uploader("ارفع ملف الأسئلة (.docx)", type=['docx'])

if u_word:
    paragraphs = extract_word_data(u_word)
    if paragraphs:
        syntax_code = generate_advanced_syntax(paragraphs)
        st.success("✅ تم توليد السينتاكس بنجاح!")
        st.code(syntax_code, language='spss')
        st.download_button("تحميل الملف (.sps)", syntax_code, "MBA_Analysis.sps")
