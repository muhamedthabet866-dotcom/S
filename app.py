import streamlit as st
import pandas as pd
import numpy as np
import re
import math

def universal_spss_engine(df, var_defs, questions_text):
    # 1. تنظيف وبناء قاموس المتغيرات (Variable Mapping)
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
        "* UNIVERSAL MBA SOLVER (Final Curriculum Edition)",
        "* Matches Questions with Dataset Mapping Automatically",
        "* " + "="*75 + ".\n"
    ]

    # [PHASE 1] تهيئة المتغيرات والقيم
    syntax.append("TITLE 'PHASE 1: Variable & Value Definitions'.")
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # تعريف القيم للمتغيرات الوصفية بناءً على المنهج
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # [PHASE 2] محرك تحليل الأسئلة الذكي
    # التقسيم بناءً على ترقيم الأسئلة الصريح
    questions = re.split(r'\n\s*\d+[\.\)]', questions_text)
    
    for i, q in enumerate(questions):
        q_content = q.strip()
        if len(q_content) < 10: continue # تجاهل السطور القصيرة جداً
        
        q_low = q_content.lower()
        syntax.append(f"TITLE 'ANALYSIS FOR QUESTION {i if i>0 else 1}'.")
        syntax.append(f"ECHO 'Processing Task: {q_content[:100]}...'.")

        # ربط السؤال بالمتغيرات (X1, X2...) آلياً
        target_vars = [code for label, code in var_map.items() if label in q_low]
        vars_str = " ".join(target_vars) if target_vars else "X1 X2"

        # --- منطق اتخاذ القرار الإحصائي (Inference Engine) ---
        
        # أ. الإحصاء الوصفي، المتوسطات، والالتواء
        if any(w in q_low for w in ["mean", "median", "mode", "skewness", "descriptive", "standard deviation"]):
            syntax.append(f"FREQUENCIES VARIABLES={vars_str} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        # ب. التكرارات، الجداول، والـ K-rule
        if any(w in q_low for w in ["frequency", "table", "classes", "k-rule"]):
            syntax.append(f"* Scientific Justification: K-rule suggests {k_rule} classes for n={n}.")
            syntax.append(f"FREQUENCIES VARIABLES={vars_str} /HISTOGRAM /ORDER=ANALYSIS.")

        # ج. مقارنة المجموعات وفروق المتوسطات (T-Test & ANOVA)
        if any(w in q_low for w in ["compare", "difference", "each city", "each gender"]):
            if "city" in q_low or "x6" in vars_str:
                syntax.append(f"ONEWAY X1 BY X6 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).") #
            else:
                syntax.append(f"T-TEST GROUPS=X4(0 1) /VARIABLES=X1.") #

        # د. الاستكشاف، فترات الثقة، والاعتدالية
        if any(w in q_low for w in ["normality", "outliers", "confidence", "examine", "extreme"]):
            syntax.append(f"EXAMINE VARIABLES={vars_str} /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in q_low:
                syntax.append(f"EXAMINE VARIABLES={vars_str} /CINTERVAL 99.") #

        # هـ. الانحدار والارتباط
        if any(w in q_low for w in ["regression", "predict", "relationship", "correlation"]):
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X1 /METHOD=ENTER X2 X3 X4 X5.") #

        # و. الرسوم البيانية المتخصصة
        if "bar chart" in q_low: syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
        if "pie chart" in q_low: syntax.append(f"GRAPH /PIE=COUNT BY X5.")

        syntax.append("ECHO '--------------------------------------------------'.\n")

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- واجهة المستخدم ---
st.set_page_config(page_title="Universal SPSS Master Solver", layout="wide")
st.title("🤖 المحرك الشامل لحل أي امتحان SPSS")

with st.sidebar:
    st.header("1. البيانات")
    up = st.file_uploader("ارفع ملف الإكسيل هنا", type=['xlsx', 'csv'])

col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("2. تعريف المتغيرات (مثال: x1=Account Balance):", height=250)
with col2:
    q_in = st.text_area("3. الصق نص الأسئلة بالكامل هنا:", height=250)

if st.button("🚀 توليد الحل الإحصائي الكامل"):
    if v_in and q_in:
        df = pd.read_excel(up) if up and up.name.endswith('xlsx') else (pd.read_csv(up) if up else None)
        final_solution = universal_spss_engine(df, v_in, q_in)
        st.subheader("✅ كود SPSS Syntax المولد:")
        st.code(final_solution, language="spss")
        st.download_button("تحميل الحل النهائي .SPS", final_solution, file_name="MBA_Comprehensive_Solution.sps")
