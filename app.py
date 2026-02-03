import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def master_spss_engine_v4(doc_upload):
    # قراءة الملف من الذاكرة
    doc = Document(io.BytesIO(doc_upload.read()))
    paragraphs = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 3]
    
    mapping = {}
    analysis_questions = []

    # 1. استخراج الخريطة (التعريفات)
    for p in paragraphs:
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            # استخراج القيم مثل 1=yes
            vals = re.findall(r"(\d+)\s*=\s*([a-zA-Zأ-ي]+)", p)
            mapping[v_name] = {"label": v_label, "values": vals}
        else:
            # تخزين الأسطر التي تبدو كطلبات تحليل
            if any(key in p.lower() for key in ['construct', 'calculate', 'draw', 'test', 'mean', 'interval', 'chart']):
                analysis_questions.append(p)

    syntax = ["* --- Final Scientific Solution for SPSS v26 --- *.\n"]
    
    # 2. توليد التعريفات (Labels)
    for var, info in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{info['label']}'.")
        if info['values']:
            syntax.append(f"VALUE LABELS {var}")
            for val, txt in info['values']: syntax.append(f"  {val} '{txt}'")
            syntax.append(".")

    syntax.append("\nSET DECIMAL=DOT.\n")

    # 3. تحليل الأسئلة (التحويل الفعلي للأوامر)
    for q in analysis_questions:
        q_low = q.lower()
        # محاولة إيجاد المتغيرات المرتبطة بالسؤال بذكاء
        target_vars = []
        for v_code, v_info in mapping.items():
            if v_code.lower() in q_low or v_info['label'].lower()[:10] in q_low:
                target_vars.append(v_code)
        
        # إذا لم يجد متغيرات محددة، يبحث عن الكلمات العامة (مثلاً account balance)
        if not target_vars:
            if "account balance" in q_low: target_vars.append("X1")
            if "atm transaction" in q_low: target_vars.append("X2")
            if "city" in q_low: target_vars.append("X6")
            if "debit card" in q_low: target_vars.append("X4")
            if "interest" in q_low: target_vars.append("X5")

        if not target_vars: continue

        syntax.append(f"\n* QUESTION: {q}.")

        # أ. فترات الثقة المنفصلة (كما طلبت 95% و 99%)
        if "confidence interval" in q_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(target_vars)} /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL {val}.")

        # ب. الرسوم البيانية (Bar, Pie, Histogram)
        elif "bar chart" in q_low:
            stat = "MEAN" if "average" in q_low else "MAX" if "maximum" in q_low else "COUNT"
            if len(target_vars) >= 2:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({target_vars[0]}) BY {target_vars[1]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {target_vars[0]}.")

        elif "pie chart" in q_low:
            syntax.append(f"GRAPH /PIE=COUNT BY {target_vars[0]}.")

        elif "histogram" in q_low:
            for v in target_vars: syntax.append(f"GRAPH /HISTOGRAM={v}.")

        # ج. الإحصاء الوصفي والتكرارات
        elif any(w in q_low for w in ["mean", "median", "calculate", "mode", "std"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(target_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        elif "frequency table" in q_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(target_vars)} /ORDER=ANALYSIS.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة تطبيق Streamlit
st.set_page_config(page_title="SPSS Master", layout="wide")
st.title("📊 نظام تحليل البيانات العلمي (v26)")

u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        st.success("تم تحميل البيانات.")
        final_syntax = master_spss_engine_v4(u_word)
        st.subheader("السينتاكس الكامل الناتج:")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل الملف .sps", final_syntax, "SPSS_Full_Solution.sps")
    except Exception as e:
        st.error(f"خطأ: {e}")
