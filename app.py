import streamlit as st
import pandas as pd
import re

def generate_target_model_syntax(df, var_defs, questions_text):
    # Header Setup
    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*73 + ".",
        "* SPSS Syntax for Data Set 4 Analysis",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* " + "="*73 + ".\n"
    ]

    # --- [Step 1: Variable and Value Labeling] ---
    syntax.append("* --- [Variable and Value Labeling] --- .")
    syntax.append("* Scientific Justification: Proper labeling ensures that the output is readable and")
    syntax.append("* that categorical variables are correctly interpreted during analysis[cite: 1, 20].\n")
    
    var_map = {}
    lines = var_defs.split('\n')
    labels_list = []
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).lower().strip()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code
            labels_list.append(f"{v_code} \"{v_label}\"")
    
    if labels_list:
        syntax.append("VARIABLE LABELS " + " /".join(labels_list) + ".")
    
    # Value Labels (Fixed curriculum standards for Data Set 4)
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\"")
    syntax.append("  /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\"")
    syntax.append("  /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\"")
    syntax.append("  /x11 1 \"Managerial\" 2 \"Technical\" 3 \"Farming\" 4 \"Service\" 5 \"Production\" 6 \"Marketing\"")
    syntax.append("  /x12 1 \"Health\" 2 \"Financial\" 3 \"Family\" 4 \"Legal\" 5 \"Personal\" 6 \"Service\" 7 \"Miscellaneous\".")
    syntax.append("EXECUTE.\n")

    # Processing Questions Content
    q_low = questions_text.lower()

    # Q1: Frequency tables
    if "frequency table" in q_low and "categorical" in q_low:
        syntax.append("* --- [Q1] Frequency tables for Categorical Data --- .")
        syntax.append("* Scientific Justification: Frequency tables are used to summarize the distribution")
        syntax.append("* and percentage of categorical variables like gender, race, and region[cite: 1].")
        syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.\n")

    # Q2-Q4: Bar Charts (Grouped)
    if "bar chart" in q_low:
        syntax.append("* --- [Q2 - Q4] Bar Charts --- .")
        syntax.append("* Scientific Justification: Bar charts provide a visual comparison of frequency counts")
        syntax.append("* and mean values (Salary/Children) across different groups[cite: 2, 3, 4].")
        syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Number of Respondents by Region'.")
        syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Average Salary by Region'.")
        syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x8) BY x2 /TITLE='Average Children by Race'.\n")

    # Q5-Q6: Pie Charts (Grouped)
    if "pie chart" in q_low:
        syntax.append("* --- [Q5 - Q6] Pie Charts --- .")
        syntax.append("* Scientific Justification: Pie charts are effective for showing the composition")
        syntax.append("* of a whole, such as total salary distribution or gender percentage[cite: 5, 6].")
        syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Sum of Salaries by Occupation'.")
        syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Percentage'.\n")

    # Q7-Q8: Continuous Data & Descriptive Stats (Grouped)
    if "continuous" in q_low or "descriptive" in q_low:
        syntax.append("* --- [Q7 - Q8] Continuous Data and Descriptive Statistics --- .")
        syntax.append("* Scientific Justification: Recoding continuous variables into classes helps in")
        syntax.append("* identifying patterns. FREQUENCIES is used here instead of DESCRIPTIVES[cite: 7, 8].")
        syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.")
        syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.")
        syntax.append("VARIABLE LABELS Salary_Classes \"Salary (5 Classes)\" Age_Classes \"Age (5 Classes)\".\nEXECUTE.")
        syntax.append("FREQUENCIES VARIABLES=Salary_Classes Age_Classes /FORMAT=NOTABLE.")
        syntax.append("FREQUENCIES VARIABLES=x3 x9 x7 x8 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.\n")

    # Q9: Normality and Outliers
    if "normality" in q_low or "outliers" in q_low:
        syntax.append("* --- [Q9] Normality and Outliers --- .")
        syntax.append("* Scientific Justification: Normality tests determine the suitability of parametric tests.")
        syntax.append("* Boxplots are the standard method for identifying extreme outliers[cite: 9].")
        syntax.append("EXAMINE VARIABLES=x3 x10 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.\n")

    # Q10: Grouped Analysis (Split File)
    if "each gender" in q_low or "each region" in q_low:
        syntax.append("* --- [Q10] Grouped Analysis for Gender and Region --- .")
        syntax.append("* Scientific Justification: Split file allows for localized descriptive analysis[cite: 10].")
        syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.")
        syntax.append("FREQUENCIES VARIABLES=x3 x9 x7 x8 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.")
        syntax.append("SPLIT FILE OFF.\n")

    # Q19-Q20: Linear Regression
    if "regression" in q_low or "y =" in q_low:
        syntax.append("* --- [Q19 - Q20] Linear Regression Model --- .")
        syntax.append("* Scientific Justification: Regression measures the strength and direction of the")
        syntax.append("* relationship between predictors and General Happiness (x5).")
        syntax.append("REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA COLLIN")
        syntax.append("  /CRITERIA=PIN(.05) POUT(.10) /NOORIGIN /DEPENDENT x5")
        syntax.append("  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="MBA SPSS Engine", layout="wide")
st.title("🎓 Professional SPSS Syntax Engine (v26)")

uploaded_file = st.file_uploader("1. Upload Excel Data File", type=['xlsx', 'csv'])

if uploaded_file:
    # Read data safely
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
    st.success("File loaded successfully.")

    col1, col2 = st.columns(2)
    with col1:
        v_in = st.text_area("2. Paste Variable Mapping (e.g., x1 = Gender):", height=200)
    with col2:
        q_in = st.text_area("3. Paste Exam Questions:", height=200)

    if st.button("Generate Final Model Syntax"):
        if v_in and q_in:
            result = generate_target_model_syntax(df, v_in, q_in)
            st.code(result, language='spss')
            st.download_button("Download .SPS File", result, file_name="MBA_Analysis_Solution.sps")
