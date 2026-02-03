import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def master_spss_engine_v8(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
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

    syntax = ["* --- Final Scientific Solution (Full Analysis) for SPSS v26 --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    syntax.append("\nSET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v][:15] in p_low]
        # دعم يدوي للأسئلة النصية
        if "balance" in p_low and "X1" not in found_vars: found_vars.append("X1")
        if "city" in p_low and "X6" not in found_vars: found_vars.append("X6")
        if "debit" in p_low and "X4" not in found_vars: found_vars.append("X4")

        if not found_vars: continue
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. التحليل المقارن (For each city / Debit card)
        if "for each city" in p_low:
            syntax.append("SORT CASES BY X6.\nSPLIT FILE LAYERED BY X6.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")
        
        elif "debit card or not" in p_low:
            syntax.append("SORT CASES BY X4.\nSPLIT FILE LAYERED BY X4.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")

        # 2. الرسوم البيانية المتطورة
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if "city" in p_low and "debit card" in p_low: # رسم مجمع
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4.")
                elif "city" in p_low:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}).")
            elif "maximum" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=MAX({found_vars[0]}) BY {found_vars[1] if len(found_vars)>1 else 'X4'}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        # 3. فترات الثقة المنفصلة
        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES=X1 /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL {val}.")

        # 4. القيم الشاذة والنورمالتي
        elif "outliers" in p_low or "extremes" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

        # 5. الإحصاء الوصفي العام
        elif any(w in p_low for w in ["mean", "median", "calculate"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        elif "frequency table" in p_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")

        elif "histogram" in p_low:
            for v in found_vars: syntax.append(f"GRAPH /HISTOGRAM={v}.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة المستخدم
st.title("🧙‍♂️ SPSS Master Pro (v26 Scientific Edition)")
u_excel = st.file_uploader("Excel File", type=['xlsx', 'xls'])
u_word = st.file_uploader("Word File (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        final_code = master_spss_engine_v8(u_word)
        st.success("✅ تم توليد الحل العلمي الكامل!")
        st.code(final_code, language='spss')
        st.download_button("تحميل الملف .sps", final_code, "Final_Solution_Scientific.sps")
    except Exception as e:
        st.error(f"Error: {e}")
