import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def master_spss_engine_final_v7(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # جمع النصوص من كل مكان في الوورد
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip(): paragraphs.append(cell.text.strip())
    
    mapping = {}
    for p in paragraphs:
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip().lower()
            mapping[v_name] = v_label

    syntax = ["* --- Final Professional Solution for SPSS v26 --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    syntax.append("\nSET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        # ربط المتغيرات (البحث عن الرمز أو الاسم النصي)
        found_vars = []
        for v_code, v_label in mapping.items():
            if v_code.lower() in p_low or v_label[:15] in p_low:
                found_vars.append(v_code)
        
        # دعم يدوي للأسئلة التي لا تحتوي على رموز صريحة
        if "balance" in p_low and "X1" not in found_vars: found_vars.append("X1")
        if "city" in p_low and "X6" not in found_vars: found_vars.append("X6")
        if "transaction" in p_low and "X2" not in found_vars: found_vars.append("X2")
        if "debit" in p_low and "X4" not in found_vars: found_vars.append("X4")

        if not found_vars: continue
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. الرسوم البيانية (تصحيح الخطأ 701 و 17807)
        if "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if len(found_vars) >= 2:
                    # الصيغة الصحيحة: MEAN(X1) BY X6
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}) BY {found_vars[1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}).")
            elif "maximum" in p_low:
                if len(found_vars) >= 2:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MAX({found_vars[0]}) BY {found_vars[1]}.")
            elif "percentage" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {found_vars[0]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        # 2. فترات الثقة (95% و 99% في جداول مستقلة)
        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL {val}.")

        # 3. الإحصاء الوصفي والتكرارات
        elif any(w in p_low for w in ["mean", "median", "calculate", "mode", "deviation"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")
        
        elif "frequency table" in p_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")

        # 4. الهيستوجرام
        elif "histogram" in p_low:
            for v in found_vars: syntax.append(f"GRAPH /HISTOGRAM={v}.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("🧙‍♂️ SPSS Master Pro (v26 Corrected)")
u_excel = st.file_uploader("Excel File", type=['xlsx', 'xls'])
u_word = st.file_uploader("Word File (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        final_code = master_spss_engine_final_v7(u_word)
        st.success("تم توليد الكود وتصحيح أخطاء الرسم البياني وفصل فترات الثقة!")
        st.code(final_code, language='spss')
        st.download_button("تحميل الملف .sps", final_code, "Final_Solution_v26.sps")
    except Exception as e:
        st.error(f"Error: {e}")
