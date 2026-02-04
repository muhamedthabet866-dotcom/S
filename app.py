import streamlit as st
import pandas as pd
import re
import math

def generate_spss_v26_syntax(df, var_defs, questions_text):
    # 1. تحليل خريطة المتغيرات (Mapping)
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().upper()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code

    # حساب حجم العينة n لضبط القواعد
    n = len(df) if df is not None else 60
    k_rule = math.ceil(math.log2(n)) if n > 0 else 6

    syntax = [
        "* Encoding: UTF-8.",
        "SET SEED=1234567.",
        "* " + "="*75,
        "* MBA SPSS v26 PROFESSIONAL SOLVER - FINAL VERIFIED EDITION",
        "* Fixed: Graph Logic, Recode Intervals, and Variable Mapping",
        "* " + "="*75 + ".\n"
    ]

    # [PHASE 1] تهيئة المتغيرات (Labels & Values)
    syntax.append("VARIABLE LABELS X1 'Account Balance' /X2 'ATM Transactions' /X3 'Other Services' /X4 'Debit Card' /X5 'Interest' /X6 'City'.")
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # تقسيم الأسئلة بشكل دقيق لضمان عدم تجاهل أي سطر
    raw_qs = re.split(r'\n\s*\d+[\.\)]', questions_text)
    q_num = 1

    for q in raw_qs:
        txt = q.strip()
        if len(txt) < 5: continue
        low = txt.lower()

        syntax.append(f"* " + "-"*70)
        syntax.append(f"TITLE 'QUESTION {q_num}: Statistical Analysis'.")
        syntax.append(f"ECHO 'Task: {txt[:100]}...'.")
        syntax.append(f"* " + "-"*70)

        # --- محرك الحل الذكي الموجه لـ SPSS v26 ---

        # 1. جداول التكرار للبيانات الوصفية
        if "frequency table" in low and any(w in low for w in ["categorical", "discrete", "debit", "interest", "city"]):
            syntax.append("FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")

        # 2. فئات الرصيد (Recode X1)
        elif "frequency table" in low and "balance" in low:
            syntax.append(f"* Applying K-rule: suggested classes = {k_rule}.")
            syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_cat.")
            syntax.append("VARIABLE LABELS X1_cat 'Account Balance Classes'.")
            syntax.append("VALUE LABELS X1_cat 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 '1501-2000' 5 'Over 2000'.")
            syntax.append("FREQUENCIES VARIABLES=X1_cat /FORMAT=AVALUE.")

        # 3. فئات المعاملات (Recode X2)
        elif "frequency table" in low and "transaction" in low:
            syntax.append("RECODE X2 (0 thru 5=1) (6 thru 10=2) (11 thru 15=3) (16 thru 20=4) (21 thru HI=5) INTO X2_cat.")
            syntax.append("VARIABLE LABELS X2_cat 'ATM Transaction Classes'.")
            syntax.append("VALUE LABELS X2_cat 1 '0-5' 2 '6-10' 3 '11-15' 4 '16-20' 5 'Over 20'.")
            syntax.append("FREQUENCIES VARIABLES=X2_cat /FORMAT=AVALUE.")

        # 4. الإحصاء الوصفي والالتواء (Q4, Q6)
        elif any(w in low for w in ["mean", "median", "mode", "skewness", "calculate"]):
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        # 5. المدرجات التكرارية (Q5)
        elif "histogram" in low:
            syntax.append("GRAPH /HISTOGRAM=X1 /TITLE='Histogram of Account Balance'.")
            syntax.append("GRAPH /HISTOGRAM=X2 /TITLE='Histogram of ATM Transactions'.")

        # 6. تحليل المجموعات (Split File Q7, Q8)
        elif any(w in low for w in ["each city", "card or not"]):
            grp = "X6" if "city" in low else "X4"
            syntax.append(f"SORT CASES BY {grp}.")
            syntax.append(f"SPLIT FILE SEPARATE BY {grp}.")
            syntax.append("DESCRIPTIVES VARIABLES=X1 X2 /STATISTICS=MEAN STDDEV MIN MAX.")
            syntax.append("SPLIT FILE OFF.")

        # 7. الرسوم البيانية (Bars & Pie Q9 - Q13)
        elif "bar chart" in low:
            if "average" in low and "balance" in low:
                if "each city" in low and "card" in low: # سؤال 11 المجمع
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4.")
                else: # سؤال 9 البسيط
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
            elif "maximum" in low and "transaction" in low: # سؤال 10
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4.")
            elif "percentage" in low: # سؤال 12
                syntax.append("GRAPH /BAR(SIMPLE)=PCT BY X5.")

        elif "pie chart" in low:
            syntax.append("GRAPH /PIE=PCT BY X5 /TITLE='Interest Receiver %'.")

        # 8. فترات الثقة والاعتدالية والـ Outliers (Q14, Q15, Q16)
        elif any(w in low for w in ["confidence", "normality", "outliers"]):
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in low: syntax.append("EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 99.")
            syntax.append("ECHO 'CHECK: Shapiro-Wilk Sig > .05 => Empirical; < .05 => Chebyshev'.")

        syntax.append("\n")
        q_num += 1

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit تظل كما هي مع استدعاء الدالة الجديدة generate_spss_v26_syntax
