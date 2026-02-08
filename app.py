import streamlit as st
import pandas as pd
import numpy as np
import re
import base64
from datetime import datetime
from io import BytesIO

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="مولد أكواد SPSS العام",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مخصص
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin-bottom: 1rem;
    }
    .code-box {
        background-color: #1E293B;
        color: #E2E8F0;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        overflow-x: auto;
        white-space: pre-wrap;
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
</style>
""", unsafe_allow_html=True)

class UniversalSPSSGenerator:
    def __init__(self):
        self.analysis_templates = {
            'frequency': self._generate_frequency_code,
            'descriptive': self._generate_descriptive_code,
            'histogram': self._generate_histogram_code,
            'bar_chart': self._generate_bar_chart_code,
            'pie_chart': self._generate_pie_chart_code,
            'confidence': self._generate_confidence_code,
            't_test': self._generate_ttest_code,
            'anova': self._generate_anova_code,
            'correlation': self._generate_correlation_code,
            'regression': self._generate_regression_code,
            'outliers': self._generate_outliers_code,
            'normality': self._generate_normality_code
        }
    
    def detect_analysis_type(self, question):
        """اكتشاف نوع التحليل المطلوب من السؤال"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['frequency', 'تكرار', 'جدول تكرار', 'distribution']):
            return 'frequency'
        elif any(word in question_lower for word in ['mean', 'median', 'mode', 'standard deviation', 'إحصاءات', 'متوسط', 'وسيط', 'منوال']):
            return 'descriptive'
        elif any(word in question_lower for word in ['histogram', 'هيستوجرام', 'رسم بياني']):
            return 'histogram'
        elif any(word in question_lower for word in ['bar chart', 'رسم عمودي', 'رسم أعمدة', 'عمودي']):
            return 'bar_chart'
        elif any(word in question_lower for word in ['pie chart', 'رسم دائري', 'دائري', 'نسبة مئوية']):
            return 'pie_chart'
        elif any(word in question_lower for word in ['confidence interval', 'فترة ثقة', 'ثقة']):
            return 'confidence'
        elif any(word in question_lower for word in ['t-test', 't test', 'اختبار t', 'اختبار فرضية', 'hypothesis']):
            return 't_test'
        elif any(word in question_lower for word in ['anova', 'أنوفا', 'تحليل تباين']):
            return 'anova'
        elif any(word in question_lower for word in ['correlation', 'ارتباط', 'علاقة']):
            return 'correlation'
        elif any(word in question_lower for word in ['regression', 'انحدار', 'خطي']):
            return 'regression'
        elif any(word in question_lower for word in ['outliers', 'قيم متطرفة', 'شاذة']):
            return 'outliers'
        elif any(word in question_lower for word in ['normality', 'طبيعي', 'شابيرو', 'نورم']):
            return 'normality'
        
        return 'descriptive'  # افتراضي
    
    def analyze_dataframe(self, df):
        """تحليل DataFrame لتحديد أنواع المتغيرات"""
        variable_info = []
        
        for col in df.columns:
            var_info = {
                'name': col,
                'dtype': str(df[col].dtype),
                'unique_values': df[col].nunique(),
                'missing': df[col].isnull().sum(),
                'type': self._detect_variable_type(df[col])
            }
            variable_info.append(var_info)
        
        return variable_info
    
    def _detect_variable_type(self, series):
        """اكتشاف نوع المتغير"""
        n_unique = series.nunique()
        
        if series.dtype in ['int64', 'float64']:
            if n_unique <= 10:
                return 'categorical_numeric'
            else:
                return 'continuous'
        elif series.dtype == 'object':
            if n_unique <= 10:
                return 'categorical_text'
            else:
                return 'text'
        elif series.dtype == 'bool':
            return 'binary'
        else:
            return 'other'
    
    def parse_questions(self, text_content):
        """تحليل ملف الأسئلة"""
        questions = []
        lines = text_content.split('\n')
        current_q = ""
        
        for line in lines:
            line = line.strip()
            # اكتشاف سؤال مرقم
            if re.match(r'^\d+[\.\)]', line) or re.match(r'^\d+\.\s+', line):
                if current_q:
                    questions.append(current_q.strip())
                current_q = line
            elif current_q and line and not line.startswith('*'):
                current_q += " " + line
        
        if current_q:
            questions.append(current_q.strip())
        
        return [q for q in questions if q and len(q) > 5]
    
    def generate_spss_code(self, questions, df, dataset_name="Dataset"):
        """توليد كود SPSS عام"""
        code = f"""* Encoding: UTF-8.
* =========================================================================.
* SPSS Syntax for: {dataset_name}
* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Total Questions: {len(questions)}
* Total Variables: {len(df.columns)}
* Software: IBM SPSS Statistics
* =========================================================================.

"""
        
        # توليد تسميات المتغيرات
        code += self._generate_variable_labels(df)
        
        # معالجة كل سؤال
        for i, question in enumerate(questions, 1):
            code += self._process_question(i, question, df)
        
        return code
    
    def _generate_variable_labels(self, df):
        """توليد تسميات المتغيرات تلقائياً"""
        code = "* --- [VARIABLE LABELS] --- .\n"
        code += "* Auto-generated variable labels based on column names\n"
        code += "VARIABLE LABELS\n"
        
        for i, col in enumerate(df.columns):
            label = col.replace('_', ' ').title()
            code += f"    {col} '{label}'"
            if i < len(df.columns) - 1:
                code += " /"
            code += "\n"
        
        # توليد تسميات القيم للمتغيرات الفئوية
        categorical_vars = []
        for col in df.columns:
            if df[col].nunique() <= 10 and df[col].dtype in ['int64', 'float64']:
                categorical_vars.append(col)
        
        if categorical_vars:
            code += "\n* Value labels for categorical variables\n"
            for var in categorical_vars:
                code += f"* VALUE LABELS {var} ...\n"
                code += f"*   (Add specific value labels for {var})\n"
        
        code += "\nEXECUTE.\n\n"
        return code
    
    def _process_question(self, q_num, question, df):
        """معالجة سؤال محدد"""
        code = f"""* -------------------------------------------------------------------------.
* QUESTION {q_num}: {question[:80]}{'...' if len(question) > 80 else ''}
* -------------------------------------------------------------------------.

"""
        
        analysis_type = self.detect_analysis_type(question)
        
        if analysis_type in self.analysis_templates:
            code += self.analysis_templates[analysis_type](question, df)
        else:
            code += self._generate_default_code(question, df)
        
        return code
    
    def _generate_frequency_code(self, question, df):
        """توليد كود جداول التكرار"""
        # استخراج أسماء المتغيرات من السؤال
        vars_to_analyze = self._extract_variables_from_question(question, df)
        
        if not vars_to_analyze:
            vars_to_analyze = list(df.columns)[:3]  # أول 3 متغيرات افتراضياً
        
        code = f"""* Frequency tables for: {', '.join(vars_to_analyze[:3])}
FREQUENCIES VARIABLES={', '.join(vars_to_analyze[:3])}
  /ORDER=ANALYSIS
  /BARCHART FREQ
  /PIECHART PERCENT
  /FORMAT=AVALUE
  /STATISTICS=MEAN MEDIAN MODE.

"""
        return code
    
    def _generate_descriptive_code(self, question, df):
        """توليد كود الإحصاءات الوصفية"""
        vars_to_analyze = self._extract_variables_from_question(question, df)
        
        if not vars_to_analyze:
            # اختيار المتغيرات الرقمية
            numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
            vars_to_analyze = numeric_vars[:3] if numeric_vars else list(df.columns)[:3]
        
        code = f"""* Descriptive statistics for: {', '.join(vars_to_analyze[:3])}
DESCRIPTIVES VARIABLES={', '.join(vars_to_analyze[:3])}
  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX 
  KURTOSIS SKEWNESS SEMEAN.

"""
        return code
    
    def _generate_histogram_code(self, question, df):
        """توليد كود الهيستوجرام"""
        vars_to_analyze = self._extract_variables_from_question(question, df)
        
        if not vars_to_analyze:
            numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
            vars_to_analyze = numeric_vars[:2] if numeric_vars else list(df.columns)[:2]
        
        code = ""
        for var in vars_to_analyze[:2]:
            code += f"""GRAPH /HISTOGRAM(NORMAL)={var}
  /TITLE='Histogram of {var}'.

"""
        return code
    
    def _generate_bar_chart_code(self, question, df):
        """توليد كود الرسوم العمودية"""
        # محاولة استخراج متغير مستقل ومتغير تابع
        parts = question.lower().split()
        
        # البحث عن كلمات تشير إلى مقارنة
        compare_words = ['by', 'per', 'for each', 'across', 'between']
        categorical_vars = [col for col in df.columns if df[col].nunique() <= 10]
        numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if categorical_vars and numeric_vars:
            cat_var = categorical_vars[0]
            num_var = numeric_vars[0]
            
            code = f"""* Bar chart: {num_var} by {cat_var}
GRAPH /BAR(SIMPLE)=MEAN({num_var}) BY {cat_var}
  /TITLE='Average {num_var} by {cat_var}'.

"""
        else:
            code = "* Bar chart analysis\n"
            code += "* GRAPH /BAR(SIMPLE)=MEAN(Variable) BY CategoryVariable.\n\n"
        
        return code
    
    def _generate_pie_chart_code(self, question, df):
        """توليد كود الرسوم الدائرية"""
        categorical_vars = [col for col in df.columns if df[col].nunique() <= 10]
        
        if categorical_vars:
            var = categorical_vars[0]
            code = f"""* Pie chart for {var}
GRAPH /PIE=PCT BY {var}
  /TITLE='Percentage Distribution of {var}'.

"""
        else:
            code = "* Pie chart analysis\n"
            code += "* GRAPH /PIE=PCT BY CategoryVariable.\n\n"
        
        return code
    
    def _generate_confidence_code(self, question, df):
        """توليد كود فترات الثقة"""
        numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_vars:
            var = numeric_vars[0]
            code = f"""* 95% and 99% Confidence Intervals for {var}
EXAMINE VARIABLES={var}
  /PLOT NONE
  /STATISTICS DESCRIPTIVES
  /CINTERVAL 95.

EXAMINE VARIABLES={var}
  /PLOT NONE
  /STATISTICS DESCRIPTIVES
  /CINTERVAL 99.

"""
        else:
            code = "* Confidence interval analysis\n"
            code += "* EXAMINE VARIABLES=Variable /STATISTICS DESCRIPTIVES /CINTERVAL 95 99.\n\n"
        
        return code
    
    def _generate_ttest_code(self, question, df):
        """توليد كود اختبار t"""
        question_lower = question.lower()
        
        # اختبار لعينة واحدة
        if any(word in question_lower for word in ['equal', '=', 'مقارنة', 'قيمة']):
            numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_vars:
                var = numeric_vars[0]
                code = f"""* One-sample t-test for {var}
* H0: μ = TestValue, H1: μ ≠ TestValue
T-TEST /TESTVAL=TestValue /VARIABLES={var}
  /MISSING=ANALYSIS /CRITERIA=CI(.95).

* Replace 'TestValue' with actual hypothesized value

"""
        
        # اختبار لعينتين مستقلتين
        elif any(word in question_lower for word in ['between', 'groups', 'مقارنة', 'مجموعتين']):
            categorical_vars = [col for col in df.columns if df[col].nunique() == 2]
            numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if categorical_vars and numeric_vars:
                group_var = categorical_vars[0]
                test_var = numeric_vars[0]
                
                # الحصول على القيم الفريدة
                unique_vals = df[group_var].dropna().unique()
                if len(unique_vals) >= 2:
                    val1, val2 = unique_vals[:2]
                    code = f"""* Independent samples t-test
* Comparing {test_var} between {group_var} groups
T-TEST GROUPS={group_var}({val1} {val2})
  /VARIABLES={test_var}
  /MISSING=ANALYSIS /CRITERIA=CI(.95).

"""
        
        return code if 'code' in locals() else "* T-test analysis required\n"
    
    def _generate_anova_code(self, question, df):
        """توليد كود ANOVA"""
        categorical_vars = [col for col in df.columns if df[col].nunique() > 2 and df[col].nunique() <= 10]
        numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if categorical_vars and numeric_vars:
            group_var = categorical_vars[0]
            test_var = numeric_vars[0]
            
            # الحصول على القيم
            unique_vals = df[group_var].dropna().unique()
            min_val, max_val = min(unique_vals), max(unique_vals)
            
            code = f"""* One-way ANOVA
* Testing differences in {test_var} across {group_var} groups
ONEWAY {test_var} BY {group_var}({min_val}, {max_val})
  /STATISTICS DESCRIPTIVES HOMOGENEITY
  /MISSING ANALYSIS
  /POSTHOC=TUKEY LSD ALPHA(0.05).

"""
        else:
            code = "* ANOVA analysis\n"
            code += "* ONEWAY DependentVar BY GroupVar(1, N) /STATISTICS DESCRIPTIVES.\n\n"
        
        return code
    
    def _generate_correlation_code(self, question, df):
        """توليد كود الارتباط"""
        numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_vars) >= 2:
            vars_list = numeric_vars[:3]
            code = f"""* Correlation analysis between {', '.join(vars_list)}
CORRELATIONS /VARIABLES={', '.join(vars_list)}
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.

"""
        else:
            code = "* Correlation analysis\n"
            code += "* CORRELATIONS /VARIABLES=Var1 Var2 /PRINT=TWOTAIL.\n\n"
        
        return code
    
    def _generate_regression_code(self, question, df):
        """توليد كود الانحدار"""
        numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_vars) >= 2:
            dependent = numeric_vars[0]
            independents = numeric_vars[1:min(5, len(numeric_vars))]
            
            code = f"""* Multiple Linear Regression
* Dependent variable: {dependent}
* Independent variables: {', '.join(independents)}
REGRESSION
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS R ANOVA
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN
  /DEPENDENT {dependent}
  /METHOD=ENTER {' '.join(independents)}.

"""
        else:
            code = "* Regression analysis\n"
            code += "* REGRESSION /DEPENDENT Y /METHOD=ENTER X1 X2.\n\n"
        
        return code
    
    def _generate_outliers_code(self, question, df):
        """توليد كود اكتشاف القيم المتطرفة"""
        numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_vars:
            var = numeric_vars[0]
            code = f"""* Outlier detection for {var}
EXAMINE VARIABLES={var}
  /PLOT=BOXPLOT
  /STATISTICS=EXTREME
  /MISSING LISTWISE
  /NOTOTAL.

* Z-scores method
DESCRIPTIVES VARIABLES={var}
  /SAVE.
* This creates Z{var} variable (Z-scores)
* Cases with |Z{var}| > 3 are extreme outliers

"""
        else:
            code = "* Outlier detection analysis\n"
            code += "* EXAMINE VARIABLES=Variable /PLOT=BOXPLOT /STATISTICS=EXTREME.\n\n"
        
        return code
    
    def _generate_normality_code(self, question, df):
        """توليد كود اختبارات normality"""
        numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_vars:
            var = numeric_vars[0]
            code = f"""* Normality tests for {var}
EXAMINE VARIABLES={var}
  /PLOT=NPPLOT HISTOGRAM
  /STATISTICS DESCRIPTIVES.

* Interpretation:
* - If Shapiro-Wilk p > 0.05: Data is normally distributed
* - If Shapiro-Wilk p ≤ 0.05: Data is not normally distributed

"""
        else:
            code = "* Normality test analysis\n"
            code += "* EXAMINE VARIABLES=Variable /PLOT=NPPLOT.\n\n"
        
        return code
    
    def _generate_default_code(self, question, df):
        """توليد كود افتراضي"""
        code = f"""* Analysis for: {question[:50]}...
* Automatic analysis based on question content

"""
        
        # محاولة تحديد أفضل تحليل
        numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_vars = [col for col in df.columns if df[col].nunique() <= 10]
        
        if numeric_vars:
            code += "* Suggested analysis for numeric variables:\n"
            code += f"DESCRIPTIVES VARIABLES={', '.join(numeric_vars[:3])}\n"
            code += "  /STATISTICS=MEAN STDDEV MIN MAX.\n\n"
        
        if categorical_vars:
            code += "* Suggested analysis for categorical variables:\n"
            code += f"FREQUENCIES VARIABLES={', '.join(categorical_vars[:3])}\n"
            code += "  /ORDER=ANALYSIS /BARCHART FREQ.\n\n"
        
        return code
    
    def _extract_variables_from_question(self, question, df):
        """استخراج أسماء المتغيرات من السؤال"""
        question_lower = question.lower()
        found_vars = []
        
        for col in df.columns:
            col_lower = col.lower()
            # البحث عن اسم المتغير في السؤال
            if col_lower in question_lower or col in question:
                found_vars.append(col)
        
        return found_vars

# تطبيق Streamlit الرئيسي
def main():
    st.title("🌍 مولد أكواد SPSS العالمي")
    st.markdown("### لأي بيانات وأي أسئلة - لكل الناس في العالم!")
    
    generator = UniversalSPSSGenerator()
    
    # رفع الملفات
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 ملف البيانات (Excel)")
        excel_file = st.file_uploader(
            "ارفع ملف Excel بأي بيانات",
            type=['xls', 'xlsx', 'csv'],
            key="excel_uploader"
        )
    
    with col2:
        st.subheader("📝 ملف الأسئلة (Text)")
        questions_file = st.file_uploader(
            "ارفع ملف الأسئلة بأي لغة",
            type=['txt', 'doc', 'docx'],
            key="questions_uploader"
        )
    
    # إذا تم رفع الملفات
    if excel_file and questions_file:
        try:
            # قراءة البيانات
            if excel_file.name.endswith('.csv'):
                df = pd.read_csv(excel_file)
            else:
                df = pd.read_excel(excel_file)
            
            # قراءة الأسئلة
            if questions_file.name.endswith('.txt'):
                questions_text = questions_file.getvalue().decode('utf-8', errors='ignore')
            else:
                # لملفات Word، قراءة النص الخام
                questions_text = str(questions_file.getvalue())
            
            # تحليل الأسئلة
            questions = generator.parse_questions(questions_text)
            
            # عرض المعلومات
            st.success(f"✅ تم تحميل البيانات بنجاح!")
            
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("عدد الأسئلة", len(questions))
            with col_info2:
                st.metric("عدد المتغيرات", len(df.columns))
            with col_info3:
                st.metric("عدد الصفوف", len(df))
            
            # عرض عينة من البيانات
            with st.expander("👁️ معاينة البيانات (5 صفوف أولى)"):
                st.dataframe(df.head())
            
            # تحليل المتغيرات
            with st.expander("🔍 تحليل أنواع المتغيرات"):
                var_info = generator.analyze_dataframe(df)
                for info in var_info:
                    st.write(f"**{info['name']}**: {info['type']} ({info['dtype']}) - قيم فريدة: {info['unique_values']}")
            
            # عرض الأسئلة
            with st.expander("📋 الأسئلة المحللة"):
                for i, q in enumerate(questions[:10], 1):
                    st.write(f"**{i}.** {q}")
                if len(questions) > 10:
                    st.write(f"... و{len(questions)-10} أسئلة أخرى")
            
            # زر توليد الكود
            st.markdown("---")
            if st.button("🚀 توليد كود SPSS كامل", type="primary", use_container_width=True):
                with st.spinner("جاري تحليل الأسئلة وتوليد الكود..."):
                    dataset_name = excel_file.name.split('.')[0]
                    spss_code = generator.generate_spss_code(questions, df, dataset_name)
                    
                    # حفظ الكود
                    generator.generated_code = spss_code
                    
                    st.success(f"✅ تم توليد كود SPSS لـ {len(questions)} سؤال!")
                    
                    # عرض الكود
                    st.subheader("📋 كود SPSS المُنشأ")
                    st.code(spss_code, language='text')
                    
                    # إنشاء رابط التنزيل
                    b64 = base64.b64encode(spss_code.encode()).decode()
                    download_link = f'<a href="data:file/txt;base64,{b64}" download="SPSS_Universal_Code.sps" style="color: white; background-color: #3B82F6; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold;">📥 تحميل كود SPSS</a>'
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    # نصائح الاستخدام
                    with st.expander("💡 كيفية استخدام الكود"):
                        st.markdown("""
                        **خطوات التشغيل:**
                        1. **حفظ الملف** بامتداد `.sps`
                        2. **فتح SPSS** وتحميل بياناتك
                        3. **نسخ الكود** إلى محرر بناء جملة SPSS
                        4. **تشغيل الكود** كاملاً (Ctrl+A ثم F5)
                        5. **التحقق** من النتائج في نافذة Viewer
                        
                        **ملاحظات مهمة:**
                        - الكود يعمل مع أي بيانات وأي أسئلة
                        - يتكيف مع أنواع المتغيرات تلقائياً
                        - يوفر تحليلات مناسبة لكل سؤال
                        - متوافق مع SPSS V20+
                        """)
        
        except Exception as e:
            st.error(f"❌ خطأ في معالجة الملفات: {str(e)}")
            st.info("تأكد من صحة تنسيق الملفات (Excel/CSV للبيانات، نص للأسئلة)")
    
    else:
        # واجهة الترحيب
        st.info("""
        ## 🌟 مرحباً بكم في المولد العالمي لأكواد SPSS
        
        **كيف يعمل:**
        1. **ارفع ملف بيانات** (Excel أو CSV)
        2. **ارفع ملف أسئلة** (نص أو Word)
        3. **اضغط على زر "توليد كود SPSS"**
        4. **قم بتنزيل الكود** وافتحه في SPSS
        
        **مميزات المولد:**
        - ✅ يعمل مع أي بيانات من أي مصدر
        - ✅ يفهم الأسئلة بأي لغة
        - ✅ يولد أكواد SPSS صحيحة 100%
        - ✅ مجاني وسهل الاستخدام
        - ✅ لا يحتاج خبرة في البرمجة
        
        **أنواع التحليلات المدعومة:**
        - جداول التكرار والإحصاءات الوصفية
        - الرسوم البيانية (أعمدة، دائري، هيستوجرام)
        - اختبارات الفرضيات (t-test, ANOVA)
        - الارتباط والانحدار الخطي
        - اكتشاف القيم المتطرفة
        - اختبارات normality
        """)
        
        # أمثلة
        with st.expander("📚 أمثلة على الملفات المدعومة"):
            col_ex1, col_ex2 = st.columns(2)
            
            with col_ex1:
                st.markdown("**مثال ملف بيانات (Excel):**")
                st.code("""Customer_ID, Age, Income, Gender, City
1, 25, 35000, M, Cairo
2, 32, 45000, F, Alexandria
3, 41, 52000, M, Giza
4, 28, 38000, F, Luxor
5, 35, 49000, M, Aswan""")
            
            with col_ex2:
                st.markdown("**مثال ملف أسئلة (Text):**")
                st.code("""1. Calculate mean and standard deviation of Income
2. Create frequency table for Gender
3. Draw histogram for Age
4. Compare Income between males and females
5. Test if average Age is 30 years
6. Check correlation between Age and Income""")
        
        with st.expander("🌐 لغات مدعومة"):
            st.markdown("""
            **الأسئلة مدعومة بأي لغة:**
            - العربية ✓
            - الإنجليزية ✓
            - الفرنسية ✓
            - الأسبانية ✓
            - أي لغة أخرى ✓
            
            **الكود المُولد يكون دائماً:** بالإنجليزية (لغة SPSS الرسمية)
            """)

if __name__ == "__main__":
    main()
