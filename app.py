import streamlit as st
import pandas as pd
import re

def generate_fixed_syntax(var_defs, questions_text):
    var_map = {}
    variable_labels = []
    
    # تحسين استخراج المتغيرات والوصف
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().lower()
            v_label = match.group(2).strip()
            # إزالة أي شرح إضافي بين الأقواس من اسم المتغير
            clean_label = re.sub(r'\(.*\)', '', v_label).strip()
            var_map[clean_label.lower()] = v_code
            variable_labels.append(f"{v_code} \"{v_label}\"")

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*70,
        "* Intelligent SPSS Syntax Generator (Data Set 1)",
        "* " + "="*70 + ".\n"
    ]

    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # تصحيح الـ Value Labels (فقط للمتغيرات المنطقية)
    syntax.append("VALUE LABELS x4 1 'Yes' 0 'No' /x5 1 'Yes' 0 'No'.")
    syntax.append("EXECUTE.\n")

    q_low = questions_text.lower()

    # [Q1] Frequency Tables for Categorical
    if "frequency table" in q_low and "categorical" in q_low:
        syntax.append("* [Q1] Frequency tables for discrete variables.")
        syntax.append("FREQUENCIES VARIABLES=x4 x5 x6 /ORDER=ANALYSIS.\n")

    # [Q2-Q4] Continuous Data Analysis (Account Balance x1 & Transactions x2)
    if "account balance" in q_low or "transactions" in q_low:
        syntax.append("* [Q4] Descriptive Statistics for Continuous Data.")
        syntax.append("FREQUENCIES VARIABLES=x1 x2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.\n")
        
        syntax.append("* [Q5] Histograms for Continuous Data.")
        syntax.append("GRAPH /HISTOGRAM=x1 /TITLE='Account Balance Distribution'.")
        syntax.append("GRAPH /HISTOGRAM=x2 /TITLE='ATM Transactions Distribution'.\n")

    # [Q7-Q8] Specialized Bar & Pie Charts
    if "bar chart" in q_low:
        syntax.append("* [Q7] Bar Charts: Mean Balance by City.")
        syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x1) BY x6 /TITLE='Average Balance by City'.")
        if "debit card" in q_low:
            syntax.append("GRAPH /BAR(GROUPED)=MEAN(x1) BY x6 BY x4 /TITLE='Avg Balance by City & Debit Card'.\n")

    if "pie chart" in q_low:
        syntax.append("* [Q8] Pie Chart for Interest.")
        syntax.append("GRAPH /PIE=COUNT BY x5 /TITLE='Percentage of Interest Receivers'.\n")

    # [Q9] Normality & Outliers
    if "outliers" in q_low or "normality" in q_low:
        syntax.append("* [Q9] Explore: Normality and Outliers.")
        syntax.append("EXAMINE VARIABLES=x1 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES /CINTERVAL 95.\n")

    # [Grouped Analysis]
    if "each city" in q_low or "each gender" in q_low:
        syntax.append("* Split File Analysis for City/Debit Card.")
        syntax.append("SORT CASES BY x6 x4.\nSPLIT FILE LAYERED BY x6 x4.")
        syntax.append("DESCRIPTIVES VARIABLES=x1 x2 /STATISTICS=MEAN MEDIAN STDDEV.")
        syntax.append("SPLIT FILE OFF.\n")

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# UI Code remains the same...
