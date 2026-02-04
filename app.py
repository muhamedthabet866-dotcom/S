import streamlit as st
import pandas as pd
import numpy as np
import re
import math

def generate_error_free_syntax(df, var_defs, questions_text):
    # 1. بناء قاموس المتغيرات
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
    k_rule = math.ceil(math.log2(n)) if n > 0 else 6

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*75,
        "* UNIVERSAL EXAM SOLVER - PERFECT EDITION v5.0",
        "* Fixed Variable Matching & Dynamic Recoding Logic",
        "* " + "="*75 + ".\n"
    ]

    # [PRE-ANALYSIS]
    syntax.append("TITLE 'PRE-ANALYSIS SETUP: Definitions'.")
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("EXECUTE.\n")

    # تقسيم الأسئلة
    questions = re.split(r'\n\s*\d+[\.\)]', questions_text)
    q_idx = 1

    for q in questions:
        q_content = q.strip()
        if len(q_content) < 10: continue
        q_low = q_content.lower()

        syntax.append(f"* " + "-"*70)
        syntax.append(f"TITLE 'QUESTION {q_idx}: {q_content[:60]}...'.")
        syntax.append(f"* " + "-"*70)

        # تحديد المتغير المستهدف بناءً على الكلمات المفتاحية
        v_target = "X1" # افتراضي (Balance)
        if "transaction" in q_low or "x2" in q_low: v_target = "X2"
        elif "interest" in q_low or "x5" in q_low: v_target = "X5"
        elif "card" in q_low or "x4" in q_low: v_target = "X4"
        elif "city" in q_low or "x6" in q_low: v_target = "X6"

        # --- المنطق الإحصائي المطور ---

        # جداول التكرار (Categorical)
        if "frequency table" in q_low and any(w in q_low for w in ["categorical", "discrete", "debit", "interest", "city"]):
            syntax.append(f"FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")
            syntax.append(f"ECHO 'INTERPRETATION: Categorical distribution analysis'.")

        # التقسيم (Recode) - ذكي حسب المتغير
        elif "frequency table" in q_low and ("classes" in q_low or "suitable" in q_low or "appropriate" in q_low):
            syntax.append(f"* K-rule applied: 2^{k_rule} >= {n}.")
            if v_target == "X1":
                syntax.append(f"RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_Classes.")
                syntax.append("VALUE LABELS X1_Classes 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 '1501-2000' 5 'Over 2000'.")
            else:
                syntax.append(f"RECODE X2 (2 thru 5=1) (6 thru 9=2) (10 thru 13=3) (14 thru 17=4) (18 thru 21=5) (22 thru 25=6) INTO X2_Krule.")
                syntax.append("VALUE LABELS X2_Krule 1 '2-5' 2 '6-9' 3 '10-13' 4 '14-17' 5 '18-21' 6 '22-25'.")
            syntax.append(f"FREQUENCIES VARIABLES={v_target}_Classes if exists /FORMAT=AVALUE.")

        # الإحصاء الوصفي (Mean, Skewness...)
        elif any(w in q_low for w in ["mean", "median", "mode", "calculate"]):
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS.")

        # الرسوم البيانية المتطورة
        elif "bar chart" in q_low:
            stat = "MAX" if "max" in q_low else ("PCT" if "percentage" in q_low else "MEAN")
            group = "X6" if "city" in q_low else "X4"
            syntax.append(f"GRAPH /BAR({('GROUPED' if 'each' in q_low and 'city' in q_low else 'SIMPLE')})={stat}({v_target}) BY {group} {'BY X4' if 'grouped' in q_low else ''}.")

        elif "pie chart" in q_low:
            syntax.append(f"GRAPH /PIE=PCT BY X5 /TITLE='Percentage of Interest Receivers'.")

        # تحليل المجموعات (Split File)
        elif "each city" in q_low or "card or not" in q_low:
            group = "X6" if "city" in q_low else "X4"
            syntax.append(f"SORT CASES BY {group}.\nSPLIT FILE SEPARATE BY {group}.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE SKEWNESS.\nSPLIT FILE OFF.")

        # الاستكشاف (Confidence & Normality)
        elif any(w in q_low for w in ["confidence", "normality", "outliers"]):
            syntax.append(f"EXAMINE VARIABLES=X1 /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            if "99" in q_low: syntax.append(f"EXAMINE VARIABLES=X1 /CINTERVAL 99.")
            syntax.append("ECHO 'RULE: Shapiro-Wilk > 0.05 => Empirical Rule; < 0.05 => Chebyshev Rule'.")

        syntax.append("\n")
        q_idx += 1

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# (واجهة Streamlit تظل كما هي...)
