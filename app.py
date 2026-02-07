import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# --- إعداد الصفحة ---
st.set_page_config(page_title="SPSS Universal Solver", layout="wide", page_icon="🧠")
st.title("🎓 المهندس محمد - المحرك الشامل لحل امتحانات SPSS")
st.markdown("### 🔓 هذا النظام يحلل أي ملف إكسيل مع أي أسئلة دون تجهيز مسبق.")

# --- 1. القواعد العامة (Fallback Rules) ---
# هذه القواعد تعمل إذا لم ترفع ملف rules.csv
DEFAULT_RULES = [
    {"keyword": "frequency", "template": "FREQUENCIES VARIABLES={var} /FORMAT=AVALUE /STATISTICS=MEAN MEDIAN MODE STDDEV /HISTOGRAM."},
    {"keyword": "descriptive", "template": "DESCRIPTIVES VARIABLES={var} /STATISTICS=MEAN STDDEV MIN MAX KURTOSIS SKEWNESS."},
    {"keyword": "bar chart", "template": "GRAPH /BAR(SIMPLE)=MEAN({y}) BY {group}."},
    {"keyword": "pie chart", "template": "GRAPH /PIE=COUNT BY {group}."},
    {"keyword": "histogram", "template": "GRAPH /HISTOGRAM(NORMAL)={var}."},
    {"keyword": "normality", "template": "EXAMINE VARIABLES={var} /PLOT NPPLOT /STATISTICS DESCRIPTIVES."},
    {"keyword": "regression", "template": "REGRESSION /DEPENDENT {y} /METHOD=ENTER {x_list} /STATISTICS COEFF OUTS R ANOVA."},
    {"keyword": "correlation", "template": "CORRELATIONS /VARIABLES={var} /PRINT=TWOTAIL NOSIG."},
    {"keyword": "t-test", "template": "T-TEST GROUPS={group}(0 1) /VARIABLES={var}."},
    {"keyword": "anova", "template": "ONEWAY {var} BY {group} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY."},
    {"keyword": "outlier", "template": "EXAMINE VARIABLES={var} /PLOT BOXPLOT."},
    {"keyword": "confidence", "template": "EXAMINE VARIABLES={var} /CINTERVAL 95."},
]

# --- 2. دوال الذكاء البرمجي ---

def detect_variable_type(series):
    """تحديد نوع المتغير (Scale/Nominal) بناءً على محتوى البيانات"""
    if pd.api.types.is_numeric_dtype(series):
        # إذا كان الرقمي له قيم فريدة قليلة (أقل من 10) نعتبره فئات (Nominal)
        if series.nunique() <= 10: 
            return 'Nominal'
        return 'Scale'
    return 'Nominal' # النصوص تعتبر Nominal

def find_matching_columns(question_text, df_columns):
    """
    دالة البحث الذكي: تربط كلمات السؤال بأسماء أعمدة الإكسيل
    """
    matches = []
    q_lower = question_text.lower()
    
    for col in df_columns:
        col_clean = col.strip().lower()
        # 1. تطابق تام
        if col_clean in q_lower:
            matches.append(col)
        # 2. تطابق جزئي (لو اسم العمود Salary_2020 والسؤال فيه Salary)
        else:
            parts = col_clean.split('_') # تقسيم الاسم المعقد
            for part in parts:
                if len(part) > 2 and part in q_lower: # تجاهل الكلمات القصيرة
                    matches.append(col)
                    break
    return list(set(matches)) # إزالة التكرار

def sturges_recode(col_name, series):
    """توليد كود Recode تلقائي باستخدام Sturges Rule"""
    n = len(series.dropna())
    if n == 0: return "", col_name
    
    k = math.ceil(1 + 3.322 * math.log10(n))
    min_v = math.floor(series.min())
    max_v = math.ceil(series.max())
    
    if max_v == min_v: width = 1
    else: width = (max_v - min_v) / k
    
    new_var = f"{col_name}_Cat"
    # تنظيف اسم المتغير الجديد من الرموز ليتوافق مع SPSS
    new_var = re.sub(r'\W+', '', new_var) 
    
    syntax = f"\n* --- RECODE (Sturges Rule: k={k}) for {col_name} ---.\n"
    syntax += f"RECODE {col_name} "
    
    curr = min_v
    for i in range(1, k+1):
        end = curr + width
        syntax += f"({curr:.2f} THRU {end:.2f}={i}) "
        curr = end
        
    syntax += f"INTO {new_var}.\nEXECUTE.\n"
    return syntax, new_var

# --- 3. الواجهة والمدخلات ---

with st.sidebar:
    st.header("1. البيانات (الخطوة الأهم)")
    uploaded_file = st.file_uploader("ارفع ملف الإكسيل (لأي امتحان)", type=['xlsx', 'csv'])
    
    df = None
    col_info = {} # لتخزين نوع كل عمود
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
            else: df = pd.read_excel(uploaded_file)
            
            # تنظيف أسماء الأعمدة (إزالة المسافات)
            df.columns = [c.strip() for c in df.columns]
            
            st.success(f"تم تحميل الملف: {len(df)} صف و {len(df.columns)} عمود.")
            
            st.write("---")
            st.write("**الأعمدة المكتشفة:**")
            for col in df.columns:
                v_type = detect_variable_type(df[col])
                col_info[col] = v_type
                icon = "🔢" if v_type == 'Scale' else "🔤"
                st.caption(f"{icon} {col} ({v_type})")
                
        except Exception as e:
            st.error(f"خطأ في الملف: {e}")

    st.write("---")
    st.header("2. ملف القواعد (اختياري)")
    rules_file = st.file_uploader("ملف rules.csv", type=['csv'])
    rules_data = DEFAULT_RULES
    if rules_file:
        try:
            rdf = pd.read_csv(rules_file)
            # التأكد من وجود الأعمدة المطلوبة وتوحيد اسمائها
            rdf.columns = [c.lower().strip() for c in rdf.columns]
            # تحويل للدكشنري
            rules_data = []
            for _, row in rdf.iterrows():
                # البحث عن العمود الذي يحتوي keyword أو template
                k = row.get('keyword', row.get('keyword ', ''))
                t = row.get('syntax_template', row.get('template', ''))
                if k and t:
                    rules_data.append({"keyword": str(k).lower(), "template": str(t)})
            st.success("تم تفعيل القواعد الخارجية.")
        except:
            st.warning("فشل قراءة ملف القواعد، جاري استخدام القواعد الافتراضية.")

# --- 4. المحرك الرئيسي ---

st.subheader("📝 منطقة الأسئلة (انسخ الأسئلة كما هي)")
questions_text = st.text_area("الأسئلة:", height=200, placeholder="Ex: Analyze the salary. Draw histogram for Age...")

if st.button("🚀 حل الامتحان"):
    if df is None:
        st.error("⚠️ يجب رفع ملف إكسيل أولاً ليعمل المحرك.")
    elif not questions_text:
        st.warning("⚠️ اكتب الأسئلة.")
    else:
        final_syntax = ["* Encoding: UTF-8.", "SET SEED=12345.", "OUTPUT MODIFY /SELECT ALL /REPORT PRINT LOG.", ""]
        
        # تقسيم الأسئلة
        questions = re.split(r'(?:\n|\d+\.\s)', questions_text)
        
        q_idx = 0
        for q in questions:
            q = q.strip()
            if len(q) < 3: continue
            q_idx += 1
            q_lower = q.lower()
            
            final_syntax.append(f"\n* ---------------- Q{q_idx}: {q} ----------------.")
            
            # A) البحث عن المتغيرات داخل السؤال
            matched_cols = find_matching_columns(q, df.columns)
            
            if not matched_cols:
                final_syntax.append(f"* Warning: لم يتم العثور على اسم عمود يطابق كلمات السؤال.")
                final_syntax.append(f"* Columns available: {', '.join(df.columns)}")
                continue
                
            # تصنيف المتغيرات المكتشفة
            scale_vars = [c for c in matched_cols if col_info[c] == 'Scale']
            nom_vars = [c for c in matched_cols if col_info[c] == 'Nominal']
            
            # B) هل السؤال يطلب تقسيم (Split)؟
            split_block_start = ""
            split_block_end = ""
            split_var = None
            if any(x in q_lower for x in ['for each', 'per ', 'by city', 'by gender']):
                # نبحث عن متغير اسمي في السؤال ليكون هو المقسم
                if nom_vars:
                    split_var = nom_vars[0]
                    split_block_start = f"SORT CASES BY {split_var}.\nSPLIT FILE SEPARATE BY {split_var}."
                    split_block_end = "SPLIT FILE OFF."

            # C) هل السؤال يطلب فئات (Classes/Recode)؟
            recode_syntax = ""
            active_vars = matched_cols.copy() # نسخة قابلة للتعديل
            
            if any(x in q_lower for x in ['class', 'group', 'intervals']):
                if scale_vars:
                    target = scale_vars[0] # نأخذ أول متغير رقمي
                    rec_code, new_var_name = sturges_recode(target, df[target])
                    recode_syntax = rec_code
                    # استبدال المتغير الأصلي بالمتغير الجديد في القائمة
                    active_vars = [new_var_name if x == target else x for x in active_vars]
                    # إضافة المتغير الجديد كـ Nominal (لأنه أصبح فئات)
                    nom_vars.append(new_var_name)

            # D) تطبيق القاعدة المناسبة
            rule_found = False
            # ترتيب القواعد بالأطول أولاً (لتجنب تداخل chart مع bar chart)
            sorted_rules = sorted(rules_data, key=lambda x: len(x['keyword']), reverse=True)
            
            for rule in sorted_rules:
                if rule['keyword'] in q_lower:
                    template = rule['template']
                    
                    # ملء القالب (Template Filling Logic)
                    cmd = template
                    
                    # {var} -> كل المتغيرات
                    if '{var}' in cmd: cmd = cmd.replace('{var}', " ".join(active_vars))
                    if '=var' in cmd: cmd = cmd.replace('=var', f"={' '.join(active_vars)}")
                    
                    # {group} -> متغير اسمي
                    if '{group}' in cmd:
                        g_var = split_var if split_var else (nom_vars[0] if nom_vars else "MISSING_GROUP")
                        cmd = cmd.replace('{group}', g_var)
                    
                    # {y} و {x} للانحدار
                    if '{y}' in cmd:
                        # التابع هو الرقمي
                        y_val = scale_vars[0] if scale_vars else active_vars[0]
                        cmd = cmd.replace('{y}', y_val)
                        # الباقي هو المستقل
                        x_vals = [v for v in active_vars if v != y_val]
                        if '{x_list}' in cmd: cmd = cmd.replace('{x_list}', " ".join(x_vals))
                    
                    # تجميع الكود النهائي للسؤال
                    if split_block_start: final_syntax.append(split_block_start)
                    if recode_syntax: final_syntax.append(recode_syntax)
                    
                    final_syntax.append(f"* Rule Applied: {rule['keyword']}")
                    final_syntax.append(cmd)
                    
                    if split_block_end: final_syntax.append(split_block_end)
                    
                    rule_found = True
                    break
            
            if not rule_found:
                # Fallback: وصف المتغيرات المكتشفة
                final_syntax.append("* No specific rule matched. Running Descriptives:")
                final_syntax.append(f"DESCRIPTIVES VARIABLES={' '.join(active_vars)} /STATISTICS=MEAN STDDEV MIN MAX.")

        st.success("تم إنشاء الكود بنجاح!")
        st.code("\n".join(final_syntax), language='spss')
