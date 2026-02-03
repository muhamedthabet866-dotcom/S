import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج المتغيرات والتعريفات من ملف الوورد (حتى من داخل الجداول)
def extract_context(doc_upload):
    try:
        doc_bytes = doc_upload.read()
        doc = Document(io.BytesIO(doc_bytes))
        doc_upload.seek(0)
        
        full_text_list = []
        # قراءة الفقرات
        for p in doc.paragraphs:
            if p.text.strip(): full_text_list.append(p.text.strip())
        # قراءة الجداول (لأن التعريفات x1=.. غالباً ما تكون في جداول)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip(): full_text_list.append(cell.text.strip())
        
        full_content = "\n".join(full_text_list)
        mapping = {}
        # البحث عن نمط x1 = gender أو x1 : gender
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", full_content, re.IGNORECASE)
        for var, label in matches:
            v_key = var.lower().strip()
            if v_key not in mapping:
                mapping[v_key] = label.strip().title()
        
        return mapping, full_text_list
    except:
        return {}, []

# 2. محرك توليد السينتاكس الذكي (Smart Mapping & Scientific Justification)
def generate_final_syntax(paragraphs, var_map):
    # خريطة ذكية لربط الكلمات المفتاحية بالرموز البرمجية
    smart_vars = {
        "salary": "x3", "age": "x9", "children": "x8", "gender": "x1",
        "race": "x2", "region": "x4", "happiness": "x5", "occupation": "x11",
        "exciting": "x6", "brothers": "x7", "school": "x10", "problem": "x12"
    }

    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - FINAL TARGET SYNTAX v26",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* Formatting Instruction: Use Times New Roman, Size 12 in Word.",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable and Value Labeling] --- .",
        "* Scientific Justification: Proper labeling ensures readability and correct interpretation."
    ]

    # كتابة Variable Labels المستخرجة من الوورد
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels_code = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels_code) + ".")
    
    # كتابة Value Labels (الثوابت في المنهج)
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\" \n  /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\" \n  /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\" \n  /x11 1 \"Managerial\" 2 \"Technical\" 3 \"Farming\" 4 \"Service\" 5 \"Production\" 6 \"Marketing\".\nEXECUTE.\n")

    q_count = 1
    for p in paragraphs:
        p_low = p.lower()
        # تخطي أسطر الترويسة والتعريفات
        if any(x in p_low for x in ["where:", "=", "dr.", "academy", "applied statistics"]) or len(p) < 25:
            continue

        syntax.append(f"* --- [Q{q_count}] {p[:90]}... --- .")

        # --- الإحصاء الوصفي (التكرارات) ---
        if "frequency table" in p_low and "categorical" in p_low:
            syntax.append("* Scientific Justification: Frequency tables summarize categorical distributions.")
            syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")

        # --- الرسوم البيانية الذكية ---
        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Bar charts provide visual comparison of group metrics.")
            if "average" in p_low or "mean" in p_low:
                # تحديد المتغيرات بناءً على محتوى السؤال
                dep = smart_vars.get("salary") if "salary" in p_low else ("x8" if "children" in p_low else "x3")
                indep = "x2" if "race" in p_low else ("x4" if "region" in p_low else "x1")
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({dep}) BY {indep} /TITLE='Average Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Frequency Distribution'.")

        elif "pie chart" in p_low:
            syntax.append("* Scientific Justification: Pie charts show the composition of a whole.")
            if "sum" in p_low:
                syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Sum of Salaries'.")
            else:
                syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Distribution'.")

        # --- منطق الـ Recode (الفئات) ---
        elif "continuous data" in p_low or "five classes" in p_low:
            syntax.append("* Scientific Justification: Recoding continuous variables into class intervals identifies patterns.")
            if "salary" in p_low:
                syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.\nVARIABLE LABELS Salary_Classes \"Salary (5 Classes)\".\nEXECUTE.")
            if "age" in p_low:
                syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.\nVARIABLE LABELS Age_Classes \"Age (5 Classes)\".\nEXECUTE.")
            syntax.append("FREQUENCIES VARIABLES=Salary_Classes Age_Classes /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE.")

        # --- التحليل الطبقي (Split File) ---
        elif "each gender in each region" in p_low:
            syntax.append("* Scientific Justification: Split file allows for localized descriptive analysis for subgroups.")
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.\nFREQUENCIES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN MEDIAN MODE STDDEV.\nSPLIT FILE OFF.")

        # --- اختبارات الفرضيات (T-Test & ANOVA) ---
        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Inferential tests evaluate significant differences between groups.")
            if "35000" in p_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "gender" in p_low or "independent" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            else:
                # ONEWAY ANOVA للأصناف المتعددة (Chapter 6)
                dep = "x8" if "children" in p_low else "x3"
                factor = "x4" if "region" in p_low else ("x2" if "race" in p_low else "x11")
                syntax.append(f"ONEWAY {dep} BY {factor} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- الارتباط والانحدار (Chapter 8, 10) ---
        elif "correlation" in p_low:
            if "happiness" in p_low or "occupation" in p_low:
                syntax.append("* Scientific Justification: Spearman Rho is used for ordinal data types.")
                syntax.append("NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.")
            else:
                syntax.append("CORRELATIONS /VARIABLES=x3 x9 /PRINT=TWOTAIL /METHOD=PEARSON.")

        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Regression measures predictors effect on General Happiness (x5).")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_count += 1

    syntax.append("\n* --- End of Script --- .\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Engine", layout="wide")
st.title("🎓 محرك الأكواد الإحصائية الاحترافي (SPSS v26)")
st.subheader("توليد كود Syntax مطابق لمنهج الدكتور محمد عبد السلام")

col1, col2 = st.columns(2)
with col1:
    u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
with col2:
    u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # قراءة البيانات والتعريفات
        var_map, paragraphs = extract_context(u_word)
        
        if not paragraphs:
            st.error("لم يتم العثور على فقرات أسئلة في ملف الوورد المرفق.")
        else:
            # توليد السينتاكس
            final_syntax = generate_final_syntax(paragraphs, var_map)
            
            st.success("✅ تم توليد السينتاكس بنجاح وتطبيق المنطق الإحصائي المستهدف.")
            st.code(final_syntax, language='spss')
            
            st.download_button(
                label="تحميل ملف السينتاكس الجاهز (.sps)",
                data=final_syntax,
                file_name="MBA_Analysis_Report.sps",
                mime="text/plain"
            )
    except Exception as e:
        st.error(f"حدث خطأ غير متوقع: {e}")
