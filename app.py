import streamlit as st
import pandas as pd
import re

# Function to generate SPSS Syntax based on curriculum logic
def generate_final_exam_syntax(df, var_defs, questions_text):
    syntax = [
        "* Encoding: UTF-8.", 
        "SET DECIMAL=DOT.", 
        "* " + "="*65 + ".", 
        "* SPSS Comprehensive Solution for MBA Exam", 
        "* Prepared for: Dr. Mohamed A. Salam",
        "* " + "="*65 + ".\n"
    ]
    
    # 1. Variable Definitions Setup
    syntax.append("* --- [Step 1: Variable and Value Labeling] --- .")
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        # Regex to capture patterns like x1 = Gender or x1 : Gender
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_name = match.group(1).lower().strip()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_name
            syntax.append(f"VARIABLE LABELS {v_name} \"{v_label}\".")
    syntax.append("EXECUTE.\n")

    # 2. Analyzing Questions and Mapping to SPSS Commands
    qs = questions_text.split('\n')
    for i, q in enumerate(qs):
        q_low = q.lower().strip()
        if len(q_low) < 5: continue
        
        syntax.append(f"* [Q{i+1}] {q[:100]}")

        # Map variables mentioned in the question text
        found_vars = [v for label, v in var_map.items() if label in q_low]

        # --- Charts (Bar & Pie) ---
        if "chart" in q_low:
            if "bar chart" in q_low:
                if "average" in q_low and len(found_vars) >= 2:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}) BY {found_vars[1]}.")
                elif found_vars:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")
            elif "pie chart" in q_low and found_vars:
                syntax.append(f"GRAPH /PIE=COUNT BY {found_vars[0]}.")

        # --- Descriptive Statistics ---
        elif any(word in q_low for word in ["mean", "median", "mode", "deviation", "find the"]):
            if found_vars:
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.")

        # --- Classes / Recoding ---
        elif "classes" in q_low or "continuous" in q_low:
            for v in found_vars:
                if v in df.columns:
                    v_min, v_max = df[v].min(), df[v].max()
                    step = (v_max - v_min) / 5
                    syntax.append(f"* Recoding {v} into 5 classes based on range.")
                    syntax.append(f"RECODE {v} (LO THRU {v_min+step:.1f}=1) ({v_min+step:.1f} THRU {v_min+2*step:.1f}=2) "
                                 f"({v_min+2*step:.1f} THRU {v_min+3*step:.1f}=3) ({v_min+3*step:.1f} THRU {v_min+4*step:.1f}=4) "
                                 f"(HI=5) INTO {v}_CL.")
                    syntax.append(f"FREQUENCIES VARIABLES={v}_CL /FORMAT=NOTABLE.")

        # --- Hypothesis Testing (T-Test & ANOVA) ---
        elif any(word in q_low for word in ["test", "difference", "hypothesis"]):
            if "35000" in q_low and found_vars:
                syntax.append(f"T-TEST /TESTVAL=35000 /VARIABLES={found_vars[0]}.")
            elif "region" in q_low or "race" in q_low:
                dep = found_vars[0] if found_vars else "x3"
                factor = "x4" if "region" in q_low else "x2"
                syntax.append(f"ONEWAY {dep} BY {factor} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- Correlation and Regression ---
        elif "correlation" in q_low:
            if found_vars:
                syntax.append(f"CORRELATIONS /VARIABLES={' '.join(found_vars)} /PRINT=TWOTAIL NOSIG.")
        
        elif "regression" in q_low or "y =" in q_low:
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN /DEPENDENT x5 /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("") # Spacer
        
    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit Interface Setup ---
st.set_page_config(page_title="SPSS Syntax Generator", layout="wide")
st.title("🎓 Professional SPSS Syntax Generator (v26)")
st.markdown("Automate your statistical analysis based on the MBA curriculum.")

# 1. Data Upload Section
st.subheader("Step 1: Upload Data File")
uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    # Read the file into a DataFrame
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success("Data file loaded successfully!")
    st.dataframe(df.head(3)) # Show preview of the first 3 rows

    # 2. Text Input Sections
    col1, col2 = st.columns(2)
    with col1:
        st.info("Example format: x1 = gender / x3 = salary")
        v_in = st.text_area("Step 2: Paste Variable Definitions (from 'Where' section):", height=250)
    with col2:
        st.info("Paste the questions exactly as they appear in the exam.")
        q_in = st.text_area("Step 3: Paste Exam Questions:", height=250)

    # 3. Generate Output
    if st.button("Generate Final SPSS Syntax"):
        if v_in and q_in:
            final_output = generate_final_exam_syntax(df, v_in, q_in)
            st.code(final_output, language='spss')
            st.download_button(
                label="Download .SPS File", 
                data=final_output, 
                file_name="SPSS_Analysis_Output.sps", 
                mime="text/plain"
            )
        else:
            st.warning("Please provide both variable definitions and questions.")
