import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def master_spss_engine_v21(doc_upload):
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        # قراءة النصوص الخام للملفات القديمة .doc
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    mapping = {}
    for p in paragraphs:
        match = re.search(r"([Xx]\d+)\s*=\s*([^(\n\r.]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            mapping[v_name] = v_label

    syntax = ["* --- Final Scientific Universal Solution (DS 1, 3, 4) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    
    # تعريف القيم الافتراضية للنماذج
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X11 1 'Far East' 2 'Europe' 3 'North America'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue
        
        # ربط المتغيرات بالأسئلة (تغطية الأسماء والرموز)
        found_vars = [v for v in mapping.keys() if v in p.upper() or mapping[v].lower()[:10] in p_low]
        if "balance" in p_low: found_vars.append("X1")
        if "transaction" in p_low: found_vars.append("X2")
        if "city" in p_low: found_vars.append("X6")
        if "debit" in p_low: found_vars.append("X4")
        if "salary" in p_low: found_vars.append("X3")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and "normality" not in p_low: continue
        
        syntax.append(f"\n* QUESTION: {p}.")

        # 1. التكرارات (السؤال الأول المفقود في خرجك)
        if "frequency table" in p_low:
            if any(k in p_low for k in ["classes", "k rule"]):
                target = found_vars[0] if found_vars else "X1"
                syntax.append(f"RECODE {target} (LO thru HI=COPY) INTO {target}_CL.\nFREQUENCIES VARIABLES={target}_CL.")
            else:
                syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")

        # 2. الإحصاء الوصفي والالتواء
        elif any(w in p_low for w in ["mean", "median", "calculate", "skewness"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS SESKEW.")

        # 3. فترات الثقة (فصل 95% و 99% في جداول مستقلة)
        elif "confidence interval" in p_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars) if found_vars else 'X1'} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 4. الرسوم البيانية (تصحيح المنطق)
        elif "bar chart" in p_low:
            stat = "MEAN" if "average" in p_low else "MAX" if "maximum" in p_low else "PCT" if "percentage" in p_low else "COUNT"
            if len(found_vars) >= 2:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({found_vars[0]}) BY {found_vars[1]}.")
            elif "each city" in p_low and "X6" in mapping:
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {found_vars[0] if found_vars else 'X1'}.")

        # 5. الهيستوجرام والـ Pie Chart
        elif "histogram" in p_low:
            for v in [v for v in found_vars if v in ["X1", "X2", "X3"]]:
                syntax.append(f"GRAPH /HISTOGRAM={v}.")
        elif "pie chart" in p_low:
            syntax.append(f"GRAPH /PIE=COUNT BY {found_vars[0] if found_vars else 'X5'}.")

        # 6. النورمالتي والقيم الشاذة (السؤال الأخير المفقود)
        elif "normality" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars) if found_vars else 'X1'} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in p_low or "extremes" in p_low:
            syntax.append(f"EXAMINE VARIABLES={found_vars[0] if found_vars else 'X1'} /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.title("📊 المحلل الإحصائي المطور (v21) - DS 1, 3, 4")
u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الوورد (الأسئلة)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        final_syntax = master_spss_engine_v21(u_word)
        st.code(final_syntax, language='spss')
        st.download_button("تحميل السينتاكس النهائي (.sps)", final_syntax, "Final_Solution_v21.sps")
    except Exception as e:
        st.error(f"Error: {e}")
