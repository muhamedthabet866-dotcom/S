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

    # 2. حساب خصائص البيانات (K-rule) [cite: 2]
    n = len(df) if df is not None else 100
    k_rule = round(1 + 3.322 * math.log10(n))

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* UNIVERSAL AUTO-SOLVER (MBA CURRICULUM EDITION)",
        "* FIXED: Pattern Matching Engine (No Syntax Errors)",
        "* " + "="*75 + ".\n"
    ]

    # [PHASE 1] تهيئة المتغيرات والقيم [cite: 2]
    syntax.append("TITLE 'PHASE 1: Variable & Value Definitions'.")
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # تعريف القيم الافتراضية بناءً على المنهج [cite: 2]
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # [PHASE 2] محرك تحليل الأسئلة - تم إصلاح الخطأ البرمجي هنا
    # تم تغيير الـ Regex ليكون بسيطاً وآمناً
    questions = re.split(r'\n\d+[\.\)]|\[source', questions_text)
    
    for i, q in enumerate(questions):
        q_content = q.strip()
        if len(q_content) < 5: continue
        
        q_low = q_content.lower()
        syntax.append(f"TITLE 'ANALYSIS FOR TASK: {i}'.")
        syntax.append(f"ECHO 'Question: {q_content[:100]}...'.")

        # ربط السؤال بالمتغيرات (X1, X2...) آلياً
        target_vars = [code for label, code in var_map.items() if label in q_low]
        vars_str = " ".join(target_vars) if target_vars else "X1 X2"

        # --- محرك اتخاذ القرار الإحصائي (Logic Engine) ---
        
        # أ. الإحصاء الوصفي والالتواء [cite: 2]
        if any(w in q_low for w in ["mean", "median", "mode", "skewness", "descriptive"]):
            syntax.append(f"FREQUENCIES VARIABLES={vars_str} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE SKEWNESS /FORMAT=NOTABLE.")

        # ب. التكرارات والرسم البياني [cite: 2]
        if any(w in q_low for w in ["frequency", "table", "classes"]):
            syntax.append(f"* Using K-rule: {k_rule} classes[cite: 2].")
            syntax.append(f"FREQUENCIES VARIABLES={vars_str} /HISTOGRAM /ORDER=ANALYSIS.")

        # ج. مقارنة المجموعات (T-Test & ANOVA) [cite: 4, 6]
        if any(w in q_low for w in ["compare", "difference", "between"]):
            if "city" in q_low or "group" in q_low:
                syntax.append(f"ONEWAY X1 BY X6 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
            else:
                syntax.append(f"T-TEST GROUPS=X4(0 1) /VARIABLES=X1.")

        # د. الاستكشاف والاعتدالية 
        if any(w in q_low for w in ["normality", "outliers", "confidence", "examine"]):
            syntax.append(f"EXAMINE VARIABLES={vars_str} /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in q_low: syntax.append(f"EXAMINE VARIABLES={vars_str} /CINTERVAL 99.")

        # هـ. الانحدار والارتباط 
        if any(w in q_low for w in ["regression", "predict", "relationship"]):
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X1 /METHOD=ENTER X2 X3 X4 X5.")

        syntax.append("ECHO '--------------------------------------------------'.\n")

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="Universal SPSS Master Solver", layout="wide")
st.title("🤖 المحرك الشامل لحل أي امتحان SPSS")
st.markdown("هذا البرنامج مصمم ليناسب منهج **د. محمد عبد السلام** ويحل أي امتحان ترفعه.")

with st.sidebar:
    st.header("1. البيانات")
    up = st.file_uploader("ارفع ملف الإكسيل (Data Set)", type=['xlsx', 'csv'])

col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("2. تعريف المتغيرات (مثال: x1=Account Balance):", height=250)
with col2:
    q_in = st.text_area("3. الصق نص الأسئلة بالكامل:", height=250)

if st.button("🚀 توليد الحل الإحصائي الكامل"):
    if v_in and q_in:
        df = None
        if up:
            df = pd.read_excel(up) if up.name.endswith('xlsx') else pd.read_csv(up)
        
        final_solution = universal_spss_engine(df, v_in, q_in)
        st.subheader("✅ كود SPSS Syntax المولد:")
        st.code(final_solution, language="spss")
        st.download_button("تحميل الحل النهائي .SPS", final_solution, file_name="Universal_Exam_Solution.sps")
