import streamlit as st
import pandas as pd
from docx import Document
import re
import io

def generate_professional_spss_v26(doc_upload, excel_vars):
    # قراءة محتوى ملف الوورد
    doc_bytes = doc_upload.read()
    try:
        doc = Document(io.BytesIO(doc_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except:
        paragraphs = re.findall(r'[ -~]{5,}', doc_bytes.decode('ascii', errors='ignore'))

    # تحديد أسماء المتغيرات من الإكسيل (أو افتراضية)
    v = {f"X{i+1}": excel_vars[i] if i < len(excel_vars) else f"VAR{i+1}" for i in range(10)}

    # بداية السينتاكس بتنسيق مطابلق لطلبك
    syntax = [
        "* Encoding: UTF-8.",
        "* -------------------------------------------------------------------------",
        "* MBA STATISTICAL ANALYSIS REPORT - SPSS SYNTAX v26",
        "* Formatting Instruction: When copying results to Word, use Times New Roman, Size 12.",
        "* -------------------------------------------------------------------------",
        "\n* [1] Setup Labels and Categories.",
        "VARIABLE LABELS"
    ]
    
    # توليد تسميات المتغيرات تلقائياً
    for key, name in v.items():
        syntax.append(f"    {key} \"{name}\"")
    syntax[-1] = syntax[-1] + "." # إضافة نقطة النهاية

    syntax.append("\nVALUE LABELS X4 0 \"No\" 1 \"Yes\"")
    syntax.append("    /X5 0 \"No\" 1 \"Yes\"")
    syntax.append("    /X6 1 \"City 1\" 2 \"City 2\" 3 \"City 3\" 4 \"City 4\".")

    # معالجة الأسئلة من الوورد وتحويلها إلى أوامر متوافقة مع المنهج
    for i, p in enumerate(paragraphs):
        p_low = p.lower()
        syntax.append(f"\n* --- Analysis for Question: {p} --- *")

        # [2] التكرارات (Categorical)
        if any(w in p_low for w in ["frequency", "table", "categories"]):
            syntax.append(f"* [{i+2}] Frequency Tables.")
            syntax.append(f"FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.")

        # [3] الإحصاء الوصفي والالتواء (Chapter 2)
        elif any(w in p_low for w in ["mean", "descriptive", "skewness"]):
            syntax.append(f"* [{i+2}] Descriptive Statistics & Normality.")
            syntax.append(f"FREQUENCIES VARIABLES=X1 X2\n  /FORMAT=NOTABLE\n  /STATISTICS=STDDEV VARIANCE RANGE MINIMUM MAXIMUM MEAN MEDIAN MODE SKEWNESS SESKEW.")
            syntax.append("* COMMENT: Check Skewness; if between -1 and +1, data is acceptable for parametric tests.")

        # [4] الرسوم البيانية المتطورة (Chapter 2 & 8)
        elif "bar chart" in p_low:
            if "city" in p_low and "debit" in p_low:
                syntax.append(f"GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 /TITLE=\"Avg Balance by City & Debit Card\".")
            else:
                syntax.append(f"GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 /TITLE=\"Mean Account Balance by City\".")
        
        elif "pie" in p_low:
            syntax.append(f"GRAPH /PIE=PCT BY X5 /TITLE=\"Distribution Percentage\".")

        # [5] فحص التوزيع والاعتلالات (Chapter 3 & 7)
        elif any(w in p_low for w in ["normality", "outliers", "examine"]):
            syntax.append(f"* [{i+2}] Inferential Statistics (Confidence Intervals & Outliers).")
            syntax.append(f"EXAMINE VARIABLES=X1\n  /PLOT BOXPLOT NPPLOT\n  /CINTERVAL 95\n  /STATISTICS DESCRIPTIVES.")

        # [6] اختبارات "ت" (Chapter 4 & 5)
        elif "independent" in p_low:
            syntax.append(f"T-TEST GROUPS=X4(0 1) /VARIABLES=X1 /CRITERIA=CI(.95).")
        
        elif "paired" in p_low or "before" in p_low:
            syntax.append(f"T-TEST PAIRS=X1 WITH X2 (PAIRED) /CRITERIA=CI(.95).")

        # [7] تحليل التباين والارتباط والانحدار (Chapters 6, 8, 9, 10)
        elif "anova" in p_low:
            syntax.append(f"ONEWAY X1 BY X6 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).")
        
        elif "correlation" in p_low:
            syntax.append(f"CORRELATIONS /VARIABLES=X1 X2 /PRINT=TWOTAIL /METHOD=PEARSON.")

        elif "regression" in p_low:
            syntax.append(f"REGRESSION /STATISTICS COEFF OUTS R ANOVA COLLIN TOL /DEPENDENT X1 /METHOD=ENTER X2.")

    syntax.append("\nEXECUTE.")
    return "\n".join(syntax)

# واجهة Streamlit
st.set_page_config(page_title="SPSS Syntax Pro Generator", layout="wide")
st.title("🛠️ محرك توليد التقارير الإحصائية (MBA Standard)")

u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls'])
u_word = st.file_uploader("2. ارفع ملف المتطلبات (Word)", type=['docx'])

if u_excel and u_word:
    try:
        df = pd.read_excel(u_excel)
        excel_vars = df.columns.tolist()
        
        final_syntax = generate_professional_spss_v26(u_word, excel_vars)
        
        st.success("✅ تم توليد السينتاكس بنجاح متوافق مع v26 ومعايير التقرير المطلوبة.")
        
        st.code(final_syntax, language='spss')
        
        st.download_button(
            label="تحميل ملف السينتاكس (.sps)",
            data=final_syntax,
            file_name="MBA_Analysis_Report.sps",
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"Error: {e}")
