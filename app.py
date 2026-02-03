import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج الميتا-داتا من الوورد (قراءة التعريفات X1, X2...)
def get_variable_mapping(doc):
    full_text = "\n".join([p.text for p in doc.paragraphs])
    mapping = {}
    matches = re.findall(r"(x\d+)\s*=\s*([^(\n\r\t]+)", full_text, re.IGNORECASE)
    for var, label in matches:
        mapping[var.lower()] = label.strip()
    return mapping

# 2. المحرك الرئيسي لتوليد الـ Syntax
def generate_spss_expert_syntax(doc_upload, excel_cols):
    doc_bytes = doc_upload.read()
    doc = Document(io.BytesIO(doc_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    var_map = get_variable_mapping(doc)
    
    # رأس ملف السينتاكس
    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* SPSS Syntax Generated for MBA Statistical Analysis",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Variable and Value Labeling] --- .",
        "* Scientific Justification: Proper labeling ensures readability and correct interpretation.",
        "VARIABLE LABELS"
    ]

    # توليد التسميات
    labels_list = []
    for var in [f"x{i}" for i in range(1, 14)]:
        lbl = var_map.get(var, f"Variable {var}")
        labels_list.append(f"  {var} \"{lbl}\"")
    syntax.append(" /\n".join(labels_list) + ".")

    # تعريف القيم الثابتة للمنهج
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\"")
    syntax.append("  /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\"")
    syntax.append("  /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if "where:" in p_low or "=" in p_low: continue # تخطي قسم التعريفات

        syntax.append(f"* --- [Q{q_idx}] {p[:50]}... --- .")
        
        # منطق اختيار الاختبار الإحصائي بناءً على الكلمات المفتاحية
        if "frequency table" in p_low:
            syntax.append("* Scientific Justification: Summarizing categorical distributions.")
            syntax.append(f"FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")

        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Visual comparison of group means or counts.")
            if "average" in p_low or "mean" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Average Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4.")

        elif "pie chart" in p_low:
            syntax.append("* Scientific Justification: Showing the composition of a whole.")
            syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Distribution Percentage'.")

        elif "descriptive" in p_low or "mean" in p_low:
            syntax.append("FREQUENCIES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.")

        elif "normality" in p_low or "outliers" in p_low:
            syntax.append("* Scientific Justification: Testing assumptions and identifying extremes.")
            syntax.append("EXAMINE VARIABLES=x3 x10 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.")

        elif "test the hypothesis" in p_low or "difference" in p_low:
            syntax.append("* Scientific Justification: Inferential testing for group differences.")
            if "independent" in p_low or "gender" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            elif "anova" in p_low or "region" in p_low or "occupation" in p_low:
                syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES.")

        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Measuring predictor strength on the dependent variable.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- واجهة المستخدم Streamlit ---
st.set_page_config(page_title="MBA SPSS Syntax Gen", layout="wide")
st.title("🚀 محرك الأكواد الإحصائية الاحترافي (SPSS v26)")
st.subheader("توليد Syntax مطابق لمنهج الدكتور محمد عبد السلام")

c1, c2 = st.columns(2)
with c1:
    u_excel = st.file_uploader("ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
with c2:
    u_word = st.file_uploader("ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # قراءة الأعمدة
        df = pd.read_excel(u_excel) if not u_excel.name.endswith('.csv') else pd.read_csv(u_excel)
        
        # التوليد
        sps_code = generate_spss_expert_syntax(u_word, df.columns.tolist())
        
        st.success("✅ تم إنشاء الكود بنجاح مع التبريرات العلمية!")
        st.code(sps_code, language='spss')
        
        st.download_button(
            label="تحميل ملف السينتاكس (.sps)",
            data=sps_code,
            file_name="MBA_Final_Analysis.sps",
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
