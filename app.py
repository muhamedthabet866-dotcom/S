import streamlit as st
import pandas as pd
import numpy as np
from docx import Document
import tempfile
import os
import re
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="SPSS Exam Solver",
    page_icon="🎓",
    layout="wide"
)

# العنوان
st.title("🎓 محلل الامتحانات الإحصائية المتقدم")
st.markdown("### حل تلقائي لأي امتحان إحصائي باستخدام SPSS")

class SPSSExamSolver:
    def __init__(self, df: pd.DataFrame, questions_text: str):
        self.df = df
        self.questions_text = questions_text
        self.variable_info = self._analyze_variables()
        self.questions = self._parse_questions()
        
    def _analyze_variables(self) -> Dict:
        """تحليل عميق للمتغيرات من البيانات"""
        variable_info = {}
        
        for col in self.df.columns:
            var_data = self.df[col].dropna()
            
            # معلومات أساسية
            info = {
                'name': col,
                'dtype': str(self.df[col].dtype),
                'n_unique': len(var_data.unique()),
                'missing': self.df[col].isna().sum(),
                'values': []
            }
            
            # تحديد النوع الإحصائي
            if self.df[col].dtype in ['int64', 'float64']:
                if info['n_unique'] <= 10:
                    info['type'] = 'CATEGORICAL'
                    info['values'] = sorted(var_data.unique().tolist())
                else:
                    info['type'] = 'CONTINUOUS'
                    info['stats'] = {
                        'mean': var_data.mean(),
                        'std': var_data.std(),
                        'min': var_data.min(),
                        'max': var_data.max()
                    }
            else:
                info['type'] = 'STRING'
            
            # البحث عن تسميات من البيانات
            if 'x' in col.lower() or 'var' in col.lower():
                # محاولة تخمين معنى المتغير من القيم
                if info['type'] == 'CATEGORICAL':
                    if set(info['values']) == {0, 1}:
                        info['label'] = f"Binary Variable {col}"
                    elif all(v in [1, 2, 3, 4, 5] for v in info['values']):
                        info['label'] = f"Likert Scale {col}"
            
            variable_info[col] = info
        
        return variable_info
    
    def _parse_questions(self) -> List[Dict]:
        """تحليل الأسئلة بشكل متقدم"""
        questions = []
        lines = self.questions_text.split('\n')
        
        current_q = None
        q_num = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # البحث عن بداية سؤال مرقم
            match = re.match(r'^(\d+)[\.\)]\s*(.*)', line)
            if match:
                if current_q:
                    questions.append(current_q)
                
                q_num = int(match.group(1))
                q_text = match.group(2)
                
                current_q = {
                    'number': q_num,
                    'text': q_text,
                    'full_text': line,
                    'variables': [],
                    'analysis_type': 'UNKNOWN',
                    'conditions': []
                }
            elif current_q:
                current_q['full_text'] += " " + line
        
        if current_q:
            questions.append(current_q)
        
        # تحليل كل سؤال
        for q in questions:
            self._analyze_single_question(q)
        
        return questions
    
    def _analyze_single_question(self, question: Dict):
        """تحليل مفصل لسؤال واحد"""
        text = question['full_text'].lower()
        
        # 1. استخراج المتغيرات المذكورة
        found_vars = []
        for var_name, var_info in self.variable_info.items():
            var_lower = var_name.lower()
            
            # البحث بالاسم المباشر
            if var_lower in text:
                found_vars.append(var_name)
            
            # البحث بالمرادفات
            synonyms = self._get_variable_synonyms(var_name, var_info)
            for synonym in synonyms:
                if synonym in text:
                    found_vars.append(var_name)
                    break
        
        question['variables'] = list(set(found_vars))
        
        # 2. تحديد نوع التحليل
        question['analysis_type'] = self._detect_analysis_type(text)
        
        # 3. استخراج الشروط
        question['conditions'] = self._extract_conditions(text)
        
        # 4. استخراج القيم المرجعية
        question['reference_values'] = self._extract_reference_values(text)
    
    def _get_variable_synonyms(self, var_name: str, var_info: Dict) -> List[str]:
        """إرجاع مرادفات للمتغير"""
        synonyms = []
        
        # رموز X شائعة
        if var_name.startswith('X') or var_name.startswith('x'):
            num_match = re.search(r'\d+', var_name)
            if num_match:
                num = num_match.group()
                synonyms.extend([f"x{num}", f"variable {num}", f"var{num}"])
        
        # مرادفات حسب النوع
        if var_info['type'] == 'CONTINUOUS':
            if 'salary' in var_name.lower():
                synonyms.extend(['salary', 'مرتب', 'راتب', 'دخل'])
            elif 'age' in var_name.lower():
                synonyms.extend(['age', 'عمر', 'سن'])
        
        return [s.lower() for s in synonyms]
    
    def _detect_analysis_type(self, text: str) -> str:
        """تحديد نوع التحليل بدقة"""
        
        analysis_patterns = {
            'FREQUENCY_TABLE': [
                r'frequency table', r'جدول تكراري', r'توزيع تكراري',
                r'construct.*frequency', r'إنشاء جدول'
            ],
            'DESCRIPTIVE_STATS': [
                r'mean.*median.*mode', r'متوسط.*وسيط',
                r'standard deviation', r'انحراف معياري',
                r'find.*mean', r'احسب.*المتوسط'
            ],
            'BAR_CHART': [
                r'bar chart', r'رسم بياني عمودي', r'مخطط عمودي',
                r'draw.*bar', r'ارسم.*عمودي'
            ],
            'PIE_CHART': [
                r'pie chart', r'رسم دائري', r'مخطط دائري',
                r'draw.*pie', r'ارسم.*دائري'
            ],
            'HISTOGRAM': [
                r'histogram', r'مدرج تكراري'
            ],
            'CONFIDENCE_INTERVAL': [
                r'confidence interval', r'فترة ثقة',
                r'\d+% confidence', r'ثقة \d+%'
            ],
            'T_TEST_ONE_SAMPLE': [
                r'test.*hypothesis.*equal', r'اختبار.*يساوي',
                r'average.*equal', r'متوسط.*يساوي'
            ],
            'T_TEST_INDEPENDENT': [
                r'difference between', r'اختلاف بين',
                r'compare.*groups', r'مقارنة.*مجموعات',
                r'no significant difference', r'لا يوجد فرق معنوي'
            ],
            'ANOVA': [
                r'anova', r'تحليل تباين',
                r'difference between.*groups', r'اختلاف.*مجموعات',
                r'more than two groups', r'أكثر من مجموعتين'
            ],
            'CORRELATION': [
                r'correlation', r'ارتباط',
                r'relationship between', r'علاقة بين'
            ],
            'REGRESSION': [
                r'regression', r'انحدار',
                r'predict.*from', r'تنبؤ.*من',
                r'linear model', r'نموذج خطي'
            ],
            'CROSS_TABULATION': [
                r'crosstab', r'جدول متقاطع',
                r'relation.*between.*categorical', r'علاقة.*فئوية'
            ]
        }
        
        for analysis_type, patterns in analysis_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return analysis_type
        
        return 'DESCRIPTIVE_STATS'  # إفتراضي
    
    def _extract_conditions(self, text: str) -> List[Dict]:
        """استخراج الشروط من السؤال"""
        conditions = []
        
        # شروط زمنية
        time_patterns = [
            (r'before (\d{4})', 'year_lt'),
            (r'after (\d{4})', 'year_gt'),
            (r'in (\d{4})', 'year_eq')
        ]
        
        for pattern, cond_type in time_patterns:
            match = re.search(pattern, text)
            if match:
                conditions.append({
                    'type': cond_type,
                    'value': int(match.group(1)),
                    'variable': 'year'  # سيتغير حسب السياق
                })
        
        # شروط مقارنة
        comp_patterns = [
            (r'greater than (\d+)', 'gt'),
            (r'less than (\d+)', 'lt'),
            (r'equal to (\d+)', 'eq'),
            (r'between (\d+) and (\d+)', 'between')
        ]
        
        for pattern, cond_type in comp_patterns:
            match = re.search(pattern, text)
            if match:
                if cond_type == 'between':
                    conditions.append({
                        'type': cond_type,
                        'value': [int(match.group(1)), int(match.group(2))]
                    })
                else:
                    conditions.append({
                        'type': cond_type,
                        'value': int(match.group(1))
                    })
        
        # شروط فئوية
        if 'male' in text or 'female' in text:
            conditions.append({
                'type': 'gender',
                'value': 'male' if 'male' in text else 'female'
            })
        
        return conditions
    
    def _extract_reference_values(self, text: str) -> Dict:
        """استخراج القيم المرجعية من السؤال"""
        values = {}
        
        # استخراج أرقام
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            values['numbers'] = [float(n) for n in numbers]
        
        # استخراج نسب مئوية
        percentages = re.findall(r'(\d+)%', text)
        if percentages:
            values['percentages'] = [int(p) for p in percentages]
        
        # استخراج قيم اختبار
        test_matches = re.findall(r'equal (\d+)', text)
        if test_matches:
            values['test_value'] = float(test_matches[0])
        
        return values
    
    def generate_spss_syntax(self) -> str:
        """توليد كود SPSS كامل"""
        
        syntax = f"""* ================================================
* SPSS SYNTAX GENERATED BY EXAM SOLVER
* Dataset: {len(self.df.columns)} variables, {len(self.df)} cases
* Questions analyzed: {len(self.questions)}
* Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
* ================================================

DATASET NAME ExamData WINDOW=FRONT.
DATASET ACTIVATE ExamData.

* ----------------------------------------------------------------
* VARIABLE DEFINITION AND RECODING
* ----------------------------------------------------------------\n"""
        
        # تعريف المتغيرات وإعادة الترميز
        syntax += self._generate_variable_definitions()
        
        # تحليل كل سؤال
        syntax += "\n* ----------------------------------------------------------------"
        syntax += "\n* QUESTION-BY-QUESTION ANALYSIS"
        syntax += "\n* ----------------------------------------------------------------\n"
        
        for q in self.questions:
            syntax += self._generate_question_analysis(q)
        
        # تحليلات إضافية
        syntax += self._generate_additional_analyses()
        
        # إنهاء
        syntax += """
* ----------------------------------------------------------------
* SAVE RESULTS
* ----------------------------------------------------------------
DATASET CLOSE ALL.
SAVE OUTFILE='Exam_Analysis_Results.sav'
  /COMPRESSED.
EXECUTE.

* ================= END OF SYNTAX =================
"""
        
        return syntax
    
    def _generate_variable_definitions(self) -> str:
        """توليد تعريفات المتغيرات وإعادة الترميز"""
        syntax = ""
        
        for var_name, info in self.variable_info.items():
            # إضافة تسمية
            label = info.get('label', var_name)
            syntax += f'VARIABLE LABELS {var_name} "{label}".\n'
            
            # تحديد مستوى القياس
            if info['type'] == 'CONTINUOUS':
                syntax += f'VARIABLE LEVEL {var_name} (SCALE).\n'
            else:
                syntax += f'VARIABLE LEVEL {var_name} (NOMINAL).\n'
            
            # إعادة ترميز المتغيرات الفئوية
            if info['type'] == 'CATEGORICAL' and info['values']:
                syntax += f'VALUE LABELS {var_name}\n'
                for val in info['values']:
                    # محاولة تخمين معنى القيمة
                    if val == 0:
                        label = "No/False/Female"
                    elif val == 1:
                        label = "Yes/True/Male"
                    elif val == 2:
                        label = "Sometimes/Other"
                    else:
                        label = f"Value {val}"
                    
                    syntax += f'  {val} "{label}"\n'
                syntax += '.\n'
            
            # إنشاء متغيرات جديدة للشروط
            syntax += self._generate_derived_variables(var_name, info)
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def _generate_derived_variables(self, var_name: str, info: Dict) -> str:
        """إنشاء متغيرات مشتقة"""
        syntax = ""
        
        # إذا كان متغير سنة، ننشئ فئات زمنية
        if 'year' in var_name.lower() or 'built' in var_name.lower():
            syntax += f"* Create time categories for {var_name}\n"
            syntax += f"IF ({var_name} < 1990) time_cat_{var_name} = 1.\n"
            syntax += f"IF ({var_name} >= 1990 AND {var_name} <= 2000) time_cat_{var_name} = 2.\n"
            syntax += f"IF ({var_name} > 2000) time_cat_{var_name} = 3.\n"
            syntax += f"VARIABLE LABELS time_cat_{var_name} 'Time Categories for {var_name}'.\n"
            syntax += f"VALUE LABELS time_cat_{var_name}\n"
            syntax += "  1 'Before 1990'\n"
            syntax += "  2 '1990-2000'\n"
            syntax += "  3 'After 2000'\n.\n"
        
        # إذا كان متغير راتب، ننشئ فئات
        elif 'salary' in var_name.lower() or 'income' in var_name.lower():
            syntax += f"* Create salary groups for {var_name}\n"
            syntax += f"IF ({var_name} < 40000) salary_group = 1.\n"
            syntax += f"IF ({var_name} >= 40000 AND {var_name} < 70000) salary_group = 2.\n"
            syntax += f"IF ({var_name} >= 70000) salary_group = 3.\n"
            syntax += f"VARIABLE LABELS salary_group 'Salary Groups'.\n"
            syntax += f"VALUE LABELS salary_group\n"
            syntax += "  1 'Low (<40K)'\n"
            syntax += "  2 'Medium (40K-70K)'\n"
            syntax += "  3 'High (>70K)'\n.\n"
        
        return syntax
    
    def _generate_question_analysis(self, question: Dict) -> str:
        """توليد تحليل لسؤال معين"""
        syntax = f"\n* QUESTION {question['number']}: {question['text'][:50]}...\n"
        syntax += f"* Analysis Type: {question['analysis_type']}\n"
        
        if question['variables']:
            syntax += f"* Variables: {', '.join(question['variables'])}\n"
        
        # توليد الكود بناءً على نوع التحليل
        analysis_funcs = {
            'FREQUENCY_TABLE': self._generate_frequency_analysis,
            'DESCRIPTIVE_STATS': self._generate_descriptive_analysis,
            'BAR_CHART': self._generate_chart_analysis,
            'PIE_CHART': self._generate_chart_analysis,
            'HISTOGRAM': self._generate_chart_analysis,
            'CONFIDENCE_INTERVAL': self._generate_confidence_analysis,
            'T_TEST_ONE_SAMPLE': self._generate_ttest_analysis,
            'T_TEST_INDEPENDENT': self._generate_ttest_independent,
            'ANOVA': self._generate_anova_analysis,
            'CORRELATION': self._generate_correlation_analysis,
            'REGRESSION': self._generate_regression_analysis,
            'CROSS_TABULATION': self._generate_crosstab_analysis
        }
        
        func = analysis_funcs.get(question['analysis_type'], self._generate_descriptive_analysis)
        syntax += func(question)
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def _generate_frequency_analysis(self, question: Dict) -> str:
        """تحليل التكرارات"""
        if not question['variables']:
            return "* No variables specified for frequency analysis\n"
        
        syntax = "FREQUENCIES VARIABLES="
        syntax += " ".join(question['variables'][:5]) + "\n"
        syntax += "  /FORMAT=NOTABLE\n"
        syntax += "  /BARCHART FREQ\n"
        syntax += "  /PIECHART FREQ\n"
        syntax += "  /ORDER=ANALYSIS.\n"
        
        # جداول متقاطعة إذا كان هناك متغيرين
        if len(question['variables']) >= 2:
            syntax += f"\n* Cross-tabulation for {question['variables'][0]} by {question['variables'][1]}\n"
            syntax += f"CROSSTABS\n"
            syntax += f"  /TABLES={question['variables'][0]} BY {question['variables'][1]}\n"
            syntax += "  /FORMAT=AVALUE TABLES\n"
            syntax += "  /CELLS=COUNT ROW COLUMN TOTAL\n"
            syntax += "  /COUNT ROUND CELL.\n"
        
        return syntax
    
    def _generate_descriptive_analysis(self, question: Dict) -> str:
        """تحليل وصفي"""
        if not question['variables']:
            vars_to_use = list(self.variable_info.keys())[:5]
        else:
            vars_to_use = question['variables']
        
        syntax = "DESCRIPTIVES VARIABLES="
        syntax += " ".join(vars_to_use) + "\n"
        syntax += "  /SAVE\n"
        syntax += "  /STATISTICS=MEAN STDDEV MIN MAX SEMEAN KURTOSIS SKEWNESS.\n"
        
        # Explore لكل متغير
        for var in vars_to_use[:3]:
            if self.variable_info[var]['type'] == 'CONTINUOUS':
                syntax += f"\nEXAMINE VARIABLES={var}\n"
                syntax += "  /PLOT=BOXPLOT HISTOGRAM NPPLOT\n"
                syntax += "  /COMPARE VARIABLE\n"
                syntax += "  /STATISTICS=NONE\n"
                syntax += "  /CINTERVAL 95\n"
                syntax += "  /MISSING LISTWISE\n"
                syntax += "  /NOTOTAL.\n"
        
        return syntax
    
    def _generate_chart_analysis(self, question: Dict) -> str:
        """تحليل الرسوم البيانية"""
        if not question['variables']:
            return "* No variables specified for chart\n"
        
        chart_type = question['analysis_type']
        var1 = question['variables'][0]
        
        if chart_type == 'BAR_CHART':
            if len(question['variables']) >= 2:
                var2 = question['variables'][1]
                syntax = f"GRAPH\n"
                syntax += f"  /BAR(GROUPED)=MEAN({var2}) BY {var1}\n"
                syntax += f"  /MISSING=REPORT.\n"
            else:
                syntax = f"GRAPH\n"
                syntax += f"  /BAR(SIMPLE)=COUNT BY {var1}\n"
                syntax += f"  /MISSING=REPORT.\n"
        
        elif chart_type == 'PIE_CHART':
            syntax = f"GRAPH\n"
            syntax += f"  /PIE=PCT BY {var1}\n"
            syntax += f"  /MISSING=REPORT.\n"
        
        elif chart_type == 'HISTOGRAM':
            syntax = f"GRAPH\n"
            syntax += f"  /HISTOGRAM={var1}\n"
            syntax += f"  /NORMAL\n"
            syntax += f"  /MISSING=REPORT.\n"
        
        return syntax
    
    def _generate_confidence_analysis(self, question: Dict) -> str:
        """تحليل فترات الثقة"""
        if not question['variables']:
            return "* No variables for confidence intervals\n"
        
        syntax = ""
        for var in question['variables'][:3]:
            if self.variable_info[var]['type'] == 'CONTINUOUS':
                syntax += f"EXAMINE VARIABLES={var}\n"
                syntax += "  /PLOT NONE\n"
                syntax += "  /STATISTICS DESCRIPTIVES\n"
                syntax += "  /CINTERVAL 95 99\n"
                syntax += "  /MISSING LISTWISE.\n\n"
        
        return syntax
    
    def _generate_ttest_analysis(self, question: Dict) -> str:
        """اختبار t لعينة واحدة"""
        if not question['variables']:
            return "* No variables for t-test\n"
        
        test_value = question.get('reference_values', {}).get('test_value', 0)
        
        syntax = "T-TEST\n"
        syntax += f"  /TESTVAL={test_value}\n"
        syntax += f"  /MISSING=ANALYSIS\n"
        syntax += f"  /VARIABLES={question['variables'][0]}\n"
        syntax += "  /CRITERIA=CI(.95).\n"
        
        return syntax
    
    def _generate_ttest_independent(self, question: Dict) -> str:
        """اختبار t لعينتين مستقلتين"""
        if len(question['variables']) < 2:
            return "* Need group and test variables\n"
        
        group_var = question['variables'][0]
        test_var = question['variables'][1]
        
        syntax = f"T-TEST GROUPS={group_var}\n"
        syntax += f"  /VARIABLES={test_var}\n"
        syntax += f"  /MISSING=ANALYSIS\n"
        syntax += "  /CRITERIA=CI(.95).\n"
        
        return syntax
    
    def _generate_anova_analysis(self, question: Dict) -> str:
        """تحليل ANOVA"""
        if len(question['variables']) < 2:
            return "* Need factor and dependent variables\n"
        
        factor_var = question['variables'][0]
        dv_vars = question['variables'][1:]
        
        syntax = ""
        for dv in dv_vars[:2]:
            syntax += f"ONEWAY {dv} BY {factor_var}\n"
            syntax += "  /STATISTICS DESCRIPTIVES HOMOGENEITY BROWNFORSYTHE WELCH\n"
            syntax += "  /MISSING ANALYSIS\n"
            syntax += "  /POSTHOC=TUKEY LSD ALPHA(0.05).\n\n"
        
        return syntax
    
    def _generate_correlation_analysis(self, question: Dict) -> str:
        """تحليل الارتباط"""
        if not question['variables']:
            vars_to_use = list(self.variable_info.keys())[:5]
        else:
            vars_to_use = question['variables']
        
        syntax = "CORRELATIONS\n"
        syntax += "  /VARIABLES="
        syntax += " ".join(vars_to_use) + "\n"
        syntax += "  /PRINT=TWOTAIL NOSIG\n"
        syntax += "  /MISSING=PAIRWISE.\n"
        
        # مصفوفة الانتشار
        if len(vars_to_use) >= 2:
            syntax += f"\nGRAPH\n"
            syntax += f"  /SCATTERPLOT(MATRIX)={' '.join(vars_to_use[:4])}\n"
            syntax += f"  /MISSING=LISTWISE.\n"
        
        return syntax
    
    def _generate_regression_analysis(self, question: Dict) -> str:
        """تحليل الانحدار"""
        if len(question['variables']) < 2:
            return "* Need dependent and independent variables\n"
        
        dv = question['variables'][0]
        ivs = question['variables'][1:4]  # أول 3 متغيرات مستقلة
        
        syntax = f"REGRESSION\n"
        syntax += f"  /MISSING LISTWISE\n"
        syntax += f"  /STATISTICS COEFF OUTS R ANOVA\n"
        syntax += f"  /CRITERIA=PIN(.05) POUT(.10)\n"
        syntax += f"  /NOORIGIN\n"
        syntax += f"  /DEPENDENT {dv}\n"
        syntax += f"  /METHOD=ENTER {' '.join(ivs)}.\n"
        
        return syntax
    
    def _generate_crosstab_analysis(self, question: Dict) -> str:
        """تحليل الجداول المتقاطعة"""
        if len(question['variables']) < 2:
            return "* Need two variables for crosstab\n"
        
        row_var = question['variables'][0]
        col_var = question['variables'][1]
        
        syntax = f"CROSSTABS\n"
        syntax += f"  /TABLES={row_var} BY {col_var}\n"
        syntax += "  /FORMAT=AVALUE TABLES\n"
        syntax += "  /STATISTICS=CHISQ PHI\n"
        syntax += "  /CELLS=COUNT ROW COLUMN TOTAL\n"
        syntax += "  /COUNT ROUND CELL.\n"
        
        return syntax
    
    def _generate_additional_analyses(self) -> str:
        """تحليلات إضافية تلقائية"""
        syntax = """
* ----------------------------------------------------------------
* AUTOMATIC ADDITIONAL ANALYSES
* ----------------------------------------------------------------

* 1. Normality tests for all continuous variables
DATASET ACTIVATE ExamData.
EXAMINE VARIABLES=ALL
  /PLOT=NPPLOT
  /COMPARE VARIABLE
  /STATISTICS=NONE
  /CINTERVAL 95
  /MISSING LISTWISE
  /NOTOTAL.

* 2. Outlier detection
EXAMINE VARIABLES=ALL
  /PLOT=BOXPLOT
  /COMPARE VARIABLE
  /STATISTICS=EXTREME
  /CINTERVAL 95
  /MISSING LISTWISE
  /NOTOTAL.

* 3. Correlation matrix for all continuous variables
CORRELATIONS
  /VARIABLES=ALL
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.

* 4. Factor analysis (if many variables)
"""
        
        if len(self.df.columns) > 5:
            syntax += """
FACTOR
  /VARIABLES=ALL
  /MISSING=LISTWISE
  /ANALYSIS=ALL
  /PRINT=INITIAL EXTRACTION ROTATION
  /CRITERIA=MINEIGEN(1) ITERATE(25)
  /EXTRACTION=PC
  /CRITERIA=ITERATE(25)
  /ROTATION=VARIMAX
  /METHOD=CORRELATION.
"""
        
        return syntax

# ===== واجهة Streamlit =====

def main():
    # شريط جانبي
    with st.sidebar:
        st.header("⚙️ إعدادات الامتحان")
        
        st.subheader("📁 رفع ملفات الامتحان")
        
        excel_file = st.file_uploader(
            "ملف البيانات (Excel)",
            type=['xls', 'xlsx', 'csv'],
            help="ارفع ملف البيانات الخام"
        )
        
        word_file = st.file_uploader(
            "ملف الأسئلة (Word)",
            type=['docx', 'doc'],
            help="ارفع ملف الأسئلة الإحصائية"
        )
        
        st.markdown("---")
        
        # خيارات متقدمة
        with st.expander("⚡ خيارات متقدمة"):
            auto_detect = st.checkbox("التعرف التلقائي على المتغيرات", value=True)
            generate_all = st.checkbox("توليد جميع التحليلات", value=True)
            debug_mode = st.checkbox("وضع التصحيح", value=False)
        
        solve_button = st.button(
            "🎯 حل الامتحان تلقائياً",
            type="primary",
            use_container_width=True
        )
    
    # المنطقة الرئيسية
    if not excel_file:
        st.info("👈 ابدأ برفع ملف البيانات من الشريط الجانبي")
        
        # شرح الميزات
        st.markdown("""
        ## 📋 ميزات محلل الامتحانات المتقدم:
        
        ### ✅ ما يفعله البرنامج:
        1. **يقرأ المتغيرات الحقيقية** من ملف Excel
        2. **يحلل أنواع البيانات** تلقائياً (فئوي/مستمر)
        3. **يستخرج الأسئلة** من ملف Word
        4. **يتعرف على نوع التحليل** المطلوب لكل سؤال
        5. **يولد كود SPSS كامل** لحل كل سؤال
        6. **ينشئ متغيرات جديدة** حسب الحاجة
        7. **يضيف تحليلات تلقائية** إضافية
        
        ### 🎯 أنواع الأسئلة المدعومة:
        - جداول التكرارات والتوزيعات
        - الإحصاءات الوصفية (متوسط، انحراف معياري...)
        - جميع أنواع الرسوم البيانية
        - فترات الثقة (95%، 99%)
        - اختبارات t (عينة واحدة/عينتين)
        - تحليل ANOVA
        - معاملات الارتباط
        - تحليل الانحدار
        - اختبارات كاي مربع
        
        ### 📊 مثال على المخرجات:
        - كود SPSS جاهز للتشغيل
        - تعريف كامل للمتغيرات
        - إعادة ترميز القيم
        - تحليل لكل سؤال
        - تحليلات إضافية تلقائية
        """)
    
    elif excel_file and solve_button:
        try:
            # تحميل البيانات
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(excel_file.getvalue())
                tmp_path = tmp.name
            
            df = pd.read_excel(tmp_path)
            os.unlink(tmp_path)
            
            # تحميل الأسئلة
            if word_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                    tmp.write(word_file.getvalue())
                    tmp_path = tmp.name
                
                doc = Document(tmp_path)
                questions_text = "\n".join([para.text for para in doc.paragraphs])
                os.unlink(tmp_path)
            else:
                questions_text = "No questions file provided"
            
            # عرض تقدم
            progress_bar = st.progress(0)
            status = st.empty()
            
            status.text("🔍 جاري تحليل البيانات...")
            solver = SPSSExamSolver(df, questions_text)
            progress_bar.progress(30)
            
            status.text("📊 تحليل المتغيرات...")
            progress_bar.progress(50)
            
            status.text("❓ تحليل الأسئلة...")
            progress_bar.progress(70)
            
            status.text("⚙️ توليد كود SPSS...")
            spss_code = solver.generate_spss_syntax()
            progress_bar.progress(100)
            
            status.text("✅ تم حل الامتحان بنجاح!")
            
            # عرض النتائج
            st.success(f"### ✨ تم تحليل {len(df.columns)} متغير و{len(solver.questions)} سؤال")
            
            # معلومات البيانات
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("المتغيرات", len(df.columns))
            with col2:
                st.metric("الحالات", len(df))
            with col3:
                st.metric("الأسئلة", len(solver.questions))
            
            # عرض المتغيرات
            with st.expander("📋 المتغيرات المكتشفة"):
                var_data = []
                for var_name, info in solver.variable_info.items():
                    var_data.append({
                        'المتغير': var_name,
                        'النوع': info['type'],
                        'القيم الفريدة': info['n_unique'],
                        'القيم المفقودة': info['missing']
                    })
                st.dataframe(pd.DataFrame(var_data))
            
            # عرض الأسئلة وتحليلها
            with st.expander("📝 تحليل الأسئلة"):
                for q in solver.questions[:10]:
                    st.markdown(f"**السؤال {q['number']}:** {q['text']}")
                    st.markdown(f"- **نوع التحليل:** {q['analysis_type']}")
                    if q['variables']:
                        st.markdown(f"- **المتغيرات:** {', '.join(q['variables'])}")
                    st.markdown("---")
            
            # عرض كود SPSS
            st.markdown("---")
            st.subheader("📜 كود SPSS الكامل")
            st.code(spss_code, language='spss', height=500)
            
            # زر التحميل
            st.download_button(
                label="💾 تحميل ملف SPSS (.sps)",
                data=spss_code,
                file_name="Exam_Solution.sps",
                mime="text/plain",
                use_container_width=True
            )
            
            # تحليل إضافي
            with st.expander("📈 تحليل البيانات الإحصائي"):
                st.write("**ملخص إحصائي:**")
                st.write(df.describe())
                
                st.write("**معلومات الأنواع:**")
                type_counts = pd.Series([info['type'] for info in solver.variable_info.values()]).value_counts()
                st.write(type_counts)
            
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")
            st.error("تفاصيل الخطأ:")
            st.code(str(e))

if __name__ == "__main__":
    main()
