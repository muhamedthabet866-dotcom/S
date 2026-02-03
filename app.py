import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from docx import Document
import io

# 1. دالة التحليل الحي الذكي (تتجنب KeyError)
def perform_live_analysis(df):
    # تحويل أسماء الأعمدة لحروف صغيرة للمطابقة
    df.columns = [c.lower() for c in df.columns]
    
    analysis_results = {}
    
    # البحث عن عمود يمثل "الراتب" أو "الرصيد" أو المتغير x3
    target_col = None
    for col in ['x3', 'salary', 'balance', 'area']:
        if col in df.columns:
            target_col = col
            break
            
    if target_col:
        # حساب الإحصاء الوصفي (Mean, Median, Skewness) [cite: 24, 34]
        analysis_results['mean'] = df[target_col].mean()
        analysis_results['median'] = df[target_col].median()
        analysis_results['skew'] = df[target_col].skew()
        
        # اختبار ت لعينة واحدة (قيمة افتراضية 35000 أو 600) 
        test_val = 35000 if 'salary' in target_col or 'x3' in target_col else 600
        t_stat, p_val = stats.ttest_1samp(df[target_col].dropna(), test_val)
        analysis_results['p_val'] = p_val
    
    return analysis_results

# --- واجهة المستخدم ---
st.title("📊 نظام التحليل الإحصائي الشامل (v5)")

u_excel = st.file_uploader("ارفع ملف الإكسيل", type=['xlsx', 'xls', 'csv'])

if u_excel:
    # قراءة الملف مع معالجة النوع (CSV أو Excel)
    if u_excel.name.endswith('.csv'):
        df = pd.read_csv(u_excel)
    else:
        df = pd.read_excel(u_excel)
        
    st.write("✅ تم تحميل الأعمدة التالية:", df.columns.tolist())

    # إجراء التحليل المباشر
    try:
        results = perform_live_analysis(df)
        
        if results:
            st.subheader("💡 المعاينة الإحصائية السريعة")
            col1, col2, col3 = st.columns(3)
            col1.metric("المتوسط (Mean)", f"{results['mean']:.2f}")
            col2.metric("الوسيط (Median)", f"{results['median']:.2f}")
            col3.metric("P-Value", f"{results['p_val']:.4f}")
            
            # قرار اختبار الفرضية [cite: 19, 30]
            if results['p_val'] < 0.05:
                st.error("القرار: نرفض الفرضية الصفرية (يوجد فرق دال إحصائياً)")
            else:
                st.success("القرار: نقبل الفرضية الصفرية (لا يوجد فرق دال)")
        else:
            st.warning("لم يتم العثور على أعمدة متوافقة للتحليل الآلي (x3 أو Salary).")
            
    except Exception as e:
        st.error(f"حدث خطأ أثناء التحليل: {e}")
