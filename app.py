import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def final_master_spss_v12(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # سحب النصوص من الفقرات والجداول لضمان شمولية الحل
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

    syntax = ["* --- Final Professional Solution (No Warnings) for SPSS v26 --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    syntax.append("\nSET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        # ربط المتغيرات (البحث عن الرمز أو الاسم النصي)
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v][:12] in p_low]
        if "balance" in p_low: found_vars.append("X1")
        if "city" in p_low: found_vars.append("X6")
        
        found_vars = list(dict.fromkeys(found_vars))
        if not found_vars: continue

        syntax.append(f"\n* QUESTION: {p}.")

        # --- تصحيح أمر EXAMINE (الحل لمشكلة التحذير) ---
        if "confidence interval" in p_low:
            for val in ["95", "99"]:
                # الصيغة الصارمة: استخدام اليساوي في كل الأوامر الفرعية
                syntax.append(f"EXAMINE VARIABLES={found_vars[0]} /PLOT=NONE /STATISTICS=DESCRIPTIVES /CINTERVAL {val}.")

        # --- تصحيح أوامر الرسوم البيانية (تجنب خطأ 701) ---
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if len(found_vars) >= 2:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}) BY {found_vars[1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}).")
            elif "percentage" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {found_vars[0]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        # --- التحليل المقارن (Split File) ---
        elif "for each city" in p_low:
            syntax.append("SORT CASES BY X6.\nSPLIT FILE LAYERED BY X6.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")

        # --- الإحصاء الوصفي ---
        elif any(w in p_low for w in ["mean", "median", "calculate", "mode"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        # --- القيم الشاذة ---
        elif "outliers" in p_low or "extremes" in p_low:
            syntax.append(f"EXAMINE VARIABLES={found_vars[0]} /PLOT=BOXPLOT /STATISTICS=DESCRIPTIVES /EXTREME(5).")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة تطبيق Streamlit
st.title("🧙‍♂️ المولد الإحصائي الذكي (v26 Professional)")
u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        final_code = final_master_spss_v12(u_word)
        st.success("✅ تم توليد السينتاكس وتصحيح أوامر EXAMINE بنجاح!")
        st.code(final_code, language='spss')
        st.download_button("تحميل الملف النهائي .sps", final_code,
