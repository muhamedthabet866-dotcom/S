import streamlit as st
import pandas as pd
import re

def generate_dynamic_syntax(var_defs, questions_text):
    # 1. تحليل خريطة المتغيرات (Variable Mapping)
    var_map = {}
    variable_labels = []
    
    lines = var_defs.split('\n')
    for line in lines:
        # البحث عن نمط مثل x1 = Account Balance
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().lower()
            v_label = match.group(2).strip()
            var_map[v_label.lower()] = v_code
            variable_labels.append(f"{v_code} \"{v_label}\"")

    syntax = [
        "* Encoding: UTF-8.",
        "* " + "="*70,
        "* Universal SPSS Syntax Generator (v2.0)",
        "* Designed to handle any Dataset & Exam Questions",
        "* " + "="*70 + ".\n"
    ]

    # إضافة التسميات (Labels)
    if variable_labels:
        syntax.append("VARIABLE LABELS " + " /".join(variable_labels) + ".")
    
    # محاولة استخراج Value Labels (مثل 1=Yes, 0=No)
    value_labels_found = []
    for line in lines:
        val_match = re.findall(r'(\d+)\s*=\s*([a-zA-Z]+)', line)
        if val_match:
            v_code_match = re.search(r'(x\d+)', line, re.IGNORECASE)
            if v_code_match:
                v_code = v_code_match.group(1).lower()
                labels = " ".join([f'{v[0]} "{v[1]}"' for v in val_match])
                value_labels_found.append(f"  /{v_code} {labels}")
    
    if value_labels_found:
        syntax.append("VALUE LABELS" + "\n".join(value_labels_found) + ".")
    
    syntax.append("EXECUTE.\n")

    # 2. تقسيم الأسئلة وتحليلها
    questions = re.split(r'\|\n\d+\.', questions_text)
    
    for q in questions:
        if not q.strip(): continue
        q_low = q.lower()
        
        # ربط المتغيرات المذكورة في السؤال بالأكواد (x1, x2...)
        mentioned_vars = []
        for label, code in var_map.items():
            if label in q_low:
                mentioned_vars.append(code)
        
        mentioned_vars = list(dict.fromkeys(mentioned_vars)) # إزالة التكرار
        vars_str = " ".join(mentioned_vars)

        if vars_str:
            syntax.append(f"* Task: {q.strip()[:80]}...")
            
            # جداول التكرار
            if any(word in q_low for word in ["frequency", "categorical", "table"]):
                syntax.append(f"FREQUENCIES VARIABLES={vars_str} /ORDER=ANALYSIS.")
            
            # الإحصاء الوصفي والالتواء
            if any(word in q_low for word in ["mean", "median", "mode", "descriptive", "deviation", "skewness"]):
                syntax.append(f"FREQUENCIES VARIABLES={vars_str} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")
            
            # الرسوم البيانية
            if "histogram" in q_low:
                for v in mentioned_vars: syntax.append(f"GRAPH /HISTOGRAM={v}.")
            
            if "bar chart" in q_low:
                if "average" in q_low or "mean" in q_low:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({mentioned_vars[0]}) BY {mentioned_vars[-1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {mentioned_vars[0]}.")

            if "pie chart" in q_low:
                syntax.append(f"GRAPH /PIE=COUNT BY {mentioned_vars[0]}.")

            # التحليل الاستكشافي (Normality & Outliers)
            if any(word in q_low for word in ["normality", "outliers", "extreme", "confidence", "examine"]):
                syntax.append(f"EXAMINE VARIABLES={vars_str} /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.")

            syntax.append("")

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Universal MBA SPSS Engine", layout="wide")

st.title("🎓 Universal SPSS Syntax Engine")
st.markdown("قم برفع ملف البيانات، ثم أدخل تعريف المتغيرات والأسئلة لتوليد الكود فوراً.")

# --- 1. خانة رفع الملف ---
uploaded_file = st.file_uploader("1. قم برفع ملف البيانات (Excel أو CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        st.success(f"✅ تم تحميل الملف بنجاح! يحتوي على ({df.shape[1]}) أعمدة.")
        
        # عرض أسماء الأعمدة الحقيقية لمساعدة المستخدم
        with st.expander("عرض أعمدة الملف المرفوع"):
            st.write(list(df.columns))
            
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")

# --- 2. مدخلات النصوص ---
col1, col2 = st.columns(2)

with col1:
    v_in = st.text_area("2. أدخل خريطة المتغيرات (مثال: x1 = Account Balance):", 
                        height=250,
                        placeholder="x1 = Account Balance\nx4 = Has a debit card (1=yes, 0=no)\nx6 = City where banking is done")

with col2:
    q_in = st.text_area("3. الصق أسئلة الامتحان هنا:", 
                        height=250,
                        placeholder="Construct a frequency table for debit card...\nCalculate mean and skewness for account balance...")

# --- 3. توليد النتائج ---
if st.button("Generate SPSS Syntax"):
    if v_in and q_in:
        final_syntax = generate_dynamic_syntax(v_in, q_in)
        
        st.divider()
        st.subheader("🚀 SPSS Syntax المولد:")
        st.code(final_syntax, language='spss')
        
        st.download_button(
            label="تحميل ملف .SPS جاهز للتشغيل",
            data=final_syntax,
            file_name="Universal_SPSS_Solution.sps",
            mime="text/plain"
        )
    else:
        st.warning("الرجاء إدخال المتغيرات والأسئلة أولاً.")
