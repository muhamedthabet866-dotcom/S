import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج المحتوى من ملف الوورد (الأسئلة والتعريفات)
def extract_word_data(doc_upload):
    try:
        doc = Document(io.BytesIO(doc_upload.read()))
        doc_upload.seek(0)
        
        full_text_list = []
        # قراءة النصوص من الفقرات والجداول لضمان استخراج x1=...
        for p in doc.paragraphs:
            if p.text.strip(): full_text_list.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip(): full_text_list.append(cell.text.strip())
        
        full_content = "\n".join(full_text_list)
        mapping = {}
        # البحث عن التعريفات (x1 = label)
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", full_content, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower().strip()] = label.strip()
            
        return mapping, full_text_list
    except Exception as e:
        st.error(f"خطأ في قراءة ملف الوورد: {e}")
        return {}, []

# 2. محرك توليد السينتاكس الذكي المتوافق مع SPSS v26 والمنهج
def generate_smart_syntax(paragraphs, var_map, excel_columns):
    # قاموس لربط الكلمات المفتاحية بالمتغيرات لضمان الدقة في كل الملفات
    keyword_map = {
        "salary": "x3", "age": "x9", "children": "x8", "gender": "x1",
        "race": "x2", "region": "x4", "happiness": "x5", "wins": "x7",
        "attendance": "x6", "area": "x3", "population": "x4"
    }

    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - UNIVERSAL SYNTAX v26",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable Labeling] --- .",
        "* Scientific Justification: Labels ensure the output is professionally readable."
    ]

    # إضافة تسميات المتغيرات المستخرجة
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels) + ".")
    
    # إضافة تعريف القيم (Value Labels) الشاملة للمنهج
    syntax.append("\nVALUE LABELS x1 1 \"Male / National\" 2 \"Female / American\" /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East / Yes\" 2 \"South East / No\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        # تخطي الأسطر التعريفية
        if any(x in p_low for x in ["where:", "=", "academy", "dr.", "best regards"]) or len(p) < 20:
            continue

        syntax.append(f"* --- [Q{q_idx}] {p[:85]}... --- .")

        # --- ذكاء اختيار الاختبارات ---
        if "frequency table" in p_low:
            if "categorical" in p_low or any(v in p_low for v in ["gender", "race", "league"]):
                syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")
            else:
                syntax.append("* Scientific Justification: Class intervals identify distribution patterns.")
                target = "x3" if "salary" in p_low else ("x9" if "age" in p_low else "x1")
                syntax.append(f"RECODE {target} (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (HI=4) INTO {target}_Cat.")
                syntax.append(f"VARIABLE LABELS {target}_Cat \"{target} (Classes)\".\nEXECUTE.\nFREQUENCIES {target}_Cat /BARCHART.")

        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Visual comparison of group frequencies or means.")
            if "average" in p_low or "mean" in p_low:
                dep = "x8" if "children" in p_low else ("x3" if "salary" in p_low or "area" in p_low else "x3")
                indep = "x2" if "race" in p_low else ("x4" if "region" in p_low or "member" in p_low else "x4")
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({dep}) BY {indep} /TITLE='Average Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Distribution'.")

        elif "each gender in each region" in p_low:
            syntax.append("* Scientific Justification: Subgroup analysis requires splitting the file.")
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.\nFREQUENCIES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")

        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Hypothesis testing for significant differences.")
            val_match = re.search(r"(\d+)", p_low)
            val = val_match.group(1) if val_match else "35000"
            if "equal" in p_low and "difference" not in p_low:
                syntax.append(f"T-TEST /TESTVAL={val} /VARIABLES=x3.")
            elif "gender" in p_low or "surface" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            else:
                syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Multiple regression measures predictor effects.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA SPSS Engine Professional", layout="wide")
st.title("📊 محرك التقارير الإحصائية MBA (إصدار شامل)")

u_excel = st.file_uploader("1. ارفع ملف البيانات (أي Dataset من 1 إلى 4)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # استخراج البيانات
        var_map, paragraphs = extract_word_data(u_word)
        
        # قراءة أعمدة الإكسيل
        df = pd.read_excel(u_excel) if not u_excel.name.endswith('.csv') else pd.read_csv(u_excel)
        excel_cols = df.columns.tolist()
        
        if not paragraphs:
            st.error("لم يتم العثور على أسئلة في ملف الوورد.")
        else:
            # توليد السينتاكس
            final_syntax = generate_smart_syntax(paragraphs, var_map, excel_cols)
            st.success("✅ تم توليد السينتاكس بنجاح لجميع الملفات المرفقة.")
            st.code(final_syntax, language='spss')
            st.download_button("تحميل السينتاكس الجاهز (.sps)", final_syntax, "MBA_Analysis_Pro.sps")
            
    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
