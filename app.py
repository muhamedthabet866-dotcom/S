import streamlit as st
import pandas as pd
import re

# دالة توليد السينتاكس بناءً على المنهج [cite: 1-10]
def generate_final_exam_syntax(df, var_defs, questions_text):
    syntax = ["* Encoding: UTF-8.", "SET DECIMAL=DOT.", "* " + "="*65 + ".", "* SPSS Comprehensive Solution for MBA Exam", "* " + "="*65 + ".\n"]
    
    # 1. تعريف المتغيرات [cite: 18, 35, 45]
    syntax.append("* --- [Chapter 1: Data Setup] --- .")
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_name = match.group(1).lower().strip()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_name
            syntax.append(f"VARIABLE LABELS {v_name} \"{v_label}\".")
    syntax.append("EXECUTE.\n")

    # 2. تحليل الأسئلة [cite: 1-10]
    qs = questions_text.split('\n')
    for q in qs:
        q_low = q.lower().strip()
        if len(q_low) < 10: continue
        syntax.append(f"* QUESTION: {q[:100]}")

        # البحث عن المتغيرات في السؤال [cite: 35, 45]
        found_vars = [v for label, v in var_map.items() if label in q_low]

        # --- الرسوم البيانية [cite: 2, 5, 20, 23] ---
        if "chart" in q_low:
            if "bar chart" in q_low:
                if "average" in q_low and len(found_vars) >= 2:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}) BY {found_vars[1]}.")
                elif found_vars:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")
            elif "pie chart" in q_low and found_vars:
                syntax.append(f"GRAPH /PIE=COUNT BY {found_vars[0]}.")

        # --- التقسيم الفئوي الذكي (Chapter 2) [cite: 7, 26, 37] ---
        elif "classes" in q_low or "continuous" in q_low:
            for v in found_vars:
                if v in df.columns:
                    v_min, v_max = df[v].min(), df[v].max()
                    step = (v_max - v_min) / 5
                    syntax.append(f"* RECODE for {v} based on range: {v_min} to {v_max}[cite: 26].")
                    syntax.append(f"RECODE {v} (LO THRU {v_min+step:.0f}=1) (HI=5) INTO {v}_CL.")
                    syntax.append(f"FREQUENCIES VARIABLES={v}_CL /FORMAT=NOTABLE.")

        # --- الاختبارات الإحصائية (Chapter 4, 6) [cite: 12, 14, 29, 30] ---
        elif "test" in q_low or "difference" in q_low:
            if "35000" in q_low and found_vars:
                syntax.append(f"T-TEST /TESTVAL=35000 /VARIABLES={found_vars[0]}.")
            elif "region" in q_low or "race" in q_low:
                # إذا كانت البيانات المرفوعة بها أكثر من مجموعتين، نستخدم ANOVA [cite: 14, 16]
                dep = found_vars[0] if found_vars else "x3"
                factor = "x4" if "region" in q_low else "x2"
                syntax.append(f"ONEWAY {dep} BY {factor} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Exam Pro", layout="wide")
st.title("🎓 محرك حل امتحانات SPSS الشامل")

# --- هذه هي الخانة التي كانت ناقصة ---
st.subheader("1. خطوة رفع الملف (ضرورية لحساب الفئات والاختبارات)")
uploaded_file = st.file_uploader("ارفع ملف الإكسيل (Excel or CSV)", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    # قراءة الملف
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success("✅ تم تحميل الملف بنجاح.")
    
    col1, col2 = st.columns(2)
    with col1:
        v_in = st.text_area("2. الصق تعريفات المتغيرات (Where: X1=...)", height=200)
    with col2:
        q_in = st.text_area("3. الصق أسئلة الامتحان هنا:", height=200)

    if st.button("توليد الحل الإحصائي"):
        if v_in and q_in:
            code = generate_final_exam_syntax(df, v_in, q_in)
            st.code(code, language='spss')
            st.download_button("تحميل الملف .SPS", code, "Exam_Solution.sps")
