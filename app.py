import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def final_fixed_spss_engine(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # 1. تجميع كل النصوص من الملف (فقرات وجداول)
    all_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip(): all_lines.append(cell.text.strip())
    
    # 2. استخراج خريطة المتغيرات (X1-X6)
    mapping = {}
    for line in all_lines:
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", line, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* --- Final Professional Complete Solution for SPSS v26 --- *.\n"]
    
    # تعريف الليبلز والقيم الأساسية
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    syntax.append("SET DECIMAL=DOT.\n")

    # 3. معالجة كل سؤال بناءً على محتواه (المنطق المصلح)
    for q in all_lines:
        q_low = q.lower()
        # تخطي أسطر التعريفات (X1=...) حتى لا تتكرر كأجوبة
        if re.search(r"X\d+\s*=", q): continue
        
        syntax.append(f"\n* QUESTION: {q}.")

        # السؤال 1: جداول تكرارية للمتغيرات التصنيفية
        if "frequency table" in q_low and any(word in q_low for word in ["debit", "interest", "city"]):
            syntax.append("FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")

        # السؤال 2 و 3: جداول فئات (Classes / K-rule)
        elif "classes" in q_low:
            if "balance" in q_low or "x1" in q_low:
                syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_Classes.")
                syntax.append("VARIABLE LABELS X1_Classes 'Account Balance Classes'.")
                syntax.append("VALUE LABELS X1_Classes 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 '1501-2000' 5 'Over 2000'.")
                syntax.append("FREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.")
            elif "transaction" in q_low or "x2" in q_low:
                syntax.append("RECODE X2 (2 thru 5=1) (6 thru 9=2) (10 thru 13=3) (14 thru 17=4) (18 thru 21=5) (22 thru 25=6) INTO X2_Krule.")
                syntax.append("VARIABLE LABELS X2_Krule 'ATM Transactions (K-Rule)'.")
                syntax.append("VALUE LABELS X2_Krule 1 '2-5' 2 '6-9' 3 '10-13' 4 '14-17' 5 '18-21' 6 '22-25'.")
                syntax.append("FREQUENCIES VARIABLES=X2_Krule.")

        # السؤال 4 و 6: الإحصاء الوصفي والالتواء
        elif any(word in q_low for word in ["mean", "median", "mode", "skewness"]):
            if "each city" in q_low:
                syntax.append("SORT CASES BY X6.\nSPLIT FILE SEPARATE BY X6.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE /FORMAT=NOTABLE.\nSPLIT FILE OFF.")
            elif "debit card or not" in q_low:
                syntax.append("SORT CASES BY X4.\nSPLIT FILE SEPARATE BY X4.\nFREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE /FORMAT=NOTABLE.\nSPLIT FILE OFF.")
            else:
                syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS SESKEW /FORMAT=NOTABLE.")

        # السؤال 5: الهيستوجرام
        elif "histogram" in q_low:
            syntax.append("GRAPH /HISTOGRAM=X1 /TITLE='Histogram of Balance'.")
            syntax.append("GRAPH /HISTOGRAM=X2 /TITLE='Histogram of Transactions'.")

        # السؤال 9، 10، 11، 12: الرسوم البيانية (Bar Charts)
        elif "bar chart" in q_low:
            if "average" in q_low and "city" in q_low:
                if "customers who have debit card" in q_low:
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 /TITLE='Avg Balance by City & Card'.")
                else:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 /TITLE='Average Balance per City'.")
            elif "maximum" in q_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4 /TITLE='Max Transactions by Card Status'.")
            elif "percentage" in q_low:
                syntax.append("GRAPH /BAR(SIMPLE)=PCT BY X5 /TITLE='Percentage of Interest Reception'.")

        # السؤال 13: Pie Chart
        elif "pie chart" in q_low:
            syntax.append("GRAPH /PIE=PCT BY X5 /TITLE='Interest Reception Distribution'.")

        # السؤال 14: فترات الثقة
        elif "confidence interval" in q_low:
            syntax.append("EXAMINE VARIABLES = X1 /STATISTICS DESCRIPTIVES /CINTERVAL 95 /PLOT NONE.")
            syntax.append("EXAMINE VARIABLES = X1 /STATISTICS DESCRIPTIVES /CINTERVAL 99 /PLOT NONE.")

        # السؤال 15: النورمالتي
        elif "normality" in q_low or "empirical" in q_low:
            syntax.append("EXAMINE VARIABLES = X1 /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")

        # السؤال 16: القيم الشاذة
        elif "outliers" in q_low:
            syntax.append("EXAMINE VARIABLES = X1 /STATISTICS DESCRIPTIVES EXTREME(5) /PLOT BOXPLOT.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Master Engine", layout="wide")
st.title("📊 المحرك الإحصائي الكامل (v26)")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("2. ارفع ملف الوورد", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        st.success("✅ تم استلام الملفات وتحليل كافة الأسئلة بنجاح.")
        final_code = final_fixed_spss_engine(u_word)
        st.code(final_code, language='spss')
        st.download_button("تحميل السينتاكس الكامل (.sps)", final_code, "SPSS_Full_Solution.sps")
    except Exception as e:
        st.error(f"Error: {e}")
