import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def universal_master_engine_v24(doc_upload):
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

    syntax = ["* --- Final Scientific Universal Solution (Fixed & Fully Complete) --- *.\n"]
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
        if "city" in p_low: found_vars.append("X6")
        if "debit" in p_low: found_vars.append("X4")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and "normality" not in p_low: continue
        
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. التكرارات والتقسيم لفئات (حل الأسئلة الفارغة والـ Recode)
        if "frequency table" in p_low:
            if "classes" in p_low or "k rule" in p_low:
                target = "X1" if "balance" in p_low else "X2" if "transaction" in p_low else found_vars[0]
                syntax.append(f"RECODE {target} (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru HI=4) INTO {target}_CL.")
                syntax.append(f"VARIABLE LABELS {target}_CL 'Categorized {target}'.")
                syntax.append(f"FREQUENCIES VARIABLES={target}_CL /ORDER=ANALYSIS.")
            else:
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars) if found_vars else 'X4 X5 X6'} /ORDER=ANALYSIS.")

        # 2. الإحصاء الوصفي والتحليل المقارن (Split File)
        elif any(w in p_low for w in ["mean", "median", "calculate", "each city", "debit card or not"]):
            if "each city" in p_low or "city" in p_low:
                syntax.append("SORT CASES BY X6.\nSPLIT FILE SEPARATE BY X6.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")
            elif "debit card" in p_low and "not" in p_low:
                syntax.append("SORT CASES BY X4.\nSPLIT FILE SEPARATE BY X4.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")
            else:
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars) if found_vars else 'X1 X2'} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS SESKEW /FORMAT=NOTABLE.")

        # 3. الرسوم البيانية (Bar & Pie)
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if "debit card" in p_low: # الرسم المجمع المطلوب
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4.")
                else:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
            elif "maximum" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {found_vars[0] if found_vars else 'X5'}.")

        elif "pie chart" in p_low:
            syntax.append("GRAPH /PIE=COUNT BY X5.")

        # 4. فترات الثقة (95% و 99% - طلبك الأساسي)
        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 5. النورمالتي والقيم الشاذة
        elif "normality" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

        elif "histogram" in p_low:
            for v in ["X1", "X2"]:
                syntax.append(f"GRAPH /HISTOGRAM={v}.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("📊 المحلل الإحصائي المطور (إصدار v24 النهائي)")
u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الوورد (الأسئلة)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        final_syntax = universal_master_engine_v24(u_word)
        st.code(final_syntax, language='spss')
        st.download_button("تحميل السينتاكس النهائي الكامل (.sps)", final_syntax, "Final_Solution_v24.sps")
    except Exception as e:
        st.error(f"Error: {e}")
