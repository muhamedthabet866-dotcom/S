import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. دالة استخراج البيانات من الوورد (الأسئلة والتعريفات)
def extract_word_content(doc_upload):
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
        # البحث عن التعريفات الديناميكية (X1 = الاسم)
        matches = re.findall(r"(x\d+)\s*[=:]\s*([^(\n\r\t.]+)", full_content, re.IGNORECASE)
        for var, label in matches:
            mapping[var.lower().strip()] = label.strip()
            
        return mapping, full_text_list
    except:
        return {}, []

# 2. محرك توليد السينتاكس الشامل (Multi-Dataset Engine)
def generate_universal_syntax(paragraphs, var_map, excel_columns):
    # تحويل أسماء أعمدة الإكسيل إلى حروف صغيرة للمطابقة
    excel_cols_low = [c.lower() for c in excel_columns]
    
    syntax = [
        "* Encoding: UTF-8.",
        "* =========================================================================.",
        "* UNIVERSAL MBA STATISTICAL REPORT - SPSS SYNTAX v26",
        f"* Generated for: {len(paragraphs)} Analysis Points",
        "* =========================================================================.\n"
    ]

    # إعداد الـ Labels بناءً على ما تم إيجاده في الوورد أو الإكسيل
    syntax.append("* --- [Step 1: Variable Labeling] --- .")
    syntax.append("VARIABLE LABELS")
    labels_to_add = []
    for col in excel_columns:
        col_low = col.lower()
        label = var_map.get(col_low, col)
        labels_to_add.append(f"  {col} \"{label}\"")
    syntax.append(" /\n".join(labels_list) if (labels_list := labels_to_add) else "* No Variables.")
    syntax.append(".")

    # إضافة Value Labels عامة (تغطي معظم ملفات المنهج)
    syntax.append("\nVALUE LABELS x1 1 \"Group 1 / Male / Far East\" 2 \"Group 2 / Female / Europe\" 3 \"Others / North America\" /x4 1 \"Yes / North\" 0 \"No / South\".\nEXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "=", "academy", "dr.", "best regards"]) or len(p) < 20:
            continue

        syntax.append(f"* --- [Q{q_idx}] {p[:85]}... --- .")
        syntax.append("* Scientific Justification: Based on MBA Statistics Curriculum.")

        # منطق الاختبارات الديناميكي
        # البحث عن المتغير التابع في السؤال
        target_var = "x1" # افتراضي
        for col in excel_cols_low:
            if col in p_low: target_var = col; break

        # 1. التكرارات والرسوم
        if "frequency table" in p_low:
            syntax.append(f"FREQUENCIES VARIABLES={target_var} /ORDER=ANALYSIS.")
        
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                # محاولة تحديد متغير التصنيف (مثل x4 أو x6 أو x11)
                factor = "x4" if "city" in p_low or "region" in p_low or "league" in p_low else "x2"
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({target_var}) BY {factor} /TITLE='Mean Analysis'.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {target_var}.")

        # 2. اختبارات الفرضيات (تغطي كل الـ Datasets)
        elif "test the hypothesis" in p_low:
            # اختبار عينة واحدة (Dataset 2 & 3)
            val_match = re.search(r"(\d+)", p_low)
            test_val = val_match.group(1) if val_match else "0"
            
            if "equal" in p_low and "difference" not in p_low:
                syntax.append(f"T-TEST /TESTVAL={test_val} /VARIABLES={target_var}.")
            elif "independent" in p_low or "male" in p_low or "surface" in p_low:
                syntax.append(f"T-TEST GROUPS=x4(0 1) /VARIABLES={target_var}.")
            else:
                syntax.append(f"ONEWAY {target_var} BY x11 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # 3. الارتباط والانحدار
        elif "correlation" in p_low:
            method = "SPEARMAN" if "happiness" in p_low or "rank" in p_low else "PEARSON"
            syntax.append(f"CORRELATIONS /VARIABLES={target_var} x2 /PRINT=TWOTAIL /METHOD={method}.")

        elif "regression" in p_low:
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT {target_var}\n  /METHOD=ENTER x1 x2 x3 x4.")

        q_idx += 1
    
    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI ---
st.set_page_config(page_title="MBA Universal SPSS Engine", layout="wide")
st.title("📊 محرك الإحصاء الشامل (Datasets 1, 2, 3, 4)")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل (أي Dataset)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (أي ملف وورد)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # قراءة الإكسيل ديناميكياً
        df = pd.read_excel(u_excel) if not u_excel.name.endswith('.csv') else pd.read_csv(u_excel)
        excel_columns = df.columns.tolist()
        
        # استخراج محتوى الوورد
        var_map, paragraphs = extract_word_content(u_word)
        
        # توليد السينتاكس
        final_code = generate_universal_syntax(paragraphs, var_map, excel_columns)
        
        st.success(f"✅ تم تحليل الملف بنجاح (تم العثور على {len(excel_columns)} متغيرات)")
        st.code(final_code, language='spss')
        st.download_button("تحميل السينتاكس (.sps)", final_code, "MBA_Universal_Analysis.sps")
        
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
