import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# دالة استخراج تسميات المتغيرات والقيم من نص الوورد
def extract_metadata(doc):
    full_text = "\n".join([p.text for p in doc.paragraphs])
    mapping = {}
    # البحث عن x1 = gender (male, female)
    matches = re.findall(r"(x\d+)\s*=\s*([^(\n\r\t]+)", full_text, re.IGNORECASE)
    for var, label in matches:
        mapping[var.lower()] = label.strip()
    return mapping

# محرك إنشاء السينتاكس المطور
def generate_spss_pro_engine(doc_upload, excel_cols):
    doc_bytes = doc_upload.read()
    doc = Document(io.BytesIO(doc_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    var_map = extract_metadata(doc)
    
    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - GENERATED SYNTAX v26",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Variable and Value Labeling] --- .",
        "* Scientific Justification: Proper labeling ensures that the output is readable."
    ]

    # 1. Variable Labels
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels) + ".")
    
    # 2. Value Labels (القيم الافتراضية الشائعة في الملفات)
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\" /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if "where:" in p_low or "=" in p_low or len(p) < 10: continue

        syntax.append(f"* --- [Q{q_idx}] {p[:70]}... --- .")

        # --- الإحصاء الوصفي والتكرارات ---
        if "frequency table" in p_low and "categorical" in p_low:
            syntax.append("* Scientific Justification: Frequency tables summarize categorical distributions.")
            syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")

        elif "frequency table" in p_low and "continuous" in p_low:
            syntax.append("* Scientific Justification: Recoding continuous variables into classes helps identify patterns.")
            if "salary" in p_low:
                syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.")
                syntax.append("VARIABLE LABELS Salary_Classes \"Salary (5 Classes)\".\nFREQUENCIES VARIABLES=Salary_Classes /BARCHART.")
            elif "age" in p_low:
                syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.")
                syntax.append("VARIABLE LABELS Age_Classes \"Age (5 Classes)\".\nFREQUENCIES VARIABLES=Age_Classes /BARCHART.")

        # --- الرسوم البيانية ---
        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Visual comparison of group frequencies or means.")
            if "average" in p_low or "mean" in p_low:
                var_target = "x3" if "salary" in p_low else ("x8" if "children" in p_low else "x1")
                group_by = "x4" if "region" in p_low else "x2"
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({var_target}) BY {group_by} /TITLE='Average Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Number of Respondents'.")

        elif "pie chart" in p_low:
            syntax.append("* Scientific Justification: Pie charts show the composition of a whole.")
            if "sum" in p_low:
                syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Sum of Salaries'.")
            else:
                syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Distribution'.")

        # --- الإحصاء الوصفي المتطور ---
        elif "mean, median, mode" in p_low:
            syntax.append("FREQUENCIES VARIABLES=x3 x9 x7 x8 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.")

        # --- التوزيع الطبيعي والقيم المتطرفة ---
        elif "normality" in p_low or "outliers" in p_low:
            syntax.append("* Scientific Justification: Identifying normality and extreme outliers.")
            syntax.append("EXAMINE VARIABLES=x3 x10 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.")

        # --- التحليل الطبقي (Split File) ---
        elif "each gender in each region" in p_low:
            syntax.append("* Scientific Justification: Split file allows for subgroup analysis.")
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.\nDESCRIPTIVES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN STDDEV MIN MAX.\nSPLIT FILE OFF.")

        # --- الفترات والفرضيات ---
        elif "confidence interval" in p_low:
            syntax.append("EXAMINE VARIABLES=x3 x9 BY x4 /STATISTICS DESCRIPTIVES /CINTERVAL 95 /PLOT NONE.")
            syntax.append("EXAMINE VARIABLES=x3 x9 BY x4 /STATISTICS DESCRIPTIVES /CINTERVAL 99 /PLOT NONE.")

        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Hypothesis testing for mean differences.")
            if "equal 35000" in p_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "difference" in p_low:
                if "gender" in p_low or "independent" in p_low:
                    syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
                else:
                    syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES.")

        # --- الارتباط والانحدار ---
        elif "correlation" in p_low:
            syntax.append("CORRELATIONS /VARIABLES=x3 x9 /PRINT=TWOTAIL /METHOD=PEARSON.")

        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Multiple regression measures predictor effects.")
            syntax.append("REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA COLLIN /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit Interface ---
st.set_page_config(page_title="MBA SPSS Expert", layout="wide")
st.title("📊 محرك التقارير الإحصائية MBA (Dr. Salam Style)")

col1, col2 = st.columns(2)
with col1:
    u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
with col2:
    u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel) if not u_excel.name.endswith('.csv') else pd.read_csv(u_excel)
        sps_code = generate_spss_pro_engine(u_word, df.columns.tolist())
        
        st.success("✅ تم توليد السينتاكس باحترافية طبقاً لمعايير المنهج.")
        st.code(sps_code, language='spss')
        
        st.download_button(label="تحميل ملف .sps", data=sps_code, file_name="MBA_Professional_Analysis.sps", mime="text/plain")
    except Exception as e:
        st.error(f"Error: {e}")
