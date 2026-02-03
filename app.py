import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def advanced_spss_engine_v18(doc_upload):
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        # دعم قراءة النصوص من ملفات doc القديمة
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    mapping = {}
    for p in paragraphs:
        match = re.search(r"([Xx]\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* --- Final Scientific Solution (Fixing Error 701) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    
    # تعريف التسميات لـ DS4 و DS3
    syntax.append("VALUE LABELS X1 1 'Male' 2 'Female' /X2 1 'White' 2 'Black' 3 'Others'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"[Xx]\d+\s*=", p): continue
        
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v].lower()[:10] in p_low]
        if "salary" in p_low: found_vars.append("X3")
        if "age" in p_low: found_vars.append("X9")
        if "region" in p_low: found_vars.append("X4")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and "normality" not in p_low and "regression" not in p_low: continue

        syntax.append(f"\n* QUESTION: {p}.")

        # 1. تصحيح الرسوم البيانية (منع خطأ 701)
        if "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                # الصيغة العلمية المعتمدة لـ SPSS v26
                target = "X3" if "salary" in p_low else found_vars[0] if found_vars else "X1"
                category = "X4" if "region" in p_low else found_vars[-1] if len(found_vars) > 1 else "X1"
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({target}) BY {category}.")
            elif "maximum" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=MAX({found_vars[0]}) BY {found_vars[1] if len(found_vars)>1 else 'X1'}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0] if found_vars else 'X1'}.")

        # 2. فترات الثقة (95% و 99% في جداول مستقلة)
        elif "confidence interval" in p_low:
            vars_list = ' '.join(found_vars) if found_vars else "X3 X9"
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={vars_list} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 3. الانحدار والارتباط (لـ DS 4)
        elif "regression" in p_low or "y = f(" in p_low:
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X5 /METHOD=ENTER X1 X2 X3 X4 X6 X7 X8 X9 X10 X11 X12.")

        # 4. التكرارات والوصف الإحصائي
        elif any(w in p_low for w in ["mean", "median", "calculate", "mode"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars) if found_vars else 'X3 X9'} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS.")

        # 5. النورمالتي والقيم الشاذة
        elif "normality" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars) if found_vars else 'X3'} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low:
            syntax.append(f"EXAMINE VARIABLES={found_vars[0] if found_vars else 'X3'} /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("🏆 المحلل الإحصائي المطور لبيانات المهندس محمد")
u_excel = st.file_uploader("ارفع ملف الإكسيل (Data set 1, 3, 4)", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (docx/doc)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        final_code = advanced_spss_engine_v18(u_word)
        st.success("✅ تم تصحيح الأوامر وفصل فترات الثقة بنجاح!")
        st.code(final_code, language='spss')
        st.download_button("تحميل السينتاكس النهائي (.sps)", final_code, "Final_Solution_v18.sps")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
