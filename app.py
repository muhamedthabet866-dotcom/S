import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def master_spss_engine_v5(doc_upload):
    # قراءة الملف من الذاكرة
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # استخراج النصوص من الفقرات ومن الجداول لضمان عدم ضياع أي سؤال
    all_text = []
    for p in doc.paragraphs:
        if p.text.strip(): all_text.append(p.text.strip())
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip(): all_text.append(cell.text.strip())
    
    mapping = {}
    analysis_lines = []

    # 1. المرحلة الأولى: استخراج التعريفات (X1, X2...)
    for line in all_text:
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", line, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            # استخراج القيم التكويدية مثل (1 = yes)
            vals = re.findall(r"(\d+)\s*[=-]\s*([a-zA-Zأ-ي]+)", line)
            mapping[v_name] = {"label": v_label, "values": vals}
        else:
            analysis_lines.append(line)

    syntax = ["* --- Final Scientific Solution for SPSS v26 --- *.\n"]
    
    # 2. توليد التعريفات (Labels)
    for var, info in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{info['label']}'.")
        if info.get("values"):
            syntax.append(f"VALUE LABELS {var}")
            for val, txt in info["values"]:
                syntax.append(f"  {val} '{txt}'")
            syntax.append(".")

    syntax.append("\nSET DECIMAL=DOT.\n")

    # 3. المرحلة الثانية: تحويل الأسئلة إلى أوامر إحصائية
    for q in analysis_lines:
        q_low = q.lower()
        
        # البحث عن المتغيرات المرتبطة بالسؤال بذكاء (بالاسم أو الرمز)
        target_vars = []
        for v_code, v_info in mapping.items():
            if v_code.lower() in q_low or v_info['label'].lower()[:12] in q_low:
                target_vars.append(v_code)
        
        # كلمات مفتاحية احتياطية لضمان الربط
        if not target_vars:
            if "balance" in q_low: target_vars.append("X1")
            if "atm" in q_low or "transaction" in q_low: target_vars.append("X2")
            if "debit" in q_low: target_vars.append("X4")
            if "interest" in q_low: target_vars.append("X5")
            if "city" in q_low: target_vars.append("X6")

        if not target_vars: continue

        syntax.append(f"\n* QUESTION: {q}.")

        # أ. فترات الثقة (فصل 95% و 99% في جداول مستقلة)
        if "confidence interval" in q_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(target_vars)} /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL {val}.")

        # ب. الرسوم البيانية (صيغة v26)
        elif "bar chart" in q_low:
            stat = "MEAN" if "average" in q_low else "MAX" if "maximum" in q_low else "PCT" if "percentage" in q_low else "COUNT"
            if len(target_vars) >= 2:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({target_vars[0]}) BY {target_vars[1]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {target_vars[0]}.")

        elif "pie chart" in q_low:
            syntax.append(f"GRAPH /PIE=COUNT BY {target_vars[0]}.")

        elif "histogram" in q_low:
            for v in target_vars: syntax.append(f"GRAPH /HISTOGRAM={v}.")

        # ج. الإحصاء الوصفي والتكرارات
        elif any(w in q_low for w in ["mean", "median", "calculate", "min", "max", "deviation"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(target_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        elif "frequency table" in q_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(target_vars)} /ORDER=ANALYSIS.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("🏆 نظام تحليل البيانات للمهندس محمد (النسخة الكاملة)")
u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        # قراءة الإكسيل مع دعم النسخ القديمة
        engine = 'xlrd' if u_excel.name.endswith('.xls') else 'openpyxl'
        df = pd.read_excel(u_excel, engine=engine)
        
        final_syntax = master_spss_engine_v5(u_word)
        st.subheader("السينتاكس المولد (يرجى التحقق من شمولية الأسئلة):")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل الملف .sps", final_syntax, "Final_Solution.sps")
    except Exception as e:
        st.error(f"خطأ: {e}")
