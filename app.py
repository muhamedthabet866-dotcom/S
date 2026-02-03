import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج المتغيرات والتعريفات من الوورد (تدعم الفقرات والجداول)
def extract_mapping_and_questions(doc_upload):
    try:
        doc = Document(io.BytesIO(doc_upload.read()))
        doc_upload.seek(0)
        
        full_text = []
        for p in doc.paragraphs:
            if p.text.strip(): full_text.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip(): full_text.append(cell.text.strip())
        
        content = "\n".join(full_text)
        mapping = {}
        # البحث عن x1 = label أو x1: label
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", content, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower().strip()] = label.strip()
            
        return mapping, full_text
    except:
        return {}, []

# 2. المحرك الإحصائي الشامل (Universal MBA Engine)
def generate_final_pro_syntax(paragraphs, var_map):
    # خريطة ذكية لربط المصطلحات بالرموز لضمان الدقة في كافة الـ Datasets
    smart_dict = {
        "salary": "x3", "age": "x9", "children": "x8", "gender": "x1",
        "race": "x2", "region": "x4", "happiness": "x5", "wins": "x7",
        "attendance": "x6", "area": "x3", "population": "x4", "wins": "x7",
        "league": "x2", "surface": "x11", "member": "x2", "g7": "x2",
        "occupation": "x11", "problem": "x12", "exciting": "x6", "balance": "x1"
    }

    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* UNIVERSAL MBA STATISTICAL ANALYSIS - PROFESSIONAL SYNTAX v4",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable and Value Labeling] --- .",
        "* Scientific Justification: Labels and values ensure professional interpretability."
    ]

    # إضافة Variable Labels المستخرجة
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels) + ".")
    
    # إضافة Value Labels الشاملة لجميع الملفات
    syntax.append("\nVALUE LABELS x1 1 \"Male / National / Natural\" 2 \"Female / American / Artificial\"")
    syntax.append("  /x2 1 \"White / Member\" 2 \"Black / Non-Member\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East / Yes\" 2 \"South East / No\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\"")
    syntax.append("  /x6 1 \"Exciting\" 2 \"Routine\" 3 \"Dull\" /x11 1 \"Managerial / Far East\" 2 \"Technical / Europe\" 3 \"Farming / North America\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "=", "academy", "dr.", "best regards"]) or len(p) < 25:
            continue

        syntax.append(f"* --- [Q{q_idx}] {p[:85]}... --- .")

        # --- 1. التكرارات والوصف (Chapter 2) ---
        if "frequency table" in p_low:
            syntax.append("* Scientific Justification: Frequency tables summarize categorical or binned data.")
            if "categorical" in p_low or any(v in p_low for v in ["gender", "race", "region", "league", "surface", "member"]):
                syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")
            else:
                # منطق الـ Recode للبيانات المستمرة
                target = smart_map.get("salary", "x3") if "salary" in p_low else ("x9" if "age" in p_low else "x3")
                syntax.append(f"RECODE {target} (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (HI=4) INTO {target}_Cat.")
                syntax.append(f"VARIABLE LABELS {target}_Cat \"{target} (Classes)\".\nEXECUTE.\nFREQUENCIES {target}_Cat /BARCHART.")

        # --- 2. الرسوم البيانية المتطورة ---
        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Bar charts provide visual comparison of means or counts.")
            if "average" in p_low or "mean" in p_low:
                # تحديد المتغير التابع والمستقل بذكاء
                dep = "x8" if "children" in p_low else ("x3" if "salary" in p_low or "area" in p_low else ("x7" if "wins" in p_low else "x3"))
                indep = "x2" if "race" in p_low or "league" in p_low or "member" in p_low else ("x4" if "region" in p_low else "x11")
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({dep}) BY {indep} /TITLE='Average Analysis'.")
            elif "maximum" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MAX(x2) BY x4 /TITLE='Max Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Frequency Analysis'.")

        elif "pie chart" in p_low:
            syntax.append("* Scientific Justification: Pie charts effectively show the composition of a whole.")
            if "sum" in p_low:
                syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Total Composition'.")
            else:
                syntax.append("GRAPH /PIE=COUNT BY x1 /TITLE='Gender Distribution'.")

        # --- 3. التحليل الطبقي (Split File) ---
        elif any(x in p_low for x in ["each gender", "each region", "each city"]):
            syntax.append("* Scientific Justification: Subgroup analysis requires splitting the file for localized descriptives.")
            sort_var = "x4" if "region" in p_low else ("x6" if "city" in p_low else "x1")
            syntax.append(f"SORT CASES BY {sort_var}.\nSPLIT FILE LAYERED BY {sort_var}.\nFREQUENCIES VARIABLES=x1 x2 x3 x9 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")

        # --- 4. اختبارات الفرضيات (Chapter 4, 5, 6) ---
        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Inferential tests evaluate if sample results differ significantly.")
            val_match = re.search(r"(\d+)", p_low)
            val = val_match.group(1) if val_match else "0"
            
            if "equal" in p_low and "difference" not in p_low:
                target = "x7" if "wins" in p_low else "x3"
                syntax.append(f"T-TEST /TESTVAL={val} /VARIABLES={target}.")
            elif "difference" in p_low:
                if any(v in p_low for v in ["gender", "league", "surface", "member", "before"]):
                    # اختبار T لمجموعتين
                    syntax.append("T-TEST GROUPS=x2(1 2) /VARIABLES=x3.")
                else:
                    # ANOVA لأكثر من مجموعتين
                    syntax.append("ONEWAY x3 BY x11 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- 5. الارتباط والانحدار (Chapter 8, 10) ---
        elif "correlation" in p_low:
            if any(x in p_low for x in ["happiness", "rank", "occupation"]):
                syntax.append("* Scientific Justification: Spearman Rho for ordinal or non-parametric data.")
                syntax.append("NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.")
            else:
                syntax.append("CORRELATIONS /VARIABLES=x3 x9 /PRINT=TWOTAIL /METHOD=PEARSON.")

        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Multiple regression measures predictors effect on dependent variable.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- واجهة Streamlit ---
st.set_page_config(page_title="Universal SPSS Automator", layout="wide")
st.title("📊 محرك الإحصاء الاحترافي الشامل (v4)")
st.markdown("يدعم Datasets 1, 2, 3, 4 مع تطبيق كافة معايير المنهج الدراسي.")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل (Data set)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        var_map, paragraphs = extract_mapping_and_questions(u_word)
        if not paragraphs:
            st.error("لم يتم العثور على محتوى في ملف الوورد.")
        else:
            final_code = generate_final_pro_syntax(paragraphs, var_map)
            st.success("✅ تم توليد السينتاكس بنجاح وتصحيح كافة أخطاء الربط.")
            st.code(final_code, language='spss')
            st.download_button("تحميل السينتاكس (.sps)", final_code, "MBA_Universal_Analysis.sps")
    except Exception as e:
        st.error(f"خطأ في المعالجة: {e}")
