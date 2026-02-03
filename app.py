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

# 2. محرك توليد السينتاكس المطور (MBA Professional Engine)
def generate_advanced_syntax(paragraphs):
    # خريطة المتغيرات لـ Data Set 1 (بناءً على التوصيف) 
    mapping = {
        "balance": "X1", "transaction": "X2", "services": "X3",
        "debit": "X4", "interest": "X5", "city": "X6"
    }
    
    syntax = [
        "* Encoding: UTF-8.",
        "* Prepared for: Dr. Mohamed A. Salam.",
        "* Scientific Justification: Based on MBA Applied Statistics Curriculum.\n",
        "VARIABLE LABELS X1 'Account Balance ($)' X2 'ATM Transactions' X3 'Other Services' "
        "X4 'Debit Card Holder' X5 'Interest Received' X6 'City Location'.",
        "VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.\nEXECUTE.\n"
    ]

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "x1 =", "dr.", "best regards"]) or len(p) < 15:
            continue
            
        syntax.append(f"* --- [QUESTION {q_idx}] {p[:80]}... --- .")
        
        # --- منطق الرسوم البيانية الذكي [cite: 2, 3, 11] ---
        if "bar chart" in p_low:
            dep = "X1" if "balance" in p_low else ("X2" if "transaction" in p_low else "X1")
            indep = "X6" if "city" in p_low else ("X4" if "debit" in p_low else "X5")
            stat = "MEAN" if "average" in p_low else ("MAX" if "maximum" in p_low else "COUNT")
            syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({dep}) BY {indep} /TITLE='{stat} of {dep} by {indep}'.")

        elif "pie chart" in p_low:
            syntax.append("GRAPH /PIE=PCT BY X5 /TITLE='Percentage of Interest Receivers'.")

        # --- منطق التكرارات وإعادة الترميز [cite: 7, 13, 23] ---
        elif "frequency table" in p_low:
            if "categorical" in p_low or any(v in p_low for v in ["has a", "city", "interest"]):
                syntax.append("FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")
            elif "balance" in p_low:
                syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (HI=4) INTO X1_Classes.")
                syntax.append("VALUE LABELS X1_Classes 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 'Over 1500'.\nEXECUTE.")
                syntax.append("FREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.")

        # --- المقاييس الوصفية والالتواء [cite: 8, 14, 24] ---
        elif any(x in p_low for x in ["mean", "median", "mode", "deviation", "skewness"]):
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS RANGE MIN MAX.")

        # --- فترات الثقة واختبارات الطبيعية [cite: 9, 15, 27] ---
        elif "confidence interval" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            syntax.append("EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 99.")

        elif "normality" in p_low or "outliers" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES.")
            syntax.append("ECHO 'RULE: If Shapiro-Wilk Sig > 0.05, apply Empirical Rule. If < 0.05, use Chebyshev'.")

        # --- التحليل الطبقي (Split File)  ---
        elif "each city" in p_low or "debit card or not" in p_low:
            sort_var = "X6" if "city" in p_low else "X4"
            syntax.append(f"SORT CASES BY {sort_var}.\nSPLIT FILE SEPARATE BY {sort_var}.")
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE.")
            syntax.append("SPLIT FILE OFF.")

        syntax.append("")
        q_idx += 1
        
    return "\n".join(syntax)

# --- واجهة Streamlit ---
st.title("🎓 MBA SPSS Professional Engine (v6)")
st.info("هذا المحرك يقوم بتحليل الأسئلة وربطها بالمتغيرات الصحيحة وفقاً لمنهج د. محمد عبد السلام.")

u_word = st.file_uploader("ارفع ملف الأسئلة (.docx)", type=['docx'])

if u_word:
    paragraphs = extract_word_data(u_word)
    if paragraphs:
        syntax_code = generate_advanced_syntax(paragraphs)
        st.success("✅ تم توليد السينتاكس بنجاح!")
        st.code(syntax_code, language='spss')
        st.download_button("تحميل الملف (.sps)", syntax_code, "Final_Analysis_Report.sps")
