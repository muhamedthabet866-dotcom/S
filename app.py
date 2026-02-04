import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# --- المحرك الذكي لتحليل المنهج والأسئلة ---
def generate_advanced_syntax(df, var_defs, questions_text):
    # 1. تحليل خريطة المتغيرات
    var_map = {}
    variable_labels = []
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().lower()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code
            variable_labels.append(f"{v_code} \"{v_label}\"")

    # حساب عدد الحالات لـ K-rule
    n = len(df) if df is not None else 100
    k_rule = round(1 + 3.322 * math.log10(n))

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* PROFESSIONAL SPSS ANALYSIS SOLUTION (Based on Dr. Mohamed Salam Curriculum)",
        "* " + "="*75 + ".\n"
    ]

    # إضافة التسميات (Chapter 2)
    if variable_labels:
        syntax.append("* [Chapter 2] Labeling Variables for readability.")
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # محاولة استخراج Value Labels (1=Yes, 0=No)
    val_labels = []
    for line in lines:
        if "=" in line and ("yes" in line.lower() or "male" in line.lower()):
            v_code_match = re.search(r'(x\d+)', line, re.IGNORECASE)
            if v_code_match:
                codes = re.findall(r'(\d+)\s*=\s*([a-zA-Z]+)', line)
                l_str = " ".join([f'{c[0]} "{c[1]}"' for c in codes])
                val_labels.append(f"  /{v_code_match.group(1).lower()} {l_str}")
    if val_labels:
        syntax.append("VALUE LABELS" + "\n".join(val_labels) + ".")
    syntax.append("EXECUTE.\n")

    q_low = questions_text.lower()

    # --- [Q1 & Q2] Frequency & K-rule (Chapter 2) ---
    if "frequency" in q_low or "table" in q_low:
        syntax.append("* [Chapter 2: Descriptive Statistics]")
        syntax.append(f"* Scientific Justification: K-rule applied (k={k_rule} classes) for continuous data distribution.")
        target_vars = " ".join([v for k, v in var_map.items() if any(word in k for word in ["balance", "transaction", "debit", "interest", "city"])])
        syntax.append(f"FREQUENCIES VARIABLES={target_vars} /FORMAT=AVALUE /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS /HISTOGRAM /ORDER=ANALYSIS.")

    # --- [Q4] Descriptive & Skewness (Chapter 2) ---
    if any(word in q_low for word in ["mean", "mode", "median", "skewness"]):
        syntax.append("\n* [Chapter 2] Measuring Central Tendency and Shape of Distribution.")
        syntax.append("* Justification: Skewness coefficient determines if data is symmetric or skewed.")
        num_vars = " ".join([v for k, v in var_map.items() if "x1" in v or "x2" in v or "balance" in k])
        syntax.append(f"DESCRIPTIVES VARIABLES={num_vars} /STATISTICS=MEAN SUM STDDEV VARIANCE RANGE MIN MAX SKEWNESS.")

    # --- [Q9] Normality & Outliers (Chapter 2 & 3) ---
    if any(word in q_low for word in ["normality", "outliers", "extreme", "confidence"]):
        syntax.append("\n* [Chapter 2 & 3] Exploring Data, Confidence Intervals, and Outliers.")
        syntax.append("* Justification: Using Boxplots to detect extremes and NPPLOT for normality testing.")
        syntax.append("EXAMINE VARIABLES=x1 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")

    # --- [Q7] Differences & T-Test/ANOVA (Chapter 4 & 6) ---
    if "compare" in q_low or "difference" in q_low or "each city" in q_low:
        if "city" in q_low:
            syntax.append("\n* [Chapter 6: One-Way ANOVA]")
            syntax.append("* Justification: Comparing means across more than 2 groups (Cities) with Tukey Post-Hoc.")
            syntax.append("ONEWAY x1 BY x6 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
        else:
            syntax.append("\n* [Chapter 4: Independent Samples T-Test]")
            syntax.append("* Justification: Comparing means of two independent groups (e.g., Debit Card: Yes/No).")
            syntax.append("T-TEST GROUPS=x4(0 1) /VARIABLES=x1.")

    # --- Regression & Correlation (Chapter 8, 9, 10) ---
    if "regression" in q_low or "relationship" in q_low:
        syntax.append("\n* [Chapter 8, 9, 10] Correlation and Multiple Regression.")
        syntax.append("* Justification: Pearson correlation measures linear strength; Regression predicts Dependent Variable.")
        syntax.append("CORRELATIONS /VARIABLES=x1 x2 x3 x4 x5 /PRINT=TWOTAIL.")
        syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT x1 /METHOD=ENTER x2 x3 x4 x5.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Engine", layout="wide")
st.title("📊 MBA SPSS Professional Solver")
st.markdown("تحليل البيانات الإحصائية طبقاً لمنهج **د. محمد عبد السلام**")

# 1. الرفع والمعالجة
uploaded_file = st.file_uploader("خطوة 1: ارفع ملف الإكسيل (Data Set)", type=['xlsx', 'csv'])
df_loaded = None
if uploaded_file:
    df_loaded = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
    st.success(f"✅ تم تحميل البيانات بنجاح ({len(df_loaded)} حالة).")
    with st.expander("معاينة الأعمدة"):
        st.write(list(df_loaded.columns))

# 2. الإدخال
col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("خطوة 2: تعريف المتغيرات (Mapping)", height=250, 
                        placeholder="x1 = Account Balance\nx4 = Debit Card (1=yes, 0=no)\nx6 = City")
with col2:
    q_in = st.text_area("خطوة 3: أسئلة الامتحان", height=250, 
                        placeholder="1. Calculate mean and skewness for balance\n2. Compare balance by city...")

# 3. النتائج
if st.button("توليد الكود والتحليل النهائي"):
    if v_in and q_in:
        final_syntax = generate_advanced_syntax(df_loaded, v_in, q_in)
        st.divider()
        st.subheader("🚀 SPSS Syntax المولد:")
        st.code(final_syntax, language="spss")
        st.download_button("تحميل ملف .SPS جاهز", final_syntax, file_name="MBA_Solution.sps")
    else:
        st.warning("الرجاء إدخال المتغيرات والأسئلة.")
