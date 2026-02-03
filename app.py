import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة ذكية لاستخراج المتغيرات حتى لو كانت داخل جداول
def extract_all_vars(doc_upload):
    try:
        # قراءة الملف
        doc_bytes = doc_upload.read()
        doc = Document(io.BytesIO(doc_bytes))
        doc_upload.seek(0) # إعادة المؤشر للبداية
        
        mapping = {}
        # البحث في الفقرات العادية
        all_text = []
        for p in doc.paragraphs:
            all_text.append(p.text)
            
        # البحث داخل الجداول (لأن الأسئلة أحياناً توضع في جداول)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    all_text.append(cell.text)
        
        full_content = "\n".join(all_text)
        
        # استخراج المتغيرات باستخدام Regular Expression مطور
        # يبحث عن x1 = Salary أو x1: Salary
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t]+)", full_content, re.IGNORECASE)
        for var, label in matches:
            var_clean = var.lower().strip()
            label_clean = label.strip()
            if var_clean not in mapping:
                mapping[var_clean] = label_clean
                
        return mapping, [t.strip() for t in all_text if len(t.strip()) > 20]
    except:
        return {}, []

# 2. محرك السينتاكس الاحترافي
def generate_final_syntax(paragraphs, var_map):
    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - FINAL PROFESSIONAL SYNTAX",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable Labeling] --- ."
    ]

    # إضافة المتغيرات التي تم العثور عليها
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels_entry = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels_entry) + ".")
    else:
        # في حال لم يجد متغيرات، يضع تعليقاً للتنبيه
        syntax.append("* WARNING: No variable definitions found in Word file. Please check formatting.")

    # تعريف القيم (Value Labels) الثابتة في المنهج
    syntax.append("\nVALUE LABELS x1 1 \"Male\" 2 \"Female\" /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East\" 2 \"South East\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        # تخطي العناوين والتعريفات
        if any(x in p_low for x in ["where:", "=", "dr.", "academy", "applied"]): continue

        syntax.append(f"* --- [Q{q_idx}] {p[:80]}... --- .")

        # منطق الاختبارات (Chapter 1-10)
        if "frequency table" in p_low:
            if "categorical" in p_low or any(v in p_low for v in ["gender", "race", "region"]):
                syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")
            else:
                syntax.append("* RECODE for Continuous Data.")
                target = "x3" if "salary" in p_low else "x9"
                syntax.append(f"RECODE {target} (LO THRU 20=1) (20 THRU 40=2) (HI=3) INTO {target}_Cat.\nFREQUENCIES {target}_Cat.")

        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                syntax.append("GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Average Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4.")

        elif "each gender in each region" in p_low:
            syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.\nDESCRIPTIVES x3 x9 x7 x8.\nSPLIT FILE OFF.")

        elif "test the hypothesis" in p_low:
            if "35000" in p_low:
                syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
            elif "gender" in p_low:
                syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
            else:
                syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        elif "regression" in p_low:
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- واجهة Streamlit ---
st.set_page_config(page_title="MBA Syntax Generator", layout="wide")
st.title("📊 مصلح السينتاكس الذكي (إصدار استخراج المتغيرات)")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الوورد", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # استخراج شامل
        var_map, paragraphs = extract_all_vars(u_word)
        
        if not var_map:
            st.warning("⚠️ تنبيه: البرنامج لم يجد تعريفات المتغيرات (x1=...) في النص أو الجداول. سيتم استخدام رموز افتراضية.")
        
        final_code = generate_final_syntax(paragraphs, var_map)
        
        st.success("✅ تم توليد الكود!")
        st.code(final_code, language='spss')
        
        st.download_button("تحميل الملف المصلح (.sps)", final_code, "MBA_Report.sps")
    except Exception as e:
        st.error(f"خطأ غير متوقع: {e}")
