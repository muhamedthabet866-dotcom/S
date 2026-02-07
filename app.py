import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# --- إعداد الصفحة ---
st.set_page_config(page_title="MBA SPSS Genius", layout="wide", page_icon="🎓")
st.title("🎓 المهندس محمد - SPSS Engine (Advanced Logic)")

# --- 1. دوال الذكاء الإحصائي ---

def get_sturges_syntax(var_code, var_name, n_rows, data_series=None):
    """توليد كود إعادة التكويد للفئات تلقائياً"""
    if n_rows == 0: # لو مفيش داتا، نستخدم قيم افتراضية
        k = 5
        width = 1000
        min_val = 0
    else:
        # Sturges Rule: k = 1 + 3.322 log(n)
        k = math.ceil(1 + 3.322 * math.log10(n_rows))
        if data_series is not None:
            min_val = math.floor(data_series.min())
            max_val = math.ceil(data_series.max())
            width = math.ceil((max_val - min_val) / k)
        else:
            return f"* Note: Load Excel file to calculate exact intervals for {var_name}.\n", var_code

    new_var = f"{var_code}_Cat"
    syntax = f"\n* --- RECODE Logic for {var_name} (Sturges k={k}) ---.\n"
    syntax += f"RECODE {var_code} "
    
    current = min_val
    for i in range(1, k+1):
        end = current + width
        if i == k: 
            syntax += f"({current} THRU HIGHEST={i}) " # آخر فئة مفتوحة
        else:
            syntax += f"({current} THRU {end}={i}) "
        current = end
    
    syntax += f"INTO {new_var}.\n"
    syntax += f"VARIABLE LABELS {new_var} 'Classes of {var_name}'.\n"
    syntax += f"EXECUTE.\n"
    return syntax, new_var

def fill_template_advanced(template, found_vars, split_var=None):
    """ملء القالب بذكاء مع تحديد المتغير التابع والمستقل"""
    syntax = template
    
    # تصنيف المتغيرات
    scale_vars = [v['code'] for v in found_vars if v['type'] == 'Scale']
    nom_vars = [v['code'] for v in found_vars if v['type'] == 'Nominal']
    all_codes = [v['code'] for v in found_vars]

    # 1. استبدال {var} بالكل
    if '{var}' in syntax:
        syntax = syntax.replace('{var}', " ".join(all_codes))
        # تصحيح خطأ شائع: لو القالب فيه var بدون أقواس
    if '=var' in syntax: 
         syntax = syntax.replace('=var', f"={' '.join(all_codes)}")

    # 2. التعامل مع {group} (المتغير المُقسِّم)
    if '{group}' in syntax:
        # لو عندنا split_var (زي سؤال for each city) نستخدمه هو
        if split_var:
            syntax = syntax.replace('{group}', split_var)
        elif nom_vars:
            syntax = syntax.replace('{group}', nom_vars[0])
        else:
            syntax = syntax.replace('{group}', "MISSING_GROUP")

    # 3. التعامل مع {y} (المتغير الرقمي/التابع)
    if '{y}' in syntax:
        # نختار أول متغير Scale كمتغير تابع
        target = scale_vars[0] if scale_vars else (all_codes[0] if all_codes else "MISSING_Y")
        syntax = syntax.replace('{y}', target)

    return syntax

# --- 2. الواجهة الجانبية ---
with st.sidebar:
    st.header("📂 1. البيانات والقواعد")
    rules_file = st.file_uploader("ملف القواعد (CSV)", type=['csv'])
    rules_df = None
    if rules_file:
        rules_df = pd.read_csv(rules_file)

    data_file = st.file_uploader("ملف البيانات (Excel/CSV)", type=['xlsx', 'csv'])
    df = None
    df_vars = {} 
    
    # Mapping افتراضي محدث لأسئلة البنك
    default_mapping = """
x1 = account balance
x2 = atm transaction
x2 = number of atm
x3 = age
x4 = city
x4 = where banking is done
x5 = debit card
x6 = interest
x6 = receive interest
"""
    if data_file:
        try:
            if data_file.name.endswith('.csv'): df = pd.read_csv(data_file)
            else: df = pd.read_excel(data_file)
            st.success(f"تم تحميل {len(df)} صف")
            # تعبئة المتغيرات من الداتا
            for i, col in enumerate(df.columns):
                 # تنظيف الاسم
                clean_name = col.strip().lower()
                # تحديد النوع
                if pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique() > 10:
                    v_type = 'Scale'
                else:
                    v_type = 'Nominal'
                
                # ربط الكود بالاسم الحقيقي والداتا
                # ملاحظة: هنا سنحاول ربط الكود X بناء على الـ Mapping لاحقاً
                # للتسهيل سنخزن الداتا باسم العمود
                df_vars[clean_name] = {'data': df[col], 'type': v_type}
                
        except Exception as e:
            st.error(e)

    v_mapping_text = st.text_area("تعريف المتغيرات:", value=default_mapping.strip(), height=200)

# --- 3. معالجة الـ Mapping ---
mapping_list = [] 
for line in v_mapping_text.split('\n'):
    if '=' in line:
        parts = line.split('=')
        code = parts[0].strip().upper()
        phrase = parts[1].strip().lower()
        # تحديد النوع افتراضياً
        v_type = 'Scale' if any(x in phrase for x in ['balance', 'transaction', 'age']) else 'Nominal'
        mapping_list.append({'code': code, 'phrase': phrase, 'type': v_type, 'real_name': phrase})

# --- 4. المحرك الرئيسي ---
st.header("📝 الأسئلة")
questions_input = st.text_area("الصق الأسئلة:", height=300)

if st.button("🚀 Run Analysis"):
    final_syntax = ["* Encoding: UTF-8.", "SET SEED=12345.", "OUTPUT MODIFY /SELECT ALL /REPORT PRINT LOG.", ""]
    
    # تقسيم الأسئلة
    questions = re.split(r'(?:\n|\d+\.\s)', questions_input)
    
    q_num = 0
    for q in questions:
        q_clean = q.strip()
        if len(q_clean) < 5: continue
        q_num += 1
        q_lower = q_clean.lower()
        
        final_syntax.append(f"\n* ---------------- Q{q_num} ----------------.")
        final_syntax.append(f"* Question: {q_clean}")

        # أ) البحث عن المتغيرات
        found_vars = []
        for item in mapping_list:
            # بحث دقيق عن الجملة
            if item['phrase'] in q_lower:
                found_vars.append(item)
        
        # إزالة التكرار
        unique = []
        seen = set()
        for v in found_vars:
            if v['code'] not in seen:
                unique.append(v)
                seen.add(v['code'])
        found_vars = unique

        if not found_vars:
            final_syntax.append("* Warning: No variables found defined in Mapping.")
            continue

        # ب) اكتشاف النية الخاصة (Logic Detection)
        
        # 1. هل يوجد طلب "For Each" أو "Per" (Split File)؟
        split_code = None
        if 'for each' in q_lower or 'per ' in q_lower:
            # البحث عن المتغير الاسمي الذي جاء بعد for each
            # نفترض أنه أحد المتغيرات الـ Nominal الموجودة في السؤال
            nominals = [v for v in found_vars if v['type'] == 'Nominal']
            if nominals:
                split_code = nominals[0]['code'] # نأخذ أول متغير اسمي وجدناه
                final_syntax.append(f"\n* --- SPLIT FILE BY {split_code} ---.")
                final_syntax.append(f"SORT CASES BY {split_code}.")
                final_syntax.append(f"SPLIT FILE SEPARATE BY {split_code}.")

        # 2. هل يوجد طلب "Classes" أو "Groups" لمتغير رقمي؟ (Recode)
        needs_recode = False
        recode_var = None
        if 'class' in q_lower or 'group' in q_lower:
            scales = [v for v in found_vars if v['type'] == 'Scale']
            if scales:
                needs_recode = True
                recode_var = scales[0] # المتغير الذي سنحوله لفئات
        
        # ج) اختيار وتطبيق القاعدة
        code_generated = ""
        rule_applied = False
        
        if rules_df is not None:
             # ترتيب القواعد بالأطول أولاً لتجنب التداخل
            sorted_rules = rules_df.sort_values(by="Keyword", key=lambda x: x.str.len(), ascending=False)
            
            for idx, row in sorted_rules.iterrows():
                if str(row['Keyword']).lower() in q_lower:
                    template = row['Syntax_Template']
                    
                    # حالة خاصة: لو السؤال يطلب فئات (Classes)، نستخدم المتغير الجديد
                    if needs_recode and recode_var:
                        # توليد كود الـ Recode
                        n_rows = len(df) if df is not None else 0
                        data_col = df_vars.get(recode_var['real_name'], {}).get('data') if df is not None else None
                        
                        rec_syntax, new_var_code = get_sturges_syntax(recode_var['code'], recode_var['phrase'], n_rows, data_col)
                        final_syntax.append(rec_syntax)
                        
                        # نعدل المتغيرات المرسلة للقالب لتشمل المتغير الجديد بدلاً من القديم
                        temp_vars = [v for v in found_vars if v['code'] != recode_var['code']]
                        temp_vars.append({'code': new_var_code, 'type': 'Nominal'}) # المتغير الجديد أصبح اسمي
                        
                        code_generated = fill_template_advanced(template, temp_vars, split_code)
                    else:
                        code_generated = fill_template_advanced(template, found_vars, split_code)
                    
                    final_syntax.append(f"* Rule: {row['Category']}")
                    final_syntax.append(code_generated)
                    rule_applied = True
                    break
        
        # د) الـ Fallback (لو مفيش قاعدة)
        if not rule_applied:
            # لو السؤال عن Outliers
            if 'outlier' in q_lower or 'extreme' in q_lower:
                target = found_vars[0]['code']
                final_syntax.append(f"EXAMINE VARIABLES={target} /PLOT BOXPLOT.")
            else:
                vars_str = " ".join([v['code'] for v in found_vars])
                final_syntax.append(f"DESCRIPTIVES VARIABLES={vars_str} /STATISTICS=MEAN STDDEV MIN MAX.")

        # هـ) إغلاق الـ Split File
        if split_code:
            final_syntax.append("SPLIT FILE OFF.")

    st.subheader("💻 الكود النهائي:")
    st.code("\n".join(final_syntax), language='spss')
