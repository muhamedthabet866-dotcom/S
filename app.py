import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# دالة ذكية لاستخراج النصوص حتى من الملفات القديمة أو التالفة
def extract_text_from_upload(doc_upload):
    doc_bytes = doc_upload.read()
    try:
        # المحاولة الأولى: باستخدام مكتبة Document للملفات الحديثة docx
        doc = Document(io.BytesIO(doc_bytes))
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        # المحاولة الثانية: سحب النصوص الخام للملفات القديمة doc
        return " ".join(re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore')))

def master_spss_engine_v20(word_file):
    text = extract_text_from_upload(word_file)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # بناء خريطة المتغيرات X1-X12
    mapping = {}
    var_matches = re.findall(r"([Xx]\d+)\s*=\s*([^(\n\r.]+)", text, re.IGNORECASE)
    for v_name, v_label in var_matches:
        mapping[v_name.upper()] = v_label.strip()

    syntax = ["* --- Final Scientific Solution for SPSS v26 (Universal DS 1,3,4) --- *.\n"]
    for var, lbl in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{lbl}'.")
    
    # تعريف القيم الافتراضية للنماذج المشهورة
    syntax.append("VALUE LABELS X4 0 'No' 1 'Yes' /X5 0 'No' 1 'Yes' /X11 1 'Far East' 2 'Europe' 3 'North America'.")
    syntax.append("SET DECIMAL=DOT.\n")

    for line in lines:
        l_low = line.lower()
        if re.search(r"X\d+\s*=", line): continue
        
        # البحث عن المتغيرات المرتبطة بالسؤال
        found_vars = [v for v in mapping.keys() if v in line.upper() or mapping[v].lower()[:10] in l_low]
        # تعزيز الربط للرصيد والراتب والسعادة (المتكررة في النماذج)
        if "balance" in l_low: found_vars.append("X1")
        if "salary" in l_low: found_vars.append("X3")
        if "happiness" in l_low: found_vars.append("X5")
        found_vars = list(dict.fromkeys(found_vars))

        if not found_vars and "normality" not in l_low and "regression" not in l_low: continue
        
        syntax.append(f"\n* QUESTION: {line}.")

        # 1. فترات الثقة (95% و 99% - طلب المهندس محمد)
        if "confidence interval" in l_low:
            for val in ["95", "99"]:
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars) if found_vars else 'X1'} /STATISTICS DESCRIPTIVES /CINTERVAL {val} /PLOT NONE.")

        # 2. تصحيح الرسوم البيانية (منع الخطأ 701)
        elif "bar chart" in l_low:
            stat = "MEAN" if "average" in l_low else "MAX" if "maximum" in l_low else "PCT" if "percentage" in l_low else "COUNT"
            if len(found_vars) >= 2:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({found_vars[0]}) BY {found_vars[1]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {found_vars[0] if found_vars else 'X1'}.")

        # 3. الانحدار والارتباط (نماذج DS 3, 4)
        elif "regression" in l_low or "y = f(" in l_low:
            syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X5 /METHOD=ENTER X1 X2 X3 X4 X6 X7 X8 X9 X10 X11 X12.")
        elif "correlation" in l_low:
            syntax.append(f"CORRELATIONS /VARIABLES={' '.join(found_vars[:2])} /PRINT=TWOTAIL NOSIG.")

        # 4. التحليلات المتقدمة (Classes & K-rule)
        elif "classes" in l_low or "k rule" in l_low:
            target = "X1" if "balance" in l_low else "X3" if "salary" in l_low else found_vars[0]
            syntax.append(f"RECODE {target} (LO thru HI=COPY) INTO {target}_Classes.\nFREQUENCIES VARIABLES={target}_Classes.")

        # 5. التوزيع الطبيعي والقيم الشاذة
        elif "normality" in l_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.")
        elif "outliers" in l_low:
            syntax.append(f"EXAMINE VARIABLES={found_vars[0] if found_vars else 'X1'} /PLOT BOXPLOT /STATISTICS DESCRIPTIVES /EXTREME(5).")

        # 6. الوصف العام والتقسيم
        elif "for each" in l_low or "split" in l_low:
            split_v = found_vars[-1] if found_vars else "X6"
            syntax.append(f"SORT CASES BY {split_v}.\nSPLIT FILE SEPARATE BY {split_v}.\nFREQUENCIES VARIABLES={' '.join(found_vars[:-1]) if len(found_vars)>1 else 'X1 X2'} /STATISTICS=MEAN MEDIAN MODE.\nSPLIT FILE OFF.")
        elif any(w in l_low for w in ["mean", "median", "frequency table"]):
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN MEDIAN MODE STDDEV SKEWNESS.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Master Engine", layout="wide")
st.title("📊 المحلل الإحصائي الشامل للمهندس محمد (DS 1, 3, 4)")

u_excel = st.file_uploader("1. ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])
u_word = st.file_uploader("2. ارفع ملف الوورد (الأسئلة)", type=['docx', 'doc'])

if u_excel and u_word:
    try:
        # قراءة البيانات للمعاينة فقط
        df = pd.read_csv(u_excel) if u_excel.name.endswith('.csv') else pd.read_excel(u_excel)
        st.success(f"✅ تم تحميل البيانات بنجاح ({len(df)} سجل).")
        
        final_syntax = master_spss_engine_v20(u_word)
        st.subheader("السينتاكس الناتج:")
        st.code(final_syntax, language='spss')
        
        st.download_button("تحميل السينتاكس النهائي (.sps)", final_syntax, "Final_Analysis_Ready.sps")
    except Exception as e:
        st.error(f"حدث خطأ في النظام: {e}")
