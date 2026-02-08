import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import base64

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
    .arabic-text {
        direction: rtl;
        text-align: right;
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
        
        if df is not None:
            # عرض المتغيرات المتاحة
            vars_list = " ".join(df.columns[:5]) if len(df.columns) > 5 else " ".join(df.columns)
            code += f"  {vars_list}\n"
            if len(df.columns) > 5:
                code += f"* There are {len(df.columns)} variables in total\n"
        else:
            code += "  Variable1 Variable2 Variable3\n"
        
        code += "  /ORDER=ANALYSIS\n"
        code += "  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MINIMUM MAXIMUM\n"
        code += "  /BARCHART FREQ\n"
        code += "  /PIECHART FREQ\n"
        code += "  /HISTOGRAM NORMAL\n"
        code += "  /FORMAT=NOTABLE\n"
        code += "  /MISSING=INCLUDE.\n\n"
        
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

def create_comprehensive_template():
    """إنشاء قالب SPSS شامل"""
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
* 3. INFERENTIAL STATISTICS
************************************************.
* Independent samples t-test.
T-TEST GROUPS=Gender(1 2)
  /MISSING=ANALYSIS
  /VARIABLES=Income Score1 Score2
  /CRITERIA=CI(.95).

* One-way ANOVA.
ONEWAY Score1 BY Education(1, 4)
  /STATISTICS DESCRIPTIVES HOMOGENEITY
  /MISSING ANALYSIS
  /POSTHOC=TUKEY LSD ALPHA(0.05).

************************************************.
* 4. CORRELATION AND REGRESSION
************************************************.
CORRELATIONS
  /VARIABLES=Income Age Score1 Score2
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.

REGRESSION
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS R ANOVA
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN
  /DEPENDENT Score1
  /METHOD=ENTER Income Age Education.

************************************************.
* 5. DATA MANAGEMENT
************************************************.
* Compute new variables.
COMPUTE BMI = Weight / ((Height/100) ** 2).
VARIABLE LABELS BMI 'Body Mass Index'.

* Recode variables.
RECODE Age (Lowest thru 30=1) (31 thru 45=2) (46 thru 60=3) (61 thru Highest=4)
  INTO Age_Group.
VARIABLE LABELS Age_Group 'Age Groups'.

* Save the data.
SAVE OUTFILE='C:\\Data\\Analysis_Data.sav'
  /COMPRESSED.

************************************************.
* END OF TEMPLATE
************************************************.
* Remember to replace variable names with your actual variable names.
* Save this syntax file with .sps extension.
"""
    return template

# إنشاء تطبيق Streamlit
def main():
    app = SPSSStreamlitApp()
    
    # عنوان التطبيق
    st.markdown('<h1 class="main-header">📊 مولد أكواد SPSS التفاعلي</h1>', unsafe_allow_html=True)
    st.markdown('<div class="section-box arabic-text">', unsafe_allow_html=True)
    st.markdown("### 🚀 أهلاً بك في مولد أكواد SPSS الأوتوماتيكي")
    st.markdown("قم بتحميل ملفات Excel وWord لإنشاء أكواد SPSS جاهزة للاستخدام")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown("## ⚙️ الإعدادات")
        st.markdown('<div class="warning-box arabic-text">', unsafe_allow_html=True)
        st.info("""
        **تعليمات الاستخدام:**
        1. قم بتحميل ملف Excel (البيانات)
        2. قم بتحميل ملف Word (الأسئلة)
        3. اضغط على زر توليد الكود
        4. قم بتحميل كود SPSS الناتج
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("## 📁 الملفات المرفوعة")
        
        # إظهار الملفات المرفوعة حالياً
        if 'excel' in app.uploaded_files:
            st.success(f"📊 {app.uploaded_files['excel']['name']}")
        if 'word' in app.uploaded_files:
            st.success(f"📝 {app.uploaded_files['word']['name']}")
        
        st.markdown("---")
        st.markdown("### 🎯 توليد سريع")
        
        # خيارات سريعة
        quick_options = st.selectbox(
            "اختر تحليل سريع",
            ["", "الإحصاءات الوصفية", "الرسوم البيانية", "اختبارات الفرضيات", "الانحدار الخطي"]
        )
        
        if quick_options:
            st.session_state.quick_analysis = quick_options
    
    # علامات التبويب الرئيسية
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 تحميل الملفات", 
        "⚡ توليد الأكواد", 
        "📊 عرض البيانات", 
        "📝 القوالب الجاهزة"
    ])
    
    with tab1:
        st.markdown('<div class="sub-header arabic-text">تحميل ملفات البيانات والأسئلة</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 ملف Excel (البيانات)")
            excel_file = st.file_uploader("اختر ملف Excel", type=['xls', 'xlsx'], key="excel_uploader")
            
            if excel_file is not None:
                try:
                    df = pd.read_excel(excel_file)
                    st.success(f"✅ تم تحميل ملف Excel بنجاح! ({len(df)} صف، {len(df.columns)} عمود)")
                    
                    # عرض عينة من البيانات
                    with st.expander("👁️ عرض عينة من البيانات"):
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**عدد الصفوف:** {len(df)}")
                            st.write(f"**عدد الأعمدة:** {len(df.columns)}")
                        with col_b:
                            st.write(f"**البيانات المفقودة:** {df.isnull().sum().sum()}")
                            st.write(f"**المتغيرات الرقمية:** {len(df.select_dtypes(include=[np.number]).columns)}")
                    
                    app.uploaded_files['excel'] = {
                        'name': excel_file.name,
                        'data': df,
                        'columns': list(df.columns)
                    }
                except Exception as e:
                    st.error(f"❌ خطأ في قراءة ملف Excel: {str(e)}")
        
        with col2:
            st.markdown("### 📝 ملف الأسئلة")
            word_file = st.file_uploader("اختر ملف الأسئلة (Word أو Text)", 
                                       type=['txt'], 
                                       key="word_uploader")
            
            if word_file is not None:
                try:
                    # قراءة ملف النص
                    text_content = word_file.getvalue().decode('utf-8')
                    
                    questions = app.parse_questions(text_content)
                    
                    st.success(f"✅ تم تحميل ملف الأسئلة بنجاح! ({len(questions)} سؤال)")
                    
                    # عرض الأسئلة
                    with st.expander("📋 عرض الأسئلة المحللة"):
                        for i, q in enumerate(questions[:5], 1):
                            st.write(f"**{i}.** {q[:150]}..." if len(q) > 150 else f"**{i}.** {q}")
                        if len(questions) > 5:
                            st.write(f"*و {len(questions)-5} أسئلة إضافية...*")
                    
                    app.uploaded_files['word'] = {
                        'name': word_file.name,
                        'questions': questions,
                        'content': text_content
                    }
                except Exception as e:
                    st.error(f"❌ خطأ في قراءة ملف الأسئلة: {str(e)}")
        
        # زر لتوليد الكود مباشرة
        if 'excel' in app.uploaded_files and 'word' in app.uploaded_files:
            st.markdown("---")
            if st.button("🚀 انتقل إلى توليد الأكواد", use_container_width=True):
                st.session_state.current_tab = 2
                st.rerun()
    
    with tab2:
        st.markdown('<div class="sub-header arabic-text">توليد أكواد SPSS</div>', unsafe_allow_html=True)
        
        if 'excel' not in app.uploaded_files or 'word' not in app.uploaded_files:
            st.warning("⚠️ يرجى تحميل ملف Excel وملف الأسئلة أولاً في علامة تبويب 'تحميل الملفات'")
        else:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown("### ⚙️ إعدادات التوليد")
                
                # خيارات التوليد
                include_descriptive = st.checkbox("تضمين الإحصاءات الوصفية", value=True)
                include_charts = st.checkbox("تضمين الرسوم البيانية", value=True)
                include_tests = st.checkbox("تضمين اختبارات الفرضيات", value=True)
                
                generate_button = st.button("🚀 توليد أكواد SPSS", 
                                          use_container_width=True,
                                          type="primary")
            
            with col2:
                if generate_button:
                    with st.spinner("🔄 جاري توليد الأكواد..."):
                        df = app.uploaded_files['excel']['data']
                        questions = app.uploaded_files['word']['questions']
                        
                        # توليد الكود الكامل
                        full_code = f"* SPSS Syntax Generated Automatically\n"
                        full_code += f"* Data File: {app.uploaded_files['excel']['name']}\n"
                        full_code += f"* Questions File: {app.uploaded_files['word']['name']}\n"
                        full_code += f"* Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        full_code += f"* Total Questions: {len(questions)}\n"
                        full_code += "************************************************.\n\n"
                        
                        # توليد كود لكل سؤال
                        progress_bar = st.progress(0)
                        for i, question in enumerate(questions, 1):
                            question_code = f"* Question {i}: {question}\n"
                            question_code += app.generate_spss_code_for_question(question, df)
                            full_code += question_code
                            full_code += "*" * 48 + ".\n\n"
                            
                            # تحديث شريط التقدم
                            progress_bar.progress(i / len(questions))
                        
                        # إضافة تذييل
                        full_code += "* End of SPSS Syntax\n"
                        full_code += "* Replace variable names with your actual variable names\n"
                        full_code += "* Save this file with .sps extension\n"
                        
                        app.generated_codes['full'] = full_code
                        
                        st.success(f"✅ تم توليد {len(questions)} كود SPSS بنجاح!")
                        
                        # عرض إحصائيات
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("عدد الأسئلة", len(questions))
                        with col_b:
                            st.metric("طول الكود", f"{len(full_code):,} حرف")
                        with col_c:
                            st.metric("عدد الأسطر", full_code.count('\n'))
            
            # عرض الكود المولد
            if 'full' in app.generated_codes:
                st.markdown("### 📋 كود SPSS المُنشأ")
                
                # عرض جزء من الكود مع إمكانية التمرير
                code_display = st.text_area(
                    "الكود المولد",
                    value=app.generated_codes['full'],
                    height=400,
                    label_visibility="collapsed"
                )
                
                # أزرار التنزيل والإجراءات
                st.markdown("---")
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                
                with col_dl1:
                    st.markdown(app.create_download_link(app.generated_codes['full'], "SPSS_Code.sps"), 
                              unsafe_allow_html=True)
                
                with col_dl2:
                    if st.button("📋 نسخ إلى الحافظة", use_container_width=True):
                        st.code(app.generated_codes['full'][:1000] + "..." if len(app.generated_codes['full']) > 1000 else app.generated_codes['full'])
                        st.success("تم نسخ جزء من الكود (استخدم زر التنزيل للكود الكامل)")
                
                with col_dl3:
                    if st.button("🔄 توليد جديد", use_container_width=True):
                        app.generated_codes = {}
                        st.rerun()
    
    with tab3:
        st.markdown('<div class="sub-header arabic-text">عرض وتحليل البيانات</div>', unsafe_allow_html=True)
        
        if 'excel' in app.uploaded_files:
            df = app.uploaded_files['excel']['data']
            
            # إحصائيات سريعة
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("📊 عدد الصفوف", f"{len(df):,}")
            with col_stat2:
                st.metric("📈 عدد الأعمدة", len(df.columns))
            with col_stat3:
                missing_total = df.isnull().sum().sum()
                st.metric("⚠️ البيانات المفقودة", f"{missing_total:,}")
            with col_stat4:
                numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                st.metric("🔢 متغيرات رقمية", numeric_cols)
            
            # علامات تبويب التحليل
            analysis_tab1, analysis_tab2, analysis_tab3, analysis_tab4 = st.tabs([
                "👁️ معاينة البيانات", 
                "📈 الإحصاءات", 
                "🔍 تحليل المتغيرات", 
                "📊 الرسوم البيانية"
            ])
            
            with analysis_tab1:
                st.dataframe(df, use_container_width=True)
                
                # خيارات المعاينة
                col_view1, col_view2 = st.columns(2)
                with col_view1:
                    show_rows = st.slider("عدد الصفوف للعرض", 5, 100, 20)
                with col_view2:
                    selected_columns = st.multiselect(
                        "اختر الأعمدة للعرض",
                        options=df.columns.tolist(),
                        default=df.columns.tolist()[:5] if len(df.columns) > 5 else df.columns.tolist()
                    )
                
                if selected_columns:
                    st.dataframe(df[selected_columns].head(show_rows), use_container_width=True)
            
            with analysis_tab2:
                st.markdown("### الإحصاءات الوصفية")
                
                # اختيار المتغيرات الرقمية
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    selected_numeric = st.multiselect(
                        "اختر المتغيرات الرقمية للإحصاءات",
                        options=numeric_cols,
                        default=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols
                    )
                    
                    if selected_numeric:
                        st.dataframe(df[selected_numeric].describe(), use_container_width=True)
                        
                        # إحصائيات إضافية
                        col_extra1, col_extra2 = st.columns(2)
                        with col_extra1:
                            st.write("**القيم المفقودة:**")
                            missing_df = df[selected_numeric].isnull().sum()
                            st.dataframe(missing_df[missing_df > 0] if missing_df.sum() > 0 else pd.DataFrame({"القيم المفقودة": [0]}))
                        
                        with col_extra2:
                            st.write("**نوع البيانات:**")
                            dtypes_df = df[selected_numeric].dtypes
                            st.dataframe(dtypes_df)
                else:
                    st.warning("لا توجد متغيرات رقمية في البيانات")
            
            with analysis_tab3:
                st.markdown("### تحليل المتغيرات الفردية")
                
                selected_var = st.selectbox(
                    "اختر متغير للتحليل",
                    options=df.columns.tolist()
                )
                
                if selected_var:
                    col_var1, col_var2 = st.columns(2)
                    
                    with col_var1:
                        st.write(f"**المتغير:** {selected_var}")
                        st.write(f"**نوع البيانات:** {df[selected_var].dtype}")
                        st.write(f"**القيم الفريدة:** {df[selected_var].nunique()}")
                        st.write(f"**القيم المفقودة:** {df[selected_var].isnull().sum()}")
                    
                    with col_var2:
                        if pd.api.types.is_numeric_dtype(df[selected_var]):
                            stats = df[selected_var].describe()
                            st.write("**الإحصاءات:**")
                            for stat, value in stats.items():
                                st.write(f"{stat}: {value:.4f}")
                        else:
                            st.write("**القيم الأكثر تكراراً:**")
                            top_values = df[selected_var].value_counts().head(5)
                            for value, count in top_values.items():
                                st.write(f"{value}: {count}")
            
            with analysis_tab4:
                st.markdown("### إنشاء رسوم بيانية سريعة")
                
                if len(df.select_dtypes(include=[np.number]).columns) >= 2:
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        x_var = st.selectbox(
                            "المتغير على المحور X",
                            options=df.select_dtypes(include=[np.number]).columns.tolist()
                        )
                    
                    with chart_col2:
                        y_var = st.selectbox(
                            "المتغير على المحور Y",
                            options=df.select_dtypes(include=[np.number]).columns.tolist()
                        )
                    
                    if x_var and y_var and x_var != y_var:
                        chart_type = st.selectbox(
                            "نوع الرسم البياني",
                            options=["مبعثر", "خطي", "عمودي", "منطقة"]
                        )
                        
                        try:
                            if chart_type == "مبعثر":
                                st.scatter_chart(df[[x_var, y_var]].dropna())
                            elif chart_type == "خطي":
                                st.line_chart(df[[x_var, y_var]].dropna())
                            elif chart_type == "عمودي":
                                st.bar_chart(df[[x_var, y_var]].dropna())
                            elif chart_type == "منطقة":
                                st.area_chart(df[[x_var, y_var]].dropna())
                        except Exception as e:
                            st.error(f"تعذر إنشاء الرسم البياني: {str(e)}")
                else:
                    st.warning("تحتاج إلى متغيرين رقميين على الأقل لإنشاء رسم بياني")
        
        else:
            st.info("📥 يرجى تحميل ملف Excel أولاً لعرض البيانات")
    
    with tab4:
        st.markdown('<div class="sub-header arabic-text">قوالب SPSS جاهزة</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="arabic-text">
        ### 📝 اختر من القوالب الجاهزة
        
        يمكنك استخدام هذه القوالب مباشرة أو تعديلها لتناسب بياناتك
        </div>
        """, unsafe_allow_html=True)
        
        # عرض القوالب
        template_options = {
            "الإحصاءات الوصفية": """* Descriptive Statistics Template
DESCRIPTIVES VARIABLES=ALL
  /STATISTICS=MEAN STDDEV MIN MAX SEMEAN VARIANCE KURTOSIS SKEWNESS RANGE.

FREQUENCIES VARIABLES=ALL
  /FORMAT=NOTABLE
  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MINIMUM MAXIMUM.""",
            
            "الرسوم البيانية": """* Charts and Graphs Template
GRAPH
  /BAR(SIMPLE)=MEAN(Var1) BY CategoryVar
  /TITLE='Bar Chart'.

GRAPH
  /HISTOGRAM(NORMAL)=Var1
  /TITLE='Histogram'.

GRAPH
  /SCATTERPLOT(BIVAR)=Var1 WITH Var2
  /TITLE='Scatter Plot'.""",
            
            "اختبارات الفرضيات": """* Hypothesis Testing Template
* Independent t-test
T-TEST GROUPS=GroupVar(1 2)
  /MISSING=ANALYSIS
  /VARIABLES=DependentVar
  /CRITERIA=CI(.95).

* One-way ANOVA
ONEWAY DependentVar BY GroupVar(1, 3)
  /STATISTICS DESCRIPTIVES HOMOGENEITY
  /MISSING ANALYSIS
  /POSTHOC=TUKEY LSD.""",
            
            "الانحدار والارتباط": """* Regression and Correlation Template
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
  /METHOD=ENTER IndependentVar1 IndependentVar2."""
        }
        
        selected_template = st.selectbox(
            "اختر قالب",
            list(template_options.keys())
        )
        
        if selected_template:
            st.code(template_options[selected_template], language="text")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown(app.create_download_link(
                    template_options[selected_template], 
                    f"SPSS_{selected_template.replace(' ', '_')}.sps"
                ), unsafe_allow_html=True)
            
            with col_t2:
                if st.button("📋 نسخ القالب", use_container_width=True):
                    st.success(f"تم نسخ قالب {selected_template}")
        
        # القالب الشامل
        st.markdown("---")
        st.markdown("### 🏆 القالب الشامل المتقدم")
        
        if st.button("🔄 إنشاء القالب الشامل", use_container_width=True):
            comprehensive_template = create_comprehensive_template()
            st.code(comprehensive_template, language="text", height=400)
            
            st.markdown(app.create_download_link(
                comprehensive_template,
                "SPSS_Master_Template.sps"
            ), unsafe_allow_html=True)
    
    # تذييل الصفحة
    st.markdown("---")
    st.markdown("""
    <div style='text-align
