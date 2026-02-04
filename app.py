import streamlit as st
import pandas as pd
import re
import math

# إعداد الصفحة لتظهر بشكل احترافي
st.set_page_config(page_title="MBA SPSS Master Solver", layout="wide", initial_sidebar_state="expanded")

st.title("🎓 المحرك الذكي لحل امتحانات SPSS")
st.markdown("""
هذا التطبيق مصمم لطلاب الـ MBA لتحويل أسئلة الامتحان وبيانات الإكسيل إلى كود **SPSS Syntax** جاهز للتنفيذ.
""")

# --- الجانب الأيسر لرفع الملفات ---
with st.sidebar:
    st.header("📂 خطوة 1: ارفع البيانات")
    uploaded_file = st.file_uploader("ارفع ملف (Excel) أو (CSV)", type=['xlsx', 'csv', 'xls'])
    
    st.header("⚙️ إعدادات المتغيرات")
    v_mapping = st.text_area("عريف المتغيرات (Mapping):", 
                             value="x1=gender\nx3=salary\nx4=region\nx5=happiness\nx9=age", 
                             height=150)

# --- الجانب الأيمن لإدخال الأسئلة ---
st.header("📝 خطوة 2: الصق أسئلة الامتحان")
questions_input = st.text_area("أدخل الأسئلة هنا (مثال: Draw a bar chart for average salary per region):", height=250)

if st.button("🚀 توليد الحل الإحصائي الكامل"):
    if questions_input:
        # 1. تحليل حجم البيانات لضبط القواعد (K-rule)
        n_size = 60 # افتراضي
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(('xlsx', 'xls')) else pd.read_csv(uploaded_file)
                n_size = len(df)
                st.success(f"✅ تم تحميل الملف بنجاح. حجم العينة: {n_size}")
            except Exception as e:
                st.error(f"خطأ في قراءة الملف: {e}")

        # 2. تحويل الـ Mapping إلى قاموس
        var_map = {}
        for line in v_mapping.split('\n'):
            if '=' in line:
                code, label = line.split('=')
                var_map[label.strip().lower()] = code.strip().upper()

        # 3. محرك ترجمة الأسئلة (Logic Engine)
        final_syntax = ["* Encoding: UTF-8.\nSET SEED=1234567.\n"]
        
        # تقسيم الأسئلة بناءً على الأرقام
        questions_list = re.split(r'(?:\n|^)\s*\d+[\.\)]', questions_input)
        
        for i, q in enumerate(questions_list):
            q_low = q.lower().strip()
            if not q_low: continue
            
            final_syntax.append(f"TITLE 'QUESTION {i}: Statistical Task'.")
            
            # منطق اختيار الاختبار (بناءً على ملف القواعد)
            if "regression" in q_low or "predict" in q_low:
                final_syntax.append("REGRESSION /STATISTICS COEFF OUTS R ANOVA /DEPENDENT X5 /METHOD=ENTER X1 X2 X3 X4 X6 X7 X8 X9 X10 X11 X12.")
            
            elif "frequency" in q_low or "classes" in q_low:
                if "salary" in q_low or "balance" in q_low:
                    final_syntax.append("RECODE X3 (LO THRU 30000=1) (30000.01 THRU 60000=2) (60000.01 THRU HI=3) INTO X3_cat.\nFREQUENCIES VARIABLES=X3_cat /FORMAT=AVALUE.")
                else:
                    final_syntax.append("FREQUENCIES VARIABLES=ALL /ORDER=ANALYSIS.")

            elif "bar chart" in q_low:
                if "average" in q_low: final_syntax.append("GRAPH /BAR(SIMPLE)=MEAN(X3) BY X4.")
                elif "max" in q_low: final_syntax.append("GRAPH /BAR(SIMPLE)=MAX(X2) BY X4.")
                else: final_syntax.append("GRAPH /BAR(SIMPLE)=COUNT BY X4.")

            elif "difference" in q_low or "compare" in q_low:
                final_syntax.append("ONEWAY X3 BY X4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

            elif "normality" in q_low or "confidence" in q_low:
                final_syntax.append("EXAMINE VARIABLES=X3 /PLOT NPPLOT /STATISTICS DESCRIPTIVES.\n* ECHO 'Sig > 0.05: Empirical Rule | Sig < 0.05: Chebyshev'.")

            else:
                final_syntax.append("DESCRIPTIVES VARIABLES=ALL /STATISTICS=MEAN STDDEV SKEWNESS.")
            
            final_syntax.append("EXECUTE.\n")

        # عرض النتيجة
        st.subheader("✅ كود SPSS Syntax المولد:")
        st.code("\n".join(final_syntax), language="spss")
        st.download_button("تحميل ملف الـ Syntax (.sps)", "\n".join(final_syntax), file_name="MBA_Solution.sps")
    else:
        st.warning("من فضلك أدخل الأسئلة أولاً.")
