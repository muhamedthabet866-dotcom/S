import streamlit as st
import re

def generate_spss_syntax(variable_definitions, questions_text):
    syntax = ["* Encoding: UTF-8.", "SET DECIMAL=DOT.", ""]
    
    # 1. Parsing Variable Definitions (Mapping)
    var_map = {} # Mapping label -> variable name (e.g., 'salary': 'x3')
    reverse_map = {} # Mapping variable name -> label
    
    lines = variable_definitions.split('\n')
    for line in lines:
        # Regex to catch patterns like "X1 = Gender" or "X3: Salary"
        match = re.search(r'(\w+)\s*[=:-]\s*([^(\n]+)', line)
        if match:
            var_name = match.group(1).strip().lower()
            label = match.group(2).strip()
            var_map[label.lower()] = var_name
            reverse_map[var_name] = label
            syntax.append(f"VARIABLE LABELS {var_name} '{label}'.")

    syntax.append("EXECUTE.\n")

    # 2. Parsing Questions
    questions = questions_text.split('\n')
    for q in questions:
        q_low = q.lower()
        if not q_low.strip(): continue
        
        syntax.append(f"* QUESTION: {q.strip()}")
        
        # --- DESCRIPTIVE STATISTICS (Chapter 2) ---
        if any(word in q_low for word in ["frequency table", "distribution"]):
            vars_to_use = [v for label, v in var_map.items() if label in q_low]
            if vars_to_use:
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(vars_to_use)} /FORMAT=NOTABLE.")
        
        elif any(word in q_low for word in ["mean", "median", "mode", "standard deviation", "min", "max"]):
            vars_to_use = [v for label, v in var_map.items() if label in q_low]
            if vars_to_use:
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(vars_to_use)} /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.")

        # --- GRAPHING (Chapter 2) ---
        elif "bar chart" in q_low:
            # Case: Average X by Y
            avg_match = re.search(r"average\s+([\w\s]+)\s+for\s+([\w\s]+)", q_low)
            if avg_match:
                target_var = next((v for label, v in var_map.items() if label in avg_match.group(1)), "VAR_X")
                group_var = next((v for label, v in var_map.items() if label in avg_match.group(2)), "VAR_Y")
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({target_var}) BY {group_var}.")
            else:
                target_var = next((v for label, v in var_map.items() if label in q_low), "VAR")
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {target_var}.")

        # --- NORMALITY & OUTLIERS (Chapter 2 & 7) ---
        elif any(word in q_low for word in ["normality", "outliers", "extreme", "empirical rule"]):
            target_var = next((v for label, v in var_map.items() if label in q_low), "VAR")
            syntax.append(f"EXAMINE VARIABLES={target_var} /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES.")

        # --- HYPOTHESIS TESTING (Chapter 4, 5, 6) ---
        elif "test the hypothesis" in q_low or "significant difference" in q_low:
            # One Sample T-Test (Equal to value)
            val_match = re.search(r"(?:equal|is)\s*(?:\$|)\s*(\d+)", q_low)
            if val_match:
                target_var = next((v for label, v in var_map.items() if label in q_low), "VAR")
                syntax.append(f"T-TEST /TESTVAL={val_match.group(1)} /VARIABLES={target_var}.")
            
            # Independent T-test (2 groups) vs ANOVA (>2 groups)
            elif "between" in q_low:
                vars_in_q = [v for label, v in var_map.items() if label in q_low]
                if len(vars_in_q) >= 2:
                    # Logic: If question mentions specific categories, use T-test or ANOVA
                    syntax.append(f"ONEWAY {vars_in_q[0]} BY {vars_in_q[1]} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- CORRELATION (Chapter 8) ---
        elif "correlation" in q_low:
            vars_in_q = [v for label, v in var_map.items() if label in q_low]
            if len(vars_in_q) >= 2:
                syntax.append(f"CORRELATIONS /VARIABLES={' '.join(vars_in_q)} /PRINT=TWOTAIL NOSIG.")

        # --- REGRESSION (Chapter 9 & 10) ---
        elif "regression" in q_low or "y =" in q_low:
            dep_var = next((v for label, v in var_map.items() if "happiness" in label or "y" in label or "dependent" in q_low), "Y_VAR")
            indep_vars = [v for v in reverse_map.keys() if v != dep_var]
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT {dep_var} /METHOD=ENTER {' '.join(indep_vars)}.")

        syntax.append("") # Spacer
        
    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# Streamlit UI
st.title("SPSS Exam Syntax Generator (Dr. Mohamed A. Salam Curriculum)")
st.subheader("تحويل أسئلة المنهج إلى كود SPSS Syntax")

col1, col2 = st.columns(2)
with col1:
    var_input = st.text_area("1. ضع تعريف المتغيرات هنا (من قسم Where):", 
                             placeholder="X1 = Gender\nX2 = Race\nX3 = Salary...")
with col2:
    ques_input = st.text_area("2. ضع أسئلة الامتحان هنا:", 
                              placeholder="Test the hypothesis that average salary is 35000\nDraw a bar chart for average salary by region...")

if st.button("توليد الكود (Generate Syntax)"):
    if var_input and ques_input:
        result = generate_spss_syntax(var_input, ques_input)
        st.code(result, language='spss')
        st.download_button("تحميل ملف Syntax", result, file_name="analysis.sps")
    else:
        st.error("الرجاء إدخال المتغيرات والأسئلة معاً.")
