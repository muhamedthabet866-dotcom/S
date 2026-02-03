import streamlit as st
import pandas as pd
from docx import Document
import re

# دالة ذكية لاستخراج خريطة المتغيرات والأسئلة
def analyze_spss_document(doc_file):
    doc = Document(doc_file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    mapping = {}
    questions = []
    
    # 1. فصل التعريفات (Where) عن أسئلة التحليل
    for p in paragraphs:
        # البحث عن التعريفات مثل X1 = ...
        match = re.search(r"(X\d+)\s*=\s*([^(\n]+)", p, re.IGNORECASE)
        if match:
            var_name = match.group(1).upper()
            var_label = match.group(2).strip()
            # استخراج القيم (Value Labels) إن وجدت مثل (1=yes)
            values = re.findall(r"(\d+)\s*=\s*([a-zA-Zأ-ي]+)", p)
            mapping[var_name] = {"label": var_label, "values": values}
        else:
            # أي سطر آخر يحتوي على كلمات تحليلية نعتبره سؤالاً
            if any(word in p.lower() for word in ['construct', 'calculate', 'draw', 'test', 'mean', 'chart']):
                questions.append(p)
                
    return mapping, questions

def generate_scientific_syntax(mapping, questions, excel_cols):
    syntax = ["* SPSS Syntax Generated for SPSS v26 - Professional Analysis.\n"]
    
    # تعريف المتغيرات أولاً (Variable & Value Labels)
    for var, info in mapping.items():
        if var in [c.upper() for c in excel_cols]:
            syntax.append(f"VARIABLE LABELS {var} '{info['label']}'.")
            if info['values']:
                syntax.append(f"VALUE LABELS {var}")
                for val, lab in info['values']:
                    syntax.append(f"  {val} '{lab}'")
                syntax.append(".")

    syntax.append("\n* --- Start of Scientific Analysis ---.\n")

    # تحليل كل سؤال وتوليد الكود المقابل له
    for q in questions:
        q_low = q.lower()
        # تحديد المتغيرات المذكورة في السؤال
        found_vars = [v for v in mapping.keys() if v in q.upper() or mapping[v]['label'].lower() in q_low]
        if not found_vars: found_vars = [v for v in mapping.keys() if v in q.upper()]

        # أ. الجداول التكرارية
        if "frequency table" in q_low:
            syntax.append(f"* {q}.\nFREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")
        
        # ب. الإحصاء الوصفي (Mean, Median, etc.)
        elif any(word in q_low for word in ["mean", "median", "mode", "calculate"]):
            syntax.append(f"* {q}.\nDESCRIPTIVES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN STDDEV MIN MAX KURTOSIS SKEWNESS.")

        # ج. الرسوم البيانية
        elif "histogram" in q_low:
            for v in found_vars:
                syntax.append(f"GRAPH /HISTOGRAM={v} /TITLE='Histogram of {v}'.")
        
        elif "bar chart" in q_low:
            if len(found_vars) >= 2:
                syntax.append(f"GRAPH /BAR(MEAN)={found_vars[0]} BY {found_vars[1]}.")
            else:
                syntax.append(f"GRAPH /BAR(COUNT) BY {' '.join(found_vars)}.")

        # د. اختبارات الفرضيات (T-Test)
        elif "test the hypothesis" in q_low or "difference" in q_low:
            if len(found_vars) >= 2:
                syntax.append(f"T-TEST GROUPS={found_vars[1]}(0 1) /VARIABLES={found_vars[0]}.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة تطبيق Streamlit
st.set_page_config(page_title="SPSS Scientific Generator", layout="wide")
st.title("🔬 المولد العلمي لسينتاكس SPSS v26")

up_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls'])
up_word = st.file_uploader("2. ارفع ملف الوورد (docx فقط)", type=['docx'])

if up_excel and up_word:
    df = pd.read_excel(up_excel)
    mapping, questions = analyze_spss_document(up_word)
    
    if mapping:
        st.success(f"تم اكتشاف {len(mapping)} متغيرات و {len(questions)} طلبات تحليل.")
        final_syntax = generate_scientific_syntax(mapping, questions, df.columns)
        
        st.subheader("السينتاكس العلمي الناتج:")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل الملف جاهزاً للتشغيل على SPSS v26", final_syntax, "analysis_v26.sps")
    else:
        st.warning("لم يتم العثور على تعريفات للمتغيرات (X1, X2...) في ملف الوورد.")
