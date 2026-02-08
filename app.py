import streamlit as st
import pandas as pd
import numpy as np
import re
import base64
from datetime import datetime
import io

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="SPSS Code Generator - Universal Version",
    page_icon="📊",
    layout="wide"
)

st.title("📊 SPSS Code Generator - Universal Version")
st.markdown("### Generates SPSS syntax for any exam")

class SPSSUniversalGenerator:
    def __init__(self):
        self.variable_mapping = {}
        self.data_types = {}
        self.question_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self):
        """تهيئة الأنماط للتعرف على الأسئلة"""
        return {
            # الأنماط الشائعة للأسئلة الإحصائية
            'frequency': [
                r'frequency.*table',
                r'freq.*distribut',
                r'count.*categor',
                r'tabulate.*'
            ],
            'descriptive': [
                r'mean.*median.*mode',
                r'descriptive.*statistics',
                r'average.*',
                r'calculate.*statistics',
                r'measures.*central.*tendency'
            ],
            'visualization': [
                r'histogram',
                r'bar.*chart',
                r'pie.*chart',
                r'graph',
                r'plot',
                r'visualize'
            ],
            'comparison': [
                r'compare.*group',
                r'by.*category',
                r'each.*group',
                r'split.*by',
                r'separate.*by'
            ],
            'correlation': [
                r'correlation',
                r'relationship.*between',
                r'association',
                r'correlate'
            ],
            'regression': [
                r'regression',
                r'predict.*',
                r'linear.*model',
                r'multiple.*regression'
            ],
            't_test': [
                r't.*test',
                r'compare.*means',
                r'independent.*sample',
                r'paired.*sample'
            ],
            'anova': [
                r'anova',
                r'analysis.*variance',
                r'compare.*more.*groups',
                r'f.*test'
            ],
            'chi_square': [
                r'chi.*square',
                r'chi.*squared',
                r'association.*categorical',
                r'contingency.*table'
            ],
            'confidence': [
                r'confidence.*interval',
                r'ci.*',
                r'interval.*estimate'
            ],
            'normality': [
                r'normality',
                r'normal.*distribut',
                r'shapiro.*wilk',
                r'kolmogorov.*smirnov'
            ],
            'outliers': [
                r'outlier',
                r'extreme.*value',
                r'unusual.*observation',
                r'detect.*outlier'
            ],
            'recode': [
                r'recode',
                r'categorize',
                r'group.*variable',
                r'create.*class'
            ],
            'transform': [
                r'transform',
                r'compute',
                r'create.*variable',
                r'new.*variable'
            ]
        }
    
    def create_download_link(self, content, filename):
        """إنشاء رابط تنزيل"""
        b64 = base64.b64encode(content.encode()).decode()
        return f'<a href="data:file/txt;base64,{b64}" download="{filename}" style="color: white; background-color: #3B82F6; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold;">📥 Download {filename}</a>'
    
    def detect_data_types(self, df):
        """اكتشاف أنواع البيانات في DataFrame"""
        data_types = {}
        for col in df.columns:
            # محاولة تحويل إلى رقم
            try:
                pd.to_numeric(df[col].dropna())
                # إذا نجح، تحقق إذا كان فئوي (عدد قيم فريد < 10)
                if df[col].nunique() <= 10 and df[col].dropna().apply(lambda x: float(x).is_integer()).all():
                    data_types[col] = 'categorical_numeric'
                else:
                    data_types[col] = 'continuous'
            except:
                # إذا فشل، فهو نصي
                if df[col].nunique() <= 15:
                    data_types[col] = 'categorical_text'
                else:
                    data_types[col] = 'text'
        
        # حفظ في الكائن
        self.data_types = data_types
        return data_types
    
    def generate_variable_labels(self, df):
        """إنشاء تسميات متغيرات ذكية"""
        labels = []
        for col in df.columns:
            # محاولة تخمين التسمية بناءً على اسم المتغير
            col_lower = col.lower()
            
            if any(word in col_lower for word in ['age', 'عمر']):
                label = 'Age'
            elif any(word in col_lower for word in ['salary', 'wage', 'دخل', 'راتب']):
                label = 'Salary'
            elif any(word in col_lower for word in ['gender', 'sex', 'جنس']):
                label = 'Gender'
            elif any(word in col_lower for word in ['education', 'تعليم']):
                label = 'Education Level'
            elif any(word in col_lower for word in ['score', 'درجة', 'mark', 'علامة']):
                label = 'Score'
            elif any(word in col_lower for word in ['height', 'طول']):
                label = 'Height'
            elif any(word in col_lower for word in ['weight', 'وزن']):
                label = 'Weight'
            elif any(word in col_lower for word in ['satisfaction', 'رضا']):
                label = 'Satisfaction Level'
            elif any(word in col_lower for word in ['time', 'وقت']):
                label = 'Time'
            elif any(word in col_lower for word in ['count', 'عدد']):
                label = 'Count'
            elif any(word in col_lower for word in ['price', 'سعر']):
                label = 'Price'
            elif any(word in col_lower for word in ['quantity', 'كمية']):
                label = 'Quantity'
            elif any(word in col_lower for word in ['rate', 'معدل']):
                label = 'Rate'
            elif any(word in col_lower for word in ['percentage', 'نسبة']):
                label = 'Percentage'
            elif any(word in col_lower for word in ['frequency', 'تكرار']):
                label = 'Frequency'
            elif any(word in col_lower for word in ['category', 'فئة']):
                label = 'Category'
            elif any(word in col_lower for word in ['group', 'مجموعة']):
                label = 'Group'
            else:
                # استخدام اسم المتغير مع تحسين التنسيق
                label = col.replace('_', ' ').title()
            
            labels.append(f"{col} '{label}'")
        
        return labels
    
    def generate_value_labels(self, df):
        """إنشاء تسميات القيم للمتغيرات الفئوية"""
        code = ""
        value_label_lines = []
        
        for col in df.columns:
            if self.data_types.get(col) in ['categorical_numeric', 'categorical_text']:
                unique_vals = df[col].dropna().unique()
                
                # إذا كانت قيماً نصية
                if self.data_types[col] == 'categorical_text':
                    # تعيين رموز رقمية
                    val_mapping = {val: i+1 for i, val in enumerate(sorted(unique_vals))}
                    line = f"    /{col} "
                    for val, code_val in val_mapping.items():
                        line += f"{code_val} '{val}' "
                    value_label_lines.append(line.strip())
                
                # إذا كانت قيماً رقمية مع عدد محدود
                elif len(unique_vals) <= 10:
                    line = f"    /{col} "
                    for val in sorted(unique_vals):
                        try:
                            val_str = str(int(float(val))) if float(val).is_integer() else str(float(val))
                            line += f"{val_str} 'Value {val_str}' "
                        except:
                            continue
                    value_label_lines.append(line.strip())
        
        if value_label_lines:
            code += "VALUE LABELS\n"
            code += "\n".join(value_label_lines)
            code += ".\n\n"
        
        return code
    
    def parse_questions(self, text_content):
        """تحليل الأسئلة من ملف النص"""
        questions = []
        lines = text_content.split('\n')
        current_q = ""
        q_number = 1
        
        for line in lines:
            line = line.strip()
            
            # التعرف على بداية سؤال جديد
            if re.match(r'^\d+[\.\)]', line) or re.match(r'^\d+\.\s+', line) or re.match(r'^Q\d+:', line):
                if current_q:
                    questions.append(current_q.strip())
                    current_q = ""
                # إزالة الرقم وعلامات الترقيم
                clean_line = re.sub(r'^\d+[\.\)]\s*', '', line)
                clean_line = re.sub(r'^Q\d+:\s*', '', clean_line)
                current_q = clean_line
            elif current_q and line and not line.startswith('*'):
                current_q += " " + line
            elif not current_q and line and len(line) > 10:  # سؤال بدون رقم
                current_q = line
        
        if current_q:
            questions.append(current_q.strip())
        
        return [q for q in questions if q and len(q) > 3]
    
    def detect_question_type(self, question):
        """اكتشاف نوع السؤال بناءً على النمط"""
        q_lower = question.lower()
        detected_types = []
        
        for q_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, q_lower):
                    detected_types.append(q_type)
                    break
        
        return detected_types if detected_types else ['general']
    
    def generate_spss_code(self, questions, df, dataset_name="Dataset"):
        """إنشاء كود SPSS"""
        # اكتشاف أنواع البيانات
        self.detect_data_types(df)
        
        code = f"""* Encoding: UTF-8.
* =========================================================================.
* SPSS Syntax for: {dataset_name}
* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Total Questions: {len(questions)}
* Total Variables: {len(df.columns)}
* SPSS Version: Universal
* =========================================================================.

"""
        
        # قسم تعريف المتغيرات
        code += self._generate_variable_section(df)
        
        # قسم الأسئلة
        code += self._generate_questions_section(questions, df)
        
        return code
    
    def _generate_variable_section(self, df):
        """إنشاء قسم تعريف المتغيرات"""
        code = """* --- [VARIABLE DEFINITIONS] --- .

"""
        
        # تسميات المتغيرات
        var_labels = self.generate_variable_labels(df)
        code += f"VARIABLE LABELS\n    {' /'.join(var_labels)}.\n\n"
        
        # تسميات القيم
        code += self.generate_value_labels(df)
        
        # معلومات حول المتغيرات
        code += "* Variable Information:\n"
        for col in df.columns:
            dtype = self.data_types.get(col, 'unknown')
            code += f"* {col}: {dtype}, Missing: {df[col].isna().sum()}/{len(df)}, Unique: {df[col].nunique()}\n"
        
        code += "EXECUTE.\n\n"
        
        return code
    
    def _generate_questions_section(self, questions, df):
        """إنشاء قسم الأسئلة"""
        code = ""
        
        for i, question in enumerate(questions, 1):
            q_types = self.detect_question_type(question)
            clean_q = question[:80].replace('"', "'") + "..." if len(question) > 80 else question.replace('"', "'")
            
            code += f"""* -------------------------------------------------------------------------.
* QUESTION {i}: {clean_q}
* Detected Types: {', '.join(q_types)}
* -------------------------------------------------------------------------.

"""
            
            # إنشاء الكود بناءً على نوع السؤال
            for q_type in q_types:
                if q_type == 'frequency':
                    code += self._generate_frequency_code(df)
                elif q_type == 'descriptive':
                    code += self._generate_descriptive_code(df)
                elif q_type == 'visualization':
                    code += self._generate_visualization_code(df, question)
                elif q_type == 'comparison':
                    code += self._generate_comparison_code(df, question)
                elif q_type == 'correlation':
                    code += self._generate_correlation_code(df)
                elif q_type == 'regression':
                    code += self._generate_regression_code(df, question)
                elif q_type == 't_test':
                    code += self._generate_ttest_code(df, question)
                elif q_type == 'anova':
                    code += self._generate_anova_code(df, question)
                elif q_type == 'chi_square':
                    code += self._generate_chisquare_code(df)
                elif q_type == 'confidence':
                    code += self._generate_confidence_code(df)
                elif q_type == 'normality':
                    code += self._generate_normality_code(df)
                elif q_type == 'outliers':
                    code += self._generate_outliers_code(df)
                elif q_type == 'recode':
                    code += self._generate_recode_code(df, question, i)
                elif q_type == 'transform':
                    code += self._generate_transform_code(df, question, i)
                else:
                    code += self._generate_general_code(df, question, i)
            
            code += "\n"
        
        return code
    
    def _generate_frequency_code(self, df):
        """إنشاء كود الجداول التكرارية"""
        categorical_vars = [col for col in df.columns 
                          if self.data_types.get(col) in ['categorical_numeric', 'categorical_text']]
        
        if categorical_vars:
            code = f"""* Frequency tables for categorical variables
FREQUENCIES VARIABLES={' '.join(categorical_vars[:5])} 
  /ORDER=ANALYSIS 
  /FORMAT=AVALUE 
  /STATISTICS=NONE 
  /BARCHART FREQ 
  /PIECHART FREQ.
"""
            if len(categorical_vars) > 5:
                code += f"""
* Additional categorical variables
FREQUENCIES VARIABLES={' '.join(categorical_vars[5:10])} 
  /ORDER=ANALYSIS.
"""
        else:
            code = """* No categorical variables found for frequency tables
* Consider recoding continuous variables if needed
"""
        
        return code + "\n"
    
    def _generate_descriptive_code(self, df):
        """إنشاء كود الإحصاءات الوصفية"""
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if continuous_vars:
            vars_list = ' '.join(continuous_vars[:5])
            code = f"""* Descriptive statistics for continuous variables
DESCRIPTIVES VARIABLES={vars_list}
  /STATISTICS=MEAN STDDEV MIN MAX SEMEAN KURTOSIS SKEWNESS.

FREQUENCIES VARIABLES={vars_list}
  /FORMAT=NOTABLE
  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE SKEWNESS SESKEW KURTOSIS SEKURT.
"""
        else:
            code = """* Descriptive statistics
* Apply to relevant variables based on your data
DESCRIPTIVES VARIABLES=ALL
  /STATISTICS=MEAN STDDEV MIN MAX.
"""
        
        return code + "\n"
    
    def _generate_visualization_code(self, df, question):
        """إنشاء كود التصورات البيانية"""
        q_lower = question.lower()
        code = ""
        
        if 'histogram' in q_lower:
            continuous_vars = [col for col in df.columns 
                             if self.data_types.get(col) == 'continuous']
            if continuous_vars:
                for var in continuous_vars[:3]:
                    code += f"""GRAPH /HISTOGRAM(NORMAL)={var}
  /TITLE='Histogram of {var}'.
"""
        
        if 'bar' in q_lower and 'chart' in q_lower:
            categorical_vars = [col for col in df.columns 
                              if self.data_types.get(col) in ['categorical_numeric', 'categorical_text']]
            continuous_vars = [col for col in df.columns 
                             if self.data_types.get(col) == 'continuous']
            
            if categorical_vars and continuous_vars:
                cat_var = categorical_vars[0]
                cont_var = continuous_vars[0]
                code += f"""GRAPH /BAR(SIMPLE)=MEAN({cont_var}) BY {cat_var}
  /TITLE='Bar Chart: Mean {cont_var} by {cat_var}'.
"""
        
        if 'pie' in q_lower and 'chart' in q_lower:
            categorical_vars = [col for col in df.columns 
                              if self.data_types.get(col) in ['categorical_numeric', 'categorical_text']]
            if categorical_vars:
                code += f"""GRAPH /PIE={categorical_vars[0]}
  /TITLE='Pie Chart: {categorical_vars[0]} Distribution'.
"""
        
        if not code:
            code = """* Visualization
GRAPH /HISTOGRAM=VAR1.
GRAPH /BAR(SIMPLE)=MEAN(VAR1) BY VAR2.
"""
        
        return code + "\n"
    
    def _generate_comparison_code(self, df, question):
        """إنشاء كود المقارنات بين المجموعات"""
        categorical_vars = [col for col in df.columns 
                          if self.data_types.get(col) in ['categorical_numeric', 'categorical_text']]
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if categorical_vars and continuous_vars:
            group_var = categorical_vars[0]
            analysis_vars = ' '.join(continuous_vars[:3])
            
            code = f"""* Compare groups for: {analysis_vars}
SORT CASES BY {group_var}.
SPLIT FILE LAYERED BY {group_var}.

DESCRIPTIVES VARIABLES={analysis_vars}
  /STATISTICS=MEAN STDDEV MIN MAX.

MEANS TABLES={analysis_vars} BY {group_var}
  /CELLS=MEAN COUNT STDDEV.

SPLIT FILE OFF.

* Boxplots for comparison
GRAPH /BOXPLOT={continuous_vars[0]} BY {group_var}
  /TITLE='Boxplot: {continuous_vars[0]} by {group_var}'.
"""
        else:
            code = """* Group comparison code template
* Replace VAR1 with your grouping variable and VAR2 with analysis variable
SORT CASES BY VAR1.
SPLIT FILE LAYERED BY VAR1.
DESCRIPTIVES VARIABLES=VAR2.
SPLIT FILE OFF.
"""
        
        return code + "\n"
    
    def _generate_correlation_code(self, df):
        """إنشاء كود الارتباط"""
        numeric_vars = [col for col in df.columns 
                       if self.data_types.get(col) in ['continuous', 'categorical_numeric']]
        
        if len(numeric_vars) >= 2:
            vars_list = ' '.join(numeric_vars[:5])
            code = f"""* Correlation analysis
CORRELATIONS
  /VARIABLES={vars_list}
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.

* Scatterplot matrix (if 3 or more variables)
{"GRAPH /SCATTERPLOT(MATRIX)=" + " ".join(numeric_vars[:3]) + "." if len(numeric_vars) >= 3 else ""}
"""
        else:
            code = """* Correlation analysis template
CORRELATIONS
  /VARIABLES=VAR1 VAR2 VAR3
  /PRINT=TWOTAIL NOSIG.
"""
        
        return code + "\n"
    
    def _generate_regression_code(self, df, question):
        """إنشاء كود الانحدار"""
        numeric_vars = [col for col in df.columns 
                       if self.data_types.get(col) in ['continuous', 'categorical_numeric']]
        
        if len(numeric_vars) >= 2:
            dependent = numeric_vars[0]
            independents = ' '.join(numeric_vars[1:4])
            
            code = f"""* Regression analysis
REGRESSION
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS R ANOVA
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN
  /DEPENDENT {dependent}
  /METHOD=ENTER {independents}.

* Check assumptions
REGRESSION
  /DEPENDENT {dependent}
  /METHOD=ENTER {independents}
  /SCATTERPLOT=(*ZRESID,*ZPRED)
  /RESIDUALS HISTOGRAM(ZRESID).
"""
        else:
            code = """* Regression analysis template
REGRESSION
  /DEPENDENT DEP_VAR
  /METHOD=ENTER IND_VAR1 IND_VAR2.
"""
        
        return code + "\n"
    
    def _generate_ttest_code(self, df, question):
        """إنشاء كود اختبار t"""
        q_lower = question.lower()
        categorical_vars = [col for col in df.columns 
                          if self.data_types.get(col) in ['categorical_numeric', 'categorical_text']]
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if len(categorical_vars) >= 1 and len(continuous_vars) >= 1:
            group_var = categorical_vars[0]
            test_var = continuous_vars[0]
            
            # تحقق إذا كان المتغير المجموعي له قيمتين فقط
            unique_groups = df[group_var].dropna().nunique()
            
            if unique_groups == 2:
                code = f"""* Independent samples t-test
T-TEST GROUPS={group_var}
  /VARIABLES={test_var}
  /CRITERIA=CI(.95)
  /MISSING=ANALYSIS.
"""
            else:
                code = f"""* Grouping variable {group_var} has {unique_groups} groups
* Consider using ANOVA for multiple groups or recoding into 2 groups
"""
        else:
            code = """* T-test template
T-TEST GROUPS=GROUP_VAR(1,2)
  /VARIABLES=TEST_VAR.
"""
        
        return code + "\n"
    
    def _generate_anova_code(self, df, question):
        """إنشاء كود ANOVA"""
        categorical_vars = [col for col in df.columns 
                          if self.data_types.get(col) in ['categorical_numeric', 'categorical_text']]
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if categorical_vars and continuous_vars:
            group_var = categorical_vars[0]
            test_var = continuous_vars[0]
            
            unique_groups = df[group_var].dropna().nunique()
            
            if unique_groups >= 2:
                code = f"""* One-way ANOVA
ONEWAY {test_var} BY {group_var}
  /STATISTICS DESCRIPTIVES HOMOGENEITY
  /MISSING ANALYSIS
  /POSTHOC=TUKEY ALPHA(0.05).

* Means plot
ONEWAY {test_var} BY {group_var}
  /PLOT MEANS.
"""
            else:
                code = f"""* Grouping variable has only {unique_groups} group(s)
* Need at least 2 groups for ANOVA
"""
        else:
            code = """* ANOVA template
ONEWAY DEP_VAR BY GROUP_VAR(1,3)
  /STATISTICS DESCRIPTIVES.
"""
        
        return code + "\n"
    
    def _generate_chisquare_code(self, df):
        """إنشاء كود كاي تربيع"""
        categorical_vars = [col for col in df.columns 
                          if self.data_types.get(col) in ['categorical_numeric', 'categorical_text']]
        
        if len(categorical_vars) >= 2:
            var1, var2 = categorical_vars[:2]
            code = f"""* Chi-square test of independence
CROSSTABS
  /TABLES={var1} BY {var2}
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ PHI
  /CELLS=COUNT EXPECTED ROW COLUMN TOTAL
  /COUNT ROUND CELL.
"""
        else:
            code = """* Chi-square test template
CROSSTABS
  /TABLES=VAR1 BY VAR2
  /STATISTICS=CHISQ.
"""
        
        return code + "\n"
    
    def _generate_confidence_code(self, df):
        """إنشاء كود فترات الثقة"""
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if continuous_vars:
            var = continuous_vars[0]
            code = f"""* Confidence intervals for {var}
EXAMINE VARIABLES={var}
  /PLOT NONE
  /STATISTICS DESCRIPTIVES
  /CINTERVAL 95
  /PERCENTILES(5,25,50,75,95).

* 95% Confidence Interval
DESCRIPTIVES VARIABLES={var}
  /STATISTICS=MEAN SEMEAN.

* 99% Confidence Interval
* Use T-TEST command for CI
T-TEST
  /TESTVAL=0
  /VARIABLES={var}
  /CRITERIA=CI(.99).
"""
        else:
            code = """* Confidence interval template
EXAMINE VARIABLES=VAR1
  /CINTERVAL 95.
"""
        
        return code + "\n"
    
    def _generate_normality_code(self, df):
        """إنشاء كود اختبارات normality"""
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if continuous_vars:
            var = continuous_vars[0]
            code = f"""* Normality tests for {var}
EXAMINE VARIABLES={var}
  /PLOT NPPLOT
  /STATISTICS DESCRIPTIVES
  /CINTERVAL 95
  /MESTIMATORS HUBER(1.339) ANDREW(1.34) HAMPEL(1.7,3.4,8.5) TUKEY(4.685)
  /PERCENTILES(5,25,50,75,95).

* Shapiro-Wilk test (for n < 2000)
EXAMINE VARIABLES={var}
  /PLOT BOXPLOT HISTOGRAM NPPLOT
  /COMPARE GROUPS
  /STATISTICS DESCRIPTIVES EXTREME
  /CINTERVAL 95
  /MISSING LISTWISE
  /NOTOTAL.

COMMENT "Interpretation: If Sig. < 0.05, reject normality. Use non-parametric tests.".
"""
        else:
            code = """* Normality test template
EXAMINE VARIABLES=VAR1
  /PLOT NPPLOT.
"""
        
        return code + "\n"
    
    def _generate_outliers_code(self, df):
        """إنشاء كود كشف القيم المتطرفة"""
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if continuous_vars:
            var = continuous_vars[0]
            code = f"""* Outlier detection for {var}
EXAMINE VARIABLES={var}
  /PLOT BOXPLOT
  /STATISTICS DESCRIPTIVES EXTREME
  /CINTERVAL 95
  /MISSING LISTWISE
  /NOTOTAL.

* Identify extreme values (more than 3 SD from mean)
DESCRIPTIVES VARIABLES={var}
  /SAVE
  /STATISTICS=MEAN STDDEV MIN MAX.

COMPUTE Z_{var} = ABS({var} - MEAN({var})) / SD({var}).
VARIABLE LABELS Z_{var} 'Z-score for {var}'.
FREQUENCIES VARIABLES=Z_{var}
  /FORMAT=NOTABLE
  /STATISTICS=MEAN STDDEV MIN MAX
  /PERCENTILES=1,5,95,99
  /ORDER=ANALYSIS.

SELECT IF (Z_{var} > 3).
LIST VARIABLES={var} Z_{var}.
USE ALL.
"""
        else:
            code = """* Outlier detection template
EXAMINE VARIABLES=VAR1
  /PLOT BOXPLOT.
"""
        
        return code + "\n"
    
    def _generate_recode_code(self, df, question, q_num):
        """إنشاء كود إعادة الترميز"""
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if continuous_vars:
            var = continuous_vars[0]
            new_var = f"Q{q_num}_RECODE"
            
            code = f"""* Recoding {var} into categories
* First, check the range
FREQUENCIES VARIABLES={var}
  /FORMAT=NOTABLE
  /STATISTICS=MINIMUM MAXIMUM
  /PERCENTILES=25,50,75.

* Recode into 3 categories (tertiles)
RANK VARIABLES={var} (A)
  /NTILES(3)
  /RANK
  /PRINT=NO
  /TIES=MEAN.

DO IF (NTRANS({var}) = 1).
  COMPUTE {new_var} = 1.
ELSE IF (NTRANS({var}) = 2).
  COMPUTE {new_var} = 2.
ELSE IF (NTRANS({var}) = 3).
  COMPUTE {new_var} = 3.
END IF.
VARIABLE LABELS {new_var} 'Recoded {var} (tertiles)'.
VALUE LABELS {new_var} 1 'Low' 2 'Medium' 3 'High'.
EXECUTE.

FREQUENCIES VARIABLES={new_var}
  /ORDER=ANALYSIS.
"""
        else:
            code = """* Recoding template
* Determine cut points first, then:
RECODE VAR1 (LOWEST THRU 50=1) (50 THRU 100=2) (100 THRU HIGHEST=3) INTO NEWVAR.
"""
        
        return code + "\n"
    
    def _generate_transform_code(self, df, question, q_num):
        """إنشاء كود التحويلات"""
        continuous_vars = [col for col in df.columns 
                         if self.data_types.get(col) == 'continuous']
        
        if continuous_vars:
            var = continuous_vars[0]
            code = f"""* Variable transformations for {var}
* Square root transformation (for right-skewed data)
COMPUTE sqrt_{var} = SQRT({var}).
VARIABLE LABELS sqrt_{var} 'Square root of {var}'.

* Logarithmic transformation
* First check for zeros or negative values
COUNT zeros = {var} (0).
LIST {var} zeros.

DO IF ({var} > 0).
  COMPUTE log_{var} = LG10({var}).
ELSE.
  COMPUTE log_{var} = $SYSMIS.
END IF.
VARIABLE LABELS log_{var} 'Log10 of {var}'.

* Standardization (z-scores)
COMPUTE z_{var} = ({var} - MEAN({var})) / SD({var}).
VARIABLE LABELS z_{var} 'Z-score of {var}'.
EXECUTE.

* Compare distributions
GRAPH /HISTOGRAM(NORMAL)={var}
  /TITLE='Original {var}'.
GRAPH /HISTOGRAM(NORMAL)=sqrt_{var}
  /TITLE='Square root transformed'.
GRAPH /HISTOGRAM(NORMAL)=log_{var}
  /TITLE='Log transformed'.
"""
        else:
            code = """* Variable transformation template
COMPUTE NEWVAR = TRANSFORMATION(OLDVAR).
"""
        
        return code + "\n"
    
    def _generate_general_code(self, df, question, q_num):
        """إنشاء كود عام للأسئلة غير المعروفة"""
        code = f"""* Analysis for: {question[:50]}...
* Suggested analysis based on question content:

* 1. Descriptive overview
DESCRIPTIVES VARIABLES=ALL
  /STATISTICS=MEAN STDDEV MIN MAX.

* 2. Check relationships (if multiple variables)
CORRELATIONS
  /VARIABLES=VAR1 VAR2 VAR3
  /PRINT=TWOTAIL NOSIG.

* 3. Visual exploration
GRAPH /HISTOGRAM=VAR1.
GRAPH /SCATTERPLOT=VAR1 WITH VAR2.

* 4. Group comparisons (if applicable)
MEANS TABLES=VAR1 BY VAR2
  /CELLS=MEAN COUNT STDDEV.

COMMENT "Review question requirements and adjust analysis accordingly.".
"""
        return code + "\n"

# التطبيق الرئيسي
def main():
    generator = SPSSUniversalGenerator()
    
    st.markdown("---")
    
    # الخيارات
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 بيانات الامتحان")
        data_source = st.radio(
            "مصدر البيانات",
            ["تحميل ملف", "إدخال يدوي", "بيانات تجريبية"]
        )
    
    with col2:
        st.subheader("📝 الأسئلة")
        questions_source = st.radio(
            "مصدر الأسئلة",
            ["تحميل ملف", "إدخال يدوي", "نماذج جاهزة"]
        )
    
    with col3:
        st.subheader("⚙️ الإعدادات")
        spss_version = st.selectbox(
            "إصدار SPSS",
            ["V26", "V27", "V28", "Universal"]
        )
        auto_detect = st.checkbox("الكشف التلقائي عن أنواع الأسئلة", value=True)
    
    # معالجة البيانات
    df = None
    questions = []
    
    if data_source == "تحميل ملف":
        data_file = st.file_uploader("اختر ملف البيانات", type=['xls', 'xlsx', 'csv', 'sav', 'txt'])
        if data_file:
            try:
                if data_file.name.endswith('.csv'):
                    df = pd.read_csv(data_file)
                elif data_file.name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(data_file)
                elif data_file.name.endswith('.txt'):
                    df = pd.read_csv(data_file, delimiter='\t')
                else:
                    st.warning("نوع الملف غير معروف. حاول تحويله إلى CSV أو Excel.")
            except Exception as e:
                st.error(f"خطأ في قراءة الملف: {e}")
    
    elif data_source == "إدخال يدوي":
        sample_data = st.text_area(
            "أدخل بيانات CSV (صف العنوان، ثم البيانات)",
            value="""var1,var2,var3,group
25,1500,1,A
30,2000,2,B
28,1800,1,A
35,2200,2,B
22,1600,1,A"""
        )
        if sample_data:
            try:
                df = pd.read_csv(io.StringIO(sample_data))
            except:
                st.error("تنسيق CSV غير صحيح")
    
    else:  # بيانات تجريبية
        df_type = st.selectbox("نوع البيانات التجريبية", ["بيانات طلاب", "بيانات مبيعات", "بيانات استبيان", "بيانات طبية"])
        if df_type == "بيانات طلاب":
            np.random.seed(42)
            df = pd.DataFrame({
                'student_id': range(1, 101),
                'age': np.random.randint(18, 25, 100),
                'gpa': np.round(np.random.normal(3.0, 0.5, 100), 2),
                'hours_studied': np.random.randint(10, 40, 100),
                'gender': np.random.choice(['M', 'F'], 100),
                'major': np.random.choice(['Science', 'Arts', 'Business'], 100),
                'test_score': np.random.randint(60, 100, 100)
            })
        elif df_type == "بيانات مبيعات":
            np.random.seed(42)
            df = pd.DataFrame({
                'transaction_id': range(1, 101),
                'amount': np.round(np.random.exponential(100, 100), 2),
                'items': np.random.randint(1, 20, 100),
                'customer_age': np.random.randint(18, 70, 100),
                'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
                'month': np.random.choice(['Jan', 'Feb', 'Mar', 'Apr'], 100),
                'weekday': np.random.choice(range(1, 8), 100)
            })
    
    # معالجة الأسئلة
    if questions_source == "تحميل ملف":
        questions_file = st.file_uploader("اختر ملف الأسئلة", type=['txt', 'docx', 'pdf'])
        if questions_file:
            if questions_file.name.endswith('.txt'):
                questions_text = questions_file.getvalue().decode('utf-8')
                questions = generator.parse_questions(questions_text)
    
    elif questions_source == "إدخال يدوي":
        questions_text = st.text_area(
            "أدخل الأسئلة (سؤال في كل سطر، أو مرقمة)",
            height=200,
            value="""1. Calculate descriptive statistics for all variables.
2. Create frequency tables for categorical variables.
3. Test if there is a significant difference in test scores between genders.
4. Examine the relationship between hours studied and GPA.
5. Check for outliers in the test scores.
6. Create a bar chart showing average GPA by major.
7. Perform a regression analysis with GPA as dependent variable.
8. Test the normality of the test scores distribution."""
        )
        if questions_text:
            questions = generator.parse_questions(questions_text)
    
    else:  # نماذج جاهزة
        exam_template = st.selectbox(
            "اختر نموذج الامتحان",
            ["امتحان إحصاء عام", "بحث علمي", "تحليل استبيان", "تحليل تجريبي"]
        )
        if exam_template == "امتحان إحصاء عام":
            questions = [
                "Calculate mean, median, mode, and standard deviation for all continuous variables.",
                "Create frequency distributions for all categorical variables.",
                "Test for normality using appropriate statistical tests.",
                "Perform correlation analysis between key variables.",
                "Conduct t-test or ANOVA for group comparisons.",
                "Create appropriate visualizations (histograms, bar charts, scatter plots).",
                "Check for outliers and extreme values.",
                "Interpret the results in the context of the research questions."
            ]
        elif exam_template == "بحث علمي":
            questions = [
                "State the research hypotheses.",
                "Describe the sample characteristics.",
                "Check data quality and missing values.",
                "Test assumptions for parametric tests.",
                "Conduct main statistical analyses.",
                "Perform post-hoc tests if needed.",
                "Report effect sizes and confidence intervals.",
                "Discuss limitations and implications."
            ]
    
    if df is not None and questions:
        st.success(f"✅ تم تحميل {len(questions)} سؤال و {len(df.columns)} متغير")
        
        # عرض المعاينة
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("👁️ معاينة البيانات"):
                st.dataframe(df.head())
                st.write(f"**الأبعاد:** {df.shape[0]} صف × {df.shape[1]} عمود")
                st.write("**أنواع البيانات:**")
                data_types = generator.detect_data_types(df)
                for col, dtype in data_types.items():
                    st.write(f"- {col}: {dtype}")
        
        with col2:
            with st.expander("📋 الأسئلة"):
                for i, q in enumerate(questions[:15], 1):
                    q_types = generator.detect_question_type(q)
                    st.write(f"**{i}.** {q[:80]}...")
                    if q_types:
                        st.caption(f"النوع: {', '.join(q_types)}")
                if len(questions) > 15:
                    st.write(f"... و{len(questions)-15} أسئلة أخرى")
        
        # خيارات متقدمة
        with st.expander("⚙️ خيارات متقدمة"):
            col1, col2 = st.columns(2)
            with col1:
                include_comments = st.checkbox("تضمين تعليقات توضيحية", value=True)
                add_interpretation = st.checkbox("إضافة تفسيرات النتائج", value=True)
            with col2:
                language = st.selectbox("لغة المخرجات", ["English", "العربية", "Bilingual"])
                code_format = st.selectbox("تنسيق الكود", ["Detailed", "Minimal", "Custom"])
        
        st.markdown("---")
        
        # زر إنشاء الكود
        if st.button("🚀 إنشاء كود SPSS", type="primary", use_container_width=True):
            with st.spinner("جارٍ إنشاء كود SPSS..."):
                try:
                    dataset_name = "Exam_Analysis"
                    spss_code = generator.generate_spss_code(questions, df, dataset_name)
                    
                    # إضافة رأس إضافي
                    header = f"""* =========================================================================.
* SPSS ANALYSIS CODE
* Generated for: {dataset_name}
* Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Questions: {len(questions)}
* Variables: {len(df.columns)}
* =========================================================================.

"""
                    spss_code = header + spss_code
                    
                    # إضافة نصائح
                    tips = """
* =========================================================================.
* TIPS FOR USING THIS CODE:
* 1. Open SPSS and load your data file
* 2. Open a new syntax window (File > New > Syntax)
* 3. Paste this code into the syntax window
* 4. Select all code (Ctrl+A) and run (F5 or click the green arrow)
* 5. Check the output viewer for results
* 6. Save output using File > Save As > Output
* =========================================================================.
"""
                    spss_code += tips
                    
                    # عرض الكود
                    st.subheader("📋 كود SPSS النهائي")
                    st.code(spss_code, language='text', height=500)
                    
                    # روابط التنزيل
                    st.markdown("---")
                    st.subheader("📥 تحميل الملفات")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(generator.create_download_link(spss_code, "SPSS_Code.sps"), 
                                  unsafe_allow_html=True)
                    
                    with col2:
                        # حفظ البيانات كملف دليل
                        data_guide = f"""# Data Guide for SPSS Analysis
Dataset: {dataset_name}
Variables: {len(df.columns)}
Observations: {len(df)}

## Variable Information:
"""
                        for col in df.columns:
                            dtype = generator.data_types.get(col, 'unknown')
                            unique_vals = df[col].nunique()
                            missing = df[col].isna().sum()
                            data_guide += f"""
{col}:
  - Type: {dtype}
  - Unique values: {unique_vals}
  - Missing: {missing}
  - Sample values: {list(df[col].dropna().unique())[:5] if unique_vals > 5 else list(df[col].dropna().unique())}
"""
                        
                        st.markdown(generator.create_download_link(data_guide, "Data_Guide.txt"), 
                                  unsafe_allow_html=True)
                    
                    with col3:
                        # كود تحضيري
                        prep_code = """* DATA PREPARATION CODE
* Run this before main analysis

* Check for missing values
MISSING VALUES ALL ().
MISSING VALUES ANALYSIS
  /VARIABLES=ALL
  /CATEGORICAL=ALL.

* Define missing values
MISSING VALUES var1 var2 var3 (999, -1, -99).

* Recode if needed
RECODE var1 (MISSING=SYSMIS) (ELSE=COPY).

* Save prepared dataset
SAVE OUTFILE='prepared_data.sav'
  /COMPRESSED.
"""
                        st.markdown(generator.create_download_link(prep_code, "Data_Preparation.sps"), 
                                  unsafe_allow_html=True)
                    
                    # نصائح إضافية
                    with st.expander("💡 نصائح للاستخدام"):
                        st.markdown("""
                        **نصائح مهمة:**
                        1. **تحقق من البيانات**: تأكد من صحة البيانات قبل التشغيل
                        2. **عدل المتغيرات**: استبدل أسماء المتغيرات بأسماء متغيراتك الفعلية
                        3. **حفظ الملفات**: احفظ الملفات بانتظام
                        4. **التوثيق**: قم بتوثيق أي تغييرات تجريها على الكود
                        5. **النسخ الاحتياطي**: احتفظ بنسخة احتياطية من البيانات والكود
                        
                        **للأسئلة الصعبة:**
                        - راجع وثائق SPSS
                        - استشر المشرف أو الزملاء
                        - ابحث في المنتديات المتخصصة
                        - جرب التحليلات البديلة
                        """)
                    
                except Exception as e:
                    st.error(f"❌ خطأ في إنشاء الكود: {str(e)}")
                    st.exception(e)
    
    else:
        # التعليمات
        st.info("""
        ## 🎯 كيفية استخدام المولد الشامل
        
        **الخطوة 1: تحضير البيانات**
        - يمكنك تحميل ملف (Excel، CSV، إلخ)
        - أو إدخال البيانات يدوياً
        - أو استخدام بيانات تجريبية
        
        **الخطوة 2: إدخال الأسئلة**
        - يمكنك تحميل ملف نصي بالأسئلة
        - أو كتابتها مباشرة
        - أو اختيار نموذج جاهز
        
        **الخطوة 3: ضبط الإعدادات**
        - اختيار إصدار SPSS
        - تفعيل الكشف التلقائي
        - اختيار خيارات الإخراج
        
        **الخطوة 4: إنشاء الكود**
        - انقر على زر "إنشاء كود SPSS"
        - انتظر حتى يتم الإنشاء
        - حمل الملفات الناتجة
        
        **الخطوة 5: التشغيل في SPSS**
        1. افتح SPSS
        2. حمل بياناتك
        3. افتح محرر الصيغ (Syntax Editor)
        4. الصق الكود المولد
        5. شغل الكود (Ctrl+A ثم F5)
        
        **المميزات:**
        - ✅ يعمل مع أي امتحان إحصائي
        - ✅ دعم متعدد اللغات
        - ✅ كشف تلقائي لأنواع الأسئلة
        - ✅ تكامل مع جميع إصدارات SPSS
        - ✅ إخراج احترافي وجاهز للاستخدام
        """)
        
        # أمثلة
        with st.expander("📚 أمثلة لأنواع الأسئلة المدعومة"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **الأسئلة الوصفية:**
                - احسب المتوسط والوسيط والمنوال
                - أنشئ جداول تكرارية
                - ارسم مخططات بيانية
                - ابحث عن القيم المتطرفة
                
                **الأسئلة الاستدلالية:**
                - اختبارات t
                - تحليل التباين ANOVA
                - اختبارات مربع كاي
                - تحليل الارتباط
                - تحليل الانحدار
                """)
            
            with col2:
                st.markdown("""
                **أسئلة التصور البياني:**
                - المدرجات التكرارية
                - المخططات الشريطية
                - المخططات الدائرية
                - مخططات الصندوق
                - مخططات الانتشار
                
                **أسئلة متقدمة:**
                - فترات الثقة
                - اختبارات normality
                - تحويلات البيانات
                - إعادة ترميز المتغيرات
                - تحليل المجموعات
                """)

if __name__ == "__main__":
    main()
