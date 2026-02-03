import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def universal_spss_engine_v22(doc_upload):
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        # استخراج النصوص الخام للملفات القديمة .doc لضمان شمولية الحل 
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    mapping = {}
    for p in paragraphs:
        # استخراج تعريفات المتغيرات X1-X12 من ملف الوورد [cite: 10]
        match = re.search(r"([Xx]\d+)\s*=\s*([^(\n\r.]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* --- Final Scientific Solution (Strict SPSS v26 Compliance) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    
    # تعريف القيم لضمان دقة تحليل البيانات الاسمية [cite: 10]
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        # ربط المتغيرات بالأسئلة بناءً على الأسماء والرموز [cite: 1, 6, 10]
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v].lower()[:10] in p_low]
        if "balance" in p_low: found_vars.append("X1")
        if "transaction" in p_low: found_vars.append("X2")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and "normality" not in p_low: continue
        
        syntax.append(f"\n* QUESTION: {p}.")

        # --- تصحيح أمر فترات الثقة (95% و 99% - الترتيب الآمن)  ---
        if "confidence interval" in p_low:
            for val in ["95", "99"]:
                # الترتيب الصحيح: Variables ثم Statistics ثم Cinterval ثم Plot 
                syntax.append(f"EXAMINE VARIABLES = {' '.join(found_vars) if found_vars else 'X1'} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # --- تصحيح الرسوم البيانية (منع الخطأ 701) [cite: 6, 7] ---
        elif "bar chart" in p_low:
            stat = "MEAN" if "average" in p_low else "MAX" if "maximum" in p_low else "PCT" if "percentage" in p_low else "COUNT"
            if len(found_vars) >= 2:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({found_vars[0]}) BY {found_vars[1]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {found_vars[0] if found_vars else 'X1'}.")

        # --- التحليل الوصفي والالتواء [cite: 4, 6] ---
        elif any(w in p_low for w in ["mean", "median", "calculate", "skewness"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS SESKEW /FORMAT=NOTABLE.")

        # --- القيم الشاذة والنورمالتي  ---
        elif "normality" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars) if found_vars else 'X1'} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low or "extremes" in p_low:
            syntax.append(f"EXAMINE VARIABLES={found_vars[0] if found_vars else 'X1'} /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("📊 المحلل الإحصائي المطور (إصلاح EXAMINE)")
u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الوورد (الأسئلة)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        final_syntax = universal_spss_engine_v22(u_word)
        st.code(final_syntax, language='spss')
        st.download_button("تحميل السينتاكس المصلح (.sps)", final_syntax, "Final_Solution_v22.sps")
    except Exception as e:
        st.error(f"Error: {e}")
