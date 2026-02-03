import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def advanced_spss_engine_v16(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # استخراج النصوص من الفقرات والجداول
    all_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip(): all_text.append(cell.text.strip())
    
    mapping = {}
    for line in all_text:
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", line, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* --- Advanced Academic Solution for SPSS v26 --- *.\n"]
    syntax.append("* [PRE-ANALYSIS] Defining Labels and Value Formats.")
    
    # 1. التعريفات الأساسية
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    
    # إضافة Value Labels للمتغيرات التصنيفية المعروفة
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes'.")
    syntax.append("SET DECIMAL=DOT.\n")

    # 2. منطق الأسئلة (المحرك المتقدم)
    for q in all_text:
        q_low = q.lower()
        if re.search(r"X\d+\s*=", q): continue
        
        # ربط المتغيرات
        found_vars = [v for v in mapping.keys() if v in q.upper() or mapping[v].lower()[:10] in q_low]
        if "balance" in q_low: found_vars.append("X1")
        if "transaction" in q_low: found_vars.append("X2")
        if "city" in q_low: found_vars.append("X6")
        if "debit" in q_low: found_vars.append("X4")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and not any(k in q_low for k in ['normality', 'outlier']): continue

        syntax.append(f"\n* QUESTION: {q}.")

        # أ. تقسيم الفئات (Recoding) - السؤال 2 و 3
        if "frequency table" in q_low and "classes" in q_low:
            if "balance" in q_low:
                syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_Classes.")
                syntax.append("VARIABLE LABELS X1_Classes 'Account Balance Classes'.")
                syntax.append("VALUE LABELS X1_Classes 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 '1501-2000' 5 'Over 2000'.")
                syntax.append("FREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.")
            elif "transaction" in q_low:
                syntax.append("* Applying K-Rule: 2^k >= n (n=60, k=6).")
                syntax.append("RECODE X2 (2 thru 5=1) (6 thru 9=2) (10 thru 13=3) (14 thru 17=4) (18 thru 21=5) (22 thru 25=6) INTO X2_Krule.")
                syntax.append("VARIABLE LABELS X2_Krule 'ATM Transactions (K-Rule Classes)'.")
                syntax.append("VALUE LABELS X2_Krule 1 '2-5' 2 '6-9' 3 '10-13' 4 '14-17' 5 '18-21' 6 '22-25'.")
                syntax.append("FREQUENCIES VARIABLES=X2_Krule.")

        # ب. فترات الثقة (فصل 95% و 99% - طلب أساسي)
        elif "confidence interval" in q_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES = X1 /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")
            syntax.append("ECHO 'INTERPRETATION: Compare the precision between 95% and 99% intervals'.")

        # ج. الرسوم البيانية مع العناوين (تصحيح خطأ 701)
        elif "bar chart" in q_low:
            if "average" in q_low or "mean" in q_low:
                if "city" in q_low and "debit card" in p_low if 'p_low' in locals() else "debit card" in q_low:
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 /TITLE='Avg Balance by City and Card Status'.")
                else:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 /TITLE='Average Account Balance per City'.")
            elif "maximum" in q_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4 /TITLE='Max Transactions by Debit Status'.")
            elif "percentage" in q_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {found_vars[0]} /TITLE='Percentage Distribution'.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        elif "pie chart" in q_low:
            syntax.append("GRAPH /PIE=PCT BY X5 /TITLE='Market Share: Interest Reception'.")

        # د. التحليل المقارن (Split File)
        elif "for each city" in q_low or "debit card or not" in q_low:
            split_var = "X6" if "city" in q_low else "X4"
            syntax.append(f"SORT CASES BY {split_var}.\nSPLIT FILE SEPARATE BY {split_var}.")
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS /FORMAT=NOTABLE.")
            syntax.append("SPLIT FILE OFF.")

        # هـ. الإحصاء الوصفي والالتواء
        elif any(w in q_low for w in ["mean", "median", "calculate", "skewness"]):
            syntax.append(f"FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS SESKEW /FORMAT=NOTABLE.")
            syntax.append("ECHO 'NOTE: If Mean > Median, distribution is Right-Skewed'.")

        # و. النورمالتي والقيم الشاذة
        elif "normality" in q_low or "empirical" in q_low:
            syntax.append("EXAMINE VARIABLES = X1 /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in q_low:
            syntax.append("EXAMINE VARIABLES = X1 /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

        elif "histogram" in q_low:
            for v in [v for v in found_vars if v in ['X1', 'X2']]:
                syntax.append(f"GRAPH /HISTOGRAM={v} /TITLE='Distribution Analysis'.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Advanced Pro", layout="wide")
st.title("🧙‍♂️ المحرك الإحصائي المتقدم (v26 Academic)")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("2. ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        st.success("✅ تم تحليل البيانات وربطها بالمنطق الإحصائي المتقدم.")
        final_code = advanced_spss_engine_v16(u_word)
        st.code(final_code, language='spss')
        st.download_button(label="تحميل السينتاكس النهائي (.sps)", data=final_code, file_name="Advanced_SPSS_Analysis.sps", mime="text/plain")
    except Exception as e:
        st.error(f"Error: {e}")
