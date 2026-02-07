import streamlit as st
import pandas as pd
import numpy as np
import re
import math

# --- إعداد الصفحة ---
st.set_page_config(page_title="SPSS Exam Solver", layout="wide", page_icon="🧠")
st.title("🎓 المهندس محمد - المحرك الذكي (Auto-Map Logic)")
st.markdown("""
### 💡 فكرة التحديث:
يقوم البرنامج بقراءة النص كاملاً أولاً لاستخراج تعريفات المتغيرات (مثلاً: X1 = Balance)، ثم يطبقها على الأسئلة السابقة.
""")

# --- 1. القواعد الافتراضية (SPSS Syntax Rules) ---
RULES = [
    {"keys": ["frequency", "count"], "cmd": "FREQUENCIES VARIABLES={var} /FORMAT=AVALUE /STATISTICS=MEAN MEDIAN MODE STDDEV /HISTOGRAM."},
    {"keys": ["descriptive", "mean", "stddev", "variance"], "cmd": "DESCRIPTIVES VARIABLES={var} /STATISTICS=MEAN STDDEV VARIANCE RANGE MIN MAX SKEWNESS KURTOSIS."},
    {"keys": ["histogram"], "cmd": "GRAPH /HISTOGRAM(NORMAL)={var}."},
    {"keys": ["bar chart"], "cmd": "GRAPH /BAR(SIMPLE)=MEAN({y}) BY {group}."}, # للوسط الحسابي
    {"keys": ["percentage", "pie"], "cmd": "GRAPH /PIE=COUNT BY {group}."},
    {"keys": ["confidence interval"], "cmd": "EXAMINE VARIABLES={var} /CINTERVAL 95."},
    {"keys": ["normality", "empirical", "chebycheve"], "cmd": "EXAMINE VARIABLES={var} /PLOT NPPLOT /STATISTICS DESCRIPTIVES."},
    {"keys": ["outlier", "extreme"], "cmd": "EXAMINE VARIABLES={var} /PLOT BOXPLOT."},
]

# --- 2. دوال الذكاء البرمجي ---

def extract_variable_map(text):
    """
    وظيفة ذكية تستخرج تعريفات المتغيرات من نص الامتحان
    X1 = Account Balance -> {'account balance': 'X1', ...}
    """
    mapping = {}
    var_types = {} # لتحديد Scale/Nominal تخمينياً
    
    # البحث عن نمط: X followed by number = something
    pattern = re.compile(r'\b(X\d+)\s*=\s*(.+)', re.IGNORECASE)
    
    lines = text.split('\n')
    for line in lines:
        match = pattern.search(line)
        if match:
            code = match.group(1).upper() # X1
            desc = match.group(2).strip().lower() # account balance in $
            
            # تنظيف الوصف من أي زيادات
            clean_desc = desc.split('(')[0].strip() # إزالة (1=yes...)
            
            mapping[clean_desc] = code
            # إضافة كلمات مفتاحية فرعية للقاموس
            if "balance" in clean_desc: mapping["balance"] = code
            if "transaction" in clean_desc: mapping["transaction"] = code
            if "age" in clean_desc: mapping["age"] = code
            if "city" in clean_desc: mapping["city"] = code
            if "interest" in clean_desc: mapping["interest"] = code
            if "debit" in clean_desc: mapping["debit"] = code
            if "service" in clean_desc: mapping["service"] = code
            
            # تخمين النوع
            if any(w in desc for w in ['balance', 'age', 'transaction', 'amount', 'salary']):
                var_types[code] = 'Scale'
            else:
                var_types[code] = 'Nominal'
                
    return mapping, var_types

def sturges_recode(var_code, n=100):
    """توليد كود الفئات (Recode)"""
    # بما أننا لا نملك البيانات، سنفترض قيماً تقريبية أو نتركها للمستخدم
    new_var = f"{var_code}_Cat"
    syntax = f"\n* --- RECODE for {var_code} (Sturges Rule Applied) ---.\n"
    syntax += f"* Note: Replace min/max values based on your actual data.\n"
    syntax += f"RECODE {var_code} (Lowest THRU 1000=1) (1000 THRU 5000=2) (5000 THRU Highest=3) INTO {new_var}.\n"
    syntax += f"VARIABLE LABELS {new_var} 'Classes of {var_code}'.\n"
    syntax += "EXECUTE.\n"
    return syntax, new_var

# --- 3. الواجهة والتشغيل ---

st.warning("⚠️ هام: انسخ نص الامتحان كاملاً (الأسئلة + تعريفات المتغيرات X1=...) وضعه في الصندوق بالأسفل.")

questions_input = st.text_area("منطقة النص:", height=400, placeholder="Q1: ...\n...\nX1 = Account Balance...")

if st.button("🚀 حل الامتحان"):
    if not questions_input:
        st.error("الرجاء لصق النص أولاً.")
    else:
        # 1. القراءة الاستباقية (Learning Phase)
        var_map, var_types = extract_variable_map(questions_input)
        
        st.success(f"تم اكتشاف {len(var_types)} متغيرات: {list(var_types.keys())}")
        
        final_syntax = ["* Encoding: UTF-8.", "SET SEED=12345.", "OUTPUT MODIFY /SELECT ALL /REPORT PRINT LOG.", ""]
        
        # 2. معالجة الأسئلة
        questions = re.split(r'(?:\n|^)(?:Q\d+|Question\s*\d+|\d+\.)[:\s]', questions_input)
        
        q_idx = 0
        for q in questions:
            q = q.strip()
            # تجاهل الأسطر التي هي عبارة عن تعريفات فقط
            if q.startswith("X") and "=" in q: continue
            if len(q) < 5: continue
            
            q_idx += 1
            q_lower = q.lower()
            
            final_syntax.append(f"\n* ---------------- Q{q_idx}: {q[:50]}... ----------------.")
            
            # A. البحث عن المتغيرات (Matching)
            found_codes = []
            for key, code in var_map.items():
                if key in q_lower:
                    found_codes.append(code)
            
            # إزالة التكرار والحفاظ على الترتيب
            found_codes = list(dict.fromkeys(found_codes))
            
            if not found_codes:
                final_syntax.append("* Note: No variables detected in this question text.")
                continue

            # تصنيف المتغيرات المكتشفة
            scale_vars = [c for c in found_codes if var_types.get(c) == 'Scale']
            nom_vars = [c for c in found_codes if var_types.get(c) == 'Nominal']

            # B. المنطق الخاص (Split File / Recode)
            extra_syntax_top = ""
            extra_syntax_bottom = ""
            
            # 1. Split File (For each city...)
            split_var = None
            if any(w in q_lower for w in ['for each', 'per ', 'by city']):
                if nom_vars:
                    split_var = nom_vars[0]
                elif found_codes: # fallback
                     split_var = found_codes[-1] 
                
                if split_var:
                    extra_syntax_top += f"SORT CASES BY {split_var}.\nSPLIT FILE SEPARATE BY {split_var}.\n"
                    extra_syntax_bottom += "SPLIT FILE OFF.\n"

            # 2. Recode (Classes)
            processed_vars = found_codes.copy()
            if any(w in q_lower for w in ['class', 'group', 'distribution']):
                if scale_vars:
                    target = scale_vars[0]
                    rec_code, new_var = sturges_recode(target)
                    extra_syntax_top += rec_code
                    # استبدال المتغير الأصلي بالمتغير الفئوي الجديد في الأمر التالي
                    processed_vars = [new_var if x == target else x for x in processed_vars]
                    # إضافة الجديد لقائمة Nominal
                    nom_vars.append(new_var)

            # C. تطبيق القواعد
            rule_match = False
            
            # حالة خاصة: Bar Chart لمتوسط (Requires Scale variable as target)
            if "bar chart" in q_lower and ("average" in q_lower or "mean" in q_lower):
                if scale_vars and nom_vars:
                    cmd = f"GRAPH /BAR(SIMPLE)=MEAN({scale_vars[0]}) BY {nom_vars[0]}."
                    final_syntax.append(extra_syntax_top + cmd + "\n" + extra_syntax_bottom)
                    rule_match = True
            
            # حالة خاصة: Bar Chart لنسبة/تكرار (Nominal only)
            elif "bar chart" in q_lower and not rule_match:
                 target = nom_vars[0] if nom_vars else processed_vars[0]
                 # إذا ذكر متغيرين nominal (مثل debit card و customers)
                 if len(nom_vars) >= 2:
                     cmd = f"GRAPH /BAR(GROUPED)=COUNT BY {nom_vars[0]} BY {nom_vars[1]}."
                 else:
                     cmd = f"GRAPH /BAR(SIMPLE)=COUNT BY {target}."
                 final_syntax.append(extra_syntax_top + cmd + "\n" + extra_syntax_bottom)
                 rule_match = True

            # باقي القواعد العامة
            if not rule_match:
                for rule in RULES:
                    if any(k in q_lower for k in rule['keys']):
                        cmd = rule['cmd']
                        
                        # تعويض المتغيرات
                        # {var} للكل
                        cmd = cmd.replace('{var}', " ".join(processed_vars))
                        
                        # {group} للمتغير الاسمي
                        g_var = split_var if split_var else (nom_vars[0] if nom_vars else "X_GROUP")
                        cmd = cmd.replace('{group}', g_var)
                        
                        # {y} للمتغير الكمي
                        y_var = scale_vars[0] if scale_vars else "X_SCALE"
                        cmd = cmd.replace('{y}', y_var)
                        
                        final_syntax.append(extra_syntax_top + cmd)
                        if extra_syntax_bottom: final_syntax.append(extra_syntax_bottom)
                        
                        rule_match = True
                        break
            
            # Fallback
            if not rule_match:
                final_syntax.append(f"DESCRIPTIVES VARIABLES={' '.join(processed_vars)} /STATISTICS=MEAN STDDEV MIN MAX.")

        st.success("تم توليد الكود! 👇")
        st.code("\n".join(final_syntax), language='spss')
