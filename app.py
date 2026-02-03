import streamlit as st
import pandas as pd
from docx import Document
import re

def smart_analysis_v2(doc_file, df_columns):
    doc = Document(doc_file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 5]
    
    mapping = {}
    for p in paragraphs:
        match = re.search(r"(X\d+)\s*=\s*([^(\n]+)", p, re.IGNORECASE)
        if match:
            var_name = match.group(1).upper()
            label_text = match.group(2).strip().lower()
            mapping[var_name] = label_text

    syntax = ["* --- Corrected Scientific Analysis for SPSS v26 --- *.\n"]
    
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    for p in paragraphs:
        p_low = p.lower()
        vars_in_q = [v for v in mapping.keys() if v in p.upper() or (len(mapping[v]) > 4 and mapping[v][:12] in p_low)]
        
        # --- تصحيح أوامر الرسم البياني ---

        # 1. Bar Chart (المعدل أو التكرار)
        if "bar chart" in p_low:
            if ("average" in p_low or "mean" in p_low) and len(vars_in_q) >= 2:
                # الصيغة الصحيحة لـ Mean Bar Chart في SPSS v26
                syntax.append(f"* {p}.\nGRAPH /BAR(SIMPLE)=MEAN({vars_in_q[0]}) BY {vars_in_q[1]}.")
            elif vars_in_q:
                syntax.append(f"* {p}.\nGRAPH /BAR(SIMPLE)=COUNT BY {vars_in_q[0]}.")

        # 2. Histogram
        elif "histogram" in p_low:
            for v in vars_in_q:
                syntax.append(f"* {p}.\nGRAPH /HISTOGRAM={v}.")

        # 3. Pie Chart
        elif "pie chart" in p_low:
            if vars_in_q:
                syntax.append(f"* {p}.\nGRAPH /PIE=COUNT BY {vars_in_q[0]}.")

        # 4. Frequencies & Descriptives
        elif any(word in p_low for word in ["frequency table", "categorical"]):
            if vars_in_q:
                syntax.append(f"* {p}.\nFREQUENCIES VARIABLES={' '.join(vars_in_q)} /ORDER=ANALYSIS.")

        elif any(word in p_low for word in ["mean", "median", "calculate", "standard deviation"]):
            if vars_in_q:
                syntax.append(f"* {p}.\nDESCRIPTIVES VARIABLES={' '.join(vars_in_q)} /STATISTICS=MEAN STDDEV MIN MAX KURTOSIS SKEWNESS.")

        # 5. Hypothesis Testing (T-TEST)
        elif "test the hypothesis" in p_low or "difference" in p_low:
            if len(vars_in_q) >= 2:
                syntax.append(f"* {p}.\nT-TEST GROUPS={vars_in_q[1]}(0 1) /VARIABLES={vars_in_q[0]}.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة المستخدم
st.title("🧙‍♂️ SPSS Master Generator (V26 Optimized)")
up_excel = st.file_uploader("Excel Data", type=['xlsx', 'xls'])
up_word = st.file_uploader("Word Questions (docx)", type=['docx'])

if up_excel and up_word:
    df = pd.read_excel(up_excel)
    final_syntax = smart_analysis_v2(up_word, df.columns)
    st.code(final_syntax, language='spss')
    st.download_button("Download Corrected Syntax", final_syntax, "SPSS_Fixed.sps")
