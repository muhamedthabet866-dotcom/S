import streamlit as st
import pandas as pd
import re

# تحميل القواعد من ملفك (تم دمج المنطق يدوياً لضمان السرعة)
STRATEGIES = {
    "k-rule": "RECODE {var} (LO THRU {low}=1) ({low}.01 THRU {mid}=2) ({mid}.01 THRU HI=3) INTO {var}_cat.\nVALUE LABELS {var}_cat 1 'Low' 2 'Mid' 3 'High'.\nFREQUENCIES VARIABLES={var}_cat /FORMAT=AVALUE.",
    "descriptive": "FREQUENCIES VARIABLES={vars} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE SKEWNESS /FORMAT=NOTABLE.",
    "normality": "EXAMINE VARIABLES={var} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.\n* Note: If p > 0.05, data is normal (Empirical Rule).",
    "anova": "ONEWAY {num_var} BY {cat_var} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).",
    "regression": "REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA /DEPENDENT={dep} /METHOD=ENTER {indep}.",
    "correlation": "CORRELATIONS /VARIABLES={vars} /PRINT=TWOTAIL NOSIG."
}

def generate_perfect_syntax_from_file(df, var_defs, questions_text):
    # بناء الـ Mapping
    var_map = {}
    lines = var_defs.split('\n')
    for line in lines:
        match = re.search(r'(x\d+)\s*[=:]\s*([^(\n\r]+)', line, re.IGNORECASE)
        if match:
            v_code = match.group(1).strip().upper()
            v_label = match.group(2).strip().lower()
            var_map[v_label] = v_code

    syntax = ["* Encoding: UTF-8.\nTITLE 'Automated Solution based on Logic File'.\n"]
    
    # تقسيم الأسئلة والتحليل
    questions = re.split(r'\n\s*\d+[\.\)]', questions_text)
    for q in questions:
        q_low = q.lower().strip()
        if not q_low: continue
        
        # استخراج المتغيرات المذكورة
        found = [code for label, code in var_map.items() if label in q_low]
        v1 = found[0] if found else "X1"
        v_list = " ".join(found) if found else "X1 X2 X3"

        # تطبيق استراتيجيات ملفك الإكسيل
        if "frequency" in q_low or "classes" in q_low:
            syntax.append(STRATEGIES["k-rule"].format(var=v1, low=500, mid=1500))
        elif "mean" in q_low or "median" in q_low:
            syntax.append(STRATEGIES["descriptive"].format(vars=v_list))
        elif "difference" in q_low or "compare" in q_low:
            syntax.append(STRATEGIES["anova"].format(num_var="X3", cat_var="X4"))
        elif "regression" in q_low or "predict" in q_low:
            indep = " ".join([v for v in found if v != "X5"])
            syntax.append(STRATEGIES["regression"].format(dep="X5", indep=indep))
        elif "normality" in q_low or "empirical" in q_low:
            syntax.append(STRATEGIES["normality"].format(var=v1))

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("🚀 محرك SPSS العبقري (مدعوم بملف القواعد)")
# ... (بقية واجهة المستخدم)
