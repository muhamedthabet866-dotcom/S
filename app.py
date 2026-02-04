import streamlit as st
import pandas as pd
import math
import re

def generate_perfect_syntax(df, var_defs, questions_text):
    # 1. تحليل خريطة المتغيرات وتنظيفها
    var_map = {}
    variable_labels = []
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().lower()
            v_label = match.group(2).strip()
            # تنظيف التسمية من أي إضافات
            clean_label = re.sub(r'\(.*\)', '', v_label).strip()
            var_map[clean_label.lower()] = v_code
            variable_labels.append(f"{v_code} \"{v_label}\"")

    # حساب K-rule بناءً على عدد البيانات المرفوعة
    n = len(df) if df is not None else 100
    k_val = round(1 + 3.322 * math.log10(n))

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* MBA PERFECT SOLVER: DATA SET 1 ANALYSIS",
        "* Built according to Dr. Mohamed Salam Curriculum",
        "* " + "="*75 + ".\n"
    ]

    # التسميات والقيم
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # تحسين استخراج الـ Value Labels لـ x4 و x5 حصراً
    syntax.append("VALUE LABELS x4 1 'Yes' 0 'No' /x5 1 'Yes' 0 'No'.")
    syntax.append("EXECUTE.\n")

    q_low = questions_text.lower()

    # [Q1] الجداول التكرارية للبيانات الوصفية
    if "frequency table" in q_low and "categorical" in q_low:
        syntax.append("* [Q1] Frequency tables for categorical variables (Debit Card, Interest, City).")
        syntax.append("FREQUENCIES VARIABLES=x4 x5 x6 /ORDER=ANALYSIS.\n")

    # [Q2-Q4] الإحصاء الوصفي والـ K-rule
    if "balance" in q_low or "transaction" in q_low:
        syntax.append(f"* [Q2-Q4] Descriptive Statistics with K-rule (k={k_val}).")
        syntax.append("* Justification: Using mean, median, and skewness to analyze distribution shape.")
        syntax.append("FREQUENCIES VARIABLES=x1 x2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /HISTOGRAM /FORMAT=NOTABLE.\n")

    # [Q9] الاستكشاف وفترات الثقة
    if "confidence" in q_low or "outliers" in q_low:
        syntax.append("* [Q9] Normality, Outliers, and Confidence Intervals (95% & 99%).")
        syntax.append("EXAMINE VARIABLES=x1 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
        syntax.append("EXAMINE VARIABLES=x1 /CINTERVAL 99.\n")

    # [Q4/Q7 مكرر] التحليل المقارن (Split File)
    if "each city" in q_low or "each debit" in q_low:
        syntax.append("* [Task] Grouped Analysis for each City and Debit Card status.")
        syntax.append("SORT CASES BY x6 x4.\nSPLIT FILE LAYERED BY x6 x4.")
        syntax.append("DESCRIPTIVES VARIABLES=x1 x2 /STATISTICS=MEAN MEDIAN STDDEV SKEWNESS.")
        syntax.append("SPLIT FILE OFF.\n")

    # [Q7-Q8] الرسوم البيانية
    if "bar chart" in q_low:
        syntax.append("* [Q7] Bar Charts for Comparison.")
        syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x1) BY x6 /TITLE='Average Balance by City'.")
        syntax.append("GRAPH /BAR(GROUPED)=MEAN(x1) BY x6 BY x4 /TITLE='Avg Balance by City & Debit Card'.")
    
    if "pie chart" in q_low:
        syntax.append("\n* [Q8] Pie Chart for Interest Percentage.")
        syntax.append("GRAPH /PIE=COUNT BY x5 /TITLE='Percentage of Customers Receiving Interest'.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- واجهة المستخدم ---
st.set_page_config(page_title="MBA Ideal SPSS Solver", layout="wide")
st.title("🎓 المحلل الإحصائي المثالي (منهج د. محمد عبد السلام)")

up = st.file_uploader("1. ارفع ملف الداتا (Data Set 1)", type=['xlsx', 'csv'])
c1, c2 = st.columns(2)
with c1:
    v_in = st.text_area("2. كود المتغيرات (x1=Balance...)", height=200)
with c2:
    q_in = st.text_area("3. أسئلة الامتحان (انسخ الأسئلة هنا)", height=200)

if st.button("توليد الحل النموذجي"):
    if v_in and q_in:
        df = pd.read_excel(up) if up and up.name.endswith('xlsx') else (pd.read_csv(up) if up else None)
        result = generate_perfect_syntax(df, v_in, q_in)
        st.subheader("✅ الحل المثالي الجاهز للـ SPSS:")
        st.code(result, language="spss")
        st.download_button("تحميل ملف .SPS", result, file_name="Perfect_Solution.sps")
