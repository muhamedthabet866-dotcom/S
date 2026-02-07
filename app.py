import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# --- إعداد الصفحة ---
st.set_page_config(page_title="MBA SPSS Genius", layout="wide")

st.title("🎓 المهندس محمد - المحرك الذكي لـ SPSS (MBA Edition)")
st.markdown("""
### الميزات الجديدة:
1. **تحليل ذكي:** يحدد نوع المتغير (Scale/Nominal) من ملف الإكسيل تلقائياً.
2. **قواعد المنهج:** يطبق قواعد (Empirical vs Chebyshev) وقواعد (Sturges) للفئات.
3. **ربط تلقائي:** يفهم أسئلة الامتحان ويستخرج المتغيرات المطلوبة.
""")

# --- دوال مساعدة للمنهج (MBA Logic) ---
def determine_measure(series):
    """تحديد نوع المتغير: Scale أو Nominal بناءً على البيانات"""
    if pd.api.types.is_numeric_dtype(series):
        if series.nunique() < 10: # لو الأرقام قليلة جداً نعتبره فئات (مثل 1=ذكر، 2=أنثى)
            return "Nominal"
        return "Scale"
    return "Nominal"

def sturges_rule(n):
    """حساب عدد الفئات المثالي"""
    if n == 0: return 5
    return math.ceil(1 + 3.322 * math.log10(n))

def generate_recode_syntax(var_code, series, n):
    """توليد كود إعادة التكويد (Recode) لعمل فئات"""
    k = sturges_rule(n)
    min_val = math.floor(series.min())
    max_val = math.ceil(series.max())
    width = math.ceil((max_val - min_val) / k)
    
    syntax = f"* Recoding {var_code} into {k} classes (Width={width}).\n"
    syntax += f"RECODE {var_code} "
    
    current = min_val
    for i in range(1, k+1):
        end = current + width
        if i == k: end = "HI" # آخر فئة مفتوحة
        syntax += f"({current} THRU {end}={i}) "
        current = end if end != "HI" else end
        
    syntax += f"INTO {var_code}_Cat.\n"
    syntax += f"VARIABLE LABELS {var_code}_Cat 'Categorized {var_code}'.\n"
    return syntax, f"{var_code}_Cat"

# --- الواجهة الجانبية ---
with st.sidebar:
    st.header("1. البيانات والتعريفات")
    uploaded_file = st.file_uploader("ارفع ملف البيانات (Excel/CSV)", type=['xlsx', 'csv'])
    
    # محاولة قراءة أسماء الأعمدة تلقائياً لعمل Mapping مقترح
    default_mapping = "x1=Gender\nx2=Education\nx3=Salary\nx4=Age\nx5=Satisfaction"
    
    df = None
    df_vars = {} # لتخزين نوع كل متغير (Scale/Nominal)
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"تم التحميل: {len(df)} صف")
            
            # تحليل المتغيرات
            st.subheader("تحليل المتغيرات المكتشفة:")
            detected_map = []
            for i, col in enumerate(df.columns):
                m_type = determine_measure(df[col])
                code = f"X{i+1}"
                df_vars[col.lower()] = {'code': code, 'type': m_type, 'data': df[col]}
                detected_map.append(f"{code}={col}")
                st.caption(f"**{col}** -> {code} ({m_type})")
            
            if st.checkbox("استخدام الأسماء من الملف للمقترحات؟"):
                default_mapping = "\n".join(detected_map)
                
        except Exception as e:
            st.error(f"خطأ في الملف: {e}")

    v_mapping_text = st.text_area("تعديل الـ Mapping (X=Name):", value=default_mapping, height=150)

# --- المعالجة الرئيسية ---
# تحويل الـ Mapping النصي إلى قاموس للبحث
mapping_dict = {} # Name -> Code
code_to_type = {} # Code -> Type (Scale/Nominal)

for line in v_mapping_text.split('\n'):
    if '=' in line:
        code, name = line.split('=')
        c = code.strip().upper()
        n = name.strip().lower()
        mapping_dict[n] = c
        # لو مفيش ملف، نفترض الافتراضي
        if df is None:
             # افتراض بسيط: لو الاسم فيه salary/age/income يبقى Scale غير كدة Nominal
            if any(x in n for x in ['salary', 'age', 'income', 'score', 'sales']):
                code_to_type[c] = 'Scale'
            else:
                code_to_type[c] = 'Nominal'
        elif n in df_vars:
            code_to_type[c] = df_vars[n]['type']

st.header("2. الصق أسئلة الامتحان")
questions_input = st.text_area("الأسئلة:", height=150, placeholder="مثال: Analyze the distribution of Salary. Predict Satisfaction based on Salary and Age.")

if st.button("🚀 تحليل وتوليد السنتاكس"):
    if not questions_input:
        st.warning("ادخل الأسئلة أولاً")
    else:
        final_syntax = ["* Encoding: UTF-8.", "SET SEED=12345.", ""]
        
        # تقسيم الأسئلة
        questions = re.split(r'(?:\n|\. )', questions_input)
        
        for q_idx, q in enumerate(questions):
            q_clean = q.strip()
            if not q_clean: continue
            
            final_syntax.append(f"\n* --- QUESTION: {q_clean} ---.")
            q_lower = q_clean.lower()
            
            # 1. استخراج المتغيرات المذكورة في السؤال
            found_vars = [] # list of (name, code, type)
            for name, code in mapping_dict.items():
                if name in q_lower:
                    v_type = code_to_type.get(code, 'Scale') # Default Scale if unknown
                    found_vars.append({'name': name, 'code': code, 'type': v_type})
            
            # 2. المحرك المنطقي (Logic Engine)
            
            # --- الحالة A: الانحدار والتنبؤ (Regression) ---
            if any(w in q_lower for w in ['predict', 'impact', 'effect', 'regression']):
                # نبحث عن المتغير التابع (Dependent) - غالباً يأتي قبل "based on" أو بعد "predict"
                # للتبسيط هنا: سنعتبر أول متغير مذكور هو التابع، والباقي مستقل
                if len(found_vars) >= 2:
                    dep = found_vars[0]['code']
                    indep = " ".join([v['code'] for v in found_vars[1:]])
                    final_syntax.append(f"* Regression to predict {found_vars[0]['name']}.")
                    final_syntax.append(f"REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA")
                    final_syntax.append(f" /DEPENDENT {dep} /METHOD=ENTER {indep}.")
                    final_syntax.append(f"* Check Anova Sig < 0.05 for Model Fit.")
                else:
                    final_syntax.append("* Error: Need at least 2 variables for regression.")

            # --- الحالة B: التوزيع الطبيعي والوصف (Descriptive / Normality) ---
            elif any(w in q_lower for w in ['distribution', 'normality', 'skewness', 'describe']):
                for v in found_vars:
                    if v['type'] == 'Scale':
                        final_syntax.append(f"DESCRIPTIVES VARIABLES={v['code']} /STATISTICS=MEAN STDDEV SKEWNESS KURTOSIS MIN MAX.")
                        final_syntax.append(f"* RULE: If Skewness is between -1 and 1 -> Normal Distribution (Use Empirical Rule).")
                        final_syntax.append(f"* RULE: If Skewness < -1 or > 1 -> Skewed (Use Chebyshev Theorem).")
                        final_syntax.append(f"EXAMINE VARIABLES={v['code']} /PLOT BOXPLOT NPPLOT.")

            # --- الحالة C: جداول التكرار والفئات (Frequencies / Classes) ---
            elif any(w in q_lower for w in ['frequency', 'class', 'group', 'table']):
                for v in found_vars:
                    if v['type'] == 'Scale' and df is not None:
                        # هنا نطبق Sturges Rule ونعمل Recode
                        rec_syntax, new_var = generate_recode_syntax(v['code'], df_vars[v['name']]['data'], len(df))
                        final_syntax.append(rec_syntax)
                        final_syntax.append(f"FREQUENCIES VARIABLES={new_var} /ORDER=ANALYSIS.")
                    else:
                        final_syntax.append(f"FREQUENCIES VARIABLES={v['code']} /ORDER=ANALYSIS.")

            # --- الحالة D: المقارنة (Differences / T-Test / ANOVA) ---
            elif any(w in q_lower for w in ['difference', 'compare', 'mean of']):
                # نحتاج متغير Scale (للمتوسط) ومتغير Nominal (للمجموعات)
                scale_v = next((v for v in found_vars if v['type'] == 'Scale'), None)
                nom_v = next((v for v in found_vars if v['type'] == 'Nominal'), None)
                
                if scale_v and nom_v:
                    final_syntax.append(f"* Comparing Mean of {scale_v['name']} across groups of {nom_v['name']}.")
                    final_syntax.append(f"MEANS TABLES={scale_v['code']} BY {nom_v['code']} /CELLS=MEAN COUNT STDDEV.")
                    final_syntax.append(f"ONEWAY {scale_v['code']} BY {nom_v['code']} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
                else:
                    final_syntax.append("* Hint: For comparisons, mention one Metric (Scale) and one Grouping (Nominal) variable.")

            # --- الحالة E: الرسم البياني (Charts) ---
            elif 'chart' in q_lower or 'plot' in q_lower or 'graph' in q_lower:
                for v in found_vars:
                    if v['type'] == 'Scale':
                        final_syntax.append(f"GRAPH /HISTOGRAM={v['code']}.")
                    else:
                        final_syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {v['code']}.")

            else:
                # الحالة العامة
                if found_vars:
                    vars_str = " ".join([v['code'] for v in found_vars])
                    final_syntax.append(f"DESCRIPTIVES VARIABLES={vars_str} /STATISTICS=MEAN STDDEV.")

        st.subheader("📝 كود الحل (Copy & Paste to SPSS):")
        full_text = "\n".join(final_syntax)
        st.code(full_text, language='spss')
