import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج المتغيرات والتعريفات من ملف الوورد
def extract_context(doc_upload):
    try:
        doc_bytes = doc_upload.read()
        doc = Document(io.BytesIO(doc_bytes))
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
        # البحث عن x1 = gender أو x1 : gender
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", full_content, re.IGNORECASE)
        for var, label in matches:
            v_key = var.lower().strip()
            if v_key not in mapping:
                mapping[v_key] = label.strip().title()
        
        return mapping, full_text_list
    except:
        return {}, []

# 2. محرك توليد السينتاكس الاحترافي (MBA Style)
def generate_mba_syntax(paragraphs, var_map):
    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - SPSS SYNTAX v26",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* Formatting Instruction: When copying results to Word, use Times New Roman, Size 12.",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable and Value Labeling] --- .",
        "* Scientific Justification: Proper labeling ensures that the output is readable and ",
        "* that categorical variables are correctly interpreted during analysis."
    ]

    # كتابة Variable Labels
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels_code = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels_code) + ".")
    
    # كتابة Value Labels (بناءً على النماذج المرفقة)
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\" \n  /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\" \n  /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\" \n  /x11 1 \"Managerial\" 2 \"Technical\" 3 \"Farming\" 4 \"Service\" 5 \"Production\" 6 \"Marketing\".\nEXECUTE.\n")

    q_count = 1
    for p in paragraphs:
        p_low = p.lower()
        # تخطي أسطر التعريفات والعناوين العامة
        if any(x in p_low for x in ["where:", "=", "dr.", "academy", "applied statistics"]) or len(p) < 25:
            continue

        syntax.append(f"* --- [Q{q_count}] {p[:90]}... --- .")

        # منطق التكرارات (Categorical)
        if "frequency table" in p_low and "categorical" in p_low:
            syntax.append("* Scientific Justification: Frequency tables summarize the distribution of categorical variables.")
            syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")

        # منطق الرسوم البيانية
        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Bar charts provide a visual comparison across different groups.")
            if "average salary" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Average Salary by Region'.")
            elif "children" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x8) BY x2 /TITLE='Average Children by Race'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Respondents Count'.")

        elif "pie chart" in p_low:
            syntax.append("* Scientific Justification: Pie charts are effective for showing the composition of a whole.")
            if "sum of salaries" in p_low:
                syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Salary Composition by Occupation'.")
            else:
                syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Percentage'.")

        # منطق الـ Recode (Classes)
        elif "continuous data" in p_low or "classes" in p_low:
            syntax.append("* Scientific Justification: Recoding continuous variables into classes helps in identifying patterns.")
            if "salary" in p_low:
                syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.")
                syntax.append("VARIABLE LABELS Salary_Classes \"Salary (5 Classes)\".\nEXECUTE.")
            if "age" in p_low:
                syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.")
                syntax.append("VARIABLE LABELS Age_Classes \"Age (5 Classes)\".\nEXECUTE.")
            syntax.append("FREQUENCIES VARIABLES=Salary_Classes Age_Classes /STATISTICS=MEAN MEDIAN MODE.")

        # منطق التحليل الطبقي (Split File)
        elif "each gender in each region" in p_low:
            syntax.append("* Scientific Justification: Split file allows for localized descriptive analysis for subgroups.")
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.\nFREQUENCIES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN MEDIAN MODE STDDEV.\nSPLIT FILE OFF.")

        # منطق اختبارات الفرضيات (T-Test vs ANOVA)
        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Inferential tests evaluate significant differences between groups.")
            if "35000" in p_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "gender" in p_low or "independent" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            elif "region" in p_low or "race" in p_low or "occupation" in p_low:
                # ANOVA للأصناف المتعددة
                target = "x3" if "salary" in p_low else "x5"
                factor = "x4" if "region" in p_low else ("x2" if "race" in p_low else "x11")
                syntax.append(f"ONEWAY {target} BY {factor} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # منطق الارتباط والانحدار
        elif "correlation" in p_low:
            if "happiness" in p_low or "occupation" in p_low:
                syntax.append("* Scientific Justification: Spearman Rho is used for ordinal or non-parametric data.")
                syntax.append("NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.")
            else:
                syntax.append("CORRELATIONS /VARIABLES=x3 x9 /PRINT=TWOTAIL /METHOD=PEARSON.")

        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Regression measures the strength and effect of predictors on the dependent variable.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_count += 1

    syntax.append("\n* --- End of Analysis --- .\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Pro Generator", layout="wide")
st.title("🎓 محرك التقارير الإحصائية MBA (SPSS v26)")
st.info("هذا البرنامج يقوم بتحليل ملف الوورد وتوليد كود Syntax احترافي يتضمن التبريرات العلمية والمنطق الإحصائي المتقدم.")

col1, col2 = st.columns(2)
with col1:
    u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
with col2:
    u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # استخراج البيانات
        var_map, paragraphs = extract_context(u_word)
        
        if not var_map:
            st.warning("⚠️ لم يتم العثور على تعريفات للمتغيرات (مثل x1=...). سيتم استخدام مسميات افتراضية.")
        
        final_syntax = generate_mba_syntax(paragraphs, var_map)
        
        st.success("✅ تم توليد السينتاكس بنجاح!")
        st.code(final_syntax, language='spss')
        
        st.download_button(
            label="تحميل ملف السينتاكس الجاهز (.sps)",
            data=final_syntax,
            file_name="MBA_Professional_Analysis.sps",
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
