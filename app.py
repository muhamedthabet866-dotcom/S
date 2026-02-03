import streamlit as st
import pandas as pd
from docx import Document
import re

def master_spss_engine(doc_file, df_cols):
    doc = Document(doc_file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 5]
    
    # 1. بناء القاموس الذكي للمتغيرات (Mapping)
    mapping = {}
    for p in paragraphs:
        # البحث عن نمط X1 = Label
        match = re.search(r"(X\d+)\s*=\s*([^(\n\r]+)", p, re.IGNORECASE)
        if match:
            v_name = match.group(1).upper()
            v_label = match.group(2).strip()
            # استخراج القيم (1=yes, 0=no)
            vals = re.findall(r"(\d+)\s*=\s*([a-zA-Zأ-ي]+)", p)
            mapping[v_name] = {"label": v_label, "values": vals}

    syntax = ["* --- Final Scientific Syntax for SPSS v26 (Fixing Error 17807) --- *.\n"]
    
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
        # تخطي أسطر التعريفات
        if re.search(r"X\d+\s*=", p): continue
        
        # البحث عن المتغيرات المذكورة في السؤال (بالرمز أو بالاسم)
        found_vars = []
        for v_code, v_info in mapping.items():
            clean_label = v_info['label'].lower()
            if v_code.lower() in p_low or (len(clean_label) > 4 and clean_label[:15] in p_low):
                found_vars.append(v_code)
        
        if not found_vars: continue

        syntax.append(f"\n* QUESTION: {p}.")
        
        # --- منطق الأوامر المتوافق مع v26 ---

        # أ. الجداول التكرارية
        if "frequency table" in p_low:
            syntax.append(f"FREQUENCIES VARIABLES={' '.join(found_vars)} /ORDER=ANALYSIS.")

        # ب. الإحصاء الوصفي (Mean, Std Dev, etc.)
        elif any(w in p_low for w in ["mean", "median", "calculate", "descriptive"]):
            # التحقق من وجود "for each" (طلب تقسيم البيانات)
            if "for each" in p_low or "per" in p_low:
                split_var = found_vars[-1] # عادة آخر متغير هو المتغير التصنيفي (مثل المدينة)
                analysis_vars = [v for v in found_vars if v != split_var]
                syntax.append(f"SORT CASES BY {split_var}.\nSPLIT FILE LAYERED BY {split_var}.")
                syntax.append(f"DESCRIPTIVES VARIABLES={' '.join(analysis_vars)} /STATISTICS=MEAN STDDEV MIN MAX SKEWNESS.")
                syntax.append("SPLIT FILE OFF.")
            else:
                syntax.append(f"DESCRIPTIVES VARIABLES={' '.join(found_vars)} /STATISTICS=MEAN STDDEV MIN MAX SKEWNESS.")

        # ج. الرسوم البيانية (التصحيح النهائي لخطأ 17807)
        elif "histogram" in p_low:
            for v in found_vars: syntax.append(f"GRAPH /HISTOGRAM={v}.")

        elif "bar chart" in p_low:
            if "average" in p_low or "mean" in p_low:
                if len(found_vars) >= 3: # طلب Clustered Bar (بناءً على متغيرين)
                    syntax.append(f"GRAPH /BAR(GROUPED)=MEAN({found_vars[0]}) BY {found_vars[1]} BY {found_vars[2]}.")
                elif len(found_vars) == 2: # Bar بسيط بمتوسط
                    syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN({found_vars[0]}) BY {found_vars[1]}.")
            elif "percentage" in p_low:
                syntax.append(f"GRAPH /BAR(SIMPLE)=PCT BY {found_vars[0]}.")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=COUNT BY {found_vars[0]}.")

        elif "pie chart" in p_low:
            syntax.append(f"GRAPH /PIE=COUNT BY {found_vars[0]}.")

        # د. اختبارات الفرضيات و فترات الثقة
        elif "confidence interval" in p_low:
            syntax.append(f"EXAMINE VARIABLES={' '.join(found_vars)} /PLOT NONE /STATISTICS DESCRIPTIVES /CINTERVAL 95.")

        elif "test" in p_low and "hypothesis" in p_low:
            if len(found_vars) >= 2:
                syntax.append(f"T-TEST GROUPS={found_vars[1]}(0 1) /VARIABLES={found_vars[0]}.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة المستخدم
st.set_page_config(page_title="SPSS Master", layout="wide")
st.title("🏆 المولد الإحصائي الذكي (v26 Professional)")

u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls'])
u_word = st.file_uploader("ارفع ملف الوورد (.docx)", type=['docx'])

if u_excel and u_word:
    df = pd.read_excel(u_excel)
    syntax_result = master_spss_engine(u_word, df.columns)
    st.success("تم تحليل الأسئلة علمياً وتصحيح أوامر الرسم البياني!")
    st.code(syntax_result, language='spss')
    st.download_button("تحميل السينتاكس النهائي", syntax_result, "SPSS_Final_Ready.sps")
