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

    # 2. تحديد خصائص البيانات (Data Profiling)
    n = len(df) if df is not None else 100
    k_rule = round(1 + 3.322 * math.log10(n))

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* UNIVERSAL AUTO-SOLVER (MBA CURRICULUM EDITION)",
        "* Matches Any Exam Questions with Any Dataset Mapping",
        "* " + "="*75 + ".\n"
    ]

    # [PHASE 1] تهيئة المتغيرات بناءً على المنهج
    syntax.append("TITLE 'PHASE 1: Variable & Value Definitions'.")
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # التعرف الذكي على المتغيرات الوصفية لإضافة Value Labels
    categorical_vars = [v for k, v in var_map.items() if any(word in k for word in ["gender", "card", "interest", "city", "region", "yes", "no"])]
    if categorical_vars:
        labels_code = " /".join([f"{v} 0 'No/Group A' 1 'Yes/Group B'" for v in categorical_vars if v != "X6"])
        if labels_code: syntax.append(f"VALUE LABELS {labels_code}.")
    syntax.append("EXECUTE.\n")

    # [PHASE 2] محرك تحليل الأسئلة (Pattern Matching Engine)
    # هذا الجزء يحلل أي نص سؤال ويستخرج المهمة المطلوبة منه
    questions = re.split(r'\n\d+[\.\)]|\', questions_text)
    
    for i, q in enumerate(questions):
        if len(q.strip()) < 5: continue
        q_low = q.lower()
        syntax.append(f"TITLE 'QUESTION ANALYSIS: Task {i}'.")
        syntax.append(f"ECHO 'Processing Question: {q.strip()[:100]}...'.")

        # البحث عن المتغيرات المذكورة في هذا السؤال تحديداً
        target_vars = [code for label, code in var_map.items() if label in q_low]
        vars_str = " ".join(target_vars) if target_vars else "X1 X2" # افتراضي إذا لم يجد

        # --- القواعد الذكية لاختيار الاختبار (Decision Logic) ---
        
        # أ. الإحصاء الوصفي (Chapter 2)
        if any(w in q_low for w in ["mean", "median", "mode", "descriptive", "skewness", "variance"]):
            syntax.append(f"FREQUENCIES VARIABLES={vars_str} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE SKEWNESS /FORMAT=NOTABLE.")

        # ب. جداول التكرار وفئات الـ K-rule (Chapter 2)
        if "frequency" in q_low or "table" in q_low or "classes" in q_low:
            syntax.append(f"* Applying K-rule: {k_rule} classes recommended.")
            syntax.append(f"FREQUENCIES VARIABLES={vars_str} /HISTOGRAM /ORDER=ANALYSIS.")

        # ج. المقارنات وفروق المتوسطات (Chapter 4, 5, 6)
        if any(w in q_low for w in ["compare", "difference", "effect", "between"]):
            grouping_var = "X6" if "city" in q_low or "group" in q_low else "X4"
            if "city" in q_low or "more than two" in q_low:
                syntax.append(f"ONEWAY X1 BY {grouping_var} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).") #
            else:
                syntax.append(f"T-TEST GROUPS={grouping_var}(0 1) /VARIABLES=X1.") #

        # د. الاستكشاف وفترات الثقة والاعتدالية (Chapter 3)
        if any(w in q_low for w in ["normality", "outliers", "confidence", "extreme", "examine"]):
            syntax.append(f"EXAMINE VARIABLES={vars_str} /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in q_low: syntax.append(f"EXAMINE VARIABLES={vars_str} /CINTERVAL 99.")

        # هـ. الرسوم البيانية
        if "bar" in q_low: syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
        if "pie" in q_low: syntax.append(f"GRAPH /PIE=COUNT BY {target_vars[0] if target_vars else 'X5'}.")
        if "histogram" in q_low: syntax.append(f"GRAPH /HISTOGRAM={vars_str}.")

        # و. الارتباط والانحدار (Chapter 8, 9, 10)
        if "regression" in q_low or "predict" in q_low or "relationship" in q_low:
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X1 /METHOD=ENTER X2 X3 X4.") #

        syntax.append("ECHO '--------------------------------------------------'.\n")

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- واجهة Streamlit ---
st.set_page_config(page_title="Universal SPSS Solver", layout="wide")
st.title("🤖 المحرك الشامل لحل أي امتحان SPSS")
st.info("هذا التطبيق مبرمج ليفهم 'منطق المنهج' ويطبقه على أي بيانات أو أسئلة ترفعها.")

with st.sidebar:
    st.header("الإعدادات")
    up = st.file_uploader("1. ملف البيانات", type=['xlsx', 'csv'])

col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("2. تعريف متغيرات الامتحان الحالي:", height=300, 
                        placeholder="X1 = Account Balance\nX2 = Transactions...")
with col2:
    q_in = st.text_area("3. الصق نص الأسئلة بالكامل (أي امتحان):", height=300, 
                        placeholder="Construct a frequency table...\nCompare means between cities...")

if st.button("🚀 حل الامتحان وتوليد الـ Syntax"):
    if v_in and q_in:
        df = pd.read_excel(up) if up and up.name.endswith('xlsx') else (pd.read_csv(up) if up else None)
        final_solution = universal_spss_engine(df, v_in, q_in)
        st.subheader("✅ كود الحل النموذجي المولد:")
        st.code(final_solution, language="spss")
        st.download_button("تحميل ملف الحل .SPS", final_solution, file_name="Universal_Solution.sps")
