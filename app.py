import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# دالة التحليل الذكي للسؤال بناءً على المنهج الشامل
def intelligent_spss_engine(doc_upload):
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    mapping = {}
    for p in paragraphs:
        match = re.search(r"([Xx]\d+)\s*=\s*([^(\n\r.]+)", p, re.IGNORECASE)
        if match:
            mapping[match.group(1).upper()] = match.group(2).strip()

    syntax = ["* Encoding: UTF-8.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        # ربط المتغيرات الموجودة في السؤال
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping.get(v, "").lower()[:10] in p_low]
        found_vars = list(dict.fromkeys(found_vars))
        
        syntax.append(f"\n* QUESTION: {p}.")

        # --- المحرك الذكي لاختيار الاختبار (Selection Logic) ---
        
        # 1. اختبارات الفرضيات (T-Test & ANOVA) - فصول 4، 5، 6
        if any(w in p_low for w in ["test", "difference", "significant", "hypothesis", "impact"]):
            if "gender" in p_low or "two groups" in p_low or "independent" in p_low:
                syntax.append(f"T-TEST GROUPS=X4(0 1) /VARIABLES=X1 X3 /CRITERIA=CI(.95).")
            elif "before" in p_low and "after" in p_low:
                syntax.append("T-TEST PAIRS=BEFORE WITH AFTER (PAIRED) /CRITERIA=CI(.95) /MISSING=ANALYSIS.")
            elif "anova" in p_low or "more than two" in p_low or "city" in p_low:
                syntax.append(f"ONEWAY X1 X3 BY X6 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")

        # 2. الارتباط والانحدار - فصول 8، 9، 10
        elif "regression" in p_low or "y =" in p_low or "predict" in p_low:
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X1 /METHOD=ENTER {' '.join([v for v in mapping.keys() if v != 'X1'])}.")
        elif "correlation" in p_low:
            syntax.append(f"CORRELATIONS /VARIABLES={' '.join(found_vars) if len(found_vars)>1 else 'X1 X2 X3'} /PRINT=TWOTAIL NOSIG.")

        # 3. الإحصاء الوصفي والرسوم - فصول 1، 2
        elif "frequency table" in p_low:
            if "classes" in p_low or "k rule" in p_low:
                target = found_vars[0] if found_vars else "X1"
                syntax.append(f"RECODE {target} (LO thru HI=COPY) INTO {target}_CL.\nFREQUENCIES VARIABLES={target}_CL /FORMAT=NOTABLE.")
            else:
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars) if found_vars else 'X4 X5 X6'}.")
        
        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0] if found_vars else 'X5'}.")

        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars) if found_vars else 'X1'} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 4. التوزيع الطبيعي والقيم الشاذة - فصل 2
        elif "normality" in p_low or "normality test" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars) if found_vars else 'X1'} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low:
            syntax.append(f"EXAMINE VARIABLES={found_vars[0] if found_vars else 'X1'} /PLOT BOXPLOT /EXTREME(5).")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة المستخدم
st.set_page_config(page_title="SPSS Master Engine v40", layout="wide")
st.title("🤖 المحلل الإحصائي الذكي الشامل للمهندس محمد")
st.write("هذا المحرك مبرمج بناءً على الفصول العشرة للمنهج ليحل أي بيانات إحصائية.")

u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel/CSV)", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        final_syntax = intelligent_spss_engine(u_word)
        st.success("✅ تم تحليل الأسئلة وتوليد السينتاكس بناءً على منطق المنهج الكامل.")
        st.code(final_syntax, language='spss')
        st.download_button("تحميل السينتاكس النهائي (.sps)", final_syntax, "Master_Solution.sps")
    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
