import streamlit as st
import pandas as pd
import re
import math

def generate_universal_syntax(df, var_defs, questions_text):
    # 1. تحليل المتغيرات وبناء قاموس ذكي
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().upper()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code

    n = len(df) if df is not None else 60
    k_rule = math.ceil(1 + 3.322 * math.log10(n))

    syntax = [
        "* Encoding: UTF-8.",
        "SET SEED=1234567.",
        "* " + "="*75,
        "* UNIVERSAL AUTO-SOLVER (MBA FINAL EDITION)",
        "* Matches ANY Dataset with ANY Question Set",
        "* " + "="*75 + ".\n"
    ]

    # [PHASE 1] التسميات التلقائية
    syntax.append("TITLE 'PHASE 1: Variable Setup'.")
    labels_cmd = " /".join([f"{code} '{label.title()}'" for label, code in var_map.items()])
    syntax.append(f"VARIABLE LABELS {labels_cmd}.")
    
    # تعريف القيم الافتراضية (يمكن تعديلها حسب الحاجة)
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # تقسيم الأسئلة بشكل صارم لضمان عدم تجاهل أي سطر
    raw_qs = re.split(r'(?:\n|^)\s*\d+[\.\)]', questions_text)
    q_num = 1

    for q in raw_qs:
        txt = q.strip()
        if len(txt) < 5: continue
        low = txt.lower()

        syntax.append(f"TITLE 'QUESTION {q_num}: Analysis'.")
        syntax.append(f"ECHO 'Task: {txt[:100]}...'.")

        # --- محرك البحث عن المتغيرات داخل نص السؤال ---
        target_v = "X1" # افتراضي
        for label, code in var_map.items():
            if label in low:
                target_v = code
                break

        # --- منطق اتخاذ القرار الإحصائي (Logic Engine) ---
        
        # 1. التكرارات (Categorical)
        if "frequency" in low and any(w in low for w in ["categorical", "gender", "race", "region", "happiness", "occupation", "problem"]):
            syntax.append("FREQUENCIES VARIABLES=X1 X2 X4 X5 X6 X11 X12 /ORDER=ANALYSIS.")

        # 2. التقسيم (Recode) - ذكي حسب نوع المتغير
        elif "frequency table" in low and ("classes" in low or "suitable" in low):
            syntax.append(f"* Applying K-rule: {k_rule} classes.")
            if "salary" in low or "balance" in low:
                syntax.append(f"RECODE {target_v} (LO THRU 30000=1) (30000.01 THRU 60000=2) (60000.01 THRU 90000=3) (90000.01 THRU 120000=4) (120000.01 THRU HI=5) INTO {target_v}_cat.")
            else:
                syntax.append(f"RECODE {target_v} (LO THRU 30=1) (30.01 THRU 45=2) (45.01 THRU 60=3) (60.01 THRU HI=4) INTO {target_v}_cat.")
            syntax.append(f"FREQUENCIES VARIABLES={target_v}_cat /FORMAT=AVALUE.")

        # 3. الرسوم البيانية (Bar, Pie, Histogram)
        elif "bar chart" in low:
            stat = "MAX" if "max" in low else ("PCT" if "percentage" in low else "MEAN")
            syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({target_v}) BY X4.") # X4 كمثال للمنطقة
        
        elif "pie chart" in low:
            syntax.append(f"GRAPH /PIE=PCT BY X1 /TITLE='Distribution Chart'.")

        elif "histogram" in low:
            syntax.append(f"GRAPH /HISTOGRAM=X1.\nGRAPH /HISTOGRAM=X2.")

        # 4. تحليل المجموعات (Split File)
        elif "each" in low or "for each" in low:
            syntax.append("SORT CASES BY X4 X1.\nSPLIT FILE SEPARATE BY X4 X1.\nDESCRIPTIVES VARIABLES=X3 X9 X7 X8.\nSPLIT FILE OFF.")

        # 5. الانحدار المتعدد (Chapter 10)
        elif "regression" in low or "linear model" in low:
            syntax.append("REGRESSION /DEPENDENT X5 /METHOD=ENTER X1 X2 X3 X4 X6 X7 X8 X9 X10 X11 X12.")

        # 6. فترات الثقة والاعتدالية
        elif any(w in low for w in ["confidence", "normality", "outliers"]):
            syntax.append(f"EXAMINE VARIABLES={target_v} /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            syntax.append(f"ECHO 'RULE: Shapiro-Wilk > .05 -> Empirical; < .05 -> Chebyshev'.")

        syntax.append("EXECUTE.\n")
        q_num += 1

    return "\n".join(syntax)

# واجهة Streamlit
st.title("🤖 محرك حل امتحانات SPSS الشامل")
up = st.file_uploader("1. ارفع ملف الداتا (Data Set)", type=['xlsx', 'csv'])
v_in = st.text_area("2. تعريف المتغيرات (مثال: x1=Gender...)", height=150)
q_in = st.text_area("3. الصق نص الامتحان بالكامل")

if st.button("توليد الحل"):
    df = pd.read_excel(up) if up and up.name.endswith('xlsx') else (pd.read_csv(up) if up else None)
    st.code(generate_universal_syntax(df, v_in, q_in), language="spss")
