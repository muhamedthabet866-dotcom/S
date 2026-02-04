import streamlit as st
import pandas as pd
import re
import math

# 1. القواعد المستخرجة من ملفك الإكسيل (Logic Engine)
RULES = {
    "k-rule": "RECODE {var} (LO THRU {low}=1) ({low}.01 THRU {mid}=2) ({mid}.01 THRU HI=3) INTO {var}_cat.\nVARIABLE LABELS {var}_cat 'Categorized {var}'.\nVALUE LABELS {var}_cat 1 'Low' 2 'Mid' 3 'High'.\nFREQUENCIES VARIABLES={var}_cat /FORMAT=AVALUE /HISTOGRAM.",
    "descriptive": "FREQUENCIES VARIABLES={vars} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE SKEWNESS KURTOSIS /FORMAT=NOTABLE.",
    "normality": "EXAMINE VARIABLES={var} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.\n* Note: Sig > 0.05 means Normal (Empirical Rule), Sig < 0.05 (Chebyshev).",
    "regression": "REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA /DEPENDENT={dep} /METHOD=ENTER {indeps}.",
    "compare_groups": "ONEWAY {num_var} BY {cat_var} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).",
    "correlation": "CORRELATIONS /VARIABLES={vars} /PRINT=TWOTAIL NOSIG."
}

def generate_syntax(questions, var_map):
    syntax = ["* Encoding: UTF-8.\nSET SEED=1234567.\n"]
    
    # تهيئة المتغيرات
    labels = " /".join([f"{code} '{label}'" for label, code in var_map.items()])
    syntax.append(f"VARIABLE LABELS {labels}.\nEXECUTE.")

    for i, q in enumerate(questions.split('\n')):
        q_low = q.lower().strip()
        if len(q_low) < 5: continue
        
        syntax.append(f"\n* --- Question {i+1}: {q_low[:50]} ---")
        
        # ربط السؤال بالقاعدة (بناءً على ملف القواعد الخاص بك)
        if "regression" in q_low or "model" in q_low:
            indeps = " ".join([v for v in var_map.values() if v != "X5"])
            syntax.append(RULES["regression"].format(dep="X5", indeps=indeps))
        
        elif "frequency" in q_low or "classes" in q_low:
            v = "X3" if "salary" in q_low or "balance" in q_low else "X1"
            syntax.append(RULES["k-rule"].format(var=v, low=30000, mid=60000))
            
        elif "mean" in q_low or "median" in q_low or "calculate" in q_low:
            v_list = " ".join([v for label, v in var_map.items() if label in q_low])
            syntax.append(RULES["descriptive"].format(vars=v_list if v_list else "X1 X2 X3"))

        elif "difference" in q_low or "compare" in q_low:
            syntax.append(RULES["compare_groups"].format(num_var="X3", cat_var="X4"))

        elif "normality" in q_low:
            syntax.append(RULES["normality"].format(var="X3"))
            
        syntax.append("EXECUTE.")

    return "\n".join(syntax)

# --- الواجهة ---
st.title("🤖 المحرك الذكي المعتمد على قواعدك")
v_map_raw = st.text_area("1. المابينج (x1=gender...)", "x1=gender\nx3=salary\nx5=happiness\nx4=region")
q_raw = st.text_area("2. الأسئلة")

if st.button("توليد الكود"):
    # تحويل المابينج لقاموس
    v_map = {line.split('=')[1].strip().lower(): line.split('=')[0].strip().upper() for line in v_map_raw.split('\n') if '=' in line}
    st.code(generate_syntax(q_raw, v_map), language="spss")
