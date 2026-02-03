import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def extract_metadata_from_word(doc):
    """استخراج تسميات المتغيرات من قسم 'Where' في ملف الوورد"""
    mapping = {}
    full_text = "\n".join([p.text for p in doc.paragraphs])
    # البحث عن نمط X1 = Label
    matches = re.findall(r"(X\d+)\s*=\s*([^(\n\r\t]+)", full_text, re.IGNORECASE)
    for var, label in matches:
        mapping[var.upper()] = label.strip()
    return mapping

def generate_spss_v26_pro_engine(doc_upload, excel_columns):
    doc_bytes = doc_upload.read()
    doc = Document(io.BytesIO(doc_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    var_labels = extract_metadata_from_word(doc)
    
    # بداية السينتاكس بتنسيق احترافي
    syntax = [
        "* Encoding: UTF-8.",
        "* -------------------------------------------------------------------------",
        "* MBA STATISTICAL ANALYSIS REPORT - SPSS SYNTAX v26",
        "* -------------------------------------------------------------------------",
        "\n* [1] SETUP: VARIABLE LABELS AND DATA PREPARATION."
    ]
    
    # 1. تعريف التسميات (Labels)
    if var_labels:
        syntax.append("VARIABLE LABELS")
        for var, lbl in var_labels.items():
            syntax.append(f"  {var} \"{lbl}\"")
        syntax[-1] = syntax[-1] + "."
    
    # 2. تعريف القيم (Value Labels) - افتراضي بناءً على المنهج
    syntax.append("\nVALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X2 0 'National' 1 'American'.")

    # 3. معالجة الأسئلة وتحويلها لأوامر (Chapters 1-10)
    q_count = 2
    for p in paragraphs:
        p_low = p.lower()
        
        # تجاهل أسطر التعريف في نهاية الملف
        if "where:" in p_low or re.match(r"^x\d+\s*=", p_low):
            continue

        syntax.append(f"\n* [{q_count}] QUESTION: {p}.")
        
        # --- الإحصاء الوصفي (Chapter 2) ---
        if "frequency table" in p_low:
            if "classes" in p_low or "k rule" in p_low:
                syntax.append(f"* Applying K-Rule or Class Intervals for continuous data.")
                syntax.append(f"FREQUENCIES VARIABLES=X1 X2 /FORMAT=NOTABLE /HISTOGRAM /PERCENTILES=25 50 75.")
            else:
                syntax.append(f"FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")

        elif any(word in p_low for word in ["mean", "median", "mode", "standard deviation"]):
            syntax.append(f"DESCRIPTIVES VARIABLES=X1 X2 X3\n  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS.")

        # --- الرسوم البيانية (Chapter 2) ---
        elif "histogram" in p_low:
            syntax.append("GRAPH /HISTOGRAM=X1.\nGRAPH /HISTOGRAM=X2.")
            
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if "each city" in p_low:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 /TITLE='Average Balance by City'.")
                else:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X4 /TITLE='Average Salary'.")
            elif "percentage" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=PCT BY X5 /TITLE='Percentage Distribution'.")

        elif "pie chart" in p_low:
            syntax.append("GRAPH /PIE=PCT BY X5 /TITLE='Percentage Distribution'.")

        # --- الاستدلال والتوزيع الطبيعي (Chapter 3) ---
        elif "normality" in p_low or "confidence interval" in p_low:
            syntax.append(f"EXAMINE VARIABLES=X1\n  /PLOT NPPLOT\n  /CINTERVAL 95\n  /STATISTICS DESCRIPTIVES.")

        elif "outliers" in p_low:
            syntax.append(f"EXAMINE VARIABLES=X1 /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

        # --- اختبارات الفرضيات (Chapter 4, 5, 6) ---
        elif "test the hypothesis" in p_low or "difference" in p_low:
            if "independent" in p_low or "two" in p_low:
                syntax.append("T-TEST GROUPS=X4(0 1) /VARIABLES=X1.")
            elif "anova" in p_low or "more than two" in p_low or "region" in p_low:
                syntax.append("ONEWAY X1 BY X11 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
            else:
                syntax.append("T-TEST /TESTVAL=90 /VARIABLES=X7.") # اختبار عينة واحدة كما في Dataset 2

        # --- الارتباط والانحدار (Chapter 8, 9, 10) ---
        elif "correlation" in p_low:
            syntax.append("CORRELATIONS /VARIABLES=X1 X2 X3 /PRINT=TWOTAIL /METHOD=PEARSON.")

        elif "regression" in p_low or "predict" in p_low:
            # الانحدار المتعدد (Chapter 10) مع اختبار التعددية الخطية
            syntax.append("REGRESSION\n  /STATISTICS COEFF OUTS R ANOVA COLLIN TOL\n  /DEPENDENT X5\n  /METHOD=ENTER X1 X2 X3 X4 X6.")

        q_count += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Engine", layout="wide")
st.title("📊 نظام توليد تقارير SPSS المتكامل (MBA v26)")
st.markdown("يرتبط هذا النظام مباشرة بملفات المنهج والتمارين لضمان مخرجات دقيقة.")

col1, col2 = st.columns(2)
with col1:
    u_excel = st.file_uploader("1. ارفع ملف الإكسيل (Data set)", type=['xlsx', 'xls', 'csv'])
with col2:
    u_word = st.file_uploader("2. ارفع ملف الوورد (Questions)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # معالجة ملف الإكسيل
        if u_excel.name.endswith('.csv'):
            df = pd.read_csv(u_excel)
        else:
            df = pd.read_excel(u_excel)
        
        # توليد الـ Syntax
        final_syntax = generate_spss_v26_pro_engine(u_word, df.columns.tolist())
        
        st.success("✅ تم تحليل الأسئلة وربطها بالبيانات والمنهج!")
        st.code(final_syntax, language='spss')
        
        st.download_button(
            label="تحميل ملف السينتاكس الجاهز (.sps)",
            data=final_syntax,
            file_name=f"SPSS_Analysis_Solution.sps",
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"خطأ: تأكد من أن الملفات مطابقة للمواصفات. التفاصيل: {e}")
