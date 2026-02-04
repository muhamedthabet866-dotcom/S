import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# دالة ذكية لاستخراج المتغير من نص السؤال بناءً على المابينج
def find_vars_in_question(q_text, var_map):
    found = []
    # ترتيب المابينج حسب طول الوصف (الأطول أولاً) لتجنب التداخل
    sorted_map = sorted(var_map.items(), key=lambda x: len(x[0]), reverse=True)
    for label, code in sorted_map:
        if label in q_text.lower():
            found.append(code)
    return list(dict.fromkeys(found)) # إزالة التكرار

def generate_genius_syntax(df, var_defs, questions_text):
    # 1. بناء قاموس المتغيرات (Mapping)
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

    n = len(df) if df is not None else 60
    k_rule = math.ceil(math.log2(n)) if n > 0 else 6 # قاعدة 2^k >= n

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* MBA GENIUS SPSS SOLVER - NO ERROR EDITION",
        "* Automatically detects variables and tasks question-by-question",
        "* " + "="*75 + ".\n"
    ]

    # [PRE-ANALYSIS] تهيئة البيانات
    syntax.append("TITLE 'PRE-ANALYSIS: Variable & Value Setup'.")
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # تقسيم الأسئلة (نظام تقسيم صارم لعدم تجاهل أي سؤال)
    raw_questions = re.split(r'\n\s*\d+[\.\)]|\[source', questions_text)
    q_count = 1

    for q in raw_questions:
        q_text = q.strip()
        if len(q_text) < 5: continue
        q_low = q_text.lower()
        
        # استخراج المتغيرات المذكورة في هذا السؤال تحديداً
        found_vars = find_vars_in_question(q_low, var_map)
        # تحديد المتغير المستهدف (الرقمي عادة X1 أو X2) والمتغير التقسيمي (X4 أو X6)
        quant_vars = [v for v in found_vars if v in ['X1', 'X2', 'X3']]
        cat_vars = [v for v in found_vars if v in ['X4', 'X5', 'X6']]
        
        main_v = quant_vars[0] if quant_vars else ("X1" if "balance" in q_low else "X2")
        group_v = cat_vars[0] if cat_vars else ("X6" if "city" in q_low else "X4")

        syntax.append(f"* " + "-"*70)
        syntax.append(f"TITLE 'QUESTION {q_count}: Statistical Task'.")
        syntax.append(f"ECHO 'Processing: {q_text[:100]}...'.")
        syntax.append(f"* " + "-"*70)

        # --- محرك اتخاذ القرار (Decision Engine) ---

        # 1. الجداول التكرارية للبيانات الوصفية
        if "frequency table" in q_low and any(w in q_low for w in ["categorical", "discrete", "debit", "interest", "city"]):
            syntax.append(f"FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")

        # 2. التقسيم (Recode) - اختيار المتغير الصحيح X1 أو X2
        elif "frequency table" in q_low and any(w in q_low for w in ["classes", "k-rule", "suitable"]):
            syntax.append(f"* K-rule Rule: 2^{k_rule} >= {n}.")
            if "balance" in q_low or "x1" in q_low:
                syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru HI=4) INTO X1_Classes.")
                syntax.append("VALUE LABELS X1_Classes 1 'Low' 2 'Mid' 3 'High' 4 'Very High'.\nFREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.")
            else:
                syntax.append("RECODE X2 (2 thru 7=1) (7.01 thru 12=2) (12.01 thru 17=3) (17.01 thru HI=4) INTO X2_Classes.")
                syntax.append("VALUE LABELS X2_Classes 1 '2-7' 2 '8-12' 3 '13-17' 4 '18+'.\nFREQUENCIES VARIABLES=X2_Classes /FORMAT=AVALUE.")

        # 3. الإحصاء الوصفي والالتواء
        elif any(w in q_low for w in ["mean", "median", "mode", "calculate", "skewness"]):
            syntax.append(f"FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        # 4. المدرج التكراري (Histogram) - لضمان عدم التجاهل
        elif "histogram" in q_low:
            syntax.append("GRAPH /HISTOGRAM=X1 /TITLE='Histogram of Account Balance'.")
            syntax.append("GRAPH /HISTOGRAM=X2 /TITLE='Histogram of ATM Transactions'.")

        # 5. الرسوم البيانية (Bar & Pie) - ذكاء اختيار القياس والمحور
        elif "bar chart" in q_low:
            measure = "MAX" if "max" in q_low else ("PCT" if "percentage" in q_low else "MEAN")
            target = "X2" if "transaction" in q_low else "X1"
            if "grouped" in q_low or ("city" in q_low and "card" in q_low):
                syntax.append(f"GRAPH /BAR(GROUPED)={measure}({target}) BY X6 BY X4.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={measure}({target}) BY {group_v}.")

        elif "pie chart" in q_low:
            syntax.append(f"GRAPH /PIE=PCT BY X5 /TITLE='Percentage of Interest Interest'.")

        # 6. تحليل المجموعات (Split File)
        elif any(w in q_low for w in ["each city", "card or not", "debit card or not"]):
            syntax.append(f"SORT CASES BY {group_v}.\nSPLIT FILE SEPARATE BY {group_v}.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE SKEWNESS.\nSPLIT FILE OFF.")

        # 7. الاعتدالية والـ Outliers
        elif any(w in q_low for w in ["normality", "outliers", "confidence", "extreme"]):
            syntax.append(f"EXAMINE VARIABLES=X1 /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in q_low: syntax.append(f"EXAMINE VARIABLES=X1 /CINTERVAL 99.")
            syntax.append("ECHO 'RULE: Shapiro-Wilk > 0.05 => Empirical; else Chebyshev'.")

        syntax.append("\n")
        q_count += 1

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# (واجهة Streamlit تظل كما هي...)
