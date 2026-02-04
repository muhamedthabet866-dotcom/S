import streamlit as st
import pandas as pd
import re
import numpy as np

def generate_smart_syntax(df, variable_defs, questions_text):
    syntax = ["* Encoding: UTF-8.", "SET DECIMAL=DOT.", ""]
    
    # 1. Map Variables from User Inputs & Data columns
    var_map = {} # label -> var_name
    reverse_map = {} # var_name -> label
    
    # Extract labels from the "Where: X1=..." section
    lines = variable_defs.split('\n')
    for line in lines:
        match = re.search(r'(\w+)\s*[=:-]\s*([^(\n]+)', line)
        if match:
            v_name = match.group(1).strip().lower()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_name
            reverse_map[v_name] = v_label
            syntax.append(f"VARIABLE LABELS {v_name} '{v_label}'.")

    syntax.append("EXECUTE.\n")

    # 2. Process Questions using Data Intelligence
    questions = questions_text.split('\n')
    for q in questions:
        q_low = q.lower()
        if not q_low.strip(): continue
        syntax.append(f"* QUESTION: {q.strip()}")

        # Find which variables from our data are mentioned in this question
        mentioned_vars = []
        for label, v_code in var_map.items():
            if label in q_low or v_code in q_low:
                mentioned_vars.append(v_code)
        
        # --- A. RECODE / Classes (Chapter 2) ---
        if "classes" in q_low or "frequency table" in q_low:
            for v in mentioned_vars:
                if v in df.columns:
                    # Calculate 5 classes automatically
                    v_min, v_max = df[v].min(), df[v].max()
                    step = (v_max - v_min) / 5
                    bins = [v_min + i*step for i in range(6)]
                    recode_cmd = f"RECODE {v} (LO THRU {bins[1]:.1f}=1) ({bins[1]:.1f} THRU {bins[2]:.1f}=2) " \
                                 f"({bins[2]:.1f} THRU {bins[3]:.1f}=3) ({bins[3]:.1f} THRU {bins[4]:.1f}=4) " \
                                 f"({bins[4]:.1f} THRU HI=5) INTO {v}_CL."
                    syntax.append(recode_cmd)
                    syntax.append(f"FREQUENCIES VARIABLES={v}_CL /FORMAT=NOTABLE.")

        # --- B. Descriptive Stats (Chapter 2) ---
        elif any(word in q_low for word in ["mean", "median", "mode", "standard deviation"]):
            if mentioned_vars:
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(mentioned_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.")

        # --- C. Hypothesis Testing (Chapters 4, 6) ---
        elif "test the hypothesis" in q_low or "difference" in q_low:
            # One Sample T-test
            val_match = re.search(r"(?:equal|is)\s*(?:\$|)\s*(\d+)", q_low)
            if val_match and mentioned_vars:
                syntax.append(f"T-TEST /TESTVAL={val_match.group(1)} /VARIABLES={mentioned_vars[0]}.")
            
            # Independent Groups (T-test vs ANOVA)
            elif "between" in q_low and len(mentioned_vars) >= 2:
                dep_var = mentioned_vars[0]
                group_var = mentioned_vars[1]
                # Intelligence: Check number of unique values in grouping variable
                unique_vals = df[group_var].dropna().unique()
                if len(unique_vals) == 2:
                    syntax.append(f"T-TEST GROUPS={group_var}({int(min(unique_vals))} {int(max(unique_vals))}) /VARIABLES={dep_var}.")
                else:
                    syntax.append(f"ONEWAY {dep_var} BY {group_var} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- D. Regression & Correlation (Chapters 8, 9, 10) ---
        elif "regression" in q_low or "y =" in q_low:
            if len(mentioned_vars) > 1:
                dep = mentioned_vars[0]
                indeps = " ".join(mentioned_vars[1:])
                syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT {dep} /METHOD=ENTER {indeps}.")
        
        elif "correlation" in q_low:
            if len(mentioned_vars) >= 2:
                syntax.append(f"CORRELATIONS /VARIABLES={' '.join(mentioned_vars)} /PRINT=TWOTAIL NOSIG.")

        syntax.append("") # Spacer
    
    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# Streamlit UI
st.set_page_config(page_title="SPSS Smart Analyzer", layout="wide")
st.title("🎓 SPSS Smart Syntax Generator")
st.write("ارفع ملف البيانات، ضع الأسئلة، واحصل على الحل جاهزاً لبرنامج SPSS")

# 1. File Upload
uploaded_file = st.file_uploader("اختر ملف البيانات (Excel or CSV)", type=['csv', 'xlsx', 'xls'])

if uploaded_file:
    # Load data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"تم تحميل الملف بنجاح! يحتوي على {df.shape[1]} أعمدة.")
    st.dataframe(df.head(3)) # Show preview

    # 2. Input Fields
    col1, col2 = st.columns(2)
    with col1:
        var_input = st.text_area("أدخل تعريفات المتغيرات (مثال: X1=Gender):", height=200)
    with col2:
        ques_input = st.text_area("أدخل أسئلة الامتحان هنا:", height=200)

    # 3. Generate
    if st.button("توليد الحل الإحصائي"):
        if var_input and ques_input:
            syntax_code = generate_smart_syntax(df, var_input, ques_input)
            st.text_area("SPSS Syntax Output:", syntax_code, height=400)
            st.download_button("Download .SPS File", syntax_code, file_name="Exam_Solution.sps")
        else:
            st.warning("يرجى ملء صناديق النصوص لتوليد الكود.")
