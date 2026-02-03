import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def universal_spss_engine_v17(doc_upload):
    # قراءة النص من ملف الوورد (دعم ملفات doc و docx)
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        # محاولة قراءة النصوص الخام إذا كان الملف بتنسيق قديم
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    mapping = {}
    for p in paragraphs:
        match = re.search(r"([Xx]\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* --- Universal Academic Solution (Support for DS 1, 3, 4) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"[Xx]\d+\s*=", p): continue
        
        # ربط المتغيرات بالأسئلة
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v].lower()[:10] in p_low]
        if not found_vars and "normality" not in p_low and "regression" not in p_low: continue

        syntax.append(f"\n* QUESTION: {p}.")

        # 1. الانحدار الخطي المتعدد (سؤال متكرر في DS 4)
        if "regression" in p_low or "y = f(" in p_low:
            dep_var = "X5" if "happiness" in p_low else found_vars[0] if found_vars else "Y"
            indep_vars = [v for v in mapping.keys() if v != dep_var]
            syntax.append(f"REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA /NOORIGIN /DEPENDENT {dep_var} /METHOD=ENTER {' '.join(indep_vars)}.")

        # 2. الارتباط (Correlation)
        elif "correlation" in p_low:
            syntax.append(f"CORRELATIONS /VARIABLES={' '.join(found_vars[:2])} /PRINT=TWOTAIL NOSIG /MISSING=PAIRWISE.")

        # 3. اختبارات الفروض (Hypothesis Testing / T-Test)
        elif "test the hypothesis" in p_low or "significant difference" in p_low:
            if "different region" in p_low or "different occupation" in p_low:
                # ANOVA (أكثر من مجموعتين)
                syntax.append(f"ONEWAY {' '.join(found_vars[:1])} BY {found_vars[-1]} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
            else:
                # Independent T-Test
                syntax.append(f"T-TEST GROUPS={found_vars[-1]}(1 2) /VARIABLES={found_vars[0]}.")

        # 4. فترات الثقة (95% و 99% - طلب المهندس محمد)
        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 5. الرسوم البيانية المتطورة
        elif "bar chart" in p_low:
            stat = "MEAN" if "average" in p_low else "MAX" if "maximum" in p_low else "PCT" if "percentage" in p_low else "COUNT"
            if len(found_vars) >= 2:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({found_vars[0]}) BY {found_vars[1]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {found_vars[0]}.")

        # 6. التوزيع الطبيعي والقيم الشاذة
        elif "normality" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low:
            syntax.append(f"EXAMINE VARIABLES={found_vars[0]} /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

        # 7. التكرارات والوصف العام
        elif any(w in p_low for w in ["mean", "median", "frequency table"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("🏆 المحلل الإحصائي الشامل (DS 1, 3, 4)")
u_excel = st.file_uploader("ارفع ملف الإكسيل (Data set 3 or 4)", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد الخاص بالنموذج", type=['doc', 'docx'])

if u_excel and u_word:
    try:
        final_code = universal_spss_engine_v17(u_word)
        st.code(final_code, language='spss')
        st.download_button("تحميل السينتاكس (.sps)", final_code, "Full_Analysis.sps")
    except Exception as e:
        st.error(f"Error: {e}")
