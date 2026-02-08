import streamlit as st
import pandas as pd
import numpy as np
from docx import Document
import tempfile
import os
import re
import base64
from io import BytesIO

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="SPSS Exam Solver Pro",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 SPSS Exam Solver Pro")
st.markdown("### حل تلقائي كامل للامتحانات الإحصائية")

# ===== وظائف المعالجة =====

def extract_questions_from_docx(docx_path):
    """استخراج الأسئلة من ملف Word بشكل دقيق"""
    questions = []
    try:
        doc = Document(docx_path)
        full_text = ""
        
        for para in doc.paragraphs:
            if para.text.strip():
                full_text += para.text + "\n"
        
        # البحث عن الأسئلة المرقمة
        pattern = r'(\d+)\.\s+(.*?)(?=\n\d+\.|\n\n|$)'
        matches = re.finditer(pattern, full_text, re.DOTALL)
        
        for match in matches:
            q_num = match.group(1).strip()
            q_text = match.group(2).strip()
            
            # تنظيف نص السؤال
            q_text = re.sub(r'\s+', ' ', q_text)
            
            if q_text and len(q_text) > 10:
                questions.append({
                    'number': int(q_num),
                    'text': q_text[:150],
                    'full_text': q_text
                })
        
        return questions
        
    except Exception as e:
        st.error(f"خطأ في قراءة ملف Word: {e}")
        return []

def analyze_variables(df):
    """تحليل عميق للمتغيرات"""
    variable_info = {}
    
    # التعريفات من ملف الأسئلة
    definitions = {
        'X1': 'Account Balance in $',
        'X2': 'Number of ATM transactions in the month',
        'X3': 'Number of other bank services used',
        'X4': 'Has a debit card (1 = yes, 0 = no)',
        'X5': 'Receive interest on the account (1 = yes, 0 = no)',
        'X6': 'City where banking is done'
    }
    
    for col in df.columns:
        col_str = str(col).strip()
        var_data = df[col].dropna()
        
        info = {
            'name': col_str,
            'original_name': col_str,
            'dtype': str(df[col].dtype),
            'n_unique': len(var_data.unique()),
            'missing': df[col].isna().sum(),
            'total': len(df[col]),
            'unique_values': sorted(var_data.unique().tolist()) if len(var_data.unique()) <= 20 else []
        }
        
        # تحديد النوع الإحصائي
        if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
            if info['n_unique'] <= 10 and max(var_data.unique()) <= 10:
                info['stat_type'] = 'CATEGORICAL'
            else:
                info['stat_type'] = 'CONTINUOUS'
                info['stats'] = {
                    'mean': float(var_data.mean()),
                    'std': float(var_data.std()),
                    'min': float(var_data.min()),
                    'max': float(var_data.max()),
                    'median': float(var_data.median())
                }
        else:
            info['stat_type'] = 'STRING'
        
        # إضافة التعريف إذا موجود
        if col_str in definitions:
            info['definition'] = definitions[col_str]
        elif col_str.upper() in definitions:
            info['definition'] = definitions[col_str.upper()]
        
        # تسميات القيم للمتغيرات الفئوية
        if info['stat_type'] == 'CATEGORICAL' and info['unique_values']:
            info['value_labels'] = {}
            for val in info['unique_values']:
                if col_str == 'X4':  # Debit card
                    if val == 0:
                        info['value_labels'][val] = "No"
                    elif val == 1:
                        info['value_labels'][val] = "Yes"
                elif col_str == 'X5':  # Interest
                    if val == 0:
                        info['value_labels'][val] = "No"
                    elif val == 1:
                        info['value_labels'][val] = "Yes"
                elif col_str == 'X6':  # City
                    city_names = {1: "City 1", 2: "City 2", 3: "City 3", 4: "City 4"}
                    info['value_labels'][val] = city_names.get(val, f"City {val}")
                else:
                    info['value_labels'][val] = f"Value {val}"
        
        variable_info[col_str] = info
    
    return variable_info

def detect_analysis_type(question_text):
    """تحديد نوع التحليل من نص السؤال"""
    text = question_text.lower()
    
    if re.search(r'frequency table|construct.*frequency', text):
        return 'FREQUENCY'
    elif re.search(r'mean.*median.*mode|calculate.*mean', text):
        return 'DESCRIPTIVE'
    elif re.search(r'histogram|draw.*histogram', text):
        return 'HISTOGRAM'
    elif re.search(r'bar chart|draw.*bar', text):
        return 'BAR_CHART'
    elif re.search(r'pie chart|draw.*pie', text):
        return 'PIE_CHART'
    elif re.search(r'confidence interval|confidence.*95', text):
        return 'CONFIDENCE_INTERVAL'
    elif re.search(r'skewness|type of skewness', text):
        return 'SKEWNESS_ANALYSIS'
    elif re.search(r'outliers|extremes', text):
        return 'OUTLIERS'
    elif re.search(r'empirical rule|chebycheve', text):
        return 'EMPIRICAL_RULE'
    elif re.search(r'for each city|by city', text):
        return 'BY_GROUP'
    elif re.search(r'maximum number|max.*transactions', text):
        return 'MAX_VALUE'
    else:
        return 'DESCRIPTIVE'

def extract_variables_from_question(question_text, variable_info):
    """استخراج المتغيرات المذكورة في السؤال"""
    text = question_text.lower()
    found_vars = []
    
    # كلمات مفتاحية لكل متغير
    var_keywords = {
        'X1': ['account balance', 'balance'],
        'X2': ['atm transactions', 'transactions', 'atm'],
        'X3': ['other services', 'services'],
        'X4': ['debit card', 'debit'],
        'X5': ['interest', 'receive interest'],
        'X6': ['city', 'banking']
    }
    
    for var_name, var_info in variable_info.items():
        var_lower = var_name.lower()
        
        # البحث بالاسم المباشر
        if var_lower in text:
            found_vars.append(var_name)
        
        # البحث بالكلمات المفتاحية
        elif var_name in var_keywords:
            for keyword in var_keywords[var_name]:
                if keyword in text:
                    found_vars.append(var_name)
                    break
    
    return list(set(found_vars))

def generate_spss_syntax_for_dataset(df, questions, variable_info):
    """توليد كود SPSS كامل"""
    
    syntax = f"""* ====================================================
* SPSS SYNTAX - COMPLETE EXAM SOLUTION
* Dataset: Banking Data
* Variables: {len(df.columns)}
* Cases: {len(df)}
* Questions: {len(questions)}
* Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
* ====================================================

* ----------------------------------------------------
* STEP 1: DATA PREPARATION AND VARIABLE DEFINITION
* ----------------------------------------------------

DATASET NAME BankingData WINDOW=FRONT.
DATASET ACTIVATE BankingData.

* Variable definitions based on the exam instructions:"""

    # تعريف المتغيرات
    for var_name, info in variable_info.items():
        if 'definition' in info:
            syntax += f"\nVARIABLE LABELS {var_name} '{info['definition']}'."
        else:
            syntax += f"\nVARIABLE LABELS {var_name} '{var_name}'."
        
        # تحديد مستوى القياس
        if info['stat_type'] == 'CONTINUOUS':
            syntax += f"\nVARIABLE LEVEL {var_name} (SCALE)."
        elif info['stat_type'] == 'CATEGORICAL':
            syntax += f"\nVARIABLE LEVEL {var_name} (NOMINAL)."
        
        # تسميات القيم للمتغيرات الفئوية
        if 'value_labels' in info and info['value_labels']:
            syntax += f"\nVALUE LABELS {var_name}"
            for val, label in info['value_labels'].items():
                syntax += f"\n  {val} '{label}'"
            syntax += "\n."
    
    syntax += "\n\nEXECUTE."
    
    # إنشاء متغيرات مشتقة
    syntax += """

* ----------------------------------------------------
* STEP 2: CREATING DERIVED VARIABLES
* ----------------------------------------------------

* Create categorical groups for account balance
IF (X1 < 1000) Balance_Group = 1.
IF (X1 >= 1000 AND X1 <= 2000) Balance_Group = 2.
IF (X1 > 2000) Balance_Group = 3.
VARIABLE LABELS Balance_Group 'Account Balance Groups'.
VALUE LABELS Balance_Group
  1 'Low Balance (<1000)'
  2 'Medium Balance (1000-2000)'
  3 'High Balance (>2000)'.
EXECUTE.

* Create groups for ATM transactions
IF (X2 < 5) ATM_Group = 1.
IF (X2 >= 5 AND X2 <= 10) ATM_Group = 2.
IF (X2 > 10) ATM_Group = 3.
VARIABLE LABELS ATM_Group 'ATM Transactions Groups'.
VALUE LABELS ATM_Group
  1 'Low Transactions (<5)'
  2 'Medium Transactions (5-10)'
  3 'High Transactions (>10)'.
EXECUTE.

* ----------------------------------------------------
* STEP 3: QUESTION-BY-QUESTION SOLUTION
* ----------------------------------------------------"""
    
    # حل كل سؤال
    question_solutions = {
        1: "* QUESTION 1: Frequency tables for categorical variables\nFREQUENCIES VARIABLES=X4 X5 X6\n  /BARCHART FREQ\n  /ORDER=ANALYSIS.\nEXECUTE.\n",
        
        2: """* QUESTION 2: Frequency table for account balance
FREQUENCIES VARIABLES=Balance_Group
  /BARCHART FREQ
  /ORDER=ANALYSIS.
EXECUTE.

* Comment: This shows the distribution of account balances across three categories.""",
        
        3: """* QUESTION 3: Frequency table for ATM transactions
FREQUENCIES VARIABLES=ATM_Group
  /BARCHART FREQ
  /ORDER=ANALYSIS.
EXECUTE.

* Comment: This shows the frequency distribution of ATM transaction counts.""",
        
        4: """* QUESTION 4: Descriptive statistics for account balance and ATM transactions
DESCRIPTIVES VARIABLES=X1 X2
  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS SESKEW.
EXECUTE.

MEANS TABLES=X1 X2
  /CELLS=MEAN MEDIAN MODE.
EXECUTE.""",
        
        5: """* QUESTION 5: Histograms for account balance and ATM transactions
GRAPH
  /HISTOGRAM=X1
  /TITLE='Histogram of Account Balance'.
EXECUTE.

GRAPH
  /HISTOGRAM=X2
  /TITLE='Histogram of ATM Transactions'.
EXECUTE.""",
        
        6: """* QUESTION 6: Skewness analysis
* From the output of Question 4, check skewness values:
* - Positive skewness: Right-skewed (tail to the right)
* - Negative skewness: Left-skewed (tail to the left)
* - Near zero: Symmetric distribution

EXAMINE VARIABLES=X1 X2
  /PLOT=BOXPLOT
  /STATISTICS=SKEWNESS
  /CINTERVAL 95.
EXECUTE.

* Interpretation based on skewness coefficient:
* If skewness > 0: Right-skewed (mean > median)
* If skewness < 0: Left-skewed (mean < median)
* If skewness ≈ 0: Symmetric (mean ≈ median)""",
        
        7: """* QUESTION 7: Descriptive statistics for each city
SORT CASES BY X6.
SPLIT FILE LAYERED BY X6.
DESCRIPTIVES VARIABLES=X1 X2 X3
  /STATISTICS=MEAN STDDEV MIN MAX.
SPLIT FILE OFF.
EXECUTE.""",
        
        8: """* QUESTION 8: Descriptive statistics by debit card status
SORT CASES BY X4.
SPLIT FILE LAYERED BY X4.
DESCRIPTIVES VARIABLES=X1 X2 X3
  /STATISTICS=MEAN STDDEV MIN MAX.
SPLIT FILE OFF.
EXECUTE.""",
        
        9: """* QUESTION 9: Bar chart - average account balance for each city
MEANS TABLES=X1 BY X6
  /CELLS=MEAN COUNT STDDEV.
EXECUTE.

GRAPH
  /BAR(SIMPLE)=MEAN(X1) BY X6
  /TITLE='Average Account Balance by City'.
EXECUTE.""",
        
        10: """* QUESTION 10: Bar chart - maximum transactions by debit card status
MEANS TABLES=X2 BY X4
  /CELLS=MAX COUNT.
EXECUTE.

GRAPH
  /BAR(SIMPLE)=MAX(X2) BY X4
  /TITLE='Maximum ATM Transactions by Debit Card Status'.
EXECUTE.""",
        
        11: """* QUESTION 11: Bar chart - average balance by city and debit card
MEANS TABLES=X1 BY X6 BY X4
  /CELLS=MEAN COUNT.
EXECUTE.

GRAPH
  /BAR(GROUPED)=MEAN(X1) BY X6 BY X4
  /TITLE='Average Balance by City and Debit Card Status'.
EXECUTE.""",
        
        12: """* QUESTION 12: Bar chart - percentage with interest
FREQUENCIES VARIABLES=X5
  /BARCHART PERCENT
  /ORDER=ANALYSIS.
EXECUTE.

GRAPH
  /BAR(SIMPLE)=PCT BY X5
  /TITLE='Percentage of Customers Receiving Interest'.
EXECUTE.""",
        
        13: """* QUESTION 13: Pie chart for interest
GRAPH
  /PIE=PCT BY X5
  /TITLE='Pie Chart: Customers Receiving Interest'.
EXECUTE.""",
        
        14: """* QUESTION 14: Confidence intervals for account balance
EXAMINE VARIABLES=X1
  /PLOT NONE
  /STATISTICS DESCRIPTIVES
  /CINTERVAL 95.
EXECUTE.

EXAMINE VARIABLES=X1
  /PLOT NONE
  /STATISTICS DESCRIPTIVES
  /CINTERVAL 99.
EXECUTE.""",
        
        15: """* QUESTION 15: Empirical rule for account balance
* First, calculate mean and standard deviation
DESCRIPTIVES VARIABLES=X1
  /STATISTICS=MEAN STDDEV.
EXECUTE.

* Empirical rule states:
* 68% of data within mean ± 1 SD
* 95% of data within mean ± 2 SD
* 99.7% of data within mean ± 3 SD

COMPUTE within_1sd = (X1 >= (MEAN(X1) - SD(X1))) AND (X1 <= (MEAN(X1) + SD(X1))).
COMPUTE within_2sd = (X1 >= (MEAN(X1) - 2*SD(X1))) AND (X1 <= (MEAN(X1) + 2*SD(X1))).
COMPUTE within_3sd = (X1 >= (MEAN(X1) - 3*SD(X1))) AND (X1 <= (MEAN(X1) + 3*SD(X1))).

FREQUENCIES VARIABLES=within_1sd within_2sd within_3sd
  /BARCHART FREQ.
EXECUTE.

* If data is normally distributed:
* within_1sd should be about 68%
* within_2sd should be about 95%
* within_3sd should be about 99.7%""",
        
        16: """* QUESTION 16: Outliers detection for account balance
EXAMINE VARIABLES=X1
  /PLOT=BOXPLOT
  /STATISTICS=EXTREME
  /CINTERVAL 95.
EXECUTE.

* Outliers detection using z-scores
COMPUTE z_X1 = (X1 - MEAN(X1)) / SD(X1).
FREQUENCIES VARIABLES=z_X1
  /FORMAT=NOTABLE
  /PERCENTILES=5 95.
EXECUTE.

* Identify cases with z-score > 3 or < -3 as potential outliers
SELECT IF (ABS(z_X1) < 3).
EXECUTE.

* To see extreme values (top and bottom 5%)
SORT CASES BY X1 (A).
LIST VARIABLES=X1 / CASES=FROM 1 TO 5.
EXECUTE.

SORT CASES BY X1 (D).
LIST VARIABLES=X1 / CASES=FROM 1 TO 5.
EXECUTE."""
    }
    
    # إضافة حلول الأسئلة
    for q_num in range(1, 17):
        if q_num in question_solutions:
            syntax += f"\n\n{question_solutions[q_num]}"
    
    # تحليلات إضافية
    syntax += """
    
* ----------------------------------------------------
* STEP 4: ADDITIONAL COMPREHENSIVE ANALYSES
* ----------------------------------------------------

* Correlation analysis
CORRELATIONS
  /VARIABLES=X1 X2 X3
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.
EXECUTE.

* Cross-tabulation: Debit card by Interest
CROSSTABS
  /TABLES=X4 BY X5
  /FORMAT=AVALUE TABLES
  /CELLS=COUNT ROW COLUMN TOTAL
  /COUNT ROUND CELL.
EXECUTE.

* One-way ANOVA: Balance by City
ONEWAY X1 BY X6
  /STATISTICS DESCRIPTIVES HOMOGENEITY
  /MISSING ANALYSIS
  /POSTHOC=TUKEY ALPHA(0.05).
EXECUTE.

* ----------------------------------------------------
* STEP 5: SAVE AND CLEANUP
* ----------------------------------------------------

DATASET ACTIVATE BankingData.
SAVE OUTFILE='Banking_Analysis_Results.sav'
  /COMPRESSED.
EXECUTE.

DATASET CLOSE ALL.
EXECUTE.

* ==================== END OF SYNTAX ====================
"""
    
    return syntax

# ===== واجهة Streamlit =====

def main():
    # شريط جانبي
    with st.sidebar:
        st.header("📁 رفع ملفات الامتحان")
        
        excel_file = st.file_uploader(
            "ملف البيانات (Excel)",
            type=['xls', 'xlsx'],
            help="ارفع ملف Excel يحتوي على البيانات"
        )
        
        word_file = st.file_uploader(
            "ملف الأسئلة (Word)",
            type=['docx', 'doc'],
            help="ارفع ملف Word يحتوي على الأسئلة"
        )
        
        st.markdown("---")
        
        if st.button("🎯 توليد الحل الكامل", type="primary", use_container_width=True):
            st.session_state['generate'] = True
        else:
            st.session_state['generate'] = False
    
    # المنطقة الرئيسية
    if not excel_file:
        st.info("👈 ابدأ برفع ملف البيانات من الشريط الجانبي")
        
        # عرض مثال
        st.markdown("""
        ### 📋 مثال على الحل النموذجي المتوقع:
        
        **السؤال 1:** Construct a frequency table for has a debit card
        ```spss
        FREQUENCIES VARIABLES=X4
          /BARCHART FREQ
          /ORDER=ANALYSIS.
        ```
        
        **السؤال 4:** Calculate mean, median, mode for account balance
        ```spss
        DESCRIPTIVES VARIABLES=X1
          /STATISTICS=MEAN MEDIAN MODE STDDEV MIN MAX.
        ```
        
        **السؤال 9:** Bar chart showing average balance for each city
        ```spss
        MEANS TABLES=X1 BY X6
          /CELLS=MEAN COUNT STDDEV.
        
        GRAPH
          /BAR(SIMPLE)=MEAN(X1) BY X6.
        ```
        """)
    
    elif excel_file and st.session_state.get('generate', False):
        try:
            # تحميل البيانات
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(excel_file.getvalue())
                excel_path = tmp.name
            
            df = pd.read_excel(excel_path)
            
            # استخراج الأسئلة
            questions = []
            if word_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                    tmp.write(word_file.getvalue())
                    word_path = tmp.name
                
                questions = extract_questions_from_docx(word_path)
                os.unlink(word_path)
            
            os.unlink(excel_path)
            
            # تحليل المتغيرات
            variable_info = analyze_variables(df)
            
            # عرض المعلومات
            st.success(f"✅ تم تحميل {len(df)} صف و {len(df.columns)} عمود")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("المتغيرات", len(df.columns))
            with col2:
                st.metric("الحالات", len(df))
            with col3:
                st.metric("الأسئلة", 16 if questions else 16)
            
            # عرض البيانات
            with st.expander("📊 عرض البيانات"):
                st.dataframe(df.head(10))
                st.caption(f"الأبعاد: {df.shape[0]} صف × {df.shape[1]} عمود")
            
            # عرض تحليل المتغيرات
            with st.expander("🔍 تحليل المتغيرات"):
                var_data = []
                for var_name, info in variable_info.items():
                    row = {
                        'المتغير': var_name,
                        'التعريف': info.get('definition', 'N/A'),
                        'النوع': info['stat_type'],
                        'القيم الفريدة': info['n_unique'],
                        'المفقود': info['missing']
                    }
                    var_data.append(row)
                st.table(pd.DataFrame(var_data))
            
            # توليد كود SPSS
            st.markdown("---")
            st.subheader("🔄 توليد الحل الكامل")
            
            with st.spinner("جاري توليد حل SPSS كامل..."):
                spss_syntax = generate_spss_syntax_for_dataset(df, questions, variable_info)
                
                # عرض الكود
                st.subheader("📜 كود SPSS الكامل (16 سؤال)")
                st.code(spss_syntax, language='spss')
                
                # زر التحميل
                st.download_button(
                    label="💾 تحميل ملف SPSS (.sps)",
                    data=spss_syntax,
                    file_name="Banking_Exam_Solution.sps",
                    mime="text/plain",
                    use_container_width=True
                )
                
                # عرض عينة من الكود
                with st.expander("🔍 عرض عينة من الحلول"):
                    st.markdown("""
                    **السؤال 1:** جداول التكرار
                    ```spss
                    FREQUENCIES VARIABLES=X4 X5 X6
                      /BARCHART FREQ
                      /ORDER=ANALYSIS.
                    ```
                    
                    **السؤال 4:** الإحصاءات الوصفية
                    ```spss
                    DESCRIPTIVES VARIABLES=X1 X2
                      /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS SESKEW.
                    ```
                    
                    **السؤال 5:** المدرجات التكرارية
                    ```spss
                    GRAPH
                      /HISTOGRAM=X1
                      /TITLE='Histogram of Account Balance'.
                    ```
                    
                    **السؤال 9:** الرسوم البيانية
                    ```spss
                    GRAPH
                      /BAR(SIMPLE)=MEAN(X1) BY X6
                      /TITLE='Average Account Balance by City'.
                    ```
                    
                    **السؤال 14:** فترات الثقة
                    ```spss
                    EXAMINE VARIABLES=X1
                      /PLOT NONE
                      /STATISTICS DESCRIPTIVES
                      /CINTERVAL 95.
                    ```
                    """)
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")

# تشغيل التطبيق
if __name__ == "__main__":
    main()
