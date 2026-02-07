import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# --- إعداد الصفحة ---
st.set_page_config(page_title="MBA SPSS Genius", layout="wide", page_icon="🎓")

st.title("🎓 المهندس محمد - المحرك الذكي لـ SPSS (MBA Edition)")
st.markdown("""
### 🚀 المميزات:
1. **يعمل بملف القواعد:** يقرأ أوامر المنهج من ملف Excel/CSV خارجي.
2. **تحليل ذكي:** يستبدل الرموز {var}, {group} بأسماء الأعمدة تلقائياً.
3. **مرونة:** عدل ملف القواعد وسيتم تحديث البرنامج فوراً.
""")

# --- 1. دوال مساعدة (Helpers) ---

def determine_measure(series):
    """تحديد نوع المتغير: Scale أو Nominal"""
    if pd.api.types.is_numeric_dtype(series):
        if series.nunique() < 15 and pd.api.types.is_integer_dtype(series): 
            return "Nominal"
        return "Scale"
    return "Nominal"

def sturges_rule(n):
    if n <= 0: return 5
    return math.ceil(1 + 3.322 * math.log10(n))

def fill_template(template, found_vars):
    """
    دالة ذكية لملء الفراغات في كود الـ SPSS القادم من ملف القواعد
    {var} -> يضع كل المتغيرات
    {group} -> يضع متغير اسمي (Nominal)
    {y} -> يضع المتغير التابع (أول متغير Scale)
    {x_list} -> يضع باقي المتغيرات المستقلة
    """
    syntax = template
    
    # تصنيف المتغيرات المكتشفة
    scale_vars = [v['code'] for v in found_vars if v['type'] == 'Scale']
    nom_vars = [v['code'] for v in found_vars if v['type'] == 'Nominal']
    all_codes = [v['code'] for v in found_vars]

    # 1. التعامل مع {var} أو {var1} (متغيرات عامة)
    if '{var}' in syntax:
        syntax = syntax.replace('{var}', " ".join(all_codes))
    
    # 2. التعامل مع {group} (للمقارنات والرسوم)
    if '{group}' in syntax:
        if nom_vars:
            syntax = syntax.replace('{group}', nom_vars[0])
        else:
            return f"* Error: Template requires a Grouping Variable (Nominal), but none found."

    # 3. التعامل مع Regression {y} و {x_list}
    if '{y}' in syntax:
        if len(scale_vars) >= 1:
            syntax = syntax.replace('{y}', scale_vars[0]) # نفترض الأول هو التابع
            
            # الباقي هم المستقلين
            remaining = [v for v in all_codes if v != scale_vars[0]]
            if '{x_list}' in syntax:
                syntax = syntax.replace('{x_list}', " ".join(remaining))
            if '{x}' in syntax: # لو معادلة انحدار بسيط
                syntax = syntax.replace('{x}', remaining[0] if remaining else "MISSING_IV")
        else:
            return "* Error: Regression requires at least one Scale variable."

    return syntax

# --- 2. الواجهة الجانبية (Sidebar) ---
with st.sidebar:
    st.header("📂 1. ملف القواعد (المنهج)")
    rules_file = st.file_uploader("ارفع ملف القواعد (spss_rules.csv)", type=['csv', 'xlsx'])
    
    rules_df = None
    if rules_file:
        try:
            if rules_file.name.endswith('.csv'):
                rules_df = pd.read_csv(rules_file)
            else:
                rules_df = pd.read_excel(rules_file)
            st.success(f"✅ تم تحميل {len(rules_df)} قاعدة.")
        except Exception as e:
            st.error(f"خطأ في ملف القواعد: {e}")

    st.markdown("---")
    st.header("📊 2. ملف البيانات")
    data_file = st.file_uploader("ارفع ملف البيانات (Data)", type=['xlsx', 'csv'])
    
    df = None
    df_vars = {} 
    
    # Mapping الافتراضي
    default_mapping = "x1=Gender\nx2=Education\nx3=Salary\nx4=Age\nx5=Satisfaction"

    if data_file:
        try:
            if data_file.name.endswith('.csv'):
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            st.success(f"✅ البيانات: {len(df)} صف")
            
            detected_map = []
            for i, col in enumerate(df.columns):
                clean_col = col.strip()
                m_type = determine_measure(df[col])
                code = f"X{i+1}"
                df_vars[clean_col.lower()] = {'code': code, 'type': m_type}
                detected_map.append(f"{code}={clean_col}")
            
            if st.checkbox("استخدام أسماء الملف؟", value=True):
                default_mapping = "\n".join(detected_map)
                
        except Exception as e:
            st.error(f"خطأ بيانات: {e}")

    v_mapping_text = st.text_area("X-Mapping:", value=default_mapping, height=150)

# --- 3. معالجة الـ Mapping ---
mapping_dict = {}
code_to_type = {}

for line in v_mapping_text.split('\n'):
    line = line.strip()
    if line and '=' in line:
        parts = line.split('=')
        if len(parts) == 2:
            c = parts[0].strip().upper()
            n = parts[1].strip().lower()
            mapping_dict[n] = c
            
            if df is not None and n in df_vars:
                code_to_type[c] = df_vars[n]['type']
            else:
                # تخمين النوع لو مفيش داتا
                if any(x in n for x in ['salary', 'age', 'score', 'sales']):
                    code_to_type[c] = 'Scale'
                else:
                    code_to_type[c] = 'Nominal'

# --- 4. واجهة الأسئلة والتحليل ---
st.header("📝 3. محرك الأسئلة")
questions_input = st.text_area("اكتب أسئلة الامتحان:", height=100, placeholder="Ex: Analyze frequency of Gender. Run regression for Salary based on Age.")

if st.button("🚀 توليد الكود (Run)"):
    if not questions_input:
        st.warning("ادخل الأسئلة أولاً.")
    else:
        final_syntax = ["* Encoding: UTF-8.", "SET SEED=12345.", "OUTPUT MODIFY /SELECT ALL /REPORT PRINT LOG.", ""]
        
        questions = re.split(r'(?:\n|\. )', questions_input)
        
        for q_idx, q in enumerate(questions):
            q_clean = q.strip()
            if not q_clean: continue
            
            final_syntax.append(f"\n* --- Q{q_idx+1}: {q_clean} ---.")
            q_lower = q_clean.lower()
            
            # أ) استخراج المتغيرات
            found_vars = []
            for name, code in mapping_dict.items():
                if re.search(r'\b' + re.escape(name) + r'\b', q_lower):
                    v_type = code_to_type.get(code, 'Scale')
                    found_vars.append({'name': name, 'code': code, 'type': v_type})
            
            # إزالة التكرار
            unique_vars = []
            seen = set()
            for v in found_vars:
                if v['code'] not in seen:
                    unique_vars.append(v)
                    seen.add(v['code'])
            found_vars = unique_vars

            if not found_vars:
                final_syntax.append("* Warning: No variables found from Mapping.")
                continue

            # ب) البحث في ملف القواعد (Priority 1)
            rule_matched = False
            if rules_df is not None:
                for idx, row in rules_df.iterrows():
                    keyword = str(row['Keyword']).lower().strip()
                    # بحث عن الكلمة المفتاحية في السؤال
                    if keyword in q_lower:
                        template = row['Syntax_Template']
                        generated_code = fill_template(template, found_vars)
                        final_syntax.append(f"* Rule Applied: {row['Category']} ({keyword})")
                        final_syntax.append(generated_code)
                        rule_matched = True
                        break # نكتفي بأول قاعدة تطابق (يمكنك إزالتها لو عايز يطبق كله)
            
            # ج) المنطق الاحتياطي (Fallback Logic) لو مفيش ملف قواعد أو لم نجد قاعدة
            if not rule_matched:
                final_syntax.append("* No rule matched in CSV, using Default Logic:")
                # هنا نضع منطق بسيط جداً للطوارئ
                vars_str = " ".join([v['code'] for v in found_vars])
                final_syntax.append(f"DESCRIPTIVES VARIABLES={vars_str} /STATISTICS=MEAN STDDEV MIN MAX.")

        # عرض النتيجة
        st.subheader("💻 كود SPSS النهائي:")
        full_text = "\n".join(final_syntax)
        st.code(full_text, language='spss')
