import streamlit as st
import pandas as pd
import re

def generate_expert_syntax(var_defs, questions_text):
    # 1. استخراج المتغيرات
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().lower()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code

    syntax = ["* Encoding: UTF-8.", "* " + "="*70, "* MBA Expert SPSS Engine - Final Curriculum Edition", "* " + "="*70 + ".\n"]

    # 2. منطق تحليل الأسئلة بناءً على المنهج
    q_low = questions_text.lower()
    
    # --- الإحصاء الوصفي (Chapter 2) ---
    if any(word in q_low for word in ["mean", "median", "mode", "skewness", "deviation"]):
        syntax.append("* [Chapter 2: Descriptive Statistics]")
        syntax.append("* Justification: Summarizing data using central tendency and dispersion[cite: 2].")
        # استهداف المتغيرات الرقمية (مثل Account Balance)
        targets = [v for k, v in var_map.items() if "balance" in k or "transaction" in k or "x1" in v or "x2" in v]
        if targets:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(targets)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE SKEWNESS /HISTOGRAM.")

    # --- اختبارات T-Test (Chapter 4 & 5) ---
    if "compare" in q_low or "difference" in q_low:
        if "each gender" in q_low or "debit card" in q_low:
            syntax.append("\n* [Chapter 4: Independent Samples T-Test]")
            syntax.append("* Justification: Comparing means of two independent groups[cite: 4].")
            syntax.append("T-TEST GROUPS=x4(0 1) /MISSING=ANALYSIS /VARIABLES=x1 /CRITERIA=CI(.95).")

    # --- تحليل التباين (Chapter 6: ANOVA) ---
    if "city" in q_low and ("difference" in q_low or "compare" in q_low):
        syntax.append("\n* [Chapter 6: One-Way ANOVA]")
        syntax.append("* Justification: Comparing means between more than two groups (Cities).")
        syntax.append("ONEWAY x1 BY x6 /STATISTICS DESCRIPTIVES /MISSING ANALYSIS /POSTHOC=TUKEY ALPHA(0.05).")

    # --- الارتباط والانحدار (Chapter 8, 9, 10) ---
    if "relationship" in q_low or "correlation" in q_low:
        syntax.append("\n* [Chapter 8: Correlation Analysis]")
        syntax.append("* Justification: Measuring the strength and direction of the linear relationship.")
        syntax.append("CORRELATIONS /VARIABLES=x1 x2 x3 /PRINT=TWOTAIL NOSIG /MISSING=PAIRWISE.")

    if "regression" in q_low or "predict" in q_low:
        syntax.append("\n* [Chapter 10: Multiple Regression]")
        syntax.append("* Justification: Analyzing the effect of multiple independent variables on a dependent variable[cite: 10].")
        syntax.append("REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA /DEPENDENT x1 /METHOD=ENTER x2 x3 x4 x5.")

    # --- الاستكشاف والـ K-rule (Chapter 2) ---
    if "classes" in q_low or "normality" in q_low:
        syntax.append("\n* [Chapter 2: Data Exploration & Normality]")
        syntax.append("* Justification: Identifying outliers and testing for normality distribution[cite: 2, 9].")
        syntax.append("EXAMINE VARIABLES=x1 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="MBA SPSS Master", layout="wide")
st.title("🎓 محرك SPSS الشامل (منهج د. محمد عبد السلام)")

uploaded_file = st.file_uploader("1. ارفع ملف البيانات", type=['xlsx', 'csv'])
col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("2. تعريف المتغيرات (مثال: x1 = Account Balance):", height=200)
with col2:
    q_in = st.text_area("3. أسئلة الامتحان:", height=200)

if st.button("توليد الحل النموذجي"):
    if v_in and q_in:
        solution = generate_expert_syntax(v_in, q_in)
        st.code(solution, language="spss")
        st.download_button("تحميل الملف .SPS", solution, file_name="Exam_Solution.sps")
