import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def advanced_master_engine_v32(doc_upload):
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    mapping = {}
    for p in paragraphs:
        match = re.search(r"([Xx]\d+)\s*=\s*([^(\n\r.]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* Encoding: UTF-8.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v].lower()[:10] in p_low]
        if "balance" in p_low: found_vars.append("X1")
        if "transaction" in p_low: found_vars.append("X2")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and "normality" not in p_low: continue
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. منطق تقسيم الفئات (RECODE) - حل مشكلة السؤال 2 و 3
        if "frequency table" in p_low and "classes" in p_low:
            target = "X1" if "balance" in p_low else "X2"
            if target == "X1":
                syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru HI=4) INTO X1_Classes.")
                syntax.append("VALUE LABELS X1_Classes 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 'Over 1500'.")
                syntax.append("FREQUENCIES VARIABLES=X1_Classes.")
            else: # السؤال 3 (K-rule)
                syntax.append("RECODE X2 (0 thru 5=1) (5.01 thru 10=2) (10.01 thru 15=3) (15.01 thru 20=4) (20.01 thru HI=5) INTO X2_Classes.")
                syntax.append("VALUE LABELS X2_Classes 1 '0-5' 2 '6-10' 3 '11-15' 4 '16-20' 5 'Over 20'.")
                syntax.append("FREQUENCIES VARIABLES=X2_Classes.")

        # 2. الإحصاء الوصفي (السؤال 4 و 6) - منع التكرار
        elif any(w in p_low for w in ["mean", "median", "calculate", "skewness"]):
            if "discuss" not in p_low: # تنفيذ الأمر للسؤال 4 فقط وتجنب تكراره في 6
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS SESKEW /FORMAT=NOTABLE.")
            else:
                syntax.append("ECHO 'Refer to Statistics table from Question 4 to discuss skewness'.")

        # 3. الرسوم البيانية (Bar, Histogram, Pie)
        elif "bar chart" in p_low:
            if "average" in p_low:
                if "grouped" in p_low or "one graph" in p_low:
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4.")
                else:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
            elif "maximum" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {found_vars[0] if found_vars else 'X5'}.")

        elif "histogram" in p_low:
            for v in ["X1", "X2"]: syntax.append(f"GRAPH /HISTOGRAM={v}.")

        # 4. فترات الثقة (فصل الجداول بناءً على طلبك)
        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 5. النورمالتي والقيم الشاذة
        elif "normality" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("🧙‍♂️ المحرك الإحصائي الذكي (v32)")
u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("ارفع ملف الوورد", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        final_syntax = advanced_master_engine_v32(u_word)
        st.code(final_syntax, language='spss')
        st.download_button("تحميل السينتاكس المطور (.sps)", final_syntax, "Advanced_Solution_v32.sps")
    except Exception as e:
        st.error(f"Error: {e}")
