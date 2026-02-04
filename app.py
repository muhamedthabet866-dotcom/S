import streamlit as st
import pandas as pd
import re

def generate_final_syntax(df, var_defs, questions_text):
    # مصفوفة لتخزين أسطر الكود
    syntax = []
    
    # 1. الترويسة الاحترافية
    syntax.append("* Encoding: UTF-8.")
    syntax.append("* " + "="*73 + ".")
    syntax.append("* SPSS Syntax Generated for Data Analysis")
    syntax.append("* Prepared for: Dr. Mohamed A. Salam")
    syntax.append("* " + "="*73 + ".\n")

    # 2. تحليل تعريفات المتغيرات (Labeling)
    var_labels = []
    mapping = {} # اسم المتغير -> التسمية
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(\w+)\s*[=:-]\s*([^(\n]+)', line)
        if match:
            v_name = match.group(1).strip().lower()
            v_label = match.group(2).strip()
            mapping[v_label.lower()] = v_name
            var_labels.append(f"{v_name} \"{v_label}\"")

    syntax.append("* --- [Variable and Value Labeling] --- .")
    syntax.append("* Scientific Justification: Proper labeling ensures that the output is readable.")
    syntax.append("VARIABLE LABELS " + " /".join(var_labels) + ".")
    
    # إضافة Value Labels افتراضية بناءً على المنهج (يمكن توسيعها)
    syntax.append("VALUE LABELS x1 1 'Male' 2 'Female' /x4 1 'North East' 2 'South East' 3 'West'.")
    syntax.append("EXECUTE.\n")

    # 3. معالجة الأسئلة وتحويلها لأوامر إحصائية
    qs = questions_text.split('\n')
    for i, q in enumerate(qs):
        q_low = q.lower()
        if not q_low.strip(): continue

        # --- جداول التكرار (Categorical) ---
        if "frequency table" in q_low and "categorical" in q_low:
            syntax.append(f"* --- [Q{i+1}] Frequency tables for Categorical Data --- .")
            syntax.append("* Scientific Justification: Used to summarize distribution of categorical variables.")
            vars_found = [v for label, v in mapping.items() if label in q_low]
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(vars_found)} /ORDER=ANALYSIS.")

        # --- الرسوم البيانية (Charts) ---
        elif "bar chart" in q_low:
            syntax.append(f"* --- [Q{i+1}] Bar Charts Analysis --- .")
            syntax.append("* Scientific Justification: Provides visual comparison of means/counts across groups.")
            if "average" in q_low:
                # محاولة استخراج المتغير المستهدف والمجموعة
                target = next((v for label, v in mapping.items() if label in q_low), "x3")
                group = next((v for label, v in mapping.items() if "region" in label or "race" in label), "x4")
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({target}) BY {group} /TITLE='Average Analysis'.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Frequency Analysis'.")

        # --- الإحصاء الوصفي والتقسيم (Continuous) ---
        elif "continuous" in q_low or "classes" in q_low:
            syntax.append(f"* --- [Q{i+1}] Continuous Data and Descriptive Statistics --- .")
            syntax.append("* Scientific Justification: Recoding helps identifying patterns in continuous data.")
            # حساب فئات آلية بناءً على الإكسيل
            for label, v in mapping.items():
                if label in q_low and v in df.columns:
                    v_min, v_max = df[v].min(), df[v].max()
                    step = (v_max - v_min) / 5
                    syntax.append(f"RECODE {v} (LO THRU {v_min+step:.0f}=1) (HI=5) INTO {v}_Classes.")
            syntax.append(f"FREQUENCIES VARIABLES={' '.join([v for l,v in mapping.items() if l in q_low])} /STATISTICS=MEAN MEDIAN MODE STDDEV.")

        # --- اختبارات تاء (T-Tests) ---
        elif "test the hypothesis" in q_low and "equal" in q_low:
            val = re.findall(r'\d+', q_low)
            val = val[0] if val else "0"
            target = next((v for label, v in mapping.items() if label in q_low), "x3")
            syntax.append(f"* --- [Q{i+1}] One-Sample T-Tests --- .")
            syntax.append(f"* Scientific Justification: Evaluates if sample mean differs from {val}.")
            syntax.append(f"T-TEST /TESTVAL={val} /VARIABLES={target}.")

        # --- تحليل التباين (ANOVA) ---
        elif "significant difference" in q_low and "regions" in q_low:
            syntax.append(f"* --- [Q{i+1}] ONEWAY ANOVA Analysis --- .")
            syntax.append("* Scientific Justification: Compares means across three or more categories.")
            syntax.append("ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

        # --- الانحدار (Regression) ---
        elif "regression" in q_low or "y =" in q_low:
            syntax.append(f"* --- [Q{i+1}] Linear Regression Model --- .")
            syntax.append("* Scientific Justification: Measures strength/direction of relationships.")
            dep = mapping.get("general happiness", "x5")
            indeps = " ".join([v for v in mapping.values() if v != dep])
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN /DEPENDENT {dep} /METHOD=ENTER {indeps}.")

        syntax.append("") # سطر فارغ للتنظيم

    syntax.append("EXECUTE.")
    return "\n".join(syntax)

# --- واجهة Streamlit ---
st.set_page_config(page_title="SPSS Syntax Pro", layout="wide")
st.title("🚀 SPSS Syntax Professional Generator")

uploaded_file = st.file_uploader("1. ارفع ملف البيانات (Excel/CSV)", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.write("✅ تم تحميل البيانات بنجاح.")
    
    col1, col2 = st.columns(2)
    with col1:
        v_defs = st.text_area("2. تعريف المتغيرات (Where: X1=...)", height=250)
    with col2:
        q_text = st.text_area("3. أسئلة الامتحان", height=250)
        
    if st.button("توليد الكود النهائي"):
        final_code = generate_final_syntax(df, v_defs, q_text)
        st.text_area("النتيجة (SPSS Syntax):", final_code, height=400)
        st.download_button("تحميل الملف .SPS", final_code, file_name="Final_Analysis.sps")
