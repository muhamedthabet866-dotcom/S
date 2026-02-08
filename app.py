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
        
        # قراءة كل الفقرات
        paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        full_text = "\n".join(paragraphs)
        
        # البحث عن الأسئلة المرقمة
        # نمط 1: "1. نص السؤال"
        # نمط 2: "1) نص السؤال"
        # نمط 3: الأسئلة داخل النص
        patterns = [
            r'(\d+)[\.\)]\s*(.*?)(?=\d+[\.\)]|$)',  # الأسئلة المرقمة
            r'(\d+)\.\s*(.*?)(?=\n\d+\.|\n\n|$)',   # الأسئلة مع نقاط
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, full_text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                q_num = match.group(1).strip()
                q_text = match.group(2).strip()
                
                # تنظيف نص السؤال
                q_text = re.sub(r'\s+', ' ', q_text)
                
                if q_text and len(q_text) > 5:
                    questions.append({
                        'number': int(q_num),
                        'text': q_text[:200],  # أول 200 حرف فقط
                        'full_text': q_text
                    })
        
        # إذا لم نجد أسئلة مرقمة، نبحث عن كلمات مفتاحية
        if not questions:
            for para in paragraphs:
                if len(para) > 20:
                    # تحقق إذا كان يحتوي على كلمات إحصائية
                    stats_keywords = ['construct', 'calculate', 'draw', 'test', 'find', 
                                     'جدول', 'احسب', 'ارسم', 'اختبار', 'أوجد']
                    if any(keyword in para.lower() for keyword in stats_keywords):
                        questions.append({
                            'number': len(questions) + 1,
                            'text': para[:150],
                            'full_text': para
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
                        info['value_labels'][val] = "No debit card"
                    elif val == 1:
                        info['value_labels'][val] = "Has debit card"
                elif col_str == 'X5':  # Interest
                    if val == 0:
                        info['value_labels'][val] = "No interest"
                    elif val == 1:
                        info['value_labels'][val] = "Receives interest"
                elif col_str == 'X6':  # City
                    city_names = {1: "City A", 2: "City B", 3: "City C", 4: "City D"}
                    info['value_labels'][val] = city_names.get(val, f"City {val}")
                else:
                    info['value_labels'][val] = f"Value {val}"
        
        variable_info[col_str] = info
    
    return variable_info

def detect_analysis_type(question_text):
    """تحديد نوع التحليل من نص السؤال"""
    text = question_text.lower()
    
    if re.search(r'frequency table|جدول تكراري|construct.*frequency', text):
        return 'FREQUENCY'
    elif re.search(r'mean.*median.*mode|المتوسط.*الوسيط|calculate.*mean', text):
        return 'DESCRIPTIVE'
    elif re.search(r'histogram|مدرج تكراري|draw.*histogram', text):
        return 'HISTOGRAM'
    elif re.search(r'bar chart|رسم بياني عمودي|draw.*bar', text):
        return 'BAR_CHART'
    elif re.search(r'pie chart|رسم دائري|draw.*pie', text):
        return 'PIE_CHART'
    elif re.search(r'confidence interval|فترة ثقة|confidence.*95%', text):
        return 'CONFIDENCE_INTERVAL'
    elif re.search(r'skewness|انحراف|type of skewness', text):
        return 'SKEWNESS_ANALYSIS'
    elif re.search(r'outliers|extremes|القيم المتطرفة', text):
        return 'OUTLIERS'
    elif re.search(r'empirical rule|chebycheve|قاعدة', text):
        return 'EMPIRICAL_RULE'
    elif re.search(r'for each city|لكل مدينة', text):
        return 'BY_GROUP'
    else:
        return 'DESCRIPTIVE'

def extract_variables_from_question(question_text, variable_info):
    """استخراج المتغيرات المذكورة في السؤال"""
    text = question_text.lower()
    found_vars = []
    
    # كلمات مفتاحية لكل متغير
    var_keywords = {
        'X1': ['account balance', 'balance', 'x1', 'رصيد'],
        'X2': ['atm transactions', 'transactions', 'x2', 'معاملات'],
        'X3': ['other services', 'services', 'x3', 'خدمات'],
        'X4': ['debit card', 'debit', 'x4', 'بطاقة'],
        'X5': ['interest', 'receive interest', 'x5', 'فائدة'],
        'X6': ['city', 'banking done', 'x6', 'مدينة']
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
        
        # البحث بالتعريف
        if 'definition' in var_info:
            if any(word in var_info['definition'].lower() for word in text.split()):
                found_vars.append(var_name)
    
    return list(set(found_vars))

def generate_spss_syntax_for_dataset(df, questions, variable_info):
    """توليد كود SPSS كامل"""
    
    syntax = f"""* ====================================================
* SPSS SYNTAX - COMPLETE EXAM SOLUTION
* Dataset: Data set 1
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

* Create categorical groups for account balance (for frequency tables)
RECODE X1 (Lowest thru 1000=1) (1000 thru 2000=2) (2000 thru Highest=3) INTO Balance_Group.
VARIABLE LABELS Balance_Group 'Account Balance Groups'.
VALUE LABELS Balance_Group
  1 'Low Balance (<1000)'
  2 'Medium Balance (1000-2000)'
  3 'High Balance (>2000)'.
EXECUTE.

* Create groups for ATM transactions
RECODE X2 (Lowest thru 5=1) (5 thru 10=2) (10 thru Highest=3) INTO ATM_Group.
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
    for q in sorted(questions, key=lambda x: x['number']):
        syntax += f"\n\n* QUESTION {q['number']}: {q['text'][:100]}..."
        
        analysis_type = detect_analysis_type(q['full_text'])
        variables = extract_variables_from_question(q['full_text'], variable_info)
        
        if not variables:
            # استخدام المتغيرات المناسبة حسب السؤال
            if 'account balance' in q['full_text'].lower():
                variables = ['X1']
            elif 'atm' in q['full_text'].lower():
                variables = ['X2']
            elif 'debit card' in q['full_text'].lower():
                variables = ['X4']
            elif 'interest' in q['full_text'].lower():
                variables = ['X5']
            elif 'city' in q['full_text'].lower():
                variables = ['X6']
            else:
                variables = ['X1', 'X2']  # إفتراضي
        
        syntax += f"\n* Analysis Type: {analysis_type}"
        syntax += f"\n* Variables: {', '.join(variables)}"
        
        # توليد الكود المناسب
        syntax += generate_analysis_code(analysis_type, variables, q, variable_info)
    
    # تحليلات إضافية
    syntax += """
    
* ----------------------------------------------------
* STEP 4: ADDITIONAL COMPREHENSIVE ANALYSES
* ----------------------------------------------------

* Comprehensive descriptive statistics
DESCRIPTIVES VARIABLES=X1 X2 X3
  /SAVE
  /STATISTICS=MEAN STDDEV MIN MAX SEMEAN KURTOSIS SKEWNESS.

* Correlation analysis
CORRELATIONS
  /VARIABLES=X1 X2 X3
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.

* Normality tests
EXAMINE VARIABLES=X1 X2
  /PLOT HISTOGRAM NPPLOT
  /COMPARE GROUP
  /STATISTICS DESCRIPTIVES
  /CINTERVAL 95
  /MISSING LISTWISE
  /NOTOTAL.

* ----------------------------------------------------
* STEP 5: SAVE AND CLEANUP
* ----------------------------------------------------

SAVE OUTFILE='Banking_Analysis_Complete.sav'
  /COMPRESSED.
DATASET CLOSE ALL.
EXECUTE.

* ==================== END OF SYNTAX ====================
"""
    
    return syntax

def generate_analysis_code(analysis_type, variables, question, variable_info):
    """توليد كود تحليل محدد"""
    code = ""
    
    if analysis_type == 'FREQUENCY':
        code += f"\nFREQUENCIES VARIABLES={' '.join(variables)}"
        code += "\n  /FORMAT=NOTABLE"
        if 'X4' in variables or 'X5' in variables or 'X6' in variables:
            code += "\n  /BARCHART FREQ"
            code += "\n  /PIECHART FREQ"
        code += "\n  /ORDER=ANALYSIS."
    
    elif analysis_type == 'DESCRIPTIVE':
        code += f"\nDESCRIPTIVES VARIABLES={' '.join(variables)}"
        code += "\n  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS SESKEW."
        
        # إذا كان السؤال يتعلق بمجموعات
        if 'for each' in question['full_text'].lower() or 'لكل' in question['full_text'].lower():
            group_var = 'X6' if 'city' in question['full_text'].lower() else 'X4'
            code += f"\n\nSORT CASES BY {group_var}."
            code += f"\nSPLIT FILE LAYERED BY {group_var}."
            code += f"\nDESCRIPTIVES VARIABLES={' '.join([v for v in variables if v != group_var])}"
            code += "\n  /STATISTICS=MEAN STDDEV MIN MAX."
            code += "\nSPLIT FILE OFF."
    
    elif analysis_type == 'HISTOGRAM':
        for var in variables:
            if variable_info[var]['stat_type'] == 'CONTINUOUS':
                code += f"\nGRAPH"
                code += f"\n  /HISTOGRAM={var}"
                code += f"\n  /NORMAL"
                code += f"\n  /TITLE='Histogram of {var}'."
    
    elif analysis_type == 'BAR_CHART':
        if len(variables) >= 2:
            # رسم بياني مجمع
            code += f"\nGRAPH"
            code += f"\n  /BAR(GROUPED)=MEAN({variables[1]}) BY {variables[0]}"
            code += "\n  /MISSING=REPORT"
            code += f"\n  /TITLE='Bar Chart: {variables[1]} by {variables[0]}'."
        else:
            code += f"\nGRAPH"
            code += f"\n  /BAR(SIMPLE)=COUNT BY {variables[0]}"
            code += "\n  /MISSING=REPORT"
            code += f"\n  /TITLE='Bar Chart of {variables[0]}'."
    
    elif analysis_type == 'PIE_CHART':
        code += f"\nGRAPH"
        code += f"\n  /PIE=PCT BY {variables[0]}"
        code += "\n  /MISSING=REPORT"
        code += f"\n  /TITLE='Pie Chart of {variables[0]}'."
    
    elif analysis_type == 'CONFIDENCE_INTERVAL':
        for var in variables:
            if variable_info[var]['stat_type'] == 'CONTINUOUS':
                code += f"\nEXAMINE VARIABLES={var}"
                code += "\n  /PLOT NONE"
                code += "\n  /STATISTICS DESCRIPTIVES"
                code += "\n  /CINTERVAL 95 99"
                code += "\n  /MISSING LISTWISE."
    
    elif analysis_type == 'OUTLIERS':
        for var in variables:
            if variable_info[var]['stat_type'] == 'CONTINUOUS':
                code += f"\nEXAMINE VARIABLES={var}"
                code += "\n  /PLOT=BOXPLOT"
                code += "\n  /COMPARE VARIABLE"
                code += "\n  /STATISTICS=EXTREME"
                code += "\n  /CINTERVAL 95"
                code += "\n  /MISSING LISTWISE"
                code += "\n  /NOTOTAL."
    
    elif analysis_type == 'SKEWNESS_ANALYSIS':
        for var in variables:
            if variable_info[var]['stat_type'] == 'CONTINUOUS':
                code += f"\nEXAMINE VARIABLES={var}"
                code += "\n  /PLOT=BOXPLOT HISTOGRAM NPPLOT"
                code += "\n  /COMPARE VARIABLE"
                code += "\n  /STATISTICS=SKEWNESS"
                code += "\n  /CINTERVAL 95"
                code += "\n  /MISSING LISTWISE"
                code += "\n  /NOTOTAL."
    
    elif analysis_type == 'EMPIRICAL_RULE':
        for var in variables:
            if variable_info[var]['stat_type'] == 'CONTINUOUS':
                code += f"\n* Empirical Rule analysis for {var}"
                code += f"\nCOMPUTE {var}_Z = ({var} - MEAN({var})) / SD({var})."
                code += f"\nFREQUENCIES VARIABLES={var}_Z"
                code += f"\n  /FORMAT=NOTABLE"
                code += f"\n  /HISTOGRAM NORMAL"
                code += f"\n  /PERCENTILES=2.5 16 50 84 97.5."
    
    else:
        code += f"\nDESCRIPTIVES VARIABLES={' '.join(variables[:3])}"
        code += "\n  /STATISTICS=MEAN STDDEV MIN MAX."
    
    code += "\nEXECUTE."
    return code

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
                st.metric("الأسئلة", len(questions))
            
            # عرض البيانات
            with st.expander("📊 عرض البيانات"):
                st.dataframe(df.head(10))
            
            # عرض تحليل المتغيرات
            with st.expander("🔍 تحليل المتغيرات"):
                for var_name, info in variable_info.items():
                    st.markdown(f"**{var_name}**: {info.get('definition', 'No definition')}")
                    st.markdown(f"- النوع: {info['stat_type']}")
                    st.markdown(f"- القيم الفريدة: {info['n_unique']}")
                    if info['stat_type'] == 'CONTINUOUS' and 'stats' in info:
                        st.markdown(f"- المتوسط: {info['stats']['mean']:.2f}")
                        st.markdown(f"- الانحراف المعياري: {info['stats']['std']:.2f}")
                    st.markdown("---")
            
            # عرض الأسئلة المستخرجة
            with st.expander("📝 الأسئلة المستخرجة"):
                if questions:
                    for q in questions:
                        st.markdown(f"**{q['number']}. {q['text']}**")
                        analysis_type = detect_analysis_type(q['full_text'])
                        variables = extract_variables_from_question(q['full_text'], variable_info)
                        st.caption(f"نوع التحليل: {analysis_type} | المتغيرات: {variables}")
                else:
                    st.warning("لم يتم العثور على أسئلة مرقمة. جاري إنشاء أسئلة افتراضية...")
                    # إنشاء أسئلة افتراضية
                    questions = [
                        {'number': 1, 'text': 'Construct frequency tables for categorical variables', 'full_text': 'Construct frequency tables'},
                        {'number': 2, 'text': 'Calculate descriptive statistics for account balance', 'full_text': 'Calculate mean median mode'},
                        {'number': 3, 'text': 'Draw histograms for account balance', 'full_text': 'Draw histogram'},
                        {'number': 4, 'text': 'Analyze skewness of distributions', 'full_text': 'Skewness analysis'},
                        {'number': 5, 'text': 'Create bar charts by city', 'full_text': 'Bar chart by city'},
                        {'number': 6, 'text': 'Calculate confidence intervals', 'full_text': 'Confidence intervals'},
                        {'number': 7, 'text': 'Detect outliers', 'full_text': 'Outliers detection'},
                        {'number': 8, 'text': 'Apply empirical rule', 'full_text': 'Empirical rule'}
                    ]
            
            # توليد كود SPSS
            st.markdown("---")
            st.subheader("🔄 توليد الحل الكامل")
            
            with st.spinner("جاري توليد حل SPSS كامل..."):
                spss_syntax = generate_spss_syntax_for_dataset(df, questions, variable_info)
                
                # عرض الكود
                st.subheader("📜 كود SPSS الكامل")
                st.code(spss_syntax, language='spss')
                
                # زر التحميل
                st.download_button(
                    label="💾 تحميل ملف SPSS (.sps)",
                    data=spss_syntax,
                    file_name="SPSS_Exam_Solution.sps",
                    mime="text/plain",
                    use_container_width=True
                )
                
                # عرض شرح للكود
                with st.expander("📖 شرح الكود المتولد"):
                    st.markdown("""
                    ### هيكل الحل المتولد:
                    
                    1. **إعداد البيانات**: تعريف المتغيرات وتسميات القيم
                    2. **المتغيرات المشتقة**: تجميع البيانات في فئات
                    3. **حل كل سؤال**: كود SPSS خاص لكل سؤال
                    4. **تحليلات إضافية**: تحليلات شاملة للبيانات
                    5. **حفظ النتائج**: حفظ الملف للاستخدام المستقبلي
                    
                    ### كيفية الاستخدام في SPSS:
                    1. افتح SPSS
                    2. أدخل بياناتك أو افتح ملف البيانات
                    3. انسخ الكود والصقه في نافذة Syntax
                    4. اضغط Ctrl+A ثم Ctrl+R لتشغيل الكود
                    5. تحقق من النتائج في نافذة Output
                    """)
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# تشغيل التطبيق
if __name__ == "__main__":
    main()
