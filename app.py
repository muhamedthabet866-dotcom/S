import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج المحتوى من الوورد (الأسئلة والتعريفات) مع دعم الجداول
def extract_word_data(doc_upload):
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
        # البحث عن التعريفات (x1 = label)
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", full_content, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower().strip()] = label.strip()
            
        return mapping, full_text_list
    except Exception as e:
        return {}, []

# 2. المحرك الإحصائي الذكي (Smart Universal Engine)
def generate_universal_syntax(paragraphs, var_map, excel_columns):
    # خريطة لربط الكلمات المفتاحية بالمتغيرات لضمان الدقة عبر جميع الملفات
    smart_vars = {
        "salary": "x3", "age": "x9", "children": "x8", "gender": "x1",
        "race": "x2", "region": "x4", "happiness": "x5", "wins": "x7",
        "attendance": "x6", "area": "x3", "population": "x4", "balance": "x1"
    }

    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* MBA STATISTICAL ANALYSIS REPORT - UNIVERSAL PROFESSIONAL SYNTAX",
        "* Prepared for: Dr. Mohamed A. Salam",
        "* =========================================================================.\n",
        "* --- [Step 1: Variable and Value Labeling] --- .",
        "* Scientific Justification: Labels ensure the output is professionally readable."
    ]

    # إضافة Variable Labels المستخرجة ديناميكياً
    if var_map:
        syntax.append("VARIABLE LABELS")
        labels = [f"  {v} \"{l}\"" for v, l in var_map.items()]
        syntax.append(" /\n".join(labels) + ".")
    
    # إضافة Value Labels الشاملة (تغطي المجموعات في كل الملفات)
    syntax.append("\nVALUE LABELS x1 1 \"Male / National\" 2 \"Female / American\" /x2 1 \"White\" 2 \"Black\" 3 \"Others\"")
    syntax.append("  /x4 1 \"North East / Yes\" 2 \"South East / No\" 3 \"West\" /x5 1 \"Very Happy\" 2 \"Pretty Happy\" 3 \"Not Too Happy\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "=", "academy", "dr.", "best regards"]) or len(p) < 20:
            continue

        syntax.append(f"* --- [Q{q_idx}] {p[:85]}... --- .")

        # --- ذكاء الربط والاختبارات ---
        
        # 1. التكرارات وإعادة الترميز (Chapter 2)
        if "frequency table" in p_low:
            if "categorical" in p_low or any(v in p_low for v in ["gender", "race", "region", "card", "interest"]):
                syntax.append("* Scientific Justification: Summarizing categorical distributions.")
                syntax.append("FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.")
            else:
                syntax.append("* Scientific Justification: Recoding continuous variables into classes (K-Rule).")
                target = "x1" if "balance" in p_low else ("x3" if "salary" in p_low else "x9")
                syntax.append(f"RECODE {target} (LO THRU 20000=1) (20001 THRU 40000=2) (40001 THRU 60000=3) (HI=4) INTO {target}_Cat.")
                syntax.append(f"VARIABLE LABELS {target}_Cat \"{target} (Classes)\".\nEXECUTE.\nFREQUENCIES {target}_Cat /BARCHART.")

        # 2. الرسوم البيانية (Charts)
        elif "bar chart" in p_low:
            syntax.append("* Scientific Justification: Visual comparison across groups.")
            if "average" in p_low or "mean" in p_low:
                # تحديد المتغيرات بذكاء بناءً على النص
                dep = "x8" if "children" in p_low else ("x1" if "balance" in p_low else "x3")
                indep = "x2" if "race" in p_low else ("x6" if "city" in p_low else "x4")
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({dep}) BY {indep} /TITLE='Average Analysis'.")
            elif "pie" in p_low or "percentage" in p_low:
                 syntax.append("GRAPH /PIE=COUNT BY x5 /TITLE='Percentage Distribution'.")
            else:
                syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Distribution'.")

        # 3. التحليل الطبقي (Chapter 2 & 3)
        elif any(x in p_low for x in ["each city", "each gender", "each region"]):
            syntax.append("* Scientific Justification: Subgroup analysis requires splitting the file.")
            sort_var = "x6" if "city" in p_low else "x4"
            syntax.append(f"SORT CASES BY {sort_var}.\nSPLIT FILE LAYERED BY {sort_var}.\nFREQUENCIES VARIABLES=x1 x2 x3 /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")

        # 4. اختبارات الفرضيات (Chapter 4, 5, 6)
        elif "test the hypothesis" in p_low:
            syntax.append("* Scientific Justification: Inferential testing for significant differences.")
            # استخراج قيمة الاختبار تلقائياً (مثل 35000 أو 90)
            val_match = re.search(r"(\d+)", p_low)
            val = val_match.group(1) if val_match else "0"
            
            if "equal" in p_low and "difference" not in p_low:
                syntax.append(f"T-TEST /TESTVAL={val} /VARIABLES=x3.")
            elif "independent" in p_low or "male" in p_low or "card" in p_low:
                syntax.append("T-TEST GROUPS=x4(0 1) /VARIABLES=x1.")
            else:
                syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # 5. الارتباط والانحدار (Chapter 8, 9, 10)
        elif "correlation" in p_low:
            method = "SPEARMAN" if any(x in p_low for x in ["happiness", "rank", "occupation"]) else "PEARSON"
            syntax.append(f"CORRELATIONS /VARIABLES=x1 x2 /PRINT=TWOTAIL /METHOD={method}.")

        elif "regression" in p_low:
            syntax.append("* Scientific Justification: Multiple regression measures predictor effects.")
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT x5\n  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.")

        syntax.append("")
        q_idx += 1

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- واجهة المستخدم Streamlit ---
st.set_page_config(page_title="MBA SPSS Engine", layout="wide")
st.title("🎓 محرك الأكواد الإحصائية الاحترافي (إصدار شامل)")
st.info("هذا البرنامج مبرمج خصيصاً ليتناسب مع كافة ملفات البيانات (1، 2، 3، 4) ومنهج الدكتور محمد عبد السلام.")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل (Data set)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # استخراج البيانات
        var_map, paragraphs = extract_word_data(u_word)
        
        # قراءة أعمدة الإكسيل للتأكد من المسميات
        df = pd.read_excel(u_excel) if not u_excel.name.endswith('.csv') else pd.read_csv(u_excel)
        excel_cols = df.columns.tolist()
        
        if not paragraphs:
            st.error("لم يتم العثور على أسئلة واضحة في ملف الوورد.")
        else:
            # توليد السينتاكس
            final_syntax = generate_universal_syntax(paragraphs, var_map, excel_cols)
            st.success("✅ تم توليد السينتاكس بنجاح!")
            st.code(final_syntax, language='spss')
            st.download_button("تحميل ملف .sps", final_syntax, "MBA_Statistics_Analysis.sps")
            
    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
