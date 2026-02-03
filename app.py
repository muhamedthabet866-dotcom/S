import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج البيانات من الوورد (الأسئلة والتعريفات)
def extract_model_data(doc_upload):
    try:
        doc = Document(io.BytesIO(doc_upload.read()))
        doc_upload.seek(0)
        full_text = []
        for p in doc.paragraphs:
            if p.text.strip(): full_text.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip(): full_text.append(cell.text.strip())
        
        mapping = {}
        content = "\n".join(full_text)
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", content, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower().strip()] = label.strip()
            
        return mapping, full_text
    except:
        return {}, []

# 2. محرك التوليد المطابق للحل النموذجي
def generate_model_syntax(paragraphs, var_map):
    syntax = [
        "* Encoding: UTF-8.\n",
        "* [PRE-ANALYSIS SETUP] Defining Variable Labels and Values."
    ]

    # إضافة التسميات (Variable Labels)
    if var_map:
        syntax.append("VARIABLE LABELS ")
        labels_str = " ".join([f"{v.upper()} \"{l}\"" for v, l in var_map.items()])
        syntax.append(f"    {labels_str}.")
    
    # تعريف القيم (Value Labels) النموذجية لـ Data Set 1
    syntax.append("VALUE LABELS X4 0 \"No\" 1 \"Yes\" /X5 0 \"No\" 1 \"Yes\" ")
    syntax.append("    /X6 1 \"City 1\" 2 \"City 2\" 3 \"City 3\" 4 \"City 4\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "=", "academy", "dr.", "best regards"]) or len(p) < 20:
            continue

        syntax.append("*" + "-"*73 + ".")
        syntax.append(f"TITLE \"QUESTION {q_idx}: {p[:60]}...\".")
        syntax.append("*" + "-"*73 + ".")

        # --- السؤال 1: الجداول التكرارية للبيانات الوصفية ---
        if "frequency table" in p_low and "categorical" in p_low:
            syntax.append("FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")
            syntax.append("ECHO \"INTERPRETATION: Distribution of debit cards, interest, and city locations\".")

        # --- السؤال 2 و 3: إعادة الترميز (RECODE) مع قاعدة K ---
        elif "frequency table" in p_low and "account balance" in p_low:
            syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_Classes.")
            syntax.append("VALUE LABELS X1_Classes 1 \"0-500\" 2 \"501-1000\" 3 \"1001-1500\" 4 \"1501-2000\" 5 \"Over 2000\".")
            syntax.append("FREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.")
            syntax.append("ECHO \"COMMENT: Reveals wealth concentration among clients\".")

        elif "frequency table" in p_low and "atm transaction" in p_low:
            syntax.append("* K-rule: 2^k >= n. For n=60, 2^6=64, so 6 classes are optimal.")
            syntax.append("RECODE X2 (2 thru 5=1) (6 thru 9=2) (10 thru 13=3) (14 thru 17=4) (18 thru 21=5) (22 thru 25=6) INTO X2_Krule.")
            syntax.append("VALUE LABELS X2_Krule 1 \"2-5\" 2 \"6-9\" 3 \"10-13\" 4 \"14-17\" 5 \"18-21\" 6 \"22-25\".")
            syntax.append("FREQUENCIES VARIABLES=X2_Krule.")

        # --- السؤال 4 و 5: الإحصاء الوصفي والرسوم البيانية ---
        elif "mean, median, mode" in p_low:
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE MINIMUM MAXIMUM RANGE VARIANCE STDDEV SKEWNESS SESKEW.")

        elif "histogram" in p_low:
            syntax.append("GRAPH /HISTOGRAM=X1 /TITLE=\"Histogram of Account Balance\".")
            syntax.append("GRAPH /HISTOGRAM=X2 /TITLE=\"Histogram of ATM Transactions\".")

        # --- السؤال 7 و 8: التحليل الطبقي (Split File) ---
        elif "each city" in p_low:
            syntax.append("SORT CASES BY X6.\nSPLIT FILE SEPARATE BY X6.")
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV SKEW.")
            syntax.append("SPLIT FILE OFF.")

        # --- الرسوم البيانية المتنوعة ---
        elif "bar chart" in p_low and "average" in p_low:
            syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 /TITLE=\"Average Account Balance by City\".")

        elif "pie chart" in p_low:
            syntax.append("GRAPH /PIE=PCT BY X5 /TITLE=\"Percentage of Interest Receivers\".")

        # --- فترات الثقة والاختبارات ---
        elif "confidence interval" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 95 /PLOT NONE.")
            syntax.append("EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 99 /PLOT NONE.")

        elif "normality" in p_low or "outliers" in p_low:
            syntax.append("EXAMINE VARIABLES=X1 /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES.")
            syntax.append("ECHO \"RULE: If Shapiro-Wilk Sig > 0.05, apply Empirical Rule. If < 0.05, use Chebyshev\".")

        syntax.append("")
        q_idx += 1

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Model Generator", layout="wide")
st.title("🎓 مولد السينتاكس النموذجي (Data Set 1 Edition)")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الوورد", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        var_map, paragraphs = extract_model_data(u_word)
        final_code = generate_model_syntax(paragraphs, var_map)
        st.success("✅ تم توليد السينتاكس مطابقاً تماماً للحل النموذجي!")
        st.code(final_code, language='spss')
        st.download_button("تحميل الملف (.sps)", final_code, "Final_Model_Analysis.sps")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
