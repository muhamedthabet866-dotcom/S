import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def universal_spss_engine_v18(doc_upload):
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    mapping = {}
    for p in paragraphs:
        match = re.search(r"([Xx]\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* --- Final Corrected Solution (Fixing Error 701) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"[Xx]\d+\s*=", p): continue
        
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v].lower()[:10] in p_low]
        if not found_vars and "normality" not in p_low: continue

        syntax.append(f"\n* QUESTION: {p}.")

        # --- تصحيح أوامر الرسوم البيانية (الحل الجذري لخطأ 701) ---
        if "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if len(found_vars) >= 2:
                    # الصيغة العلمية: MEAN(Variable) BY Category
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}) BY {found_vars[1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}).")
            elif "maximum" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=MAX({found_vars[0]}) BY {found_vars[1] if len(found_vars)>1 else 'X4'}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        # --- فترات الثقة (فصل 95% و 99% في جداول مستقلة) ---
        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # --- بقية الأوامر الإحصائية ---
        elif any(w in p_low for w in ["mean", "median", "calculate"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS.")

        elif "normality" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("🏆 المحلل الإحصائي المطور (Fixing Error 701)")
u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد", type=['doc', 'docx'])

if u_excel and u_word:
    try:
        final_code = universal_spss_engine_v18(u_word)
        st.code(final_code, language='spss')
        st.download_button("تحميل السينتاكس المصحح (.sps)", final_code, "SPSS_No_Errors.sps")
    except Exception as e:
        st.error(f"Error: {e}")
