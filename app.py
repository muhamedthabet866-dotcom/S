import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# --- إعداد الصفحة ---
st.set_page_config(page_title="MBA SPSS Genius", layout="wide", page_icon="🎓")

st.title("🎓 المهندس محمد - المحرك الذكي لـ SPSS (MBA Edition)")

# --- 1. دوال مساعدة (Helpers) ---
def fill_template(template, found_vars):
    """ملء القالب بالمتغيرات المكتشفة"""
    syntax = template
    
    # تجميع الأكواد حسب النوع
    scale_vars = [v['code'] for v in found_vars if v['type'] == 'Scale']
    nom_vars = [v['code'] for v in found_vars if v['type'] == 'Nominal']
    all_codes = [v['code'] for v in found_vars]

    # {var} -> تضع كل المتغيرات المكتشفة
    if '{var}' in syntax:
        syntax = syntax.replace('{var}', " ".join(all_codes))
    
    # {group} -> تحتاج متغير اسمي (Nominal)
    if '{group}' in syntax:
        if nom_vars:
            syntax = syntax.replace('{group}', nom_vars[0])
        else:
            # لو مفيش Nominal صريح، نأخذ آخر متغير تم اكتشافه كافتراض
            syntax = syntax.replace('{group}', all_codes[-1] if all_codes else "MISSING_GROUP")

    # {y} و {x} للانحدار والرسوم البيانية المتقدمة
    if '{y}' in syntax:
        # المتغير التابع عادة هو Scale (مثل الراتب أو الرصيد)
        if scale_vars:
            syntax = syntax.replace('{y}', scale_vars[0])
            remaining = [x for x in all_codes if x != scale_vars[0]]
            if '{x}' in syntax:
                syntax = syntax.replace('{x}', remaining[0] if remaining else "MISSING_X")
        else:
             # لو مفيش Scale، نستخدم الأول وخلاص
            syntax = syntax.replace('{y}', all_codes[0] if all_codes else "MISSING_Y")

    return syntax

# --- 2. الواجهة الجانبية (Sidebar) ---
with st.sidebar:
    st.header("📂 1. ملف القواعد (Rules)")
    rules_file = st.file_uploader("ارفع ملف القواعد (spss_rules.csv)", type=['csv', 'xlsx'])
    
    rules_df = None
    if rules_file:
        try:
            if rules_file.name.endswith('.csv'):
                rules_df = pd.read_csv(rules_file)
            else:
                rules_df = pd.read_excel(rules_file)
            st.success(f"✅ تم تحميل {len(rules_df)} قاعدة.")
        except:
            st.error("خطأ في قراءة ملف القواعد")

    st.markdown("---")
    st.header("📊 2. تعريف المتغيرات (Mapping)")
    
    # هذا الـ Mapping الافتراضي مصمم خصيصاً لأسئلتك الحالية
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
    v_mapping_text = st.text_area("عرف المتغيرات هنا (Code = Search Phrase):", value=default_mapping.strip(), height=250)

# --- 3. معالجة الـ Mapping (محرك البحث) ---
mapping_list = [] # List of tuples (code, phrase, type)

for line in v_mapping_text.split('\n'):
    line = line.strip()
    if line and '=' in line:
        parts = line.split('=')
        if len(parts) == 2:
            code = parts[0].strip().upper()
            phrase = parts[1].strip().lower() # الجملة التي نبحث عنها
            
            # تحديد النوع تلقائياً بناءً على كلمات مفتاحية في اسم المتغير
            v_type = 'Nominal' # الافتراضي
            if any(w in phrase for w in ['balance', 'transaction', 'age', 'salary', 'income', 'score']):
                v_type = 'Scale'
            
            mapping_list.append({'code': code, 'phrase': phrase, 'type': v_type})

# --- 4. واجهة الأسئلة والتحليل ---
st.header("📝 3. محرك الأسئلة")
questions_input = st.text_area("الأسئلة:", height=200)

if st.button("🚀 توليد الكود (Run)"):
    if not questions_input:
        st.warning("ادخل الأسئلة أولاً.")
    else:
        final_syntax = ["* Encoding: UTF-8.", "SET SEED=12345.", "OUTPUT MODIFY /SELECT ALL /REPORT PRINT LOG.", ""]
        
        # تقسيم الأسئلة بناءً على الأرقام (1. , 2. ) أو سطر جديد
        # هذا الـ Regex يفصل الأسئلة التي تبدأ برقم ونقطة
        questions = re.split(r'(?:\n|\d+\.\s)', questions_input)
        
        q_counter = 0
        for q in questions:
            q_clean = q.strip()
            # تجاهل الأسطر القصيرة جداً أو الفارغة
            if len(q_clean) < 5: continue
            
            q_counter += 1
            final_syntax.append(f"\n* ---------------------------------------------.")
            final_syntax.append(f"* Q{q_counter}: {q_clean}")
            final_syntax.append(f"* ---------------------------------------------.")
            
            q_lower = q_clean.lower()
            
            # أ) استخراج المتغيرات (Match Engine)
            found_vars = []
            
            # نبحث عن كل جملة موجودة في الـ Mapping داخل السؤال
            for item in mapping_list:
                if item['phrase'] in q_lower:
                    found_vars.append(item)
            
            # إزالة التكرار (نحتفظ بالمتغير مرة واحدة لكل سؤال)
            unique_vars = []
            seen_codes = set()
            for v in found_vars:
                if v['code'] not in seen_codes:
                    unique_vars.append(v)
                    seen_codes.add(v['code'])
            found_vars = unique_vars

            # إذا لم نجد متغيرات، نعطي تحذير وننتقل للسؤال التالي
            if not found_vars:
                final_syntax.append("* Warning: No variables found. Check your Mapping definitions.")
                continue

            # ب) البحث في ملف القواعد (Rules Engine)
            rule_matched = False
            if rules_df is not None:
                # ترتيب القواعد: نبحث عن العبارات الأطول أولاً (الأكثر تخصصاً)
                # مثلاً "bar chart" قبل "chart"
                sorted_rules = rules_df.sort_values(by="Keyword", key=lambda x: x.str.len(), ascending=False)
                
                for idx, row in sorted_rules.iterrows():
                    keyword = str(row['Keyword']).lower().strip()
                    if keyword in q_lower:
                        template = row['Syntax_Template']
                        
                        # ملء القالب
                        try:
                            generated_code = fill_template(template, found_vars)
                            final_syntax.append(f"* Rule Applied: {row['Category']} ({keyword})")
                            final_syntax.append(generated_code)
                            rule_matched = True
                            break # وجدنا قاعدة، نتوقف عن البحث لهذا السؤال
                        except Exception as e:
                            final_syntax.append(f"* Error applying rule: {e}")

            # ج) Fallback Logic (لو مفيش قاعدة طابقت)
            if not rule_matched:
                vars_str = " ".join([v['code'] for v in found_vars])
                final_syntax.append("* No specific rule matched. Generating Default Descriptives:")
                final_syntax.append(f"DESCRIPTIVES VARIABLES={vars_str} /STATISTICS=MEAN STDDEV MIN MAX.")

        # عرض النتيجة
        st.subheader("💻 كود SPSS النهائي:")
        full_text = "\n".join(final_syntax)
        st.code(full_text, language='spss')
