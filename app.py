import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def final_master_spss_v14(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # استخراج النصوص من الفقرات والجداول
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

    syntax = ["* --- Final Scientific Solution for SPSS v26 (Fixed & Complete) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    syntax.append("\nSET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        # ربط المتغيرات بالأسئلة (تحديد X1 للرصيد، X2 للعمليات، X4 للبطاقة، X5 للفائدة، X6 للمدينة)
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v][:12] in p_low]
        if "balance" in p_low: found_vars.append("X1")
        if "transaction" in p_low: found_vars.append("X2")
        if "city" in p_low: found_vars.append("X6")
        if "debit" in p_low: found_vars.append("X4")
        if "interest" in p_low: found_vars.append("X5")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and not any(key in p_low for key in ['normality', 'empirical']): continue
        
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. فترات الثقة (فصل 95% و 99% - الصيغة التي لا تسبب Warnings)
        if "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES = X1 /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 2. الرسوم البيانية (تصحيح ترتيب المتغيرات لمنع Error 701)
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if "city" in p_low and "debit card" in p_low:
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4.")
                elif "city" in p_low:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
                else:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1).")
            elif "maximum" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4.")
            elif "percentage" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {found_vars[0] if found_vars else 'X5'}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        elif "pie chart" in p_low:
            syntax.append("GRAPH /PIE=COUNT BY X5.")

        # 3. التحليل الشرطي (Split File)
        elif "for each city" in p_low:
            syntax.append("SORT CASES BY X6.\nSPLIT FILE LAYERED BY X6.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")
        elif "debit card or not" in p_low:
            syntax.append("SORT CASES BY X4.\nSPLIT FILE LAYERED BY X4.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")

        # 4. التكرارات والإحصاء الوصفي
        elif any(w in p_low for w in ["mean", "median", "calculate", "mode"]):
            vars_to_analyze = [v for v in found_vars if v in ['X1', 'X2']] or ['X1', 'X2']
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(vars_to_analyze)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        elif "frequency table" in p_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")

        elif "histogram" in p_low:
            for v in [v for v in found_vars if v in ['X1', 'X2']] or ['X1', 'X2']:
                syntax.append(f"GRAPH /HISTOGRAM={v}.")

        # 5. النورمالتي والقيم الشاذة
        elif "normality" in p_low or "empirical" in p_low:
            syntax.append("EXAMINE VARIABLES = X1 /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
            
        elif "outliers" in p_low:
            syntax.append("EXAMINE VARIABLES = X1 /STATISTICS DESCRIPTIVES EXTREME(5) /PLOT BOXPLOT.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Master Pro", layout="wide")
st.title("📊 المحلل الإحصائي الذكي (v26 - النسخة النهائية)")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("2. ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        st.success("✅ تم تحميل الملفات بنجاح.")
        final_code = final_master_spss_v14(u_word)
        st.subheader("السينتاكس الناتج (كامل وشامل):")
        st.code(final_code, language='spss')
        st.download_button(label="تحميل ملف الـ Syntax (.sps)", data=final_code, file_name="Final_SPSS_Solution.sps", mime="text/plain")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
