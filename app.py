import streamlit as st
import pandas as pd
import re
import numpy as np

# 1. Logic to identify variables and their roles in a sentence
def identify_roles(question, var_map):
    found = []
    # Identify variables mentioned in the text (either by label or code)
    for label, code in var_map.items():
        if label in question.lower() or code in question.lower():
            found.append(code)
    # Remove duplicates while preserving order
    return list(dict.fromkeys(found))

def generate_curriculum_syntax(df, var_defs, questions_text):
    syntax = [
        "* Encoding: UTF-8.",
        "SET DECIMAL=DOT.",
        "* " + "="*75 + ".",
        "* FINAL MODEL SOLUTION - ALIGNED WITH CURRICULUM (CHAPTERS 1-10)",
        "* " + "="*75 + ".\n"
    ]

    # --- Step 1: Variable and Value Labeling ---
    var_map = {} # label -> code
    reverse_map = {} # code -> label
    lines = var_defs.split('\n')
    syntax.append("* --- [PRE-ANALYSIS] Defining Labels --- .")
    
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).lower().strip()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code
            reverse_map[v_code] = v_label
            syntax.append(f"VARIABLE LABELS {v_code} \"{v_label}\".")
    
    # Standard Value Labels based on curriculum
    syntax.append("\nVALUE LABELS x1 1 'Male' 2 'Female' /x2 1 'White' 2 'Black' 3 'Other'")
    syntax.append("  /x4 1 'North East' 2 'South East' 3 'West' /x5 1 'Very Happy' 2 'Pretty Happy' 3 'Not Too Happy'.")
    syntax.append("EXECUTE.\n")

    # --- Step 2: Processing Questions ---
    qs = questions_text.split('\n')
    for q in qs:
        q_low = q.lower().strip()
        if len(q_low) < 10 or "where" in q_low: continue
        
        syntax.append(f"* QUESTION: {q[:100]}")
        vars_found = identify_roles(q_low, var_map)

        # A. Frequencies (Categorical)
        if "frequency table" in q_low and "categorical" in q_low:
            cat_vars = [v for v in vars_found if v in ['x1', 'x2', 'x4', 'x5', 'x11', 'x12']]
            if not cat_vars: cat_vars = ['x1', 'x2', 'x4', 'x5']
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(cat_vars)} /ORDER=ANALYSIS.")

        # B. Charts with Correct Variable Order
        elif "chart" in q_low:
            if "bar chart" in q_low:
                if "average" in q_low or "mean" in q_low:
                    # Logic: Average [Dependent] BY [Independent]
                    # Usually Salary (x3), Age (x9), or Children (x8) are dependent
                    dep = next((v for v in vars_found if v in ['x3', 'x9', 'x8', 'x7']), "x3")
                    indep = next((v for v in vars_found if v != dep), "x4")
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({dep}) BY {indep}.")
                else:
                    # Frequency count by group
                    indep = vars_found[0] if vars_found else "x4"
                    syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {indep}.")
            
            elif "pie chart" in q_low:
                if "sum" in q_low:
                    dep = next((v for v in vars_found if v in ['x3', 'x9']), "x3")
                    indep = next((v for v in vars_found if v != dep), "x11")
                    syntax.append(f"GRAPH /PIE=SUM({dep}) BY {indep}.")
                else:
                    indep = next((v for v in vars_found if v in ['x1', 'x5']), "x1")
                    syntax.append(f"GRAPH /PIE=COUNT BY {indep}.")

        # C. Recoding into 5 Classes (Dynamic Range)
        elif "continuous data" in q_low or "classes" in q_low:
            for v in vars_found:
                if v in df.columns:
                    v_min, v_max = df[v].min(), df[v].max()
                    step = (v_max - v_min) / 5
                    syntax.append(f"RECODE {v} (LO THRU {v_min+step:.0f}=1) ({v_min+step:.0f} THRU {v_min+2*step:.0f}=2) "
                                 f"({v_min+2*step:.0f} THRU {v_min+3*step:.0f}=3) ({v_min+3*step:.0f} THRU {v_min+4*step:.0f}=4) "
                                 f"(HI=5) INTO {v}_CL.")
                    syntax.append(f"FREQUENCIES VARIABLES={v}_CL /FORMAT=NOTABLE.")

        # D. Normality & Outliers
        elif "normality" in q_low or "outliers" in q_low:
            target = vars_found[0] if vars_found else "x3"
            syntax.append(f"EXAMINE VARIABLES={target} /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.")

        # E. Hypothesis Testing (T-Test & ANOVA)
        elif "test" in q_low or "difference" in q_low:
            if "35000" in q_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "45" in q_low:
                syntax.append("TEMPORARY.\nSELECT IF (x4=1 OR x4=2).\nT-TEST /TESTVAL=45 /VARIABLES=x9.")
            elif "region" in q_low or "race" in q_low:
                # Decide ONEWAY ANOVA vs T-TEST
                dep = next((v for v in vars_found if v in ['x3', 'x5', 'x8', 'x9']), "x3")
                indep = next((v for v in vars_found if v != dep), "x4")
                if indep in df.columns and df[indep].nunique() <= 2:
                    syntax.append(f"T-TEST GROUPS={indep}(1 2) /VARIABLES={dep}.")
                else:
                    syntax.append(f"ONEWAY {dep} BY {indep} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # F. Regression
        elif "regression" in q_low or "y =" in q_low:
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN /DEPENDENT x5")
            syntax.append("  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("") # Spacer
        
    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit Interface ---
st.set_page_config(page_title="SPSS Exam Engine", layout="wide")
st.title("🎓 Professional SPSS Syntax Engine (v26)")

# File Upload
st.subheader("Step 1: Upload Data Set (Excel/CSV)")
uploaded_file = st.file_uploader("Upload file to calculate ranges and groups", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.success("File Loaded Successfully.")

    col1, col2 = st.columns(2)
    with col1:
        v_in = st.text_area("Step 2: Paste Variable Key (from 'Where' section):", height=250)
    with col2:
        q_in = st.text_area("Step 3: Paste Exam Questions:", height=250)

    if st.button("Generate Correct SPSS Solution"):
        if v_in and q_in:
            result = generate_curriculum_syntax(df, v_in, q_in)
            st.code(result, language='spss')
            st.download_button("Download .SPS File", result, "MBA_Solution.sps")
