import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def master_spss_engine_v11(doc_upload):
    doc = Document(io.BytesIO(doc_upload.read()))
    
    # استخراج النصوص من الفقرات والجداول
    all_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip(): all_text.append(cell.text.strip())
    
    mapping = {}
    for line in all_text:
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", line, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            # استخراج القيم التكويدية (1=yes)
            vals = re.findall(r"(\d+)\s*[=-]\s*([a-zA-Zأ-ي]+)", line)
            mapping[v_name] = {"label": v_label, "values": vals}

    syntax = ["* --- Final Professional Correction (No Warnings) for SPSS v26 --- *.\n"]
    
    # 1. تعريف المتغيرات أولاً (Variable & Value Labels)
    for var, info in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{info['label']}'.")
        if info['values']:
            syntax.append(f"VALUE LABELS {var}")
            for val, txt in info['values']:
                syntax.append(f"  {val} '{txt}'")
            syntax.append(".")

    syntax.append("\nSET DECIMAL=DOT.\n")

    # 2. تحويل الأسئلة إلى أوامر معالجة دقيقة
    for q in all_text:
        q_low = q.lower()
        if re.search(r"X\d+\s*=", q): continue
        
        # ربط المتغيرات بالسؤال
        target_vars = [v for v in mapping.keys() if v in q.upper() or mapping[v]['label'].lower()[:10] in q_low]
        
        # تعزيز الربط للأسئلة النصية
        if "balance" in q_low and "X1" not in target_vars: target_vars.append("X1")
        if "city" in q_low and "X6" not in target_vars: target_vars.append("X6")
        if "debit" in q_low and "X4" not in target_vars: target_vars.append("X4")
        if "transaction" in q_low and "X2" not in target_vars: target_vars.append("X2")
        target_vars = list(dict.fromkeys(target_vars))

        if not target_vars: continue
        syntax.append(f"\n* QUESTION: {q}.")

        # --- تصحيح أمر EXAMINE لتجنب التحذير (Warning) ---
        if "confidence interval" in q_low:
            for val in ["95", "99"]:
                # الصيغة العلمية المعتمدة لـ SPSS v26
                syntax.append(f"EXAMINE VARIABLES={' '.join(target_vars)} /PLOT=NONE /STATISTICS=DESCRIPTIVES /CINTERVAL {val}.")

        # --- تصحيح أوامر الرسوم البيانية ---
        elif "bar chart" in q_low:
            if "average" in q_low or "mean" in q_low:
                if len(target_vars) >= 2:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({target_vars[0]}) BY {target_vars[1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({target_vars[0]}).")
            elif "percentage" in q_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {target_vars[0]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {target_vars[0]}.")

        elif "histogram" in q_low:
            for v in [v for v in target_vars if v in ['X1', 'X2']]:
                syntax.append(f"GRAPH /HISTOGRAM={v}.")

        # --- بقية الأوامر ---
        elif any(w in q_low for w in ["mean", "median", "calculate"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(target_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS /FORMAT=NOTABLE.")

        elif "outliers" in q_low:
            syntax.append(f"EXAMINE VARIABLES={target_vars[0]} /PLOT=BOXPLOT /STATISTICS=DESCRIPTIVES /EXTREME(5).")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة تطبيق Streamlit
st.title("🧙‍♂️ محلل SPSS الاحترافي (بدون أخطاء)")
u_excel = st.file_uploader("Excel File", type=['xlsx', 'xls'])
u_word = st.file_uploader("Word File (.docx)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        final_code = master_spss_engine_v11(u_word)
        st.success("✅ تم توليد السينتاكس وتصحيح أوامر EXAMINE!")
        st.code(final_code, language='spss')
        st.download_button("تحميل الملف .sps", final_code, "SPSS_Scientific_Analysis.sps")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
