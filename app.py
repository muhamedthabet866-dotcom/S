import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج المتغيرات والأسئلة بشكل ديناميكي
def extract_universal_data(doc_upload):
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
        # البحث عن x1 = label في أي ملف
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", full_content, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower().strip()] = label.strip()
            
        return mapping, full_text_list
    except:
        return {}, []

# 2. محرك التوليد العالمي (Universal SPSS Engine)
def generate_universal_syntax(paragraphs, var_map):
    # خريطة ذكية لربط الكلمات بالرموز بناءً على المنهج
    logic_map = {
        "salary": "x3", "age": "x9", "children": "x8", "gender": "x1",
        "race": "x2", "region": "x4", "wins": "x7", "area": "x3", 
        "population": "x4", "league": "x2", "surface": "x11", "g7": "x2"
    }

    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* UNIVERSAL MBA STATISTICAL ANALYSIS - SPSS SYNTAX v3",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Step 1: Setup Labels] --- ."
    ]

    # إضافة التسميات المستخرجة من الوورد
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels) + ".")
    
    # تعريف القيم الافتراضية (تغطي معظم الحالات في ملفاتك)
    syntax.append("\nVALUE LABELS x1 1 \"Male / National / Natural\" 2 \"Female / American / Artificial\"")
    syntax.append("  /x2 1 \"White / Member\" 2 \"Black / Non-Member\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East / Yes\" 2 \"South East / No\" 3 \"West\" /x11 1 \"Far East\" 2 \"Europe\" 3 \"North America\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "=", "academy", "dr.", "best regards"]) or len(p) < 20:
            continue

        syntax.append(f"* --- [Q{q_idx}] {p[:85]}... --- .")

        # --- ذكاء تحليل السؤال ---
        
        # 1. التكرارات والوصف (Chapter 2)
        if "frequency table" in p_low:
            syntax.append("* Scientific Justification: Summarizing distributions.")
            if "categorical" in p_low or any(v in p_low for v in ["league", "surface", "member", "region"]):
                syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x11 /ORDER=ANALYSIS.")
            else:
                # Recode للمتغيرات المستمرة
                target = "x3" if "salary" in p_low or "area" in p_low else "x7"
                syntax.append(f"RECODE {target} (LO THRU 50=1) (50 THRU 100=2) (HI=3) INTO {target}_Cat.\nEXECUTE.\nFREQUENCIES {target}_Cat.")

        # 2. الرسوم البيانية (Charts)
        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Visual comparison of metrics.")
            if "average" in p_low or "mean" in p_low:
                dep = "x3" if "salary" in p_low or "area" in p_low else "x7"
                indep = "x2" if "league" in p_low or "member" in p_low else "x11"
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({dep}) BY {indep} /TITLE='Mean Analysis'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x11.")

        # 3. اختبارات الفرضيات (Chapter 4, 5, 6)
        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Hypothesis testing for significance.")
            # استخراج قيمة الاختبار (مثل 90 فوز أو 600 مساحة)
            val_match = re.search(r"(\d+)", p_low)
            val = val_match.group(1) if val_match else "0"
            
            if "equal" in p_low and "difference" not in p_low:
                target = "x7" if "wins" in p_low else "x3"
                syntax.append(f"T-TEST /TESTVAL={val} /VARIABLES={target}.")
            elif "difference" in p_low:
                if any(v in p_low for v in ["league", "surface", "member", "gender"]):
                    syntax.append("T-TEST GROUPS=x2(1 2) /VARIABLES=x3.")
                else:
                    syntax.append("ONEWAY x3 BY x11 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # 4. الارتباط والانحدار (Chapter 8, 10)
        elif "correlation" in p_low:
            syntax.append("CORRELATIONS /VARIABLES=x3 x7 /PRINT=TWOTAIL /METHOD=PEARSON.")

        elif "regression" in p_low:
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x7.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="Universal SPSS Engine", layout="wide")
st.title("🎓 محرك الإحصاء الشامل (v3 Professional)")
st.info("هذا البرنامج يدعم الآن Datasets 1, 2, 3, 4 ويقوم بتوليد الكود بناءً على محتوى ملفاتك.")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل (Data set 1, 2, 3, or 4)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # قراءة البيانات والفقرات
        var_map, paragraphs = extract_universal_data(u_word)
        
        if not paragraphs:
            st.error("لم يتم العثور على أسئلة في ملف الوورد.")
        else:
            final_code = generate_universal_syntax(paragraphs, var_map)
            st.success("✅ تم توليد السينتاكس بنجاح!")
            st.code(final_code, language='spss')
            st.download_button("تحميل السينتاكس (.sps)", final_code, "MBA_Universal_Report.sps")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
