import streamlit as st
import pandas as pd
import re

def generate_full_curriculum_syntax(var_defs, questions_text):
    # مابينج افتراضي للمتغيرات الشائعة في Data Set 4 و 3
    smart_vars = {
        "salary": "x3", "age": "x9", "children": "x8", "gender": "x1",
        "race": "x2", "region": "x4", "happiness": "x5", "occupation": "x11",
        "exciting": "x6", "brothers": "x7", "school": "x10", "problem": "x12"
    }

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*70 + ".",
        "* MBA COMPREHENSIVE STATISTICAL ANALYSIS - ALL CHAPTERS",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* " + "="*70 + ".\n"
    ]

    # 1. معالجة التعريفات (Variable & Value Labels)
    syntax.append("* --- [CHAPTER 1 & 2: DATA PREPARATION] --- .")
    var_map = {}
    lines = var_defs.split('\n')
    
    # استخراج أسماء المتغيرات والتسميات
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_name = match.group(1).lower().strip()
            v_label = match.group(2).strip()
            var_map[v_name] = v_label
            syntax.append(f"VARIABLE LABELS {v_name} \"{v_label}\".")

    # إضافة Value Labels الشاملة للمنهج
    syntax.append("\nVALUE LABELS x1 1 'Male' 2 'Female' /x2 1 'White' 2 'Black' 3 'Others'")
    syntax.append("  /x4 1 'North East' 2 'South East' 3 'West' /x5 1 'Very Happy' 2 'Pretty Happy' 3 'Not Too Happy'")
    syntax.append("  /x11 1 'Managerial' 2 'Technical' 3 'Farming' 4 'Service' 5 'Production' 6 'Marketing'.\nEXECUTE.\n")

    # 2. محرك معالجة الأسئلة (Chapters 2 to 10)
    qs = questions_text.split('\n')
    for i, q in enumerate(qs):
        q_low = q.lower().strip()
        if len(q_low) < 10 or "where:" in q_low: continue

        syntax.append(f"* [Q] {q[:80]}...")

        # --- الفصل 2: التكرارات والرسوم ---
        if "frequency table" in q_low:
            syntax.append("* Justification: Summarizing data distribution.")
            if "categorical" in q_low:
                syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 /ORDER=ANALYSIS.")
            else:
                syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (HI=4) INTO X3_CL.")
                syntax.append("FREQUENCIES VARIABLES=X3_CL /FORMAT=AVALUE.")

        # --- الفصل 2 & 4: الرسوم البيانية المتطورة ---
        elif "bar chart" in q_low:
            syntax.append("* Justification: Visual comparison of metrics.")
            if "average" in q_low or "mean" in q_low:
                dep = "x3" if "salary" in q_low else "x8"
                indep = "x4" if "region" in q_low else "x1"
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({dep}) BY {indep}.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4.")

        # --- الفصل 4: التحليل الطبقي (Split File) ---
        elif "each gender" in q_low or "each region" in q_low:
            syntax.append("* Justification: Analyzing subgroups separately.")
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.\nDESCRIPTIVES VARIABLES=x3 x9 /STATISTICS=MEAN STDDEV.\nSPLIT FILE OFF.")

        # --- الفصل 6: ANOVA ---
        elif "difference" in q_low and ("region" in q_low or "race" in q_low):
            syntax.append("* Justification: Testing differences across >2 groups (ANOVA).")
            factor = "x4" if "region" in q_low else "x2"
            syntax.append(f"ONEWAY x3 BY {factor} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- الفصل 8: الارتباط (Correlation) ---
        elif "correlation" in q_low:
            if "happiness" in q_low or "occupation" in q_low:
                syntax.append("* Justification: Spearman Rho for ordinal data.")
                syntax.append("NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.")
            else:
                syntax.append("CORRELATIONS /VARIABLES=x3 x9 /PRINT=TWOTAIL /METHOD=PEARSON.")

        # --- الفصل 10: الانحدار المتعدد (Multiple Regression) ---
        elif "regression" in q_low or "happiness" in q_low and "x1" in q_low:
            syntax.append("* Justification: Measuring impact of multiple predictors on Y.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN /DEPENDENT x5")
            syntax.append("  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("") # سطر فارغ

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS All-in-One Engine", layout="wide")
st.title("📊 محرك SPSS الشامل (المنهج كامل - Chapters 1-10)")

col1, col2 = st.columns(2)
with col1:
    v_input = st.text_area("1. الصق تعريفات المتغيرات (مثل x1=gender):", height=300, 
                          placeholder="X1 = Gender (1=Male, 2=Female)\nX2 = Race...")
with col2:
    q_input = st.text_area("2. الصق أسئلة الامتحان هنا:", height=300,
                          placeholder="Construct the frequency table...\nDraw a bar chart for average salary...")

if st.button("توليد السينتاكس الشامل"):
    if v_input and q_input:
        final_code = generate_full_curriculum_syntax(v_input, q_input)
        st.success("✅ تم تحليل الأسئلة وتوليد الكود لكل فصول المنهج!")
        st.code(final_code, language='spss')
        st.download_button("تحميل الملف .SPS", final_code, "MBA_Full_Analysis.sps")
