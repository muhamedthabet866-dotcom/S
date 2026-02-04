import streamlit as st
import pandas as pd
import re

def generate_exact_final_syntax(df, var_defs, questions_text):
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
    [cite_start]syntax.append("* that categorical variables are correctly interpreted during analysis[cite: 1, 20].\n")
    
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
    
    syntax.append("VARIABLE LABELS " + " /".join(labels_list) + ".")
    
    # Value Labels (كما في النموذج)
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\"")
    syntax.append("  /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\"")
    syntax.append("  /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\"")
    syntax.append("  /x11 1 \"Managerial\" 2 \"Technical\" 3 \"Farming\" 4 \"Service\" 5 \"Production\" 6 \"Marketing\"")
    syntax.append("  /x12 1 \"Health\" 2 \"Financial\" 3 \"Family\" 4 \"Legal\" 5 \"Personal\" 6 \"Service\" 7 \"Miscellaneous\".")
    syntax.append("EXECUTE.\n")

    # --- معالجة الأسئلة وتجميعها ---
    q_low = questions_text.lower()

    # Q1: Frequency
    if "frequency table" in q_low and "categorical" in q_low:
        syntax.append("* --- [Q1] Frequency tables for Categorical Data --- .")
        syntax.append("* Scientific Justification: Frequency tables are used to summarize the distribution")
        [cite_start]syntax.append("* and percentage of categorical variables like gender, race, and region[cite: 1].")
        syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.\n")

    # Q2 - Q4: Bar Charts (تجميع العناوين)
    if "bar chart" in q_low:
        syntax.append("* --- [Q2 - Q4] Bar Charts --- .")
        syntax.append("* Scientific Justification: Bar charts provide a visual comparison of frequency counts")
        [cite_start]syntax.append("* and mean values (Salary/Children) across different groups[cite: 2, 3, 4].")
        syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Number of Respondents by Region'.")
        syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Average Salary by Region'.")
        syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x8) BY x2 /TITLE='Average Children by Race'.\n")

    # Q5 - Q6: Pie Charts
    if "pie chart" in q_low:
        syntax.append("* --- [Q5 - Q6] Pie Charts --- .")
        syntax.append("* Scientific Justification: Pie charts are effective for showing the composition")
        [cite_start]syntax.append("* of a whole, such as total salary distribution or gender percentage[cite: 5, 6].")
        syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Sum of Salaries by Occupation'.")
        syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Percentage'.\n")

    # Q7 - Q8: Continuous Data
    if "continuous" in q_low or "descriptive" in q_low:
        syntax.append("* --- [Q7 - Q8] Continuous Data and Descriptive Statistics --- .")
        syntax.append("* Scientific Justification: Recoding continuous variables into classes helps in")
        syntax.append("* identifying patterns. FREQUENCIES is used here instead of DESCRIPTIVES to")
        [cite_start]syntax.append("* correctly calculate Median and Mode in SPSS[cite: 7, 8].")
        syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.")
        syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.")
        syntax.append("VARIABLE LABELS Salary_Classes \"Salary (5 Classes)\" Age_Classes \"Age (5 Classes)\".\nEXECUTE.\n")
        syntax.append("FREQUENCIES VARIABLES=Salary_Classes Age_Classes /FORMAT=NOTABLE.")
        syntax.append("FREQUENCIES VARIABLES=x3 x9 x7 x8 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.\n")

    # Q9: Normality
    if "normality" in q_low or "outliers" in q_low:
        syntax.append("* --- [Q9] Normality and Outliers --- .")
        syntax.append("* Scientific Justification: Normality tests determine the suitability of parametric tests.")
        [cite_start]syntax.append("* Boxplots are the standard method for identifying extreme outliers[cite: 9].")
        syntax.append("EXAMINE VARIABLES=x3 x10 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.\n")

    # Q10: Grouped Analysis
    if "each gender" in q_low or "each region" in q_low:
        syntax.append("* --- [Q10] Grouped Analysis for Gender and Region --- .")
        syntax.append("* Scientific Justification: Split file allows for localized descriptive analysis for")
        [cite_start]syntax.append("* each subgroup (gender within regions) as requested[cite: 10].")
        syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.")
        syntax.append("FREQUENCIES VARIABLES=x3 x9 x7 x8 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.")
        syntax.append("SPLIT FILE OFF.\n")

    # Q11: Confidence Intervals
    if "confidence interval" in q_low:
        syntax.append("* --- [Q11] Confidence Intervals (95% and 99%) --- .")
        syntax.append("* Scientific Justification: Confidence intervals provide the range where the population")
        [cite_start]syntax.append("* mean is likely to fall. Run separately to avoid SPSS keyword conflicts[cite: 11].")
        syntax.append("EXAMINE VARIABLES=x3 x9 BY x4 /STATISTICS DESCRIPTIVES /CINTERVAL 95 /PLOT NONE.")
        syntax.append("EXAMINE VARIABLES=x3 x9 BY x4 /STATISTICS DESCRIPTIVES /CINTERVAL 99 /PLOT NONE.\n")

    # Q12 - Q13: T-Tests
    if "35000" in q_low or "45 years" in q_low:
        syntax.append("* --- [Q12 - Q13] One-Sample T-Tests --- .")
        syntax.append("* Scientific Justification: T-tests evaluate if the sample mean significantly differs")
        [cite_start]syntax.append("* from a hypothesized population mean ($35000 or 45 years)[cite: 12, 13].")
        syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.\n")
        syntax.append("TEMPORARY.\nSELECT IF (x4 = 1 OR x4 = 2).\nT-TEST /TESTVAL=45 /VARIABLES=x9.\n")

    # Q14 - Q17: Comparisons
    if "significant difference" in q_low or "difference" in q_low:
        syntax.append("* --- [Q14 - Q17] Comparing Group Differences --- .")
        syntax.append("* Scientific Justification: Independent T-tests compare two groups, while ANOVA")
        [cite_start]syntax.append("* tests differences across three or more categories[cite: 14, 16, 17].")
        syntax.append("T-TEST GROUPS=x4(1 2) /VARIABLES=x5.\n")
        syntax.append("RECODE x4 (1 2=1) (3=2) INTO Region_EW.\nT-TEST GROUPS=Region_EW(1 2) /VARIABLES=x8.\n")
        syntax.append("RECODE x9 (LO THRU 50=1) (50.01 THRU HI=2) INTO Age_50.\nT-TEST GROUPS=Age_50(1 2) /VARIABLES=x5.\n")
        syntax.append("T-TEST GROUPS=x2(1 2) /VARIABLES=x8.\n")
        
        # Specific Q15 logic
        syntax.append("* [Q15] Specific comparison for White respondents.")
        syntax.append("TEMPORARY.\nSELECT IF (x2 = 1).")
        syntax.append("RECODE x9 (LO THRU 45=1) (45.01 THRU HI=2) INTO Age_45_W.")
        syntax.append("T-TEST GROUPS=Age_45_W(1 2) /VARIABLES=x5.\n")
        
        syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES.")
        syntax.append("ONEWAY x5 BY x2 /STATISTICS DESCRIPTIVES.\n")

    # Q18: Schooling & Correlations
    if "schooling" in q_low or "correlation" in q_low:
        syntax.append("* --- [Q18] Schooling ANOVA and Correlations --- .")
        syntax.append("* Scientific Justification: Pearson correlation is used for continuous data, while")
        [cite_start]syntax.append("* Spearman is used for ordinal or non-normal data[cite: 18].")
        syntax.append("RECODE x10 (10 THRU 12=1) (13 THRU 17=2) (18 THRU HI=3) INTO School_Cat.\nEXECUTE.")
        syntax.append("ONEWAY x3 BY School_Cat /STATISTICS DESCRIPTIVES.\n")
        syntax.append("CORRELATIONS /VARIABLES=x3 x9.")
        syntax.append("NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.\n")

    # Q19 - Q20: Regression
    if "regression" in q_low or "y =" in q_low:
        syntax.append("* --- [Q19 - Q20] Linear Regression Model --- .")
        syntax.append("* Scientific Justification: Regression measures the strength and direction of the")
        [cite_start]syntax.append("* relationship between predictors and General Happiness (x5)[cite: 19, 20].")
        syntax.append("REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA COLLIN")
        syntax.append("  /CRITERIA=PIN(.05) POUT(.10) /NOORIGIN /DEPENDENT x5")
        syntax.append("  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("Final Model Syntax Generator")
file = st.file_uploader("Upload Excel", type=['xlsx', 'csv'])
if file:
    df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
    v_in = st.text_area("Variables", height=150)
    q_in = st.text_area("Questions", height=150)
    if st.button("Generate Final Syntax"):
        st.code(generate_exact_final_syntax(df, v_in, q_in), language='spss')
