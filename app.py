import streamlit as st
import pandas as pd
import re
import math

# إصلاح مشكلة تقسيم الأسئلة وتوليد الكود
def generate_spss_syntax(df, var_defs, questions_text):
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().upper()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code

    n = len(df) if df is not None else 60
    k = math.ceil(1 + 3.322 * math.log10(n))

    syntax = ["* Encoding: UTF-8.\nVARIABLE LABELS"]
    for label, code in var_map.items():
        syntax.append(f"  {code} '{label.title()}'")
    syntax[-1] = syntax[-1] + "."
    
    syntax.append("VALUE LABELS X4 1 'Yes' 0 'No' /X5 1 'Yes' 0 'No' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.\nEXECUTE.")

    # تقسيم الأسئلة بناءً على الأرقام
    questions = re.split(r'(?:\n|^)\s*\d+[\.\)]', questions_text)
    
    for q in questions:
        q_low = q.lower().strip()
        if not q_low: continue
        
        syntax.append(f"\n* --- Task Analysis ---")
        
        if "frequency" in q_low and any(x in q_low for x in ["categorical", "debit", "interest", "city"]):
            syntax.append("FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")
        
        if "balance" in q_low and "classes" in q_low:
            syntax.append(f"* Applying K-rule: {k} classes.\nRECODE X1 (LO THRU HI=COPY) INTO X1_Classes.\nFREQUENCIES VARIABLES=X1_Classes.")

        if "mean" in q_low or "skewness" in q_low:
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS /FORMAT=NOTABLE.")

        if "histogram" in q_low:
            syntax.append("GRAPH /HISTOGRAM=X1.\nGRAPH /HISTOGRAM=X2.")

        if "each city" in q_low:
            syntax.append("SORT CASES BY X6.\nSPLIT FILE SEPARATE BY X6.\nDESCRIPTIVES VARIABLES=X1 X2.\nSPLIT FILE OFF.")

        if "bar chart" in q_low:
            if "average" in q_low: syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
            elif "max" in q_low: syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4.")
            elif "percentage" in q_low: syntax.append("GRAPH /BAR(SIMPLE)=PCT BY X5.")

        if "pie chart" in q_low:
            syntax.append("GRAPH /PIE=PCT BY X5.")

        if "normality" in q_low or "confidence" in q_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة التطبيق
st.title("📊 MBA SPSS Smart Solver")
up = st.file_uploader("Upload Data (Excel/CSV)", type=['csv', 'xlsx'])
v_in = st.text_area("Variable Mapping (X1=Balance...)", value="X1=Balance\nX2=Transactions\nX4=Debit Card\nX5=Interest\nX6=City")
q_in = st.text_area("Paste Exam Questions Here")

if st.button("Generate Solution"):
    df = pd.read_csv(up) if up else None
    sol = generate_spss_syntax(df, v_in, q_in)
    st.code(sol, language="spss")
