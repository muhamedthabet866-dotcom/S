import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def final_advanced_spss_v17(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # سحب النصوص من الفقرات والجداول لضمان شمولية الحل
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip(): paragraphs.append(cell.text.strip())
    
    mapping = {}
    for p in paragraphs:
        # استخراج المتغيرات من ملف الوورد (X1-X6)
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip().lower()
            mapping[v_name] = v_label

    syntax = ["* --- Advanced Scientific Solution for SPSS v26 (No Warnings) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")

    # تعريف القيم للمتغيرات التصنيفية لضمان دقة المخرجات
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        # ربط المتغيرات بالأسئلة بذكاء (الاسم النصي أو الرمز)
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v][:12] in p_low]
        if "balance" in p_low: found_vars.append("X1")
        if "transaction" in p_low: found_vars.append("X2")
        if "city" in p_low: found_vars.append("X6")
        
        found_vars = list(dict.fromkeys(found_vars))
        if not found_vars and not any(k in p_low for k in ['normality', 'outlier']): continue

        syntax.append(f"\n* QUESTION: {p}.")

        # --- حل فترات الثقة (95% و 99% في جداول مستقلة) ---
        if "confidence interval" in p_low:
            for val in ["95", "99"]:
                # الصيغة الصارمة لمنع التحذير: VARIABLES متبوعة بـ STATISTICS و PLOT
                syntax.append(f"EXAMINE VARIABLES = X1 /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # --- تصحيح أوامر الرسوم البيانية ---
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if "city" in p_low and "debit card" in p_low:
                    syntax.append("GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 /TITLE='Avg Balance by City and Card'.")
                elif "city" in p_low:
                    syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 /TITLE='Avg Balance per City'.")
            elif "maximum" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4 /TITLE='Max Transactions by Status'.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        # --- التحليل المقارن (Split File) ---
        elif "for each city" in p_low:
            syntax.append("SORT CASES BY X6.\nSPLIT FILE SEPARATE BY X6.")
            syntax.append("FREQUENCIES VARIABLES=X1 X2 /STATISTICS=MEAN MEDIAN MODE /FORMAT=NOTABLE.")
            syntax.append("SPLIT FILE OFF.")

        # --- تقسيم الفئات (K-rule والـ Classes) ---
        elif "frequency table" in p_low and "classes" in p_low:
            if "balance" in p_low:
                syntax.append("RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_Classes.")
                syntax.append("FREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.")
            elif "transaction" in p_low:
                syntax.append("RECODE X2 (2 thru 5=1) (6 thru 9=2) (10 thru 13=3) (14 thru 17=4) (18 thru 21=5) (22 thru 25=6) INTO X2_Krule.")
                syntax.append("FREQUENCIES VARIABLES=X2_Krule.")

        # --- اختبارات النورمالتي والقيم الشاذة ---
        elif "normality" in p_low or "empirical" in p_low:
            syntax.append("EXAMINE VARIABLES = X1 /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low:
            syntax.append("EXAMINE VARIABLES = X1 /STATISTICS DESCRIPTIVES EXTREME(5) /PLOT BOXPLOT.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Master Pro", layout="wide")
st.title("📊 نظام تحليل البيانات للمهندس محمد (v26)")

u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        st.success("✅ تم استلام الملفات وتحليل المتطلبات الـ 16.")
        final_code = final_advanced_spss_v17(u_word)
        st.code(final_code, language='spss')
        st.download_button(label="تحميل السينتاكس النهائي (.sps)", data=final_code, file_name="Final_SPSS_Analysis.sps", mime="text/plain")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
