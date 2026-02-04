import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# دالة توليد الـ Syntax الاحترافي
def generate_final_perfect_syntax(df, var_defs, questions_text):
    # 1. تحليل خريطة المتغيرات (Variable Mapping)
    var_map = {}
    variable_labels = []
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().upper()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code
            variable_labels.append(f"{v_code} \"{v_label}\"")

    # حساب عدد الحالات لـ K-rule
    n = len(df) if df is not None else 60
    k_val = math.ceil(math.log2(n)) if n > 0 else 6

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* UNIVERSAL EXAM MASTER SOLVER (FINAL VERSION)",
        "* Matches Methodology: Dr. Mohamed Salam Curriculum",
        "* " + "="*75 + ".\n"
    ]

    # [PHASE 1] تهيئة المتغيرات والقيم
    syntax.append("TITLE 'PRE-ANALYSIS SETUP: Definitions'.")
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # تعريف التسميات للمتغيرات الفئوية
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # [PHASE 2] محرك تحليل الأسئلة (سؤال بسؤال)
    # تقسيم الأسئلة بشكل مرن (سواء بدأت برقم أو كلمة source)
    questions = re.split(r'(?:\n|^)\s*\d+[\.\)]|\[source', questions_text)
    q_count = 1

    for q in questions:
        q_content = q.strip()
        if len(q_content) < 10: continue
        q_low = q_content.lower()

        syntax.append(f"* " + "-"*70)
        syntax.append(f"TITLE 'QUESTION {q_count}: Analysis Task'.")
        syntax.append(f"ECHO 'Processing: {q_content[:100]}...'.")
        syntax.append(f"* " + "-"*70)

        # ربط المتغير الصحيح بالسؤال (ذكاء اصطناعي بسيط)
        v_target = "X1" # افتراضي (Balance)
        if "transaction" in q_low or "x2" in q_low: v_target = "X2"
        elif "interest" in q_low or "x5" in q_low: v_target = "X5"
        elif "card" in q_low or "x4" in q_low: v_target = "X4"
        elif "city" in q_low or "x6" in q_low: v_target = "X6"

        # --- القواعد الإحصائية للحل النموذجي ---

        # 1. التكرارات للمتغيرات الوصفية
        if "frequency" in q_low and any(w in q_low for w in ["categorical", "discrete", "debit", "interest", "city"]):
            syntax.append(f"FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")
            syntax.append(f"ECHO 'INTERPRETATION: Distribution of Categorical Data'.")

        # 2. الـ Recode وقاعدة K-rule
        elif "frequency" in q_low and any(w in q_low for w in ["classes", "k-rule", "suitable"]):
            syntax.append(f"* K-rule applied: 2^{k_val} >= {n}.")
            if v_target == "X1":
                syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_Classes.")
                syntax.append("VALUE LABELS X1_Classes 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 '1501-2000' 5 'Over 2000'.")
            else:
                syntax.append("RECODE X2 (2 thru 7=1) (7.01 thru 12=2) (12.01 thru 17=3) (17.01 thru 22=4) (22.01 thru HI=5) INTO X2_Classes.")
                syntax.append("VALUE LABELS X2_Classes 1 'Very Low' 2 'Low' 3 'Medium' 4 'High' 5 'Very High'.")
            syntax.append(f"FREQUENCIES VARIABLES={v_target}_Classes /FORMAT=AVALUE.")

        # 3. الإحصاء الوصفي والالتواء
        elif any(w in q_low for w in ["mean", "median", "mode", "calculate", "skewness"]):
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")
            syntax.append("ECHO 'COMMENT: Compare Mean and Median to determine Skewness type'.")

        # 4. الرسوم البيانية
        elif "histogram" in q_low:
            syntax.append(f"GRAPH /HISTOGRAM={v_target} /TITLE='Histogram of {v_target}'.")
        
        elif "bar chart" in q_low:
            stat = "MAX" if "max" in q_low else ("PCT" if "percentage" in q_low else "MEAN")
            group = "X6" if "city" in q_low else "X4"
            if "grouped" in q_low or ("city" in q_low and "card" in q_low):
                syntax.append(f"GRAPH /BAR(GROUPED)={stat}({v_target}) BY {group} BY X4.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({v_target}) BY {group}.")

        elif "pie chart" in q_low:
            syntax.append(f"GRAPH /PIE=PCT BY X5 /TITLE='Percentage of Interest Receivers'.")

        # 5. تحليل المجموعات (Split File)
        elif any(w in q_low for w in ["each city", "card or not", "debit card or not"]):
            group = "X6" if "city" in q_low else "X4"
            syntax.append(f"SORT CASES BY {group}.\nSPLIT FILE SEPARATE BY {group}.")
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE SKEWNESS /FORMAT=NOTABLE.")
            syntax.append("SPLIT FILE OFF.")

        # 6. الاعتدالية والـ Outliers
        elif any(w in q_low for w in ["normality", "outliers", "confidence", "extreme"]):
            syntax.append(f"EXAMINE VARIABLES=X1 /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in q_low: syntax.append(f"EXAMINE VARIABLES=X1 /CINTERVAL 99.")
            syntax.append("ECHO 'RULE: If Shapiro-Wilk Sig > 0.05 use Empirical Rule; else use Chebyshev'.")

        syntax.append("\n")
        q_count += 1

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA Universal Solver", layout="wide")
st.title("🎓 المحرك الإحصائي الشامل (الحل النموذجي)")

up = st.sidebar.file_uploader("1. ارفع ملف البيانات (Data Set)", type=['xlsx', 'csv'])
col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("2. تعريف المتغيرات (مثال: x1=Account Balance):", height=250, value="x1 = Account Balance\nx2 = ATM transactions\nx4 = debit card\nx5 = interest\nx6 = city")
with col2:
    q_in = st.text_area("3. الصق أسئلة أي امتحان هنا:", height=250)

if st.button("🚀 توليد الحل الإحصائي الكامل"):
    if v_in and q_in:
        try:
            df = None
            if up:
                df = pd.read_excel(up) if up.name.endswith('xlsx') else pd.read_csv(up)
            
            solution = generate_final_perfect_syntax(df, v_in, q_in)
            st.subheader("✅ كود SPSS Syntax المولد:")
            st.code(solution, language="spss")
            st.download_button("تحميل الحل النهائي .SPS", solution, file_name="Exam_Solution.sps")
        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
