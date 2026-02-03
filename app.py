import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج المتغيرات والفقرات مع دعم الجداول
def extract_full_context(doc_upload):
    try:
        doc = Document(io.BytesIO(doc_upload.read()))
        doc_upload.seek(0)
        
        full_text_list = []
        for p in doc.paragraphs:
            if p.text.strip(): full_text_list.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip(): full_text_list.append(cell.text.strip())
        
        full_content = "\n".join(full_text_list)
        mapping = {}
        # استخراج x1 = label
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", full_content, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower().strip()] = label.strip()
        
        return mapping, full_text_list
    except:
        return {}, []

# 2. محرك الإنتاج الذكي (Smart Mapping Engine)
def generate_target_syntax(paragraphs, var_map):
    # خريطة ذكية لربط الكلمات بالرموز (لضمان مطابقة المنهج)
    smart_map = {
        "salary": "x3", "age": "x9", "children": "x8", "gender": "x1",
        "race": "x2", "region": "x4", "happiness": "x5", "occupation": "x11",
        "exciting": "x6", "brothers": "x7", "school": "x10", "problem": "x12"
    }

    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - TARGET PROFESSIONAL SYNTAX",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable and Value Labeling] --- .",
        "* Scientific Justification: Proper labeling ensures that the output is readable."
    ]

    # إضافة Variable Labels
    if var_map:
        syntax.append("VARIABLE LABELS")
        syntax.append(" /\n".join([f"  {v} \"{l}\"" for v, l in var_map.items()]) + ".")
    
    # إضافة Value Labels
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\" /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\" /x11 1 \"Managerial\" 2 \"Technical\" 3 \"Farming\" 4 \"Service\" 5 \"Production\" 6 \"Marketing\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "=", "dr.", "academy", "applied"]) or len(p) < 25: continue

        syntax.append(f"* --- [Q{q_idx}] {p[:85]}... --- .")

        # --- تحليل التكرارات (Categorical) ---
        if "frequency table" in p_low and "categorical" in p_low:
            syntax.append("* Scientific Justification: Summarizing categorical distributions.")
            syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")

        # --- الرسوم البيانية الذكية ---
        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Visual comparison across groups.")
            if "average" in p_low or "mean" in p_low:
                # اختيار المتغير التابع والمستقل بذكاء
                dep = smart_map.get("salary") if "salary" in p_low else ("x8" if "children" in p_low else "x3")
                indep = smart_map.get("region") if "region" in p_low else ("x2" if "race" in p_low else "x4")
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({dep}) BY {indep} /TITLE='Average Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Frequency Distribution'.")

        elif "pie chart" in p_low:
            syntax.append("* Scientific Justification: Composition of a whole.")
            if "sum" in p_low:
                syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Sum of Salaries'.")
            else:
                syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Percentage'.")

        # --- الـ Recode المطور ---
        elif "continuous data" in p_low or "five classes" in p_low:
            syntax.append("* Scientific Justification: Recoding continuous variables into class intervals.")
            if "salary" in p_low:
                syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.\nVARIABLE LABELS Salary_Classes \"Salary (5 Classes)\".\nEXECUTE.")
            if "age" in p_low:
                syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.\nVARIABLE LABELS Age_Classes \"Age (5 Classes)\".\nEXECUTE.")
            syntax.append("FREQUENCIES VARIABLES=Salary_Classes Age_Classes /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE.")

        # --- التحليل الاستدلالي (T-Test & ANOVA) ---
        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Hypothesis testing for mean differences.")
            if "35000" in p_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "gender" in p_low or "independent" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            else:
                # منطق ANOVA الذكي
                dep = "x8" if "children" in p_low else "x3"
                factor = "x4" if "region" in p_low else ("x2" if "race" in p_low else "x11")
                syntax.append(f"ONEWAY {dep} BY {factor} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- الانحدار ---
        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Measuring predictor effects on happiness.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Target Generator", layout="wide")
st.title("🎓 محرك التقارير الإحصائية المستهدف (v26)")

u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        var_map, paragraphs = extract_full_context(u_word)
        final_syntax = generate_target_syntax(paragraphs, var_map)
        st.success("✅ تم توليد السينتاكس المطابق للمستهدف!")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل ملف .sps", final_syntax, "Final_MBA_Report.sps")
    except Exception as e:
        st.error(f"خطأ: {e}")
