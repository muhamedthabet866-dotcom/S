import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. استخراج تعريفات المتغيرات من ملف الوورد لضمان الـ Labeling الصحيح
def extract_full_metadata(doc_upload):
    try:
        doc = Document(io.BytesIO(doc_upload.read()))
        doc_upload.seek(0)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        mapping = {}
        # البحث عن التعريفات مثل x1 = gender
        matches = re.findall(r"(x\d+)\s*=\s*([^(\n\r\t]+)", full_text, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower()] = label.strip()
        return mapping, [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        return {}, []

# 2. المحرك الإحصائي الذكي المتوافق مع SPSS v26
def generate_advanced_spss_syntax(paragraphs, var_map):
    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - PROFESSIONAL SYNTAX v26",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable Labeling] --- .",
        "* Scientific Justification: Labels ensure the output is professionally readable."
    ]

    # إضافة التسميات المستخرجة تلقائياً
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels) + ".")
    
    # إضافة تعريف القيم للبيانات الوصفية
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\" /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\" /x11 1 \"Managerial\" 2 \"Technical\" 3 \"Farming\" 4 \"Service\" 5 \"Production\" 6 \"Marketing\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "=", "dr.", "regards"]) or len(p) < 20: continue

        syntax.append(f"* --- [Q{q_idx}] {p[:85]}... --- .")

        # --- الإحصاء الوصفي ---
        if "frequency table" in p_low and "categorical" in p_low:
            syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")

        # --- الرسوم البيانية المتطورة (Chapter 2) ---
        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Bar charts compare counts or means across groups.")
            if "average salary" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Avg Salary by Region'.")
            elif "average number of children" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x8) BY x2 /TITLE='Avg Children by Race'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Respondents by Region'.")

        elif "pie chart" in p_low:
            if "sum of salaries" in p_low:
                syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Total Salary Composition'.")
            else:
                syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Composition'.")

        # --- تقسيم الفئات RECODE (Chapter 2) ---
        elif "five classes" in p_low or "frequency table" in p_low and "continuous" in p_low:
            syntax.append("* Scientific Justification: Class intervals identify distribution patterns.")
            if "salary" in p_low:
                syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.")
                syntax.append("VARIABLE LABELS Salary_Classes \"Salary (5 Classes)\".\nFREQUENCIES VARIABLES=Salary_Classes /BARCHART.")
            if "age" in p_low:
                syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.")
                syntax.append("VARIABLE LABELS Age_Classes \"Age (5 Classes)\".\nFREQUENCIES VARIABLES=Age_Classes /BARCHART.")

        # --- التوزيع الطبيعي والتحليل الطبقي (Chapter 3) ---
        elif "normality" in p_low or "outliers" in p_low:
            syntax.append("EXAMINE VARIABLES=x3 x10 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.")

        elif "each gender in each region" in p_low:
            syntax.append("* Scientific Justification: Split file is required for layered group analysis.")
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.")
            syntax.append("FREQUENCIES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE.")
            syntax.append("SPLIT FILE OFF.")

        # --- اختبارات الفرضيات (Chapter 4, 6) ---
        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Statistical testing for significant differences.")
            if "35000" in p_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "gender" in p_low or "male" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            else:
                # ANOVA للمناطق أو الأعراق (أكثر من مجموعتين)
                syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- الارتباط (Chapter 8) ---
        elif "correlation" in p_low:
            if "happiness" in p_low or "occupation" in p_low:
                syntax.append("* Scientific Justification: Spearman's Rho for ordinal/non-normal data.")
                syntax.append("NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.")
            else:
                syntax.append("CORRELATIONS /VARIABLES=x3 x9 /PRINT=TWOTAIL /METHOD=PEARSON.")

        # --- الانحدار المتعدد (Chapter 10) ---
        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Measuring multiple predictors on General Happiness.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Engine v2", layout="wide")
st.title("🛠️ محرك الأكواد الإحصائية (Dr. Salam Engine)")

u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        var_map, paragraphs = extract_full_metadata(u_word)
        final_code = generate_advanced_spss_syntax(paragraphs, var_map)
        
        st.success("✅ تم توليد السينتاكس بنجاح!")
        st.code(final_code, language='spss')
        st.download_button("تحميل ملف .sps", final_code, "Analysis_Report.sps")
    except Exception as e:
        st.error(f"Error: {e}")
