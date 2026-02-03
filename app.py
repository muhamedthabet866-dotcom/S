import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def final_master_spss_v9(doc_upload):
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

    syntax = ["* --- Final Scientific Solution for SPSS v26 (All Questions Solved) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    syntax.append("\nSET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v][:15] in p_low]
        if "balance" in p_low: found_vars.append("X1")
        if "city" in p_low: found_vars.append("X6")
        if "debit" in p_low: found_vars.append("X4")
        if "interest" in p_low: found_vars.append("X5")
        if "transaction" in p_low: found_vars.append("X2")
        found_vars = list(dict.fromkeys(found_vars)) # إزالة التكرار

        if not found_vars: continue
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. الأسئلة التي تطلب "For each city" أو "Debit card or not"
        if "for each city" in p_low:
            syntax.append("SORT CASES BY X6.\nSPLIT FILE LAYERED BY X6.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")
        elif "debit card or not" in p_low:
            syntax.append("SORT CASES BY X4.\nSPLIT FILE LAYERED BY X4.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")

        # 2. تصحيح أوامر الـ Bar Chart (منع خطأ 701)
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if "city" in p_low and "debit card" in p_low: # رسم مجمع (One Graph)
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4.")
                elif "city" in p_low:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}).")
            elif "maximum" in p_low:
                target = "X2" if "transaction" in p_low else found_vars[0]
                category = "X4" if "debit" in p_low else found_vars[-1]
                syntax.append(f"GRAPH /BAR(SIMPLE)=MAX({target}) BY {category}.")
            elif "percentage" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {found_vars[0]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        # 3. فترات الثقة (95% و 99% في جداول منفصلة)
        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES=X1 /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL {val}.")

        # 4. الرسوم البيانية الأخرى
        elif "histogram" in p_low:
            for v in [v for v in found_vars if v in ['X1', 'X2']]:
                syntax.append(f"GRAPH /HISTOGRAM={v}.")
        elif "pie chart" in p_low:
            syntax.append(f"GRAPH /PIE=COUNT BY {found_vars[0]}.")

        # 5. الإحصاء الوصفي والتكرارات
        elif any(w in p_low for w in ["mean", "median", "calculate", "skewness"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join([v for v in found_vars if v in ['X1', 'X2']])} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")
        elif "frequency table" in p_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")

        # 6. القيم الشاذة (Outliers)
        elif "outliers" in p_low or "extremes" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة تطبيق Streamlit
st.title("🧙‍♂️ المولد الإحصائي الذكي (النسخة النهائية)")
u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        st.success("✅ تم استلام الملفات وتحليلها.")
        final_syntax = final_master_spss_v9(u_word)
        st.code(final_syntax, language='spss')
        st.download_button("تحميل السينتاكس النهائي", final_syntax, "SPSS_Scientific_Analysis.sps")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
