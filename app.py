import streamlit as st
import pandas as pd
import numpy as np
import re
import math

def generate_master_exam_syntax(df, var_defs, questions_text):
    # 1. تحليل المتغيرات
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().upper()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code

    # حساب الـ K-rule بناءً على حجم البيانات الفعلي
    n = len(df) if df is not None else 60
    k_val = round(1 + 3.322 * math.log10(n))
    
    syntax = [
        "* Encoding: UTF-8.",
        "SET SEED=1234567.",
        "* " + "="*75,
        "* MASTER EXAM SOLVER: DATA SET 1 (Banking Analysis)",
        "* Organized Question-by-Question for Exam Submission",
        "* " + "="*75 + ".\n"
    ]

    # [PRE-ANALYSIS]
    syntax.append("TITLE 'PRE-ANALYSIS SETUP: Labeling'.")
    labels = [f"{v} \"{k.title()}\"" for k, v in var_map.items()]
    syntax.append(f"VARIABLE LABELS {' /'.join(labels)}.")
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # [Q1] Frequency Tables
    syntax.append("TITLE 'QUESTION 1: Frequency Tables for Categorical Variables'.")
    syntax.append("FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")
    syntax.append("ECHO 'INTERPRETATION: Distribution of debit cards, interest, and city locations'.\n")

    # [Q2 & Q3] Recoding & K-Rule
    syntax.append("TITLE 'QUESTION 2 & 3: Continuous Data (Recoding & K-Rule)'.")
    syntax.append(f"* Using K-rule: k = 1 + 3.322 * log10({n}) = {k_val} classes.")
    # اقتراح RECODE افتراضي بناءً على البيانات
    syntax.append("RECODE X1 (LO THRU 1000=1) (1000.01 THRU 2000=2) (2000.01 THRU 3000=3) (3000.01 THRU HI=4) INTO X1_Classes.")
    syntax.append("VARIABLE LABELS X1_Classes 'Account Balance (Categorized)'.")
    syntax.append("FREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.\n")

    # [Q4 & Q6] Descriptives & Skewness
    syntax.append("TITLE 'QUESTION 4 & 6: Descriptive Stats & Skewness Analysis'.")
    syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")
    syntax.append("ECHO 'COMMENT: If Skewness is between -1 and +1, the distribution is approximately symmetric'.\n")

    # [Q5] Histograms
    syntax.append("TITLE 'QUESTION 5: Individual Histograms'.")
    syntax.append("GRAPH /HISTOGRAM=X1 /TITLE='Distribution of Account Balance'.")
    syntax.append("GRAPH /HISTOGRAM=X2 /TITLE='Distribution of ATM Transactions'.\n")

    # [Q7 & Q8] Split Analysis
    syntax.append("TITLE 'QUESTION 7 & 8: Grouped Analysis (City & Debit Card)'.")
    syntax.append("SORT CASES BY X6.\nSPLIT FILE SEPARATE BY X6.")
    syntax.append("DESCRIPTIVES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN STDDEV MIN MAX SKEWNESS.")
    syntax.append("SPLIT FILE OFF.\n")
    
    syntax.append("SORT CASES BY X4.\nSPLIT FILE SEPARATE BY X4.")
    syntax.append("DESCRIPTIVES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN STDDEV SKEWNESS.")
    syntax.append("SPLIT FILE OFF.\n")

    # [Visuals]
    syntax.append("TITLE 'VISUALIZATIONS: Bar and Pie Charts'.")
    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 /TITLE='Avg Balance by City'.")
    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 /TITLE='Avg Balance by City and Card Status'.")
    syntax.append("GRAPH /PIE=COUNT BY X5 /TITLE='Percentage of Customers Receiving Interest'.\n")

    # [Q9] Explore & Normality
    syntax.append("TITLE 'QUESTION 9: Normality, CI, and Outliers'.")
    syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
    syntax.append("EXAMINE VARIABLES=X1 /CINTERVAL 99.")
    syntax.append("ECHO 'RULE: If Shapiro-Wilk Sig > 0.05, apply Empirical Rule. If < 0.05, use Chebyshev'.\n")

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Master Solver", layout="wide")
st.title("🎓 المحلل الإحصائي الشامل (إصدار الامتحان)")

file = st.file_uploader("1. ارفع ملف الداتا", type=['xlsx', 'csv'])
c1, c2 = st.columns(2)
with c1:
    v_in = st.text_area("2. تعريف المتغيرات (Mapping)", value="x1 = Account Balance\nx2 = ATM Transactions\nx3 = Other Services\nx4 = Debit Card\nx5 = Interest\nx6 = City", height=200)
with c2:
    q_in = st.text_area("3. أسئلة الامتحان", height=200)

if st.button("توليد الحل التكتيكي النموذجي"):
    if v_in:
        df = pd.read_excel(file) if file and file.name.endswith('xlsx') else (pd.read_csv(file) if file else None)
        solution = generate_master_exam_syntax(df, v_in, q_in)
        st.subheader("🚀 SPSS Syntax المولد (جاهز للتسليم):")
        st.code(solution, language="spss")
        st.download_button("تحميل الحل .SPS", solution, file_name="Final_Exam_Solution.sps")
