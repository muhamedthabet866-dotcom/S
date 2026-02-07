import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# --- إعداد الصفحة ---
st.set_page_config(page_title="MBA SPSS Genius", layout="wide", page_icon="🎓")

st.title("🎓 المهندس محمد - المحرك الذكي لـ SPSS (MBA Edition)")
st.markdown("""
### 💡 الميزات المحسنة:
1. **حماية من الأخطاء:** يعمل حتى بدون ملف إكسيل (يولد كوداً عاماً).
2. **دقة البحث:** يميز بين الكلمات المتشابهة (مثلاً Age لا تختلط بـ Average).
3. **قواعد المنهج:** يطبق Sturges Rule للفئات عند توفر البيانات.
""")

# --- دوال مساعدة للمنهج (MBA Logic) ---
def determine_measure(series):
    """تحديد نوع المتغير: Scale أو Nominal بناءً على البيانات"""
    if pd.api.types.is_numeric_dtype(series):
        # لو الأرقام قليلة جداً (أقل من 15) نعتبره فئات، إلا لو كان كسرياً
        if series.nunique() < 15 and pd.api.types.is_integer_dtype(series): 
            return "Nominal"
        return "Scale"
    return "Nominal"

def sturges_rule(n):
    """حساب عدد الفئات المثالي"""
    if n <= 0: return 5
    return math.ceil(1 + 3.322 * math.log10(n))

def generate_recode_syntax(var_code, series, n):
    """توليد كود إعادة التكويد (Recode) لعمل فئات"""
    try:
        k = sturges_rule(n)
        min_val = math.floor(series.min())
        max_val = math.ceil(series.max())
        
        # تجنب القسمة على صفر لو كل القيم متساوية
        if max_val == min_val:
            k = 1
            width = 1
        else:
            width = math.ceil((max_val - min_val) / k)
        
        syntax = f"\n* --- RECODING LOGIC (Sturges Rule: k={k}) ---.\n"
        syntax += f"* Recoding {var_code} into {k} classes (Width approx {width}).\n"
        syntax += f"RECODE {var_code} "
        
        current = min_val
        for i in range(1, k+1):
            end = current + width
            # التعامل مع الفئة الأخيرة لتشمل القيم العليا (Lowest thru ... thru Highest)
            if i == 1:
                chunk = f"(Lowest THRU {end}={i})"
            elif i == k:
                chunk = f"({current} THRU Highest={i})"
            else:
                chunk = f"({current} THRU {end}={i})"
            
            syntax += f"\n  {chunk}"
            current = end
            
        syntax += f"\n  INTO {var_code}_Cat.\n"
        syntax += f"VARIABLE LABELS {var_code}_Cat 'Categorized {var_code}'.\n"
        syntax += f"EXECUTE.\n" # أمر مهم لتنفيذ الـ Recode فوراً
        return syntax, f"{var_code}_Cat"
    except Exception as e:
        return f"* Error generating recode: {str(e)}", var_code

# --- الواجهة الجانبية ---
with st.sidebar:
    st.header("📂 1. البيانات والتعريفات")
    uploaded_file = st.file_uploader("ارفع ملف البيانات (Excel/CSV)", type=['xlsx', 'csv'])
    
    default_mapping = "x1=Gender\nx2=Education\nx3=Salary\nx4=Age\nx5=Satisfaction"
    
    df = None
    df_vars = {} 
    detected_map = []

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ تم التحميل: {len(df)} صف")
            
            st.subheader("📊 المتغيرات المكتشفة:")
            for i, col in enumerate(df.columns):
                # تنظيف اسم العمود من المسافات
                clean_col_name = col.strip()
                m_type = determine_measure(df[col])
                code = f"X{i+1}"
                # تخزين الاسم lowercase للمقارنة
                df_vars[clean_col_name.lower()] = {'code': code, 'type': m_type, 'data': df[col], 'real_name': clean_col_name}
                detected_map.append(f"{code}={clean_col_name}")
                st.caption(f"**{clean_col_name}** ➝ {code} ({m_type})")
            
            if st.checkbox("استخدام الأسماء من الملف؟", value=True):
                default_mapping = "\n".join(detected_map)
                
        except Exception as e:
            st.error(f"خطأ في الملف: {e}")

    v_mapping_text = st.text_area("تعديل الـ Mapping (X=Name):", value=default_mapping, height=200, help="اكتب الكود=الاسم (كل واحد في سطر)")

# --- المعالجة الرئيسية ---
mapping_dict = {} # Name -> Code
code_to_type = {} # Code -> Type
code_to_realname = {} # Code -> Original Name (for labels)

for line in v_mapping_text.split('\n'):
    if '=' in line:
        code, name = line.split('=')
        c = code.strip().upper()
        n = name.strip().lower() # الاسم للمقارنة
        real_n = name.strip()    # الاسم للعرض
        
        mapping_dict[n] = c
        code_to_realname[c] = real_n
        
        # تحديد النوع (Logic fallback)
        if df is not None and n in df_vars:
            code_to_type[c] = df_vars[n]['type']
        else:
            # تخمين ذكي بناءً على الاسم لو مفيش داتا
            if any(x in n for x in ['salary', 'age', 'income', 'score', 'sales', 'height', 'weight']):
                code_to_type[c] = 'Scale'
            else:
                code_to_type[c] = 'Nominal'

st.header("📝 2. الصق أسئلة الامتحان")
questions_input = st.text_area("الأسئلة:", height=150, placeholder="مثال:\n1. Check the normality of Salary.\n2. Predict Satisfaction based on Salary and Age.")

if st.button("🚀 تحليل وتوليد السنتاكس"):
    if not questions_input:
        st.warning("⚠️ يرجى إدخال الأسئلة أولاً.")
    else:
        final_syntax = [
            "* Encoding: UTF-8.", 
            "SET SEED=12345.", 
            "OUTPUT MODIFY /SELECT ALL /REPORT PRINT LOG.", # لتحسين شكل المخرجات
            ""
        ]
        
        questions = re.split(r'(?:\n|\. )', questions_input)
        
        for q_idx, q in enumerate(questions):
            q_clean = q.strip()
            if not q_clean: continue
            
            final_syntax.append(f"\n* ---------------------------------------------.")
            final_syntax.append(f"* QUESTION {q_idx+1}: {q_clean}.")
            final_syntax.append(f"* ---------------------------------------------.")
            q_lower = q_clean.lower()
            
            # 1. استخراج المتغيرات (Regex Word Boundary Fix)
            found_vars = [] 
            for name, code in mapping_dict.items():
                # استخدام Regex للتأكد من أنها كلمة كاملة وليست جزءاً من كلمة
                # re.escape(name) يحمي لو الاسم فيه رموز غريبة
                if re.search(r'\b' + re.escape(name) + r'\b', q_lower):
                    v_type = code_to_type.get(code, 'Scale')
                    found_vars.append({'name': name, 'code': code, 'type': v_type})
            
            # إزالة التكرار والحفاظ على الترتيب
            # (قد يظهر المتغير مرتين لو ذكر الاسم مرتين)
            unique_vars = []
            seen_codes = set()
            for v in found_vars:
                if v['code'] not in seen_codes:
                    unique_vars.append(v)
                    seen_codes.add(v['code'])
            found_vars = unique_vars

            if not found_vars:
                final_syntax.append("* Note: No variables detected in this question based on Mapping.")
                continue

            # 2. المحرك المنطقي (Logic Engine)
            
            # --- A: Regression ---
            if any(w in q_lower for w in ['predict', 'impact', 'effect', 'regression', 'depend']):
                if len(found_vars) >= 2:
                    # افتراض: الأول هو التابع، لكن نضع تحذير
                    dep = found_vars[0]['code']
                    indep = " ".join([v['code'] for v in found_vars[1:]])
                    final_syntax.append(f"* ASSUMPTION: '{found_vars[0]['name']}' is the DEPENDENT variable.")
                    final_syntax.append(f"* If incorrect, swap {dep} with one of the independent variables.")
                    final_syntax.append(f"REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA")
                    final_syntax.append(f" /DEPENDENT {dep} /METHOD=ENTER {indep}.")
                    final_syntax.append(f"* Check Anova Sig < 0.05 => Model is Significant.")
                else:
                    final_syntax.append("* Error: Need at least 2 variables for regression.")

            # --- B: Normality & Distribution ---
            elif any(w in q_lower for w in ['distribution', 'normality', 'skewness', 'describe', 'normal']):
                for v in found_vars:
                    if v['type'] == 'Scale':
                        final_syntax.append(f"DESCRIPTIVES VARIABLES={v['code']} /STATISTICS=MEAN STDDEV SKEWNESS KURTOSIS MIN MAX.")
                        final_syntax.append(f"* RULE (Empirical): Skewness between -1 & +1 implies Normal Distribution.")
                        final_syntax.append(f"* RULE (Chebyshev): If Skewness < -1 or > +1 implies Skewed Data.")
                        final_syntax.append(f"EXAMINE VARIABLES={v['code']} /PLOT BOXPLOT NPPLOT.") # NPPLOT gives QQ Plot

            # --- C: Frequencies & Classes (Sturges Rule) ---
            elif any(w in q_lower for w in ['frequency', 'class', 'group', 'table', 'range']):
                for v in found_vars:
                    if v['type'] == 'Scale':
                        # هنا Check مهم: هل الداتا موجودة؟
                        if df is not None and v['name'] in df_vars:
                            rec_syntax, new_var = generate_recode_syntax(v['code'], df_vars[v['name']]['data'], len(df))
                            final_syntax.append(rec_syntax)
                            final_syntax.append(f"FREQUENCIES VARIABLES={new_var} /ORDER=ANALYSIS.")
                        else:
                            final_syntax.append(f"* Note: Upload Excel file to enable automatic Sturges Rule Recoding for {v['name']}.")
                            final_syntax.append(f"FREQUENCIES VARIABLES={v['code']} /FORMAT=NOTABLE /STATISTICS=STDDEV MEAN.")
                    else:
                        final_syntax.append(f"FREQUENCIES VARIABLES={v['code']} /ORDER=ANALYSIS.")

            # --- D: Comparisons (T-Test / ANOVA) ---
            elif any(w in q_lower for w in ['difference', 'compare', 'mean of', 'test']):
                scale_v = next((v for v in found_vars if v['type'] == 'Scale'), None)
                nom_v = next((v for v in found_vars if v['type'] == 'Nominal'), None)
                
                if scale_v and nom_v:
                    final_syntax.append(f"* Comparing Mean of {scale_v['name']} (Scale) across groups of {nom_v['name']} (Nominal).")
                    final_syntax.append(f"MEANS TABLES={scale_v['code']} BY {nom_v['code']} /CELLS=MEAN COUNT STDDEV.")
                    final_syntax.append(f"ONEWAY {scale_v['code']} BY {nom_v['code']} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
                else:
                    final_syntax.append("* Hint: For comparisons, ensure you mentioned one Metric (Scale) and one Grouping (Nominal) variable.")
                    final_syntax.append(f"* Detected: {[v['code'] for v in found_vars]}")

            # --- E: Charts ---
            elif any(w in q_lower for w in ['chart', 'plot', 'graph', 'draw']):
                for v in found_vars:
                    if v['type'] == 'Scale':
                        final_syntax.append(f"GRAPH /HISTOGRAM={v['code']}.")
                        final_syntax.append(f"* Add /NORMAL to overlay curve if needed.")
                    else:
                        final_syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {v['code']}.")

            # --- Fallback (General) ---
            else:
                vars_str = " ".join([v['code'] for v in found_vars])
                final_syntax.append(f"DESCRIPTIVES VARIABLES={vars_str} /STATISTICS=MEAN STDDEV.")

        st.subheader("📝 كود الحل (Copy & Paste to SPSS Syntax Editor):")
        full_text = "\n".join(final_syntax)
        st.code(full_text, language='spss')
        st.success("تم توليد الكود! انسخه والصقه في نافذة Syntax في برنامج SPSS ثم اضغط Run (السهم الأخضر).")
