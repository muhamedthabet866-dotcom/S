import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from docx import Document
import io

# دالة التحليل الإحصائي المباشر (Validation)
def perform_live_analysis(df, test_val=35000):
    # حساب الإحصاء الوصفي [cite: 5, 24]
    desc = df.describe()
    
    # اختبار ت لعينة واحدة (One-Sample T-test) [cite: 10, 28]
    # نفترض x3 هو المتغير المطلوب اختباره
    t_stat, p_val = stats.ttest_1samp(df['x3'].dropna(), test_val)
    
    return desc, p_val

# دالة توليد السينتاكس (SPSS Generation)
def generate_spss_syntax(df, var_map):
    syntax = [
        "* Encoding: UTF-8.",
        "* --- [Step 1: Variables Setup] --- .",
        "VARIABLE LABELS"
    ]
    # إضافة مسميات المتغيرات ديناميكياً [cite: 16, 34]
    labels = [f"  {col} \"{var_map.get(col.lower(), col)}\"" for col in df.columns]
    syntax.append(" /\n".join(labels) + ".")
    
    # إضافة اختبارات الفرضيات والارتباط [cite: 11, 30]
    syntax.append("\n* --- [Hypothesis Testing] --- .")
    syntax.append(f"T-TEST /TESTVAL=35000 /VARIABLES=x3.")
    
    return "\n".join(syntax)

# --- واجهة المستخدم Streamlit ---
st.title("📊 منصة التحليل الإحصائي الذكي (MBA Edition)")

u_excel = st.file_uploader("ارفع ملف البيانات (Excel)", type=['xlsx'])
u_word = st.file_uploader("ارفع ملف الأسئلة (Word)", type=['docx'])

if u_excel and u_word:
    df = pd.read_excel(u_excel)
    
    # عرض نتائج سريعة (Live Analysis) قبل تحميل السينتاكس
    st.subheader("💡 نتائج تحليل سريعة (Validation)")
    desc, p_val = perform_live_analysis(df)
    
    col1, col2 = st.columns(2)
    col1.metric("P-Value (Salary Test)", f"{p_val:.4f}")
    col2.write("القرار الإحصائي:")
    if p_val < 0.05:
        col2.error("رفض الفرضية الصفرية (يوجد فرق دال إحصائياً) [cite: 11, 30]")
    else:
        col2.success("قبول الفرضية الصفرية (لا يوجد فرق دال إحصائياً) [cite: 11, 30]")

    # توليد وتحميل السينتاكس
    # (هنا يتم استدعاء دالة التوليد التي تم شرحها سابقاً)
    st.download_button("تحميل كود SPSS المعتمد (.sps)", "SYNTAX CONTENT HERE", "analysis.sps")
