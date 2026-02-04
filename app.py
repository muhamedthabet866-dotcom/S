import streamlit as st
import pandas as pd
import re

def generate_dynamic_syntax(var_defs, questions_text):
    # 1. تحليل خريطة المتغيرات لبناء قاموس (الوصف -> اسم المتغير)
    # مثال: {'account balance': 'x1', 'debit card': 'x4'}
    var_map = {}
    variable_labels = []
    
    lines = var_defs.split('\n')
    for line in lines:
        # البحث عن نمط مثل x1 = Account Balance أو x1: Account Balance
        match = re.search(r'(x\d+)\s*[=:]\s*(.+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().lower() # x1
            v_label = match.group(2).strip() # Account Balance
            var_map[v_label.lower()] = v_code
            variable_labels.append(f"{v_code} \"{v_label}\"")

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*70,
        "* Automated SPSS Syntax Generator - Dynamic Model",
        "* Generated based on User Mapping and Questions",
        "* " + "="*70 + ".\n"
    ]

    # إضافة التسميات (Labels)
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # محاولة استخراج Value Labels إذا وجدت (مثل 1=Yes, 0=No)
    # هذا الجزء يبحث في النص عن تعريفات القيم
    value_labels_found = []
    for line in lines:
        val_match = re.findall(r'(\d+)\s*=\s*([a-zA-Z]+)', line)
        if val_match:
            # استخراج اسم المتغير من نفس السطر
            v_code_match = re.search(r'(x\d+)', line, re.IGNORECASE)
            if v_code_match:
                v_code = v_code_match.group(1).lower()
                labels = " ".join([f'{v[0]} "{v[1]}"' for v in val_match])
                value_labels_found.append(f"  /{v_code} {labels}")
    
    if value_labels_found:
        syntax.append("VALUE LABELS" + "\n".join(value_labels_found) + ".")
    
    syntax.append("EXECUTE.\n")

    # 2. تحليل الأسئلة وتوليد الأوامر
    questions = re.split(r'\|\n\d+\.', questions_text) # تقسيم الأسئلة
    
    for q in questions:
        if not q.strip(): continue
        q_low = q.lower()
        
        # تحديد المتغيرات المذكورة في هذا السؤال
        mentioned_vars = []
        for label, code in var_map.items():
            if label in q_low:
                mentioned_vars.append(code)
        
        # تنظيف المتغيرات المتكررة
        mentioned_vars = list(dict.fromkeys(mentioned_vars))
        vars_str = " ".join(mentioned_vars)

        # منطق توليد الأوامر بناءً على الكلمات المفتاحية
        if vars_str:
            syntax.append(f"* Analysis for: {q.strip()[:100]}...")
            
            # جداول التكرار
            if "frequency table" in q_low or "categorical" in q_low:
                syntax.append(f"FREQUENCIES VARIABLES={vars_str} /ORDER=ANALYSIS.")
            
            # الإحصاء الوصفي
            if any(word in q_low for word in ["mean", "median", "mode", "descriptive", "standard deviation"]):
                syntax.append(f"DESCRIPTIVES VARIABLES={vars_str} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS.")
            
            # الرسم البياني (Histogram)
            if "histogram" in q_low:
                for v in mentioned_vars:
                    syntax.append(f"GRAPH /HISTOGRAM={v}.")
            
            # الرسم البياني (Bar Chart)
            if "bar chart" in q_low:
                if "average" in q_low or "mean" in q_low:
                    # محاولة معرفة متغير التصنيف (مثلاً By City)
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({mentioned_vars[0]}) BY {mentioned_vars[-1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {mentioned_vars[0]}.")

            # الرسم البياني (Pie Chart)
            if "pie chart" in q_low:
                syntax.append(f"GRAPH /PIE=COUNT BY {mentioned_vars[0]}.")

            # اختبارات الطبيعية (Normality / Outliers)
            if any(word in q_low for word in ["normality", "outliers", "extreme", "explore"]):
                syntax.append(f"EXAMINE VARIABLES={vars_str} /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.")

            syntax.append("") # سطر فارغ للتنظيم

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="Universal SPSS Engine", layout="wide")
st.title("🤖 Universal SPSS Syntax Engine")
st.subheader("قم بإدخال أي متغيرات وأي أسئلة وسيقوم البرنامج ببناء الكود المناسب")

col1, col2 = st.columns(2)
with col1:
    v_in = st.text_area("1. أدخل تعريف المتغيرات (مثال: x1 = Account Balance):", 
                        height=250, 
                        placeholder="x1 = Account Balance\nx4 = Has a debit card (1=yes, 0=no)")
with col2:
    q_in = st.text_area("2. الصق أسئلة الامتحان هنا:", 
                        height=250, 
                        placeholder="Construct a frequency table for debit card...\nCalculate mean for account balance...")

if st.button("Generate Syntax"):
    if v_in and q_in:
        result = generate_dynamic_syntax(v_in, q_in)
        st.code(result, language='spss')
        st.download_button("Download .SPS File", result, file_name="Dynamic_Analysis.sps")
    else:
        st.error("من فضلك أدخل المتغيرات والأسئلة أولاً.")
