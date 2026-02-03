import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def universal_spss_engine_v19(doc_upload):
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        # محرك قراءة النصوص الخام للملفات القديمة .doc
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    mapping = {}
    for p in paragraphs:
        match = re.search(r"([Xx]\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* --- Universal Scientific Solution (Fixing Error 701 & Supporting DS 1,3,4) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    
    # تعريف القيم لضمان دقة المخرجات في النماذج المختلفة
    syntax.append("VALUE LABELS X2 1 'Yes' 0 'No' /X4 1 'Yes' 0 'No' /X11 1 'Far East' 2 'Europe' 3 'North America'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"[Xx]\d+\s*=", p): continue
        
        # ربط المتغيرات بالأسئلة
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v].lower()[:10] in p_low]
        # دعم يدوي لربط الكلمات بالمتغيرات (Data set 3 & 4)
        if "area" in p_low: found_vars.append("X3")
        if "population" in p_low: found_vars.append("X4")
        if "salary" in p_low: found_vars.append("X3")
        if "happiness" in p_low: found_vars.append("X5")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and "normality" not in p_low and "regression" not in p_low: continue
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. فترات الثقة (فصل 95% و 99% في جداول مستقلة)
        if "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars) if found_vars else 'X3'} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 2. تصحيح الرسوم البيانية (الحل النهائي لخطأ 701)
        elif "bar chart" in p_low:
            stat = "MEAN" if "average" in p_low else "MAX" if "maximum" in p_low else "PCT" if "percentage" in p_low else "COUNT"
            if len(found_vars) >= 2:
                # الصيغة العلمية: استخدام الأقواس حول العملية الحسابية
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({found_vars[0]}) BY {found_vars[1]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {found_vars[0]}.")

        # 3. الانحدار الخطي (سؤال Data set 4)
        elif "regression" in p_low or "y = f(" in p_low:
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X5 /METHOD=ENTER X1 X2 X3 X4 X6 X7 X8 X9 X10 X11 X12.")

        # 4. اختبارات الفروض (T-Test & ANOVA)
        elif "test the hypothesis" in p_low or "significant difference" in p_low:
            if "different region" in p_low or "different race" in p_low:
                syntax.append(f"ONEWAY {found_vars[0]} BY {found_vars[-1]} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
            else:
                syntax.append(f"T-TEST GROUPS={found_vars[-1]}(1 2) /VARIABLES={found_vars[0]}.")

        # 5. التوزيع الطبيعي والقيم الشاذة
        elif "normality" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low:
            syntax.append(f"EXAMINE VARIABLES={found_vars[0]} /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

        # 6. الإحصاء الوصفي والتكرارات
        elif any(w in p_low for w in ["mean", "median", "calculate", "frequency table"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("🏆 المحلل الإحصائي المطور (DS 1, 3, 4)")
u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد", type=['doc', 'docx'])

if u_excel and u_word:
    try:
        final_code = universal_spss_engine_v19(u_word)
        st.success("✅ تم تصحيح الأوامر وفصل فترات الثقة بنجاح!")
        st.code(final_code, language='spss')
        st.download_button("تحميل السينتاكس النهائي (.sps)", final_code, "Scientific_Analysis_v19.sps")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
