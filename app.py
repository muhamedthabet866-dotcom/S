import streamlit as st
import pandas as pd
import re
import math

def generate_ultimate_syntax(df, var_defs, questions_text):
    # 1. تحليل خريطة المتغيرات (Mapping)
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().upper()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code

    # حساب خصائص العينة n و قاعدة K-rule
    n = len(df) if df is not None else 60
    k_rule = math.ceil(1 + 3.322 * math.log10(n))

    syntax = [
        "* Encoding: UTF-8.",
        "SET SEED=1234567.",
        "* " + "="*75,
        "* PROFESSIONAL UNIVERSAL SPSS SOLVER (MBA EDITION)",
        "* Automated Decision Logic for Variables and Statistical Rules",
        "* " + "="*75 + ".\n"
    ]

    # [PHASE 1] التسميات الأساسية
    syntax.append("VARIABLE LABELS X1 'Account Balance' /X2 'ATM Transactions' /X3 'Other Services' /X4 'Debit Card' /X5 'Interest' /X6 'City'.")
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # تقسيم الأسئلة بشكل صارم لضمان حل كل سؤال
    raw_qs = re.split(r'\n\s*\d+[\.\)]', questions_text)
    q_num = 1

    for q in raw_qs:
        txt = q.strip()
        if len(txt) < 5: continue
        low = txt.lower()

        syntax.append(f"TITLE 'QUESTION {q_num}: Statistical Solution'.")
        syntax.append(f"ECHO 'Processing Question: {txt[:100]}...'.")

        # --- محرك القرارات الذكي ---
        
        # 1. جداول التكرار (الوصفية)
        if "frequency table" in low and any(w in low for w in ["categorical", "debit", "interest", "city"]):
            syntax.append("FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")

        # 2. تقسيم الفئات (Recode) - ذكي حسب نوع المتغير
        elif "frequency table" in low and ("balance" in low or "transaction" in low):
            if "balance" in low:
                syntax.append(f"* Recoding Balance into {k_rule} classes.")
                syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_cat.")
                syntax.append("VALUE LABELS X1_cat 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 '1501-2000' 5 'Over 2000'.\nFREQUENCIES VARIABLES=X1_cat.")
            else:
                syntax.append("RECODE X2 (0 thru 5=1) (5.01 thru 10=2) (10.01 thru 15=3) (15.01 thru HI=4) INTO X2_cat.")
                syntax.append("VALUE LABELS X2_cat 1 '0-5' 2 '6-10' 3 '11-15' 4 'Over 15'.\nFREQUENCIES VARIABLES=X2_cat.")

        # 3. الوصفي والالتواء
        elif any(w in low for w in ["mean", "median", "mode", "skewness"]):
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        # 4. الرسوم البيانية (Bars & Pie) - تصحيح منطق المحاور
        elif "bar chart" in low:
            if "average" in low and "balance" in low:
                if "each city" in low and "card" in low: # مجمع
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4.")
                else: # بسيط
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
            elif "maximum" in low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4.")
            elif "percentage" in low:
                syntax.append("GRAPH /BAR(SIMPLE)=PCT BY X5.")

        elif "pie chart" in low:
            syntax.append("GRAPH /PIE=PCT BY X5 /TITLE='Interest Receiver %'.")

        # 5. تحليل المجموعات (Split File)
        elif any(w in low for w in ["each city", "card or not"]):
            grp = "X6" if "city" in low else "X4"
            syntax.append(f"SORT CASES BY {grp}.\nSPLIT FILE SEPARATE BY {grp}.\nDESCRIPTIVES VARIABLES=X1 X2 /STATISTICS=MEAN STDDEV SKEWNESS.\nSPLIT FILE OFF.")

        # 6. فترات الثقة والاعتدالية
        elif any(w in low for w in ["confidence", "normality", "outliers"]):
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in low: syntax.append("EXAMINE VARIABLES=X1 /CINTERVAL 99.")
            syntax.append("ECHO 'CHECK: Shapiro-Wilk Sig > .05 -> Empirical Rule; < .05 -> Chebyshev Rule'.")

        syntax.append("EXECUTE.\n")
        q_num += 1

    return "\n".join(syntax)

# --- واجهة المستخدم (Streamlit) ---
st.title("🤖 المحرك الذكي لحل امتحانات SPSS")
up = st.file_uploader("1. ارفع ملف الداتا", type=['xlsx', 'csv'])
v_in = st.text_area("2. تعريف المتغيرات", value="X1=Balance\nX2=Transactions\nX4=Debit Card\nX5=Interest\nX6=City")
q_in = st.text_area("3. الصق نص الأسئلة هنا")

if st.button("توليد الحل الإحصائي"):
    if q_in:
        df = pd.read_excel(up) if up and up.name.endswith('xlsx') else (pd.read_csv(up) if up else None)
        sol = generate_ultimate_syntax(df, v_in, q_in)
        st.code(sol, language="spss")
