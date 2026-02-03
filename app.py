import streamlit as st
import pandas as pd
from docx import Document
import io
import re

# 1. دالة استخراج البيانات من الوورد (الأسئلة والتعريفات)
def extract_word_data(file):
    try:
        doc = Document(io.BytesIO(file.read()))
        file.seek(0)
        full_text = []
        for p in doc.paragraphs:
            if p.text.strip(): full_text.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip(): full_text.append(cell.text.strip())
        return full_text
    except:
        return []

# 2. محرك توليد السينتاكس المطور (MBA Professional Engine)
def generate_advanced_syntax(paragraphs, dataset_name):
    syntax = [
        "* Encoding: UTF-8.",
        f"* Analysis for: {dataset_name}",
        "* Prepared for: Dr. Mohamed A. Salam.\n",
        "* [Step 1: Setup Variable Labels]"
    ]

    # إعداد التسميات بناءً على نوع مجموعة البيانات [cite: 16, 34]
    if "1" in dataset_name:
        syntax.append("VARIABLE LABELS X1 'Account Balance' X2 'ATM Transactions' X3 'Other Services' X4 'Debit Card' X5 'Interest' X6 'City'.")
        syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X6 1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'.")
    elif "2" in dataset_name:
        syntax.append("VARIABLE LABELS X2 'League' X5 'Salary' X7 'Wins' X11 'Surface' X13 'Errors'.")
        syntax.append("VALUE LABELS X2 0 'National' 1 'American' /X11 0 'Natural' 1 'Artificial'.")
    elif "3" in dataset_name:
        syntax.append("VARIABLE LABELS X2 'G7 Member' X3 'Total Area' X4 'Population' X11 'Region'.")
        syntax.append("VALUE LABELS X2 1 'Yes' 0 'No' /X11 1 'Far East' 2 'Europe' 3 'North America'.")
    
    syntax.append("EXECUTE.\n")

    q_idx = 1
    for p in paragraphs:
        p_low = p.lower()
        if any(x in p_low for x in ["where:", "x1 =", "dr.", "best regards"]) or len(p) < 15:
            continue
            
        syntax.append(f"* --- [QUESTION {q_idx}] {p[:80]}... --- .")
        
        # منطق الرسوم البيانية [cite: 2, 18, 20]
        if "bar chart" in p_low:
            dep = "X1" if "balance" in p_low else ("X3" if "area" in p_low else ("X5" if "salary" in p_low else "X7"))
            indep = "X6" if "city" in p_low else ("X4" if "debit" in p_low else "X2")
            stat = "MEAN" if "average" in p_low else ("MAX" if "maximum" in p_low else "COUNT")
            syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({dep}) BY {indep} /TITLE='{stat} of {dep} by {indep}'.")

        # التكرارات وإعادة الترميز 
        elif "frequency table" in p_low:
            if "categorical" in p_low:
                syntax.append("FREQUENCIES VARIABLES=X2 X4 X5 X6 X11 /ORDER=ANALYSIS.")
            else:
                syntax.append("* Recoding continuous data into classes.")
                syntax.append("RECODE X3 (LO THRU 100=1) (101 THRU 500=2) (HI=3) INTO X3_Cat.\nFREQUENCIES X3_Cat.")

        # اختبارات الفرضيات [cite: 10, 28, 30]
        elif "test the hypothesis" in p_low:
            val_match = re.search(r"(\d+)", p_low)
            val = val_match.group(1) if val_match else "0"
            if "equal" in p_low:
                syntax.append(f"T-TEST /TESTVAL={val} /VARIABLES=X3.")
            else:
                syntax.append("ONEWAY X3 BY X11 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        syntax.append("")
        q_idx += 1
        
    return "\n".join(syntax)

# --- واجهة المستخدم Streamlit ---
st.set_page_config(page_title="MBA SPSS Engine", layout="wide")
st.title("🎓 محرك التحليل الإحصائي الاحترافي")

# قسم رفع الملفات - تأكد من ظهور زر Excel الآن
col1, col2 = st.columns(2)
with col1:
    u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
with col2:
    u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx'])

if u_excel and u_word:
    # قراءة اسم الملف لتحديد القوالب الإحصائية
    dataset_name = u_excel.name
    
    paragraphs = extract_word_data(u_word)
    if paragraphs:
        syntax_code = generate_advanced_syntax(paragraphs, dataset_name)
        st.success(f"✅ تم تحليل {dataset_name} وتوليد السينتاكس!")
        
        st.code(syntax_code, language='spss')
        
        st.download_button(
            label="تحميل ملف السينتاكس (.sps)",
            data=syntax_code,
            file_name=f"Analysis_{dataset_name.split('.')[0]}.sps",
            mime="text/plain"
        )
else:
    st.warning("الرجاء رفع ملفي الإكسيل والوورد معاً لتفعيل التحليل.")
