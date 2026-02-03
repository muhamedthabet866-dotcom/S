import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def master_spss_engine_final(doc_upload):
    # قراءة الملف من الذاكرة بشكل صحيح لتجنب خطأ التحميل
    doc = Document(io.BytesIO(doc_upload.read()))
    paragraphs = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 3]
    
    mapping = {}
    for p in paragraphs:
        # البحث عن التعريفات X1, X2...
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            # استخراج القيم التكويدية (مثل 1=yes)
            vals = re.findall(r"(\d+)\s*=\s*([a-zA-Zأ-ي]+)", p)
            mapping[v_name] = {"label": v_label, "values": vals}

    syntax = ["* --- Professional Analysis for SPSS v26 --- *.\n"]
    
    # تعريف Labels والمتغيرات
    for var, info in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{info['label']}'.")
        if info['values']:
            syntax.append(f"VALUE LABELS {var}")
            for val, txt in info['values']: syntax.append(f"  {val} '{txt}'")
            syntax.append(".")

    syntax.append("\nSET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue 
        
        # ربط المتغيرات بالأسئلة
        found_vars = [v for v in mapping.keys() if v in p.upper() or (len(mapping[v]['label']) > 4 and mapping[v]['label'][:12] in p_low)]
        
        if not found_vars: continue
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. حل فترات الثقة (كل نسبة في أمر منفصل تماماً)
        if "confidence interval" in p_low:
            intervals = re.findall(r"(\d+)%", p_low)
            if not intervals: intervals = ["95"]
            for interval in intervals:
                syntax.append(f"* Confidence Interval {interval}%.")
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL {interval}.")

        # 2. تصحيح أوامر الرسوم البيانية (تجنب Error 17807)
        elif "bar chart" in p_low:
            stat = "MEAN" if "average" in p_low or "mean" in p_low else "MAX" if "maximum" in p_low else "COUNT"
            if len(found_vars) >= 2:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({found_vars[0]}) BY {found_vars[1]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {found_vars[0]}.")

        elif "histogram" in p_low:
            for v in found_vars: syntax.append(f"GRAPH /HISTOGRAM={v}.")

        elif "pie chart" in p_low:
            syntax.append(f"GRAPH /PIE=COUNT BY {found_vars[0]}.")

        # 3. التحليلات الإحصائية الوصفية
        elif any(w in p_low for w in ["mean", "median", "calculate", "mode"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        elif "frequency table" in p_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Master Pro", layout="wide")
st.title("📊 المحلل الذكي لسينتاكس SPSS v26")

up_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls'])
up_word = st.file_uploader("2. ارفع ملف الوورد (.docx فقط)", type=['docx'])

if up_excel and up_word:
    try:
        df = pd.read_excel(up_excel)
        # تمرير الملف المرفوع مباشرة للدالة الجديدة
        syntax_result = master_spss_engine_final(up_word)
        st.success("✅ تم تحليل الأسئلة وتوليد السينتاكس بنجاح!")
        st.code(syntax_result, language='spss')
        st.download_button("تحميل ملف الـ Syntax (.sps)", syntax_result, "SPSS_Final_Ready.sps")
    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
