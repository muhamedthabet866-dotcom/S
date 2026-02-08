import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import tempfile
from pathlib import Path
import base64
from io import BytesIO

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="مولد أكواد SPSS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS لتخصيص المظهر
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #1E40AF;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .section-box {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1.5rem;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #F59E0B;
        margin-bottom: 1rem;
    }
    .spss-code {
        background-color: #1E293B;
        color: #E2E8F0;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        overflow-x: auto;
        white-space: pre-wrap;
        direction: ltr;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
    }
</style>
""", unsafe_allow_html=True)

class SPSSStreamlitApp:
    def __init__(self):
        self.uploaded_files = {}
        self.generated_codes = {}
        
    def create_download_link(self, content, filename):
        """إنشاء رابط تحميل للملف"""
        b64 = base64.b64encode(content.encode()).decode()
        return f'<a href="data:file/txt;base64,{b64}" download="{filename}">📥 تحميل {filename}</a>'
    
    def parse_questions(self, text_content):
        """تحليل النص لاستخراج الأسئلة"""
        questions = []
        lines = text_content.split('\n')
        current_q = ""
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+[\.\)]', line):
                if current_q:
                    questions.append(current_q.strip())
                current_q = line
            elif current_q and line:
                current_q += " " + line
        
        if current_q:
            questions.append(current_q.strip())
        
        return questions
    
    def generate_spss_code_for_question(self, question, df=None):
        """توليد كود SPSS لسؤال محدد"""
        code = ""
        question_lower = question.lower()
        
        # 1. جداول التكرار
        if 'frequency table' in question_lower:
            code += self.generate_frequency_code(question, df)
        
        # 2. الرسوم البيانية
        elif 'bar chart' in question_lower:
            code += self.generate_chart_code(question, 'bar')
        elif 'pie chart' in question_lower:
            code += self.generate_chart_code(question, 'pie')
        elif 'histogram' in question_lower:
            code += self.generate_chart_code(question, 'histogram')
        
        # 3. الإحصاءات الوصفية
        elif any(term in question_lower for term in ['mean', 'median', 'mode', 'standard deviation', 'range']):
            code += self.generate_descriptive_code(question)
        
        # 4. فترات الثقة
        elif 'confidence interval' in question_lower:
            code += self.generate_confidence_code(question)
        
        # 5. اختبارات الفرضيات
        elif any(term in question_lower for term in ['hypothesis', 'test the hypothesis', 't-test', 'anova']):
            code += self.generate_hypothesis_code(question)
        
        # 6. الارتباط والانحدار
        elif any(term in question_lower for term in ['correlation', 'regression', 'linear regression']):
            code += self.generate_correlation_code(question)
        
        # 7. القيم المتطرفة
        elif any(term in question_lower for term in ['outliers', 'extremes']):
            code += self.generate_outliers_code(question)
        
        else:
            code += f"* {question}\n"
            code += "* This analysis requires manual specification.\n"
            code += "* Please customize the code below with your actual variable names.\n\n"
        
        return code
    
    def generate_frequency_code(self, question, df):
        """كود جداول التكرار"""
        code = f"* {question}\n"
        code += "FREQUENCIES VARIABLES=\n"
        code += "  /ORDER=ANALYSIS\n"
        code += "  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MINIMUM MAXIMUM\n"
        code += "  /BARCHART FREQ\n"
        code += "  /PIECHART FREQ\n"
        code += "  /HISTOGRAM NORMAL\n"
        code += "  /FORMAT=NOTABLE\n"
        code += "  /MISSING=INCLUDE.\n\n"
        
        if df is not None:
            code += "* Available variables in your dataset:\n"
            for col in df.columns:
                code += f"*   {col}\n"
        
        return code
    
    def generate_chart_code(self, question, chart_type):
        """كود الرسوم البيانية"""
        code = f"* {question}\n"
        
        if chart_type == 'bar':
            code += "GRAPH\n"
            code += "  /BAR(SIMPLE)=MEAN(VariableName) BY CategoryVariable\n"
            code += "  /TITLE='Bar Chart Title'.\n\n"
        
        elif chart_type == 'pie':
            code += "GRAPH\n"
            code += "  /PIE=SUM(VariableName) BY CategoryVariable\n"
            code += "  /TITLE='Pie Chart Title'.\n\n"
        
        elif chart_type == 'histogram':
            code += "GRAPH\n"
            code += "  /HISTOGRAM(NORMAL)=VariableName\n"
            code += "  /TITLE='Histogram Title'.\n\n"
        
        return code
    
    def generate_descriptive_code(self, question):
        """كود الإحصاءات الوصفية"""
        code = f"* {question}\n"
        code += "DESCRIPTIVES VARIABLES=Variable1 Variable2 Variable3\n"
        code += "  /STATISTICS=MEAN STDDEV MIN MAX RANGE VARIANCE KURTOSIS SKEWNESS SEMEAN.\n\n"
        
        code += "EXAMINE VARIABLES=Variable1 Variable2 BY GroupVariable\n"
        code += "  /PLOT=BOXPLOT STEMLEAF HISTOGRAM\n"
        code += "  /COMPARE GROUP\n"
        code += "  /STATISTICS DESCRIPTIVES\n"
        code += "  /CINTERVAL 95\n"
        code += "  /MISSING LISTWISE\n"
        code += "  /NOTOTAL.\n\n"
        
        return code
    
    def generate_confidence_code(self, question):
        """كود فترات الثقة"""
        code = f"* {question}\n"
        code += "EXAMINE VARIABLES=VariableName\n"
        code += "  /PLOT NONE\n"
        code += "  /STATISTICS DESCRIPTIVES\n"
        code += "  /CINTERVAL 95 99\n"
        code += "  /MISSING LISTWISE\n"
        code += "  /NOTOTAL.\n\n"
        
        return code
    
    def generate_hypothesis_code(self, question):
        """كود اختبارات الفرضيات"""
        code = f"* {question}\n"
        question_lower = question.lower()
        
        if 'equal' in question_lower and ('less' in question_lower or 'greater' in question_lower):
            # اختبار t لعينة واحدة
            code += "* One-sample t-test:\n"
            code += "T-TEST\n"
            code += "  /TESTVAL=TestValue\n"
            code += "  /MISSING=ANALYSIS\n"
            code += "  /VARIABLES=VariableName\n"
            code += "  /CRITERIA=CI(.95).\n\n"
        
        elif 'difference between' in question_lower:
            # اختبار t لعينتين مستقلتين
            code += "* Independent samples t-test:\n"
            code += "T-TEST GROUPS=GroupVariable(1 2)\n"
            code += "  /MISSING=ANALYSIS\n"
            code += "  /VARIABLES=DependentVariable\n"
            code += "  /CRITERIA=CI(.95).\n\n"
        
        elif 'more than' in question_lower and 'groups' in question_lower:
            # ANOVA
            code += "* One-way ANOVA:\n"
            code += "ONEWAY DependentVariable BY GroupVariable(1, NumberOfGroups)\n"
            code += "  /STATISTICS DESCRIPTIVES HOMOGENEITY\n"
            code += "  /MISSING ANALYSIS\n"
            code += "  /POSTHOC=TUKEY LSD ALPHA(0.05).\n\n"
        
        return code
    
    def generate_correlation_code(self, question):
        """كود الارتباط والانحدار"""
        code = f"* {question}\n"
        question_lower = question.lower()
        
        if 'correlation' in question_lower:
            code += "* Correlation analysis:\n"
            code += "CORRELATIONS\n"
            code += "  /VARIABLES=Variable1 Variable2 Variable3\n"
            code += "  /PRINT=TWOTAIL NOSIG\n"
            code += "  /MISSING=PAIRWISE.\n\n"
        
        elif 'regression' in question_lower:
            code += "* Multiple linear regression:\n"
            code += "REGRESSION\n"
            code += "  /MISSING LISTWISE\n"
            code += "  /STATISTICS COEFF OUTS R ANOVA\n"
            code += "  /CRITERIA=PIN(.05) POUT(.10)\n"
            code += "  /NOORIGIN\n"
            code += "  /DEPENDENT DependentVariable\n"
            code += "  /METHOD=ENTER IndependentVar1 IndependentVar2 IndependentVar3.\n\n"
        
        return code
    
    def generate_outliers_code(self, question):
        """كود القيم المتطرفة"""
        code = f"* {question}\n"
        code += "EXAMINE VARIABLES=VariableName\n"
        code += "  /PLOT=BOXPLOT STEMLEAF\n"
        code += "  /COMPARE VARIABLES\n"
        code += "  /STATISTICS=EXTREME\n"
        code += "  /CINTERVAL 95\n"
        code += "  /MISSING=LISTWISE\n"
        code += "  /NOTOTAL.\n\n"
        
        return code

# إنشاء تطبيق Streamlit
def main():
    app = SPSSStreamlitApp()
    
    # عنوان التطبيق
    st.markdown('<h1 class="main-header">📊 مولد أكواد SPSS التفاعلي</h1>', unsafe_allow_html=True)
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown("### 🚀 أهلاً بك في مولد أكواد SPSS الأوتوماتيكي")
    st.markdown("قم بتحميل ملفات Excel وWord لإنشاء أكواد SPSS جاهزة للاستخدام")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown("## ⚙️ الإعدادات")
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.info("""
        **تعليمات الاستخدام:**
        1. قم بتحميل ملف Excel (البيانات)
        2. قم بتحميل ملف Word (الأسئلة)
        3. اضغط على زر توليد الكود
        4. قم بتحميل كود SPSS الناتج
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("## 📁 الملفات المرفوعة")
        uploaded_files = st.file_uploader(
            "اختر ملفات Excel وWord",
            type=['xls', 'xlsx', 'doc', 'docx', 'txt'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_type = "Excel" if uploaded_file.name.endswith(('.xls', '.xlsx')) else "Word"
                st.success(f"✓ {file_type}: {uploaded_file.name}")
    
    # علامات التبويب الرئيسية
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 تحميل الملفات", 
        "⚡ توليد الأكواد", 
        "📊 عرض البيانات", 
        "📝 القوالب الجاهزة"
    ])
    
    with tab1:
        st.markdown('<div class="sub-header">تحميل ملفات البيانات والأسئلة</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ملف Excel (البيانات)")
            excel_file = st.file_uploader("اختر ملف Excel", type=['xls', 'xlsx'], key="excel_uploader")
            
            if excel_file is not None:
                try:
                    df = pd.read_excel(excel_file)
                    st.success(f"تم تحميل ملف Excel بنجاح! ({len(df)} صف، {len(df.columns)} عمود)")
                    
                    # عرض عينة من البيانات
                    with st.expander("عرض عينة من البيانات"):
                        st.dataframe(df.head())
                        st.write(f"**أسماء الأعمدة:** {list(df.columns)}")
                        
                    app.uploaded_files['excel'] = {
                        'name': excel_file.name,
                        'data': df,
                        'columns': list(df.columns)
                    }
                except Exception as e:
                    st.error(f"خطأ في قراءة ملف Excel: {str(e)}")
        
        with col2:
            st.markdown("### ملف Word/Text (الأسئلة)")
            word_file = st.file_uploader("اختر ملف الأسئلة", type=['doc', 'docx', 'txt'], key="word_uploader")
            
            if word_file is not None:
                try:
                    if word_file.name.endswith(('.doc', '.docx')):
                        # لملفات Word، نقرأ النص مباشرة
                        text_content = word_file.getvalue().decode('utf-8', errors='ignore')
                    else:
                        text_content = word_file.getvalue().decode('utf-8')
                    
                    questions = app.parse_questions(text_content)
                    
                    st.success(f"تم تحميل ملف الأسئلة بنجاح! ({len(questions)} سؤال)")
                    
                    # عرض الأسئلة
                    with st.expander("عرض الأسئلة المحللة"):
                        for i, q in enumerate(questions[:10], 1):
                            st.write(f"**{i}.** {q[:100]}...")
                        if len(questions) > 10:
                            st.write(f"و {len(questions)-10} أسئلة إضافية...")
                    
                    app.uploaded_files['word'] = {
                        'name': word_file.name,
                        'questions': questions,
                        'content': text_content
                    }
                except Exception as e:
                    st.error(f"خطأ في قراءة ملف الأسئلة: {str(e)}")
    
    with tab2:
        st.markdown('<div class="sub-header">توليد أكواد SPSS</div>', unsafe_allow_html=True)
        
        if 'excel' not in app.uploaded_files or 'word' not in app.uploaded_files:
            st.warning("⚠️ يرجى تحميل ملف Excel وملف الأسئلة أولاً")
        else:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("🚀 توليد أكواد SPSS", use_container_width=True):
                    with st.spinner("جاري توليد الأكواد..."):
                        df = app.uploaded_files['excel']['data']
                        questions = app.uploaded_files['word']['questions']
                        
                        # توليد الكود الكامل
                        full_code = "* SPSS Syntax Generated Automatically\n"
                        full_code += "* Data File: " + app.uploaded_files['excel']['name'] + "\n"
                        full_code += "* Questions File: " + app.uploaded_files['word']['name'] + "\n"
                        full_code += "* Generated by SPSS Streamlit Generator\n"
                        full_code += "************************************************.\n\n"
                        
                        # توليد كود لكل سؤال
                        for i, question in enumerate(questions, 1):
                            full_code += f"* Question {i}: {question}\n"
                            full_code += app.generate_spss_code_for_question(question, df)
                            full_code += "************************************************.\n\n"
                        
                        app.generated_codes['full'] = full_code
                        
                        st.success("✅ تم توليد أكواد SPSS بنجاح!")
                        
                        # رابط تحميل
                        st.markdown(app.create_download_link(full_code, "SPSS_Generated_Code.sps"), unsafe_allow_html=True)
            
            with col2:
                if 'full' in app.generated_codes:
                    st.markdown("### 📋 كود SPSS المُنشأ")
                    
                    # عرض جزء من الكود
                    with st.expander("عرض الكود الكامل", expanded=True):
                        st.code(app.generated_codes['full'], language='text')
                    
                    # خيارات إضافية
                    st.markdown("### 🛠️ خيارات متقدمة")
                    
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        if st.button("📥 حفظ الكود", use_container_width=True):
                            with open("SPSS_Code.sps", "w", encoding="utf-8") as f:
                                f.write(app.generated_codes['full'])
                            st.success("تم حفظ الملف: SPSS_Code.sps")
                    
                    with col_b:
                        if st.button("🔄 إعادة توليد", use_container_width=True):
                            st.rerun()
                    
                    with col_c:
                        if st.button("🧹 مسح الكل", use_container_width=True):
                            app.generated_codes = {}
                            st.rerun()
    
    with tab3:
        st.markdown('<div class="sub-header">عرض وتحليل البيانات</div>', unsafe_allow_html=True)
        
        if 'excel' in app.uploaded_files:
            df = app.uploaded_files['excel']['data']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("عدد الصفوف", len(df))
            with col2:
                st.metric("عدد الأعمدة", len(df.columns))
            with col3:
                st.metric("البيانات المفقودة", df.isnull().sum().sum())
            
            # تحليل البيانات
            st.markdown("### 📈 الإحصاءات الوصفية")
            
            tab_desc, tab_info, tab_missing = st.tabs(["الإحصاءات", "معلومات البيانات", "القيم المفقودة"])
            
            with tab_desc:
                if st.button("إظهار الإحصاءات الوصفية"):
                    st.dataframe(df.describe())
            
            with tab_info:
                buffer = BytesIO()
                df.info(buf=buffer)
                info_str = buffer.getvalue().decode('utf-8')
                st.text(info_str)
            
            with tab_missing:
                missing_data = df.isnull().sum()
                if missing_data.sum() > 0:
                    st.write("القيم المفقودة في كل عمود:")
                    st.dataframe(missing_data[missing_data > 0])
                else:
                    st.success("لا توجد قيم مفقودة في البيانات!")
            
            # اختيار متغيرات للتحليل
            st.markdown("### 🔍 تحليل متغيرات محددة")
            
            if len(df.columns) > 0:
                selected_vars = st.multiselect(
                    "اختر المتغيرات للتحليل",
                    options=df.columns.tolist(),
                    default=df.columns.tolist()[:3] if len(df.columns) >= 3 else df.columns.tolist()
                )
                
                if selected_vars:
                    selected_df = df[selected_vars]
                    st.dataframe(selected_df.describe())
                    
                    # رسم بياني سريع
                    if st.checkbox("عرض رسم بياني"):
                        chart_type = st.selectbox("نوع الرسم البياني", ["خطي", "عمودي", "مبعثر"])
                        
                        if len(selected_vars) >= 2:
                            try:
                                if chart_type == "خطي":
                                    st.line_chart(selected_df.iloc[:, :2])
                                elif chart_type == "عمودي":
                                    st.bar_chart(selected_df.iloc[:, :2])
                                elif chart_type == "مبعثر":
                                    st.scatter_chart(selected_df.iloc[:, :2])
                            except:
                                st.warning("تعذر إنشاء الرسم البياني مع البيانات المحددة")
    
    with tab4:
        st.markdown('<div class="sub-header">قوالب SPSS جاهزة</div>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 📝 اختر من القوالب الجاهزة
        
        يمكنك استخدام هذه القوالب مباشرة أو تعديلها لتناسب بياناتك
        """)
        
        template_col1, template_col2 = st.columns(2)
        
        with template_col1:
            st.markdown("#### 🎯 قالب الإحصاءات الوصفية")
            descriptive_template = """
* Descriptive Statistics Template
DESCRIPTIVES VARIABLES=ALL
  /STATISTICS=MEAN STDDEV MIN MAX SEMEAN VARIANCE KURTOSIS SKEWNESS RANGE.

FREQUENCIES VARIABLES=ALL
  /FORMAT=NOTABLE
  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MINIMUM MAXIMUM.
            """
            
            if st.button("نسخ قالب الإحصاءات", use_container_width=True):
                st.code(descriptive_template, language='text')
                st.markdown(app.create_download_link(descriptive_template, "Descriptive_Template.sps"), unsafe_allow_html=True)
        
        with template_col2:
            st.markdown("#### 📊 قالب الرسوم البيانية")
            charts_template = """
* Charts and Graphs Template
GRAPH
  /BAR(SIMPLE)=MEAN(Var1) BY CategoryVar
  /TITLE='Bar Chart'.

GRAPH
  /HISTOGRAM(NORMAL)=Var1
  /TITLE='Histogram'.

GRAPH
  /SCATTERPLOT(BIVAR)=Var1 WITH Var2
  /TITLE='Scatter Plot'.
            """
            
            if st.button("نسخ قالب الرسوم", use_container_width=True):
                st.code(charts_template, language='text')
                st.markdown(app.create_download_link(charts_template, "Charts_Template.sps"), unsafe_allow_html=True)
        
        st.markdown("---")
        
        advanced_col1, advanced_col2 = st.columns(2)
        
        with advanced_col1:
            st.markdown("#### 🔬 قالب اختبارات الفرضيات")
            hypothesis_template = """
* Hypothesis Testing Template
* Independent t-test
T-TEST GROUPS=GroupVar(1 2)
  /MISSING=ANALYSIS
  /VARIABLES=DependentVar
  /CRITERIA=CI(.95).

* One-way ANOVA
ONEWAY DependentVar BY GroupVar(1, 3)
  /STATISTICS DESCRIPTIVES HOMOGENEITY
  /MISSING ANALYSIS
  /POSTHOC=TUKEY LSD.
            """
            
            if st.button("نسخ قالب الفرضيات", use_container_width=True):
                st.code(hypothesis_template, language='text')
                st.markdown(app.create_download_link(hypothesis_template, "Hypothesis_Template.sps"), unsafe_allow_html=True)
        
        with advanced_col2:
            st.markdown("#### 📈 قالب الانحدار والارتباط")
            regression_template = """
* Regression and Correlation Template
* Correlation
CORRELATIONS
  /VARIABLES=Var1 Var2 Var3
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.

* Linear Regression
REGRESSION
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS R ANOVA
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN
  /DEPENDENT DependentVar
  /METHOD=ENTER IndependentVar1 IndependentVar2.
            """
            
            if st.button("نسخ قالب الانحدار", use_container_width=True):
                st.code(regression_template, language='text')
                st.markdown(app.create_download_link(regression_template, "Regression_Template.sps"), unsafe_allow_html=True)
        
        # قالب متقدم شامل
        st.markdown("---")
        st.markdown("#### 🏆 القالب الشامل المتقدم")
        
        if st.button("إنشاء القالب الشامل", use_container_width=True):
            comprehensive_template = app.create_comprehensive_template()
            st.code(comprehensive_template, language='text')
            st.markdown(app.create_download_link(comprehensive_template, "SPSS_Master_Template.sps"), unsafe_allow_html=True)
    
    # تذييل الصفحة
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>مولد أكواد SPSS التفاعلي | تم التطوير باستخدام Streamlit و Python</p>
        <p>© 2024 - جميع الحقوق محفوظة</p>
    </div>
    """, unsafe_allow_html=True)

# إنشاء القالب الشامل
def create_comprehensive_template():
    template = """* SPSS COMPREHENSIVE MASTER TEMPLATE
************************************************.

* 1. DATA PREPARATION AND CLEANING
************************************************.
* Check for missing values.
MISSING VALUES ALL ().
PRINT /TITLE='Missing Values Analysis'.
DESCRIPTIVES VARIABLES=ALL
  /STATISTICS=MEAN STDDEV MIN MAX.

* Define variable labels.
VARIABLE LABELS
  Var1 'Variable 1 Description'
  Var2 'Variable 2 Description'
  Var3 'Variable 3 Description'.

* Define value labels.
VALUE LABELS
  Gender 1 'Male' 2 'Female'
  Education 1 'High School' 2 'Bachelor' 3 'Master' 4 'PhD'.

* Recode variables if needed.
RECODE Age (Lowest thru 30=1) (31 thru 45=2) (46 thru 60=3) (61 thru Highest=4)
  INTO Age_Group.
VARIABLE LABELS Age_Group 'Age Groups'.
VALUE LABELS Age_Group 1 '18-30' 2 '31-45' 3 '46-60' 4 '61+'.

************************************************.
* 2. DESCRIPTIVE STATISTICS
************************************************.
DESCRIPTIVES VARIABLES=Age Income Score1 Score2
  /STATISTICS=MEAN STDDEV MIN MAX SEMEAN VARIANCE KURTOSIS SKEWNESS RANGE.

FREQUENCIES VARIABLES=Gender Education Age_Group
  /ORDER=ANALYSIS
  /BARCHART FREQ
  /PIECHART FREQ.

EXAMINE VARIABLES=Income Score1 BY Gender
  /PLOT=BOXPLOT STEMLEAF HISTOGRAM NPPLOT
  /COMPARE GROUP
  /STATISTICS DESCRIPTIVES EXTREME
  /CINTERVAL 95
  /MISSING LISTWISE
  /NOTOTAL.

************************************************.
* 3. DATA VISUALIZATION
************************************************.
GRAPH
  /BAR(GROUPED)=MEAN(Income) BY Education BY Gender
  /TITLE='Average Income by Education and Gender'.

GRAPH
  /SCATTERPLOT(BIVAR)=Score1 WITH Score2 BY Gender
  /MISSING=LISTWISE
  /TITLE='Scatter Plot: Score1 vs Score2'.

GRAPH
  /HISTOGRAM(NORMAL)=Income
  /TITLE='Income Distribution'.

************************************************.
* 4. INFERENTIAL STATISTICS - T-TESTS
************************************************.
* Independent samples t-test.
T-TEST GROUPS=Gender(1 2)
  /MISSING=ANALYSIS
  /VARIABLES=Income Score1 Score2
  /CRITERIA=CI(.95).

* Paired samples t-test.
T-TEST PAIRS=Pre_Test WITH Post_Test (PAIRED)
  /CRITERIA=CI(.9500)
  /MISSING=ANALYSIS.

* One-sample t-test.
T-TEST
  /TESTVAL=100
  /MISSING=ANALYSIS
  /VARIABLES=Score1
  /CRITERIA=CI(.95).

************************************************.
* 5. ANALYSIS OF VARIANCE (ANOVA)
************************************************.
* One-way ANOVA.
ONEWAY Score1 BY Education(1, 4)
  /STATISTICS DESCRIPTIVES HOMOGENEITY BROWNFORSYTHE WELCH
  /MISSING ANALYSIS
  /POSTHOC=TUKEY LSD BONFERRONI ALPHA(0.05).

* Two-way ANOVA.
UNIANOVA Score1 BY Gender Education
  /METHOD=SSTYPE(3)
  /INTERCEPT=INCLUDE
  /POSTHOC=Gender Education (TUKEY)
  /EMMEANS=TABLES(Gender)
  /EMMEANS=TABLES(Education)
  /EMMEANS=TABLES(Gender*Education)
  /PRINT=DESCRIPTIVE ETASQ HOMOGENEITY
  /CRITERIA=ALPHA(.05)
  /DESIGN=Gender Education Gender*Education.

************************************************.
* 6. CORRELATION ANALYSIS
************************************************.
CORRELATIONS
  /VARIABLES=Income Age Score1 Score2
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.

* Partial correlation.
PARTIAL CORR
  /VARIABLES=Score1 Score2 BY Age
  /SIGNIFICANCE=TWOTAIL
  /STATISTICS=DESCRIPTIVES CORR
  /MISSING=LISTWISE.

************************************************.
* 7. REGRESSION ANALYSIS
************************************************.
* Multiple linear regression.
REGRESSION
  /DESCRIPTIVES MEAN STDDEV CORR SIG N
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS R ANOVA COLLIN TOL CHANGE ZPP
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN
  /DEPENDENT Score1
  /METHOD=ENTER Age Gender Education
  /METHOD=STEPWISE Income
  /SCATTERPLOT=(*ZRESID ,*ZPRED)
  /RESIDUALS DURBIN HISTOGRAM(ZRESID) NORMPROB(ZRESID).

* Logistic regression (if binary dependent variable).
LOGISTIC REGRESSION VARIABLES=Success
  /METHOD=ENTER Age Income Education
  /CONTRAST (Education)=Indicator
  /CLASSPLOT
  /CASEWISE OUTLIER(2)
  /PRINT=GOODFIT CI(95)
  /CRITERIA=PIN(0.05) POUT(0.10) ITERATE(20) CUT(0.5).

************************************************.
* 8. NONPARAMETRIC TESTS
************************************************.
* Mann-Whitney U test.
NPAR TESTS
  /M-W= Income BY Gender(1 2)
  /MISSING ANALYSIS.

* Kruskal-Wallis test.
NPAR TESTS
  /K-W= Income BY Education(1 4)
  /MISSING ANALYSIS.

* Wilcoxon signed-rank test.
NPAR TESTS
  /WILCOXON=Pre_Test WITH Post_Test (PAIRED)
  /MISSING ANALYSIS.

************************************************.
* 9. RELIABILITY ANALYSIS
************************************************.
RELIABILITY
  /VARIABLES=Item1 Item2 Item3 Item4 Item5
  /SCALE('Total Scale') ALL
  /MODEL=ALPHA
  /STATISTICS=DESCRIPTIVE SCALE
  /SUMMARY=TOTAL.

************************************************.
* 10. FACTOR ANALYSIS
************************************************.
FACTOR
  /VARIABLES=Item1 TO Item10
  /MISSING LISTWISE
  /ANALYSIS Item1 TO Item10
  /PRINT INITIAL EXTRACTION ROTATION
  /PLOT EIGEN
  /CRITERIA MINEIGEN(1) ITERATE(25)
  /EXTRACTION PC
  /CRITERIA ITERATE(25)
  /ROTATION VARIMAX
  /METHOD=CORRELATION.

************************************************.
* 11. DATA MANAGEMENT
************************************************.
* Compute new variables.
COMPUTE BMI = Weight / ((Height/100) ** 2).
VARIABLE LABELS BMI 'Body Mass Index'.

* Standardize variables.
DESCRIPTIVES VARIABLES=Score1 Score2
  /SAVE
  /STATISTICS=MEAN STDDEV MIN MAX.

* Split file for separate analyses.
SORT CASES BY Gender.
SPLIT FILE LAYERED BY Gender.

* Run analysis for each group.
DESCRIPTIVES VARIABLES=Income Age
  /STATISTICS=MEAN STDDEV MIN MAX.

* Reset split file.
SPLIT FILE OFF.

* Select specific cases.
USE ALL.
COMPUTE filter_$=(Age >= 18 & Age <= 65).
VARIABLE LABELS filter_$ 'Age 18-65 (FILTER)'.
FORMATS filter_$ (f1.0).
FILTER BY filter_$.
EXECUTE.

* Run filtered analysis.
DESCRIPTIVES VARIABLES=ALL
  /STATISTICS=MEAN STDDEV.

* Turn off filter.
FILTER OFF.
USE ALL.
EXECUTE.

************************************************.
* 12. OUTPUT MANAGEMENT
************************************************.
* Set output options.
SET PRINTBACK=ON.
SET OVARS=LABELS.
SET TVARS=LABELS.
SET TNUMBERS=LABELS.

* Save output to file.
OUTPUT EXPORT
  /CONTENTS= EXPORT=VISIBLE
  /DOCUMENT DOCUMENTFILE='C:\\Output\\Analysis_Results.spv'.

************************************************.
* END OF TEMPLATE
************************************************.
* Remember to replace variable names with your actual variable names.
* Save this syntax file and run in SPSS.
"""
    return template

if __name__ == "__main__":
    main()
