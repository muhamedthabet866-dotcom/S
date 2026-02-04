import streamlit as st
import pandas as pd
import re
import math

# 1. محرك الذكاء الإحصائي: يربط الكلمات المفتاحية بأوامر SPSS v26
def get_statistical_logic(q_text, var_map, n_size):
    q_low = q_text.lower()
    k_rule = math.ceil(1 + 3.322 * math.log10(n_size)) if n_size > 0 else 7
    
    # استخراج المتغيرات المذكورة في السؤال بناءً على الـ Mapping
    found_vars = [code for label, code in var_map.items() if label in q_low]
    v1 = found_vars[0] if found_vars else "X1"
    v_all = " ".join(found_vars) if found_vars else "X1 X2 X3"

    # تطبيق القواعد البرمجية (Logic من ملف الإكسيل الخاص بك)
    if any(w in q_low for w in ["frequency", "classes", "k-rule"]):
        if "balance" in q_low or "salary" in q_low or "x3" in q_low:
            return f"RECODE {v1} (LO THRU 30000=1) (30000.01 THRU 60000=2) (60000.01 THRU HI=3) INTO {v1}_cat.\nFREQUENCIES VARIABLES={v1}_cat /FORMAT=AVALUE."
        return f"FREQUENCIES VARIABLES={v_all} /ORDER=ANALYSIS."

    if any(w in q_low for w in ["mean", "median", "mode", "descriptive"]):
        return f"FREQUENCIES VARIABLES={v_all} /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE."

    if "bar chart" in q_low:
        if "average" in q_low: return f"GRAPH /BAR(SIMPLE)=MEAN({v1}) BY X4."
        if "max" in q_low: return f"GRAPH /BAR(SIMPLE)=MAX({v1}) BY X4."
        return f"GRAPH /BAR(SIMPLE)=COUNT BY {v1}."

    if "pie chart" in q_low:
        return f"GRAPH /PIE=PCT BY {v1}."

    if "histogram" in q_low:
        return f"GRAPH /HISTOGRAM={v1}."

    if any(w in q_low for w in ["normality", "empirical", "chebycheve", "outliers"]):
        return f"EXAMINE VARIABLES={v1} /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES.\n* ECHO 'Sig > 0.05: Empirical Rule | Sig < 0.05: Chebyshev'."

    if "regression" in q_low or "model" in q_low:
        return "REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X5 /METHOD=ENTER X1 X2 X3 X4 X6 X7 X8 X9 X10 X11 X12."

    if "correlation" in q_low:
        return f"CORRELATIONS /VARIABLES={v_all} /PRINT=TWOTAIL."

    if "each" in q_low or "compare" in q_low:
        return f"SORT CASES BY X4 X1.\nSPLIT FILE SEPARATE BY X4 X1.\nDESCRIPTIVES VARIABLES={v_all}.\nSPLIT FILE OFF."

    return "* [Manual Check Required for this Task]"

# 2. واجهة المستخدم باستخدام Streamlit
st.set_page_config(page_title="MBA SPSS Genius Solver", layout="wide")
st.title("🚀 محرك حل امتحانات SPSS العبقري")
st.write("ارفع ملف الداتا والصق الأسئلة، وسأقوم بتوليد كود الحل فوراً بناءً على قواعد المنهج.")

# مدخلات المستخدم
with st.sidebar:
    st.header("1. البيانات")
    uploaded_file = st.file_uploader("ارفع ملف الإكسيل", type=['csv', 'xlsx'])
    
v_mapping = st.text_area("2. تعريف المتغيرات (مثال: x1=gender)", "x1=gender\nx2=race\nx3=salary\nx4=region\nx5=happiness\nx9=age", height=150)
questions_input = st.text_area("3. الصق نص الأسئلة بالكامل هنا", height=250)

if st.button("🚀 توليد الحل النهائي"):
    if v_mapping and questions_input:
        # معالجة الـ Mapping
        var_map = {}
        for line in v_mapping.split('\n'):
            if '=' in line:
                c, l = line.split('=')
                var_map[l.strip().lower()] = c.strip().upper()

        # معالجة البيانات
        n_size = 60
        if uploaded_file:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
            n_size = len(df)

        # تقسيم الأسئلة وتوليد الكود
        final_syntax = ["* Encoding: UTF-8.\nSET SEED=1234567.\n"]
        questions_list = re.split(r'\n\s*\d+[\.\)]', questions_input)
        
        for i, q in enumerate(questions_list):
            if len(q.strip()) < 5: continue
            logic = get_statistical_logic(q, var_map, n_size)
            final_syntax.append(f"TITLE 'QUESTION {i}: Analysis'.\nECHO 'Task: {q.strip()[:50]}...'.\n{logic}\nEXECUTE.")

        st.subheader("✅ كود SPSS Syntax المولد:")
        st.code("\n\n".join(final_syntax), language="spss")
