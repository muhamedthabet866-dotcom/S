import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# دالة المعالجة الذكية - النسخة المستقرة رقم 13
def final_master_spss_v13(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # استخراج النصوص من الفقرات والجداول لضمان عدم ضياع أي سؤال
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    paragraphs.append(cell.text.strip())
    
    mapping = {}
    for p in paragraphs:
        # البحث عن التعريفات X1 = Label
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip().lower()
            mapping[v_name] = v_label

    syntax = ["* --- Final Professional Solution (Fixed Syntax) for SPSS v26 --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    syntax.append("\nSET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        # ربط المتغيرات بالأسئلة بذكاء
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v][:12] in p_low]
        if "balance" in p_low: found_vars.append("X1")
        if "city" in p_low: found_vars.append("X6")
        if "debit" in p_low: found_vars.append("X4")
        if "interest" in p_low: found_vars.append("X5")
        if "transaction" in p_low: found_vars.append("X2")
        
        found_vars = list(dict.fromkeys(found_vars))
        if not found_vars: continue

        syntax.append(f"\n* QUESTION: {p}.")

        # --- تصحيح أمر EXAMINE لضمان التوافق (إزالة علامات = الزائدة) ---
        if "confidence interval" in p_low:
            for val in ["95", "99"]:
                # الصيغة الأكثر قبولاً في SPSS v26
                syntax.append(f"EXAMINE VARIABLES = {found_vars[0]} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # --- تصحيح أوامر الرسوم البيانية ---
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if len(found_vars) >= 2:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}) BY {found_vars[1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}).")
            elif "maximum" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=MAX({found_vars[0]}) BY {found_vars[1] if len(found_vars)>1 else 'X4'}.")
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

        # --- الهيستوجرام ---
        elif "histogram" in p_low:
            for v in found_vars:
                if v in ['X1', 'X2']:
                    syntax.append(f"GRAPH /HISTOGRAM={v}.")

        # --- القيم الشاذة ---
        elif "outliers" in p_low or "extremes" in p_low:
            syntax.append(f"EXAMINE VARIABLES = {found_vars[0]} /STATISTICS DESCRIPTIVES EXTREME(5) /PLOT BOXPLOT.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة تطبيق Streamlit
st.set_page_config(page_title="SPSS Master Pro", layout="wide")
st.title("🧙‍♂️ المولد الإحصائي الذكي (v26 - النسخة المستقرة)")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("2. ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        # التعامل مع ملفات xls القديمة
        if u_excel.name.endswith('.xls'):
            df = pd.read_excel(u_excel, engine='xlrd')
        else:
            df = pd.read_excel(u_excel)
            
        st.success("✅ تم تحميل الملفات بنجاح.")
        
        final_code = final_master_spss_v13(u_word)
        st.subheader("السينتاكس الناتج:")
        st.code(final_code, language='spss')
        
        # تم تصحيح إغلاق القوس هنا لزر التحميل
        st.download_button(
            label="تحميل ملف الـ Syntax (.sps)",
            data=final_code,
            file_name="Final_SPSS_Solution.sps",
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
