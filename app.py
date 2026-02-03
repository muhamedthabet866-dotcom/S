import streamlit as st
import pandas as pd
from docx import Document
import re

def smart_analysis(doc_file, df_columns):
    doc = Document(doc_file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 5]
    
    mapping = {}
    # 1. استخراج التعريفات (الخريطة)
    for p in paragraphs:
        match = re.search(r"(X\d+)\s*=\s*([^(\n]+)", p, re.IGNORECASE)
        if match:
            var_name = match.group(1).upper()
            label_text = match.group(2).strip().lower()
            mapping[var_name] = label_text

    syntax = ["* --- Comprehensive Scientific Analysis for SPSS v26 --- *.\n"]
    
    # 2. توليد Variable Labels
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    # 3. تحليل كل سطر في الوورد لتحويله إلى أمر إحصائي
    for p in paragraphs:
        p_low = p.lower()
        
        # البحث عن المتغيرات المذكورة في هذا السطر (سواء بالرمز X1 أو بالاسم النصي)
        vars_in_q = []
        for var_code, var_label in mapping.items():
            # إذا ذكر رمز المتغير (X1) أو جزء كبير من وصفه (Account Balance)
            if var_code.lower() in p_low or (len(var_label) > 3 and var_label[:15] in p_low):
                vars_in_q.append(var_code)
        
        # --- منطق توليد الأوامر ---
        
        # أ. الجداول التكرارية (Frequency)
        if "frequency table" in p_low or "categorical" in p_low:
            if vars_in_q:
                syntax.append(f"* {p}.\nFREQUENCIES VARIABLES={' '.join(vars_in_q)} /ORDER=ANALYSIS.")

        # ب. الرسوم البيانية (Charts)
        elif "histogram" in p_low:
            for v in vars_in_q:
                syntax.append(f"* {p}.\nGRAPH /HISTOGRAM={v} /TITLE='Histogram of {v}'.")

        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                # إذا كان هناك متغيرين (مثلاً: Average Salary by City)
                if len(vars_in_q) >= 2:
                    syntax.append(f"* {p}.\nGRAPH /BAR(MEAN)={vars_in_q[0]} BY {vars_in_q[1]}.")
                elif vars_in_q:
                    syntax.append(f"* {p}.\nGRAPH /BAR(MEAN) BY {vars_in_q[0]}.")
            else:
                for v in vars_in_q:
                    syntax.append(f"* {p}.\nGRAPH /BAR(COUNT) BY {v}.")

        elif "pie chart" in p_low:
            if vars_in_q:
                syntax.append(f"* {p}.\nGRAPH /PIE={vars_in_q[0]}.")

        # ج. الإحصاء الوصفي (Calculate mean, median, etc.)
        elif any(word in p_low for word in ["mean", "median", "mode", "calculate", "standard deviation"]):
            if vars_in_q:
                syntax.append(f"* {p}.\nFREQUENCIES VARIABLES={' '.join(vars_in_q)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        # د. اختبارات الفرضيات (Hypothesis Testing)
        elif "test the hypothesis" in p_low or "significance" in p_low:
            if len(vars_in_q) >= 2:
                # T-test لمجموعتين
                syntax.append(f"* {p}.\nT-TEST GROUPS={vars_in_q[1]}(0 1) /VARIABLES={vars_in_q[0]}.")
            elif "equal" in p_low or "less than" in p_low:
                # One Sample T-test
                val = re.findall(r'\d+', p)
                test_val = val[0] if val else "0"
                syntax.append(f"* {p}.\nT-TEST /TESTVAL={test_val} /VARIABLES={vars_in_q[0]}.")

        # هـ. فترات الثقة (Confidence Interval)
        elif "confidence interval" in p_low:
            if vars_in_q:
                syntax.append(f"* {p}.\nEXAMINE VARIABLES={' '.join(vars_in_q)} /STATISTICS DESCRIPTIVES /CINTERVAL 95.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة المستخدم
st.set_page_config(page_title="SPSS Master Generator", layout="wide")
st.title("🧙‍♂️ المولد الذكي لتحليل SPSS v26")
st.markdown("يرجى التأكد من رفع ملفات **.docx** (وليس .doc القديم) لضمان دقة القراءة.")

c1, c2 = st.columns(2)
with c1: up_excel = st.file_uploader("ملف البيانات (Excel)", type=['xlsx', 'xls'])
with c2: up_word = st.file_uploader("ملف الأسئلة (Word .docx)", type=['docx'])

if up_excel and up_word:
    df = pd.read_excel(up_excel)
    final_syntax = smart_analysis(up_word, df.columns)
    
    st.success("✅ تم تحليل الأسئلة وتوليد أوامر الرسم والتحليل!")
    st.code(final_syntax, language='spss')
    st.download_button("تحميل السينتاكس العلمي الكامل (.sps)", final_syntax, "SPSS_Full_Analysis.sps")
