import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def master_spss_engine_v6(doc_upload):
    # قراءة ملف الوورد بالكامل (الفقرات والجداول)
    doc = Document(io.BytesIO(doc_upload.read()))
    all_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip(): all_text.append(cell.text.strip())

    mapping = {}
    syntax = ["* --- Professional Corrected Syntax for SPSS v26 --- *.\n"]

    # 1. استخراج التعريفات (X1, X2...)
    for line in all_lines:
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", line, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label
            syntax.append(f"VARIABLE LABELS {v_name} '{v_label}'.")

    syntax.append("\nSET DECIMAL=DOT.\n")

    # 2. تحليل الأسئلة وترجمتها لأوامر (تصحيح خطأ 701)
    for line in all_lines:
        line_low = line.lower()
        if re.search(r"X\d+\s*=", line): continue # تخطي أسطر التعريف

        # تحديد المتغيرات المرتبطة بالسؤال
        target_vars = []
        for v_code, v_label in mapping.items():
            if v_code.lower() in line_low or v_label.lower()[:12] in line_low:
                target_vars.append(v_code)
        
        # كلمات مفتاحية احتياطية (لحالات الأسئلة النصية فقط)
        if not target_vars:
            if "balance" in line_low: target_vars.append("X1")
            if "transaction" in line_low or "atm" in line_low: target_vars.append("X2")
            if "city" in line_low: target_vars.append("X6")

        if not target_vars: continue

        syntax.append(f"\n* QUESTION: {line}.")

        # أ. تصحيح أوامر الرسم البياني (تجنب اعتبار MEAN كمتغير)
        if "bar chart" in line_low:
            if "average" in line_low or "mean" in line_low:
                if len(target_vars) >= 2:
                    # الصيغة الصحيحة التي لا تسبب خطأ 701
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({target_vars[0]}) BY {target_vars[1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN BY {target_vars[0]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {target_vars[0]}.")

        # ب. فترات الثقة (فصل 95% و 99% في جداول مستقلة)
        elif "confidence interval" in line_low:
            for pct in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(target_vars)} /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL {pct}.")

        # ج. الإحصاء الوصفي (Mean, Median, etc.)
        elif any(w in line_low for w in ["mean", "median", "calculate", "mode"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(target_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        # د. الهيستوجرام
        elif "histogram" in line_low:
            for v in target_vars:
                syntax.append(f"GRAPH /HISTOGRAM={v}.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("📊 المحلل الإحصائي المطور (Fixing Error 701)")
u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        final_syntax = master_spss_engine_v6(u_word)
        st.success("✅ تم تصحيح الأوامر وتوليد السينتاكس!")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل الملف .sps", final_syntax, "SPSS_Final_Fix.sps")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
