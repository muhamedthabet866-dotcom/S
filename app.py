import streamlit as st
import pandas as pd
import numpy as np
import re
import math

def universal_spss_engine(df, var_defs, questions_text):
    # 1. بناء قاموس المتغيرات (Variable Mapping)
    var_map = {}
    variable_labels = []
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().upper()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code
            variable_labels.append(f"{v_code} \"{v_label}\"")

    # 2. حساب خصائص البيانات بناءً على الملف المرفوع
    n = len(df) if df is not None else 100
    k_rule = round(1 + 3.322 * math.log10(n))

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* UNIVERSAL AUTO-SOLVER (MBA CURRICULUM EDITION)",
        "* FIXED: Pattern Matching & String Literals",
        "* " + "="*75 + ".\n"
    ]

    # [PHASE 1] تهيئة المتغيرات
    syntax.append("TITLE 'PHASE 1: Variable & Value Definitions'.")
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # تعريف القيم الافتراضية للمتغيرات الوصفية
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # [PHASE 2] محرك تحليل الأسئلة (إصلاح الخطأ البرمجي هنا)
    # نستخدم r'' لضمان معالجة السلسلة النصية بشكل خام وتجنب مشاكل الـ Escape
    questions = re.split(r'\n\d+[\.\)]|\', questions_text)
    
    for i, q in enumerate(questions):
        q_content = q.strip()
        if len(q_content) < 5: continue
        
        q_low = q_content.lower()
        syntax.append(f"TITLE 'ANALYSIS FOR TASK: {i}'.")
        syntax.append(f"ECHO 'Question: {q_content[:100]}...'.")

        # ربط السؤال بالمتغيرات الصحيحة آلياً
        target_vars = [code for label, code in var_map.items() if label in q_low]
        vars_str = " ".join(target_vars) if target_vars else "X1 X2"

        # --- منطق اتخاذ القرار الإحصائي المعتمد على المنهج ---
        
        # أ. الإحصاء الوصفي والالتواء
        if any(w in q_low for w in ["mean", "median", "mode", "skewness", "descriptive", "distribution"]):
            syntax.append(f"FREQUENCIES VARIABLES={vars_str} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        # ب. التكرارات والـ K-rule
        if any(w in q_low for w in ["frequency", "table", "classes", "k-rule"]):
            syntax.append(f"* Applying K-rule: {k_rule} classes for distribution.")
            syntax.append(f"FREQUENCIES VARIABLES={vars_str} /HISTOGRAM /ORDER=ANALYSIS.")

        # ج. مقارنة المجموعات (T-Test & ANOVA)
        if any(w in q_low for w in ["compare", "difference", "between"]):
            if "city" in q_low or "group" in q_low:
                syntax.append(f"ONEWAY X1 BY X6 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
            else:
                syntax.append(f"T-TEST GROUPS=X4(0 1) /VARIABLES=X1.")

        # د. الاستكشاف والاعتدالية
        if any(w in q_low for w in ["normality", "outliers", "confidence", "examine", "extreme"]):
            syntax.append(f"EXAMINE VARIABLES={vars_str} /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in q_low:
                syntax.append(f"EXAMINE VARIABLES={vars_str} /CINTERVAL 99.")

        # هـ. الانحدار والارتباط
        if any(w in q_low for w in ["regression", "predict", "relationship", "correlation"]):
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X1 /METHOD=ENTER X2 X3 X4 X5.")

        syntax.append("ECHO '--------------------------------------------------'.\n")

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="Universal SPSS Solver", layout="wide")
st.title("🤖 المحرك الشامل لحل أي امتحان SPSS")

with st.sidebar:
    st.header("إعدادات البيانات")
    up = st.file_uploader("1. ارفع ملف الداتا (Excel/CSV)", type=['xlsx', 'csv'])

col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("2. تعريف المتغيرات (مثال: x1=Account Balance):", height=250)
with col2:
    q_in = st.text_area("3. الصق نص الأسئلة بالكامل (أي امتحان):", height=250)

if st.button("🚀 توليد الحل النموذجي للامتحان"):
    if v_in and q_in:
        df = None
        if up:
            df = pd.read_excel(up) if up.name.endswith('xlsx') else pd.read_csv(up)
        
        final_solution = universal_spss_engine(df, v_in, q_in)
        st.subheader("✅ كود SPSS Syntax المولد:")
        st.code(final_solution, language="spss")
        st.download_button("تحميل الحل النهائي .SPS", final_solution, file_name="MBA_Exam_Solution.sps")
