import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def clean_spss_engine_v31(doc_upload):
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

    # بداية السينتاكس مع تحديد الترميز لمنع التلف
    syntax = ["* Encoding: UTF-8.\n"]
    syntax.append("* --- Final Stable Engine (v31) --- *.\n")
    
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

        # 1. أوامر EXAMINE المحصنة (لمنع الـ Warnings والتلف)
        if "confidence interval" in p_low:
            # الصيغة المختصرة والأكثر استقراراً في SPSS v26
            syntax.append(f"EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 95.")
            syntax.append(f"EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 99.")
        
        elif "normality" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
            
        elif "outliers" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

        # 2. أوامر الرسوم البيانية (بصيغة v26 الأصلية)
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if "debit card" in p_low:
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4.")
                else:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
            elif "maximum" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=PCT BY X5.")

        # 3. الجداول التكرارية والإحصاء الوصفي
        elif any(w in p_low for w in ["mean", "median", "frequency table"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars) if found_vars else 'X1 X2'} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS.")

        elif "histogram" in p_low:
            syntax.append("GRAPH /HISTOGRAM=X1.\nGRAPH /HISTOGRAM=X2.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Fixer", layout="wide")
st.title("🛠️ مصلح ملفات SPSS (v31)")

u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("ارفع ملف الوورد", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        final_syntax = clean_spss_engine_v31(u_word)
        st.success("✅ تم توليد سينتاكس نظيف (Clean Syntax) متوافق مع v26.")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل الملف المصلح (.sps)", final_syntax, "Clean_Solution.sps")
    except Exception as e:
        st.error(f"Error: {e}")
