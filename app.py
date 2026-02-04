import streamlit as st
import pandas as pd
import numpy as np
import re
import math

def generate_ultimate_exam_syntax(df, var_defs, questions_text):
    # 1. تحليل المتغيرات (Mapping)
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

    # 2. إعدادات البيانات الأساسية
    n = len(df) if df is not None else 60
    k_rule = math.ceil(math.log2(n)) if n > 0 else 6 # قاعدة 2^k >= n
    
    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* UNIVERSAL EXAM SOLVER - MBA PROFESSIONAL EDITION",
        "* Follows Dr. Mohamed Salam Methodology Step-by-Step",
        "* " + "="*75 + ".\n"
    ]

    # [PRE-ANALYSIS SETUP]
    syntax.append("TITLE 'PRE-ANALYSIS SETUP: Defining Variable Labels and Values'.")
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # تعريف ذكي للقيم (Value Labels)
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # [PHASE 2] محرك تحليل الأسئلة "سؤال بسؤال"
    # تقسيم الأسئلة بناءً على الأرقام أو الأسطر الجديدة
    questions = re.split(r'\n\s*\d+[\.\)]', questions_text)
    q_count = 1

    for q in questions:
        q_content = q.strip()
        if len(q_content) < 10: continue
        
        q_low = q_content.lower()
        syntax.append(f"* " + "-"*75 + ".")
        syntax.append(f"TITLE 'QUESTION {q_count}: {q_content[:50]}...'.")
        syntax.append(f"* " + "-"*75 + ".")

        # تحديد المتغيرات المستهدفة في السؤال
        target_vars = [code for label, code in var_map.items() if label in q_low]
        v_main = target_vars[0] if target_vars else "X1"
        v_sec = target_vars[1] if len(target_vars) > 1 else "X2"

        # --- المنطق الإحصائي (Task Selection) ---

        # 1. الجداول التكرارية (Categorical)
        if "frequency" in q_low and any(w in q_low for w in ["categorical", "discrete", "debit", "interest", "city"]):
            syntax.append(f"FREQUENCIES VARIABLES={v_main} /ORDER=ANALYSIS.")
            syntax.append(f"ECHO 'INTERPRETATION: Distribution analysis for {v_main}'.")

        # 2. التقسيم (Recode) و K-rule
        elif "frequency" in q_low and any(w in q_low for w in ["classes", "k-rule", "suitable"]):
            syntax.append(f"* K-rule calculation: 2^{k_rule} >= {n}.")
            syntax.append(f"RECODE {v_main} (LO THRU 1000=1) (1000.01 THRU 2000=2) (2000.01 THRU HI=3) INTO {v_main}_Classes.")
            syntax.append(f"VALUE LABELS {v_main}_Classes 1 'Low' 2 'Medium' 3 'High'.")
            syntax.append(f"FREQUENCIES VARIABLES={v_main}_Classes /FORMAT=AVALUE.")
            syntax.append(f"ECHO 'COMMENT: Based on K-rule, {k_rule} classes are optimal for {v_main}'.")

        # 3. الإحصاء الوصفي والالتواء
        elif any(w in q_low for w in ["mean", "median", "mode", "skewness", "calculate"]):
            syntax.append(f"FREQUENCIES VARIABLES={v_main} {v_sec} /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS.")
            syntax.append(f"ECHO 'ANALYSIS: If Mean > Median, it is Right-Skewed. If Mean < Median, it is Left-Skewed'.")

        # 4. الرسوم البيانية (Histogram, Bar, Pie)
        elif "histogram" in q_low:
            syntax.append(f"GRAPH /HISTOGRAM={v_main} /TITLE='Histogram of {v_main}'.")
        
        elif "bar chart" in q_low:
            stat = "MEAN" if "average" in q_low else ("MAX" if "maximum" in q_low else "PCT")
            group = "X6" if "city" in q_low else "X4"
            if "grouped" in q_low or "each city" in q_low and "card" in q_low:
                syntax.append(f"GRAPH /BAR(GROUPED)={stat}({v_main}) BY {group} BY X4 /TITLE='{stat} of {v_main} by {group}'.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({v_main}) BY {group} /TITLE='{stat} of {v_main} by {group}'.")

        elif "pie chart" in q_low:
            syntax.append(f"GRAPH /PIE=PCT BY {v_main} /TITLE='Percentage Distribution of {v_main}'.")

        # 5. تحليل المجموعات (Split File)
        elif "each city" in q_low or "each gender" in q_low or "card or not" in q_low:
            group = "X6" if "city" in q_low else "X4"
            syntax.append(f"SORT CASES BY {group}.\nSPLIT FILE SEPARATE BY {group}.")
            syntax.append(f"FREQUENCIES VARIABLES={v_main} /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS.")
            syntax.append("SPLIT FILE OFF.")

        # 6. فترات الثقة والاعتدالية والـ Outliers
        elif any(w in q_low for w in ["confidence", "normality", "outliers", "extreme"]):
            syntax.append(f"EXAMINE VARIABLES={v_main} /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in q_low: syntax.append(f"EXAMINE VARIABLES={v_main} /CINTERVAL 99.")
            syntax.append("ECHO 'RULE: If Shapiro-Wilk Sig > 0.05, apply Empirical Rule. If < 0.05, use Chebyshev'.")

        syntax.append("\n")
        q_count += 1

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="Ultimate SPSS Solver", layout="wide")
st.title("🚀 المحرك الشامل لحل أي امتحان SPSS")
st.info("هذا التطبيق يتبع أسلوب 'الحل النموذجي' الذي يجمع بين التقسيم (Recode)، فصل النتائج (Split File)، والرسوم المتقدمة.")

up = st.sidebar.file_uploader("1. ارفع ملف البيانات", type=['xlsx', 'csv'])
col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("2. تعريف المتغيرات (Mapping):", height=250, value="x1 = Account Balance\nx2 = ATM transactions\nx4 = debit card\nx5 = interest\nx6 = city")
with col2:
    q_in = st.text_area("3. الصق أسئلة الامتحان (أي امتحان):", height=250)

if st.button("🚀 توليد الحل التكتيكي النموذجي"):
    if v_in and q_in:
        df = pd.read_excel(up) if up and up.name.endswith('xlsx') else (pd.read_csv(up) if up else None)
        solution = generate_ultimate_exam_syntax(df, v_in, q_in)
        st.subheader("✅ SPSS Syntax المولد (جاهز للتسليم):")
        st.code(solution, language="spss")
        st.download_button("تحميل الحل النهائي .SPS", solution, file_name="Ideal_Exam_Solution.sps")
