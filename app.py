import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def extract_metadata_and_paragraphs(doc_upload):
    try:
        doc = Document(io.BytesIO(doc_upload.read()))
        doc_upload.seek(0)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        mapping = {}
        matches = re.findall(r"(x\d+)\s*=\s*([^(\n\r\t]+)", full_text, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower()] = label.strip()
        return mapping, [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        return {}, []

def generate_spss_syntax_v26(paragraphs, var_map):
    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - PROFESSIONAL SYNTAX v26",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable Labeling] --- .",
        "* Scientific Justification: Labels ensure the output is professionally readable."
    ]

    # إضافة التسميات (Labels)
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels) + ".")
    
    # إضافة تعريف القيم (Value Labels)
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\" /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\" /x11 1 \"Managerial\" 2 \"Technical\" 3 \"Farming\" 4 \"Service\" 5 \"Production\" 6 \"Marketing\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "=", "arab academy", "graduate school", "applied statistics"]) or len(p) < 20: continue

        syntax.append(f"* --- [Q{q_idx}] {p[:80]}... --- .")

        # 1. التكرارات والرسوم البيانية
        if "frequency table" in p_low and "categorical" in p_low:
            syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")
        
        elif "bar chart" in p_low:
            if "average salary" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Avg Salary by Region'.")
            elif "average number of children" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x8) BY x2 /TITLE='Avg Children by Race'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Respondents Count'.")

        elif "pie chart" in p_low:
            if "sum of salaries" in p_low:
                syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Total Salary by Occupation'.")
            else:
                syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Distribution'.")

        # 2. إعادة الترميز (Recode) - Chapter 2
        elif "five classes" in p_low:
            syntax.append("* Scientific Justification: Class intervals help identify distribution patterns.")
            if "salary" in p_low:
                syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.\nVARIABLE LABELS Salary_Classes \"Salary (5 Classes)\".\nFREQUENCIES VARIABLES=Salary_Classes /BARCHART.")
            elif "age" in p_low:
                syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.\nVARIABLE LABELS Age_Classes \"Age (5 Classes)\".\nFREQUENCIES VARIABLES=Age_Classes /BARCHART.")

        # 3. التحليل الاستدلالي (Split File, T-Test, ANOVA)
        elif "each gender in each region" in p_low:
            syntax.append("* Scientific Justification: Subgroup analysis requires splitting the file.")
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.\nFREQUENCIES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN MEDIAN MODE STDDEV.\nSPLIT FILE OFF.")

        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Statistical testing for significant differences.")
            if "35000" in p_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "gender" in p_low or "male and female" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            elif "race" in p_low:
                syntax.append("ONEWAY x3 BY x2 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")
            elif "region" in p_low:
                syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")
            else:
                # افتراضي للمقارنة بين المجموعات
                syntax.append("ONEWAY x3 BY x11 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # 4. الارتباط والانحدار (Chapter 8, 10)
        elif "correlation" in p_low:
            if "happiness" in p_low or "occupation" in p_low:
                syntax.append("* Scientific Justification: Spearman Rho for ordinal data.")
                syntax.append("NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.")
            else:
                syntax.append("CORRELATIONS /VARIABLES=x3 x9 /PRINT=TWOTAIL /METHOD=PEARSON.")

        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Multiple regression measures predictor effects.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Engine", layout="wide")
st.title("🛠️ محرك الأكواد الإحصائية (Dr. Salam Style)")

u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        var_map, paragraphs = extract_metadata_and_paragraphs(u_word)
        final_syntax = generate_spss_syntax_v26(paragraphs, var_map)
        st.success("✅ تم توليد السينتاكس بنجاح!")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل ملف .sps", final_syntax, "Professional_Report.sps")
    except Exception as e:
        st.error(f"خطأ: {e}")
