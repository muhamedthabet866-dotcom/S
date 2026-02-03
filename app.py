import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج البيانات الوصفية من الوورد (Variable Labels)
def extract_metadata(doc_upload):
    try:
        doc = Document(io.BytesIO(doc_upload.read()))
        # إعادة مؤشر الملف للبداية لاستخدامه مرة أخرى لاحقاً
        doc_upload.seek(0)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        mapping = {}
        # البحث عن نمط x1 = gender
        matches = re.findall(r"(x\d+)\s*=\s*([^(\n\r\t]+)", full_text, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower()] = label.strip()
        return mapping, [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except Exception as e:
        return {}, []

# 2. محرك توليد السينتاكس المطور (Dr. Salam Engine)
def generate_spss_syntax(paragraphs, var_map):
    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - GENERATED SYNTAX v26",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Variable and Value Labeling] --- .",
        "* Scientific Justification: Proper labeling ensures readable outputs."
    ]

    # إضافة Variable Labels
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels) + ".")
    
    # القيمة الافتراضية للـ Value Labels بناءً على المنهج
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\" /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        # تخطي الأسطر غير المتعلقة بالأسئلة
        if "where:" in p_low or "=" in p_low or len(p) < 15: continue

        syntax.append(f"* --- [Q{q_idx}] {p[:80]}... --- .")

        # 1. التحليل الطبقي (السؤال رقم 17 الشهير في المنهج)
        if "each gender in each region" in p_low:
            syntax.append("* Scientific Justification: Subgroup analysis requires splitting the file.")
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.")
            syntax.append("DESCRIPTIVES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN STDDEV MIN MAX.")
            syntax.append("SPLIT FILE OFF.")

        # 2. التكرارات وإعادة الترميز (Recode)
        elif "frequency table" in p_low:
            if "categorical" in p_low:
                syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")
            elif "continuous" in p_low or "classes" in p_low:
                syntax.append("* Scientific Justification: Recoding continuous variables into 5 classes.")
                if "salary" in p_low:
                    syntax.append("RECODE x3 (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (60001 THRU 80000=4) (HI=5) INTO Salary_Classes.")
                    syntax.append("VARIABLE LABELS Salary_Classes \"Salary (5 Classes)\".\nFREQUENCIES VARIABLES=Salary_Classes /BARCHART.")
                elif "age" in p_low:
                    syntax.append("RECODE x9 (LO THRU 30=1) (31 THRU 45=2) (46 THRU 60=3) (61 THRU 75=4) (HI=5) INTO Age_Classes.")
                    syntax.append("VARIABLE LABELS Age_Classes \"Age (5 Classes)\".\nFREQUENCIES VARIABLES=Age_Classes /BARCHART.")

        # 3. الرسوم البيانية (Charts)
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                target = "x3" if "salary" in p_low else ("x8" if "children" in p_low else "x1")
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({target}) BY x4 /TITLE='Average Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Frequency Distribution'.")

        elif "pie chart" in p_low:
            if "sum" in p_low:
                syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Sum of Salaries'.")
            else:
                syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Distribution'.")

        # 4. اختبارات الفرضيات (T-Test & ANOVA)
        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Hypothesis testing for mean differences.")
            if "35000" in p_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "gender" in p_low or "male" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            else:
                syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # 5. الانحدار المتعدد (Chapter 10)
        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Multiple regression measures predictor effects.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit Interface ---
st.set_page_config(page_title="MBA SPSS Syntax Engine", layout="wide")
st.title("📊 نظام توليد التقارير الإحصائية (v26)")

u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # استخراج البيانات والفقرات
        var_map, paragraphs = extract_metadata(u_word)
        
        if not paragraphs:
            st.error("لم يتم العثور على أسئلة في ملف الوورد.")
        else:
            # توليد السينتاكس
            final_code = generate_spss_syntax(paragraphs, var_map)
            
            st.success("✅ تم توليد السينتاكس بنجاح!")
            st.code(final_code, language='spss')
            
            st.download_button("تحميل ملف .sps", final_code, "MBA_Analysis.sps")
            
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
