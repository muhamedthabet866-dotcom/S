import streamlit as st
import pandas as pd
from docx import Document
import re

def master_spss_engine_v3(doc_file):
    doc = Document(doc_file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 3]
    
    # 1. بناء القاموس الذكي للمتغيرات (Mapping)
    mapping = {}
    for p in paragraphs:
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            # استخراج القيم (1=yes, 0=no)
            vals = re.findall(r"(\d+)\s*=\s*([a-zA-Zأ-ي]+)", p)
            mapping[v_name] = {"label": v_label, "values": vals}

    syntax = ["* --- Final Scientific Syntax (Optimized for SPSS v26) --- *.\n"]
    
    # تعريف التسميات (Labels)
    for var, info in mapping.items():
        syntax.append(f"VARIABLE LABELS {var} '{info['label']}'.")
        if info['values']:
            syntax.append(f"VALUE LABELS {var}")
            for val, txt in info['values']: syntax.append(f"  {val} '{txt}'")
            syntax.append(".")

    syntax.append("\nSET DECIMAL=DOT.\n")

    # 2. تحليل الأسئلة وترجمتها لأوامر احترافية
    for p in paragraphs:
        p_low = p.lower()
        if re.search(r"X\d+\s*=", p): continue # تخطي أسطر التعريف
        
        # البحث عن المتغيرات المذكورة
        found_vars = []
        for v_code, v_info in mapping.items():
            clean_label = v_info['label'].lower()
            if v_code.lower() in p_low or (len(clean_label) > 4 and clean_label[:15] in p_low):
                found_vars.append(v_code)
        
        if not found_vars: continue
        syntax.append(f"\n* QUESTION: {p}.")

        # --- منطق الأوامر المتوافق علمياً ---

        # أ. الجداول التكرارية
        if "frequency table" in p_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")

        # ب. الإحصاء الوصفي (Mean, Std Dev, etc.)
        elif any(w in p_low for w in ["mean", "median", "calculate", "descriptive"]):
            if "for each" in p_low or "per" in p_low:
                split_var = found_vars[-1]
                analysis_vars = [v for v in found_vars if v != split_var]
                syntax.append(f"SORT CASES BY {split_var}.\nSPLIT FILE LAYERED BY {split_var}.")
                syntax.append(f"DESCRIPTIVES VARIABLES={' '.join(analysis_vars)} /STATISTICS=MEAN STDDEV MIN MAX SKEWNESS.")
                syntax.append("SPLIT FILE OFF.")
            else:
                syntax.append(f"DESCRIPTIVES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN STDDEV MIN MAX SKEWNESS.")

        # ج. الرسوم البيانية (حل نهائي لخطأ 17807)
        elif "histogram" in p_low:
            for v in found_vars: syntax.append(f"GRAPH /HISTOGRAM={v}.")

        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low or "maximum" in p_low:
                stat = "MEAN" if "average" in p_low or "mean" in p_low else "MAX"
                if len(found_vars) >= 2:
                    syntax.append(f"GRAPH /BAR(SIMPLE)={stat}({found_vars[0]}) BY {found_vars[1]}.")
                else:
                    syntax.append(f"GRAPH /BAR(SIMPLE)={stat} BY {found_vars[0]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        # د. فترات الثقة (الحل المنفصل 95% و 99%)
        elif "confidence interval" in p_low:
            intervals = re.findall(r"(\d+)%", p_low)
            if not intervals: intervals = ["95"] # الافتراضي إذا لم يحدد
            for interval in intervals:
                syntax.append(f"* Confidence Interval {interval}% Calculation.")
                syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL {interval}.")

        # هـ. اختبارات النورمالتي (Normality/P-P/Q-Q)
        elif "normality" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NPPLOT /STATISTICS NONE.")

        # و. اختبارات الفرضيات (T-Test)
        elif "test" in p_low and "hypothesis" in p_low:
            if len(found_vars) >= 2:
                syntax.append(f"T-TEST GROUPS={found_vars[1]}(0 1) /VARIABLES={found_vars[0]}.")
            else:
                # One sample t-test
                val = re.findall(r'\d+', p)
                test_val = val[0] if val else "0"
                syntax.append(f"T-TEST /TESTVAL={test_val} /VARIABLES={found_vars[0]}.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة المستخدم
st.set_page_config(page_title="SPSS Pro", layout="wide")
st.title("🏆 المحلل الذكي: Excel to SPSS v26")
st.markdown("تم تحديث النظام ليدعم فترات الثقة المنفصلة وتصحيح أوامر الرسم البياني.")

u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    df = pd.read_excel(u_excel)
    syntax_result = master_spss_engine_v3(up_word)
    st.success("تم توليد السينتاكس بنجاح!")
    st.code(syntax_result, language='spss')
    st.download_button("تحميل الملف النهائي", syntax_result, "SPSS_Final_Solution.sps")
