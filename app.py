import streamlit as st
import pandas as pd
import numpy as np
from docx import Document
import tempfile
import os
import re
import math
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="Dynamic SPSS Solver",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 محلل SPSS الديناميكي المتقدم")
st.markdown("### حل تلقائي لأي امتحان إحصائي مع أي بيانات")

# ===== المحلل الديناميكي =====

class DynamicSPSSAnalyzer:
    """محلل ديناميكي لأي بيانات وأي أسئلة"""
    
    def __init__(self, df: pd.DataFrame, questions_text: str):
        self.df = df
        self.questions_text = questions_text
        self.variable_info = self._analyze_variables()
        self.questions = self._parse_questions()
        self.question_mappings = self._build_question_mappings()
        
    def _analyze_variables(self) -> Dict:
        """تحليل تلقائي لجميع المتغيرات"""
        variable_info = {}
        
        for col in self.df.columns:
            col_str = str(col).strip()
            var_data = self.df[col].dropna()
            
            info = {
                'name': col_str,
                'original_name': col_str,
                'dtype': str(self.df[col].dtype),
                'n_unique': len(var_data.unique()),
                'missing': self.df[col].isna().sum(),
                'total': len(self.df[col]),
                'unique_values': sorted(var_data.unique().tolist()) if len(var_data.unique()) <= 20 else [],
                'is_numeric': pd.api.types.is_numeric_dtype(self.df[col])
            }
            
            # التخمين التلقائي لنوع المتغير
            if info['is_numeric']:
                if info['n_unique'] <= 10:
                    info['stat_type'] = 'CATEGORICAL'
                    info['measurement_level'] = 'NOMINAL'
                else:
                    info['stat_type'] = 'CONTINUOUS'
                    info['measurement_level'] = 'SCALE'
                    info['stats'] = {
                        'mean': float(var_data.mean()) if not var_data.empty else 0,
                        'std': float(var_data.std()) if not var_data.empty else 0,
                        'min': float(var_data.min()) if not var_data.empty else 0,
                        'max': float(var_data.max()) if not var_data.empty else 0,
                        'median': float(var_data.median()) if not var_data.empty else 0
                    }
            else:
                info['stat_type'] = 'STRING'
                info['measurement_level'] = 'NOMINAL'
            
            # تخمين معنى المتغير من اسمه
            info['inferred_meaning'] = self._infer_variable_meaning(col_str, info)
            
            # تخمين تسميات القيم
            if info['stat_type'] == 'CATEGORICAL' and info['unique_values']:
                info['value_labels'] = self._guess_value_labels(col_str, info['unique_values'])
            
            variable_info[col_str] = info
        
        return variable_info
    
    def _infer_variable_meaning(self, var_name: str, info: Dict) -> str:
        """تخمين معنى المتغير من اسمه وقيمه"""
        var_lower = var_name.lower()
        
        # قائمة الأنماط المعروفة
        patterns = {
            'age': ['age', 'عمر', 'سن', 'العمر'],
            'salary': ['salary', 'مرتب', 'راتب', 'دخل', 'income'],
            'gender': ['gender', 'جنس', 'sex', 'ذكر', 'أنثى'],
            'city': ['city', 'مدينة', 'محافظة', 'region'],
            'year': ['year', 'سنة', 'عام', 'تاريخ'],
            'balance': ['balance', 'رصيد', 'account'],
            'transaction': ['transaction', 'معاملة', 'عملية'],
            'service': ['service', 'خدمة'],
            'card': ['card', 'بطاقة', 'debit'],
            'interest': ['interest', 'فائدة'],
            'score': ['score', 'درجة', 'mark'],
            'count': ['count', 'عدد', 'number'],
            'percentage': ['percentage', 'نسبة', 'percent'],
            'rate': ['rate', 'معدل', 'نسبة'],
            'category': ['category', 'فئة', 'type'],
            'team': ['team', 'فريق'],
            'league': ['league', 'دوري', 'رابطة'],
            'built': ['built', 'بناء', 'تأسيس'],
            'size': ['size', 'حجم', 'سعة'],
            'attendance': ['attendance', 'حضور', 'مشاهدين'],
            'wins': ['wins', 'انتصارات', 'فوز'],
            'country': ['country', 'دولة', 'بلد'],
            'population': ['population', 'سكان', 'تعداد'],
            'area': ['area', 'مساحة'],
            'gdp': ['gdp', 'ناتج', 'اقتصاد'],
            'happiness': ['happiness', 'سعادة'],
            'education': ['education', 'تعليم', 'مدرسة'],
            'occupation': ['occupation', 'وظيفة', 'مهنة']
        }
        
        for meaning, keywords in patterns.items():
            for keyword in keywords:
                if keyword in var_lower:
                    return meaning
        
        # التخمين من القيم
        if info['is_numeric']:
            if info['n_unique'] == 2:
                return 'binary_indicator'
            elif 3 <= info['n_unique'] <= 7:
                return 'categorical_code'
        
        return 'unknown'
    
    def _guess_value_labels(self, var_name: str, values: List) -> Dict:
        """تخمين تسميات القيم الفئوية"""
        var_lower = var_name.lower()
        labels = {}
        
        for val in values:
            if isinstance(val, (int, float)):
                # أنماط ثنائية (نعم/لا)
                if val == 0:
                    labels[val] = "No/False/Female"
                elif val == 1:
                    labels[val] = "Yes/True/Male"
                elif val == 2:
                    labels[val] = "Other/Sometimes"
                # أنماط الجنس
                elif 'gender' in var_lower or 'sex' in var_lower:
                    if val == 1:
                        labels[val] = "Male"
                    elif val == 2:
                        labels[val] = "Female"
                # أنماط الموافقة (مقياس ليكرت)
                elif any(word in var_lower for word in ['agree', 'satisfy', 'rate', 'happy']):
                    if val == 1:
                        labels[val] = "Strongly Disagree/Very Unhappy"
                    elif val == 2:
                        labels[val] = "Disagree/Unhappy"
                    elif val == 3:
                        labels[val] = "Neutral"
                    elif val == 4:
                        labels[val] = "Agree/Happy"
                    elif val == 5:
                        labels[val] = "Strongly Agree/Very Happy"
                # أنماط المدن/المناطق
                elif any(word in var_lower for word in ['city', 'region', 'area']):
                    if val == 1:
                        labels[val] = "North/North East"
                    elif val == 2:
                        labels[val] = "South/South East"
                    elif val == 3:
                        labels[val] = "West"
                    elif val == 4:
                        labels[val] = "East"
                else:
                    labels[val] = f"Category {val}"
            else:
                labels[val] = str(val)
        
        return labels
    
    def _parse_questions(self) -> List[Dict]:
        """تحليل ديناميكي للأسئلة"""
        questions = []
        
        if not self.questions_text or self.questions_text.strip() == "":
            # إنشاء أسئلة افتراضية إذا لم تكن هناك أسئلة
            return self._generate_default_questions()
        
        # أنماط متعددة لاستخراج الأسئلة
        patterns = [
            r'(\d+)[\.\)]\s+(.*?)(?=\n\d+[\.\)]|\n\n|$)',  # 1. أو 1)
            r'Q(\d+)[:\-]\s+(.*?)(?=\nQ\d+[:\.\-]|\n\n|$)',  # Q1: أو Q1-
            r'Question\s+(\d+)[:\-]\s+(.*?)(?=\nQuestion\s+\d+[:\.\-]|\n\n|$)',  # Question 1:
            r'^\s*(\d+)\.\s+(.*)$',  # أسطر تبدأ برقم
        ]
        
        lines = self.questions_text.split('\n')
        full_text = ' '.join(lines)  # دمج كل النص للبحث
        
        for pattern in patterns:
            matches = re.finditer(pattern, full_text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                q_num = match.group(1).strip()
                q_text = match.group(2).strip()
                
                # تنظيف النص
                q_text = re.sub(r'\s+', ' ', q_text)
                
                if q_text and len(q_text) > 5:
                    try:
                        questions.append({
                            'number': int(q_num),
                            'text': q_text[:200],
                            'full_text': q_text,
                            'detected_type': 'unknown'
                        })
                    except ValueError:
                        continue
        
        # إذا لم نجد أسئلة مرقمة، نبحث عن فقرات تحتوي على كلمات إحصائية
        if not questions:
            for i, line in enumerate(lines):
                line = line.strip()
                if line and len(line) > 20:
                    # تحقق إذا كان يحتوي على كلمات إحصائية
                    stats_keywords = [
                        'construct', 'calculate', 'draw', 'test', 'find',
                        'create', 'build', 'analyze', 'compare', 'determine',
                        'جدول', 'احسب', 'ارسم', 'اختبار', 'أوجد',
                        'أنشئ', 'حلل', 'قارن', 'اكتشف'
                    ]
                    
                    if any(keyword in line.lower() for keyword in stats_keywords):
                        questions.append({
                            'number': i + 1,
                            'text': line[:150],
                            'full_text': line,
                            'detected_type': 'unknown'
                        })
        
        # تحديد نوع كل سؤال
        for q in questions:
            q['detected_type'] = self._detect_question_type(q['full_text'])
            q['variables'] = self._extract_variables_from_text(q['full_text'])
            q['conditions'] = self._extract_conditions(q['full_text'])
            q['analysis_method'] = self._determine_analysis_method(q)
        
        return sorted(questions, key=lambda x: x['number'])
    
    def _generate_default_questions(self) -> List[Dict]:
        """إنشاء أسئلة افتراضية بناءً على البيانات"""
        questions = []
        
        # أنواع الأسئلة الافتراضية
        default_questions = [
            (1, "Construct frequency tables for categorical variables"),
            (2, "Calculate descriptive statistics for continuous variables"),
            (3, "Draw histograms for numerical variables"),
            (4, "Create bar charts for categorical variables"),
            (5, "Analyze relationships between variables"),
            (6, "Test for normality of continuous variables"),
            (7, "Detect outliers in the data"),
            (8, "Calculate confidence intervals for means"),
            (9, "Perform correlation analysis"),
            (10, "Compare groups using appropriate tests")
        ]
        
        continuous_vars = [v for v, info in self.variable_info.items() 
                         if info['stat_type'] == 'CONTINUOUS']
        categorical_vars = [v for v, info in self.variable_info.items() 
                          if info['stat_type'] == 'CATEGORICAL']
        
        for i, (q_num, q_text) in enumerate(default_questions):
            if (q_num in [1, 4] and categorical_vars) or (q_num in [2, 3, 6, 7, 8] and continuous_vars) or q_num in [5, 9, 10]:
                questions.append({
                    'number': q_num,
                    'text': q_text,
                    'full_text': q_text,
                    'detected_type': self._detect_question_type(q_text),
                    'variables': [],
                    'conditions': [],
                    'analysis_method': 'DESCRIPTIVES'  # سيتم تحديثه لاحقاً
                })
        
        # تحديد طريقة التحليل لكل سؤال
        for q in questions:
            q['analysis_method'] = self._determine_analysis_method(q)
        
        return questions
    
    def _detect_question_type(self, text: str) -> str:
        """تحديد نوع السؤال تلقائياً"""
        text_lower = text.lower()
        
        type_patterns = {
            'frequency': ['frequency table', 'جدول تكراري', 'توزيع تكراري', 'construct frequency', 'frequency distribution'],
            'descriptive': ['mean', 'median', 'mode', 'standard deviation', 'مقاييس', 'calculate', 'احسب', 'descriptive statistics'],
            'bar_chart': ['bar chart', 'رسم بياني عمودي', 'مخطط عمودي', 'draw bar', 'bar graph'],
            'pie_chart': ['pie chart', 'رسم دائري', 'مخطط دائري', 'draw pie', 'pie graph'],
            'histogram': ['histogram', 'مدرج تكراري', 'رسم مدرج', 'histogram plot'],
            'scatter': ['scatter plot', 'مخطط انتشار', 'رسم انتشار', 'scatter diagram'],
            'boxplot': ['box plot', 'مخطط الصندوق', 'صندوقي', 'boxplot'],
            'confidence': ['confidence interval', 'فترة ثقة', 'confidence', 'ci'],
            't_test': ['t-test', 'اختبار تي', 't test', 'اختبار t', 'student t'],
            'anova': ['anova', 'تحليل التباين', 'analysis of variance', 'f-test'],
            'correlation': ['correlation', 'ارتباط', 'علاقة', 'relationship', 'correlate'],
            'regression': ['regression', 'انحدار', 'linear model', 'predict', 'تنبؤ'],
            'chi_square': ['chi-square', 'كاي مربع', 'chi square', 'χ²'],
            'normality': ['normality', 'طبيعية', 'shapiro', 'kolmogorov', 'normal distribution'],
            'outliers': ['outliers', 'قيم متطرفة', 'extreme values', 'anomalies'],
            'cross_tab': ['cross tabulation', 'جدول متقاطع', 'crosstab', 'contingency table'],
            'clustering': ['cluster', 'تجميع', 'grouping', 'segmentation'],
            'factor': ['factor analysis', 'تحليل العوامل', 'factor'],
            'reliability': ['reliability', 'موثوقية', 'cronbach', 'alpha'],
        }
        
        for q_type, keywords in type_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return q_type
        
        return 'descriptive'  # إفتراضي
    
    def _extract_variables_from_text(self, text: str) -> List[str]:
        """استخراج المتغيرات المذكورة في النص"""
        found_vars = []
        text_lower = text.lower()
        
        # البحث عن أسماء المتغيرات مباشرة
        for var_name in self.variable_info.keys():
            var_lower = var_name.lower()
            
            # البحث بالاسم
            if var_lower in text_lower:
                found_vars.append(var_name)
            
            # البحث بالمعنى المستنتج
            elif self.variable_info[var_name]['inferred_meaning'] != 'unknown':
                meaning = self.variable_info[var_name]['inferred_meaning']
                meaning_keywords = {
                    'age': ['age', 'عمر', 'سن'],
                    'salary': ['salary', 'مرتب', 'راتب', 'income', 'دخل'],
                    'gender': ['gender', 'جنس', 'ذكر', 'أنثى', 'sex'],
                    'city': ['city', 'مدينة', 'محافظة', 'region', 'منطقة'],
                    'balance': ['balance', 'رصيد', 'account', 'حساب'],
                    'transaction': ['transaction', 'معاملة', 'عملية', 'transactions'],
                    'service': ['service', 'خدمة', 'services'],
                    'card': ['card', 'بطاقة', 'debit', 'credit'],
                    'interest': ['interest', 'فائدة'],
                    'score': ['score', 'درجة', 'mark', 'نقاط'],
                    'team': ['team', 'فريق'],
                    'league': ['league', 'دوري', 'رابطة'],
                    'country': ['country', 'دولة', 'بلد'],
                    'population': ['population', 'سكان', 'تعداد'],
                    'happiness': ['happiness', 'سعادة'],
                    'education': ['education', 'تعليم']
                }
                
                if meaning in meaning_keywords:
                    for keyword in meaning_keywords[meaning]:
                        if keyword in text_lower:
                            found_vars.append(var_name)
                            break
        
        # إذا لم نجد متغيرات، نستخدم المتغيرات المناسبة تلقائياً
        if not found_vars:
            # نختار المتغيرات بناءً على نوع السؤال
            q_type = self._detect_question_type(text)
            
            if q_type in ['frequency', 'categorical', 'chi_square', 'cross_tab']:
                # متغيرات فئوية
                found_vars = [v for v, info in self.variable_info.items() 
                            if info['stat_type'] == 'CATEGORICAL'][:3]
            elif q_type in ['descriptive', 'continuous', 'histogram', 'normality', 'outliers']:
                # متغيرات مستمرة
                found_vars = [v for v, info in self.variable_info.items() 
                            if info['stat_type'] == 'CONTINUOUS'][:3]
            elif q_type in ['correlation', 'regression']:
                # متغيرات مستمرة للارتباط
                found_vars = [v for v, info in self.variable_info.items() 
                            if info['stat_type'] == 'CONTINUOUS'][:4]
            elif q_type in ['t_test', 'anova', 'compare_groups']:
                # متغير فئوي + مستمر
                cat_vars = [v for v, info in self.variable_info.items() 
                          if info['stat_type'] == 'CATEGORICAL'][:1]
                cont_vars = [v for v, info in self.variable_info.items() 
                           if info['stat_type'] == 'CONTINUOUS'][:1]
                found_vars = cat_vars + cont_vars
            else:
                # مزيج
                categorical_vars = [v for v, info in self.variable_info.items() 
                                  if info['stat_type'] == 'CATEGORICAL'][:2]
                continuous_vars = [v for v, info in self.variable_info.items() 
                                 if info['stat_type'] == 'CONTINUOUS'][:2]
                found_vars = categorical_vars + continuous_vars
        
        return list(set(found_vars))[:5]  # الحد الأقصى 5 متغيرات
    
    def _extract_conditions(self, text: str) -> List[Dict]:
        """استخراج الشروط من النص"""
        conditions = []
        text_lower = text.lower()
        
        # شروط زمنية
        time_patterns = [
            (r'before (\d{4})', 'before_year'),
            (r'after (\d{4})', 'after_year'),
            (r'in (\d{4})', 'in_year'),
            (r'from (\d{4}) to (\d{4})', 'between_years'),
            (r'(\d{4})-(\d{4})', 'year_range')
        ]
        
        # شروط مقارنة
        comp_patterns = [
            (r'greater than (\d+)', 'greater_than'),
            (r'less than (\d+)', 'less_than'),
            (r'equal to (\d+)', 'equal_to'),
            (r'between (\d+) and (\d+)', 'between'),
            (r'more than (\d+)', 'greater_than'),
            (r'at least (\d+)', 'at_least'),
            (r'at most (\d+)', 'at_most'),
            (r'over (\d+)', 'greater_than'),
            (r'under (\d+)', 'less_than')
        ]
        
        # شروط فئوية
        cat_patterns = [
            (r'male', 'gender_male'),
            (r'female', 'gender_female'),
            (r'yes', 'yes'),
            (r'no', 'no'),
            (r'urban', 'urban'),
            (r'rural', 'rural'),
            (r'american', 'american'),
            (r'national', 'national'),
            (r'g7', 'g7'),
            (r'white', 'white'),
            (r'black', 'black'),
            (r'far east', 'far_east'),
            (r'europe', 'europe'),
            (r'north america', 'north_america')
        ]
        
        all_patterns = time_patterns + comp_patterns + cat_patterns
        
        for pattern, cond_type in all_patterns:
            match = re.search(pattern, text_lower)
            if match:
                condition = {'type': cond_type}
                
                if cond_type == 'between_years' and len(match.groups()) >= 2:
                    condition['value'] = [int(match.group(1)), int(match.group(2))]
                elif cond_type == 'year_range' and len(match.groups()) >= 2:
                    condition['value'] = [int(match.group(1)), int(match.group(2))]
                elif cond_type == 'between' and len(match.groups()) >= 2:
                    condition['value'] = [int(match.group(1)), int(match.group(2))]
                elif match.groups():
                    try:
                        condition['value'] = int(match.group(1))
                    except:
                        condition['value'] = match.group(1)
                else:
                    condition['value'] = match.group(0)
                
                conditions.append(condition)
        
        return conditions
    
    def _determine_analysis_method(self, question: Dict) -> str:
        """تحديد طريقة التحليل المناسبة"""
        q_type = question['detected_type']
        variables = question['variables']
        
        if not variables:
            return 'DESCRIPTIVES'
        
        # بناء على نوع المتغيرات
        var_types = []
        for v in variables:
            if v in self.variable_info:
                var_types.append(self.variable_info[v]['stat_type'])
        
        if q_type == 'frequency':
            return 'FREQUENCIES'
        elif q_type == 'descriptive':
            return 'DESCRIPTIVES'
        elif q_type == 'bar_chart':
            if len(variables) >= 2:
                return 'GRAPH_BAR_GROUPED'
            else:
                return 'GRAPH_BAR_SIMPLE'
        elif q_type == 'pie_chart':
            return 'GRAPH_PIE'
        elif q_type == 'histogram':
            return 'GRAPH_HISTOGRAM'
        elif q_type == 't_test':
            if len(variables) >= 2:
                return 'T_TEST_INDEPENDENT'
            else:
                return 'T_TEST_ONE_SAMPLE'
        elif q_type == 'anova':
            if len(variables) >= 2:
                return 'ONEWAY_ANOVA'
        elif q_type == 'correlation':
            if len(variables) >= 2:
                return 'CORRELATIONS'
        elif q_type == 'regression':
            if len(variables) >= 2:
                return 'REGRESSION'
        elif q_type == 'chi_square':
            if len(variables) >= 2:
                return 'CROSSTABS_CHISQ'
        elif q_type == 'cross_tab':
            if len(variables) >= 2:
                return 'CROSSTABS'
        elif q_type == 'confidence':
            return 'EXAMINE_CI'
        elif q_type == 'normality':
            return 'EXAMINE_NORMALITY'
        elif q_type == 'outliers':
            return 'EXAMINE_OUTLIERS'
        
        # التخمين بناءً على المتغيرات
        if all(t == 'CONTINUOUS' for t in var_types):
            return 'CORRELATIONS'
        elif all(t == 'CATEGORICAL' for t in var_types):
            return 'CROSSTABS'
        elif len(var_types) >= 2 and var_types[0] == 'CATEGORICAL' and var_types[1] == 'CONTINUOUS':
            return 'MEANS'
        else:
            return 'DESCRIPTIVES'
    
    def _build_question_mappings(self) -> Dict:
        """بناء خرائط للأسئلة الشائعة"""
        mappings = {
            'frequency_tables': {
                'keywords': ['frequency', 'تكراري', 'جدول'],
                'method': 'FREQUENCIES',
                'template': 'FREQUENCIES VARIABLES={vars}\n  /ORDER=ANALYSIS.'
            },
            'descriptive_stats': {
                'keywords': ['mean', 'median', 'mode', 'متوسط', 'وسيط', 'منوال'],
                'method': 'DESCRIPTIVES',
                'template': 'DESCRIPTIVES VARIABLES={vars}\n  /STATISTICS=MEAN MEDIAN MODE STDDEV MIN MAX.'
            },
            'compare_groups': {
                'keywords': ['compare', 'مقارنة', 'between groups', 'بين مجموعات'],
                'method': 'MEANS',
                'template': 'MEANS TABLES={dv} BY {iv}\n  /CELLS=MEAN COUNT STDDEV.'
            },
            'relationship': {
                'keywords': ['relationship', 'علاقة', 'correlation', 'ارتباط'],
                'method': 'CORRELATIONS',
                'template': 'CORRELATIONS\n  /VARIABLES={vars}\n  /PRINT=TWOTAIL NOSIG.'
            }
        }
        return mappings
    
    def generate_spss_syntax(self) -> str:
        """توليد كود SPSS ديناميكي"""
        
        syntax = f"""* =========================================================================
* DYNAMIC SPSS SOLUTION GENERATOR
* Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
* Dataset: {len(self.df.columns)} variables, {len(self.df)} cases
* Questions analyzed: {len(self.questions)}
* =========================================================================

DATASET NAME DynamicData WINDOW=FRONT.
DATASET ACTIVATE DynamicData.

* -------------------------------------------------------------------------
* VARIABLE DEFINITION AND PREPARATION
* -------------------------------------------------------------------------

* Variable labels based on inferred meanings\n"""
        
        # تعريف المتغيرات
        for var_name, info in self.variable_info.items():
            label = info.get('inferred_meaning', var_name).replace('_', ' ').title()
            syntax += f'VARIABLE LABELS {var_name} "{label}".\n'
            syntax += f'VARIABLE LEVEL {var_name} ({info["measurement_level"]}).\n'
            
            if 'value_labels' in info and info['value_labels']:
                syntax += f'VALUE LABELS {var_name}\n'
                for val, lbl in info['value_labels'].items():
                    syntax += f'  {val} "{lbl}"\n'
                syntax += '.\n'
        
        syntax += "\nEXECUTE.\n"
        
        # إنشاء متغيرات مشتقة إذا لزم الأمر
        syntax += self._generate_derived_variables()
        
        # حل كل سؤال
        syntax += "\n* -------------------------------------------------------------------------"
        syntax += "\n* QUESTION SOLUTIONS"
        syntax += "\n* -------------------------------------------------------------------------\n"
        
        for q in self.questions:
            syntax += self._generate_question_solution(q)
        
        # تحليلات إضافية تلقائية
        syntax += self._generate_auto_analyses()
        
        # إنهاء
        syntax += """
* -------------------------------------------------------------------------
* CLEANUP AND SAVE
* -------------------------------------------------------------------------

DATASET CLOSE ALL.
SAVE OUTFILE='Dynamic_Analysis_Results.sav'
  /COMPRESSED.
EXECUTE.

* ==================== END OF DYNAMIC SOLUTION ====================
"""
        
        return syntax
    
    def _generate_derived_variables(self) -> str:
        """توليد متغيرات مشتقة تلقائياً"""
        syntax = "\n* Derived variables for analysis\n"
        
        for var_name, info in self.variable_info.items():
            if info['stat_type'] == 'CONTINUOUS' and 'stats' in info:
                # إنشاء فئات للمتغيرات المستمرة
                syntax += f"\n* Creating categories for {var_name}\n"
                mean_val = info['stats']['mean']
                syntax += f"IF ({var_name} < {mean_val:.2f}) {var_name}_Cat = 1.\n"
                syntax += f"IF ({var_name} >= {mean_val:.2f}) {var_name}_Cat = 2.\n"
                syntax += f"VARIABLE LABELS {var_name}_Cat 'Categories of {var_name}'.\n"
                syntax += f"VALUE LABELS {var_name}_Cat\n"
                syntax += f"  1 'Below Average'\n"
                syntax += f"  2 'Above Average'\n"
                syntax += f".\n"
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def _generate_question_solution(self, question: Dict) -> str:
        """توليد حل لسؤال معين"""
        q_num = question['number']
        q_text = question['text']
        q_type = question['detected_type']
        variables = question['variables']
        method = question['analysis_method']
        
        syntax = f"\n* QUESTION {q_num}: {q_text}\n"
        syntax += f"* Detected Type: {q_type}\n"
        
        if variables:
            syntax += f"* Variables: {', '.join(variables)}\n"
        
        syntax += f"* Method: {method}\n"
        
        # توليد الكود المناسب
        if method == 'FREQUENCIES':
            if variables:
                syntax += f"FREQUENCIES VARIABLES={' '.join(variables)}\n"
                syntax += "  /BARCHART FREQ\n"
                syntax += "  /ORDER=ANALYSIS.\n"
        
        elif method == 'DESCRIPTIVES':
            if variables:
                syntax += f"DESCRIPTIVES VARIABLES={' '.join(variables)}\n"
                syntax += "  /STATISTICS=MEAN MEDIAN MODE STDDEV MIN MAX SKEWNESS.\n"
        
        elif method == 'GRAPH_BAR_SIMPLE':
            if variables:
                syntax += f"GRAPH\n"
                syntax += f"  /BAR(SIMPLE)=COUNT BY {variables[0]}\n"
                syntax += f"  /TITLE='Bar Chart of {variables[0]}'.\n"
        
        elif method == 'GRAPH_BAR_GROUPED':
            if len(variables) >= 2:
                syntax += f"GRAPH\n"
                syntax += f"  /BAR(GROUPED)=MEAN({variables[1]}) BY {variables[0]}\n"
                syntax += f"  /TITLE='Grouped Bar: {variables[1]} by {variables[0]}'.\n"
        
        elif method == 'GRAPH_PIE':
            if variables:
                syntax += f"GRAPH\n"
                syntax += f"  /PIE=PCT BY {variables[0]}\n"
                syntax += f"  /TITLE='Pie Chart of {variables[0]}'.\n"
        
        elif method == 'GRAPH_HISTOGRAM':
            if variables:
                for var in variables[:2]:
                    if var in self.variable_info and self.variable_info[var]['stat_type'] == 'CONTINUOUS':
                        syntax += f"GRAPH\n"
                        syntax += f"  /HISTOGRAM={var}\n"
                        syntax += f"  /TITLE='Histogram of {var}'.\n"
        
        elif method == 'T_TEST_ONE_SAMPLE':
            if variables:
                syntax += f"T-TEST\n"
                syntax += f"  /TESTVAL=0\n"
                syntax += f"  /VARIABLES={variables[0]}\n"
                syntax += f"  /CRITERIA=CI(.95).\n"
        
        elif method == 'T_TEST_INDEPENDENT':
            if len(variables) >= 2:
                syntax += f"T-TEST GROUPS={variables[0]}\n"
                syntax += f"  /VARIABLES={variables[1]}\n"
                syntax += f"  /CRITERIA=CI(.95).\n"
        
        elif method == 'ONEWAY_ANOVA':
            if len(variables) >= 2:
                syntax += f"ONEWAY {variables[1]} BY {variables[0]}\n"
                syntax += f"  /STATISTICS DESCRIPTIVES\n"
                syntax += f"  /MISSING ANALYSIS.\n"
        
        elif method == 'CORRELATIONS':
            if len(variables) >= 2:
                syntax += f"CORRELATIONS\n"
                syntax += f"  /VARIABLES={' '.join(variables[:4])}\n"
                syntax += f"  /PRINT=TWOTAIL NOSIG.\n"
        
        elif method == 'REGRESSION':
            if len(variables) >= 2:
                syntax += f"REGRESSION\n"
                syntax += f"  /DEPENDENT {variables[0]}\n"
                syntax += f"  /METHOD=ENTER {' '.join(variables[1:3])}\n"
                syntax += f"  /STATISTICS COEFF R ANOVA.\n"
        
        elif method == 'CROSSTABS' or method == 'CROSSTABS_CHISQ':
            if len(variables) >= 2:
                syntax += f"CROSSTABS\n"
                syntax += f"  /TABLES={variables[0]} BY {variables[1]}\n"
                syntax += f"  /CELLS=COUNT ROW COLUMN.\n"
                if method == 'CROSSTABS_CHISQ':
                    syntax += f"  /STATISTICS=CHISQ.\n"
        
        elif method == 'MEANS':
            if len(variables) >= 2:
                syntax += f"MEANS TABLES={variables[1]} BY {variables[0]}\n"
                syntax += f"  /CELLS=MEAN COUNT STDDEV.\n"
        
        elif method == 'EXAMINE_CI':
            if variables:
                syntax += f"EXAMINE VARIABLES={variables[0]}\n"
                syntax += f"  /PLOT NONE\n"
                syntax += f"  /STATISTICS DESCRIPTIVES\n"
                syntax += f"  /CINTERVAL 95.\n"
        
        elif method == 'EXAMINE_NORMALITY':
            if variables:
                syntax += f"EXAMINE VARIABLES={variables[0]}\n"
                syntax += f"  /PLOT NPPLOT\n"
                syntax += f"  /STATISTICS DESCRIPTIVES.\n"
        
        elif method == 'EXAMINE_OUTLIERS':
            if variables:
                syntax += f"EXAMINE VARIABLES={variables[0]}\n"
                syntax += f"  /PLOT BOXPLOT\n"
                syntax += f"  /STATISTICS EXTREME.\n"
        
        else:
            # حل عام
            if variables:
                syntax += f"DESCRIPTIVES VARIABLES={' '.join(variables[:3])}\n"
                syntax += f"  /STATISTICS=MEAN STDDEV MIN MAX.\n"
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def _generate_auto_analyses(self) -> str:
        """توليد تحليلات تلقائية إضافية"""
        syntax = "\n* -------------------------------------------------------------------------"
        syntax += "\n* AUTOMATIC ADDITIONAL ANALYSES"
        syntax += "\n* -------------------------------------------------------------------------\n"
        
        # العثور على المتغيرات المستمرة والفئوية
        continuous_vars = [v for v, info in self.variable_info.items() 
                         if info['stat_type'] == 'CONTINUOUS']
        categorical_vars = [v for v, info in self.variable_info.items() 
                          if info['stat_type'] == 'CATEGORICAL']
        
        # 1. تحليل وصفي شامل
        if continuous_vars:
            syntax += "\n* Comprehensive descriptive analysis\n"
            syntax += f"DESCRIPTIVES VARIABLES={' '.join(continuous_vars[:5])}\n"
            syntax += "  /STATISTICS=MEAN STDDEV MIN MAX SKEWNESS KURTOSIS.\n"
            syntax += "EXECUTE.\n"
        
        # 2. تحليل الارتباطات
        if len(continuous_vars) >= 2:
            syntax += "\n* Correlation matrix\n"
            syntax += f"CORRELATIONS\n"
            syntax += f"  /VARIABLES={' '.join(continuous_vars[:4])}\n"
            syntax += "  /PRINT=TWOTAIL NOSIG.\n"
            syntax += "EXECUTE.\n"
        
        # 3. تحليل التكرارات
        if categorical_vars:
            syntax += "\n* Frequency analysis for categorical variables\n"
            syntax += f"FREQUENCIES VARIABLES={' '.join(categorical_vars[:3])}\n"
            syntax += "  /BARCHART FREQ\n"
            syntax += "  /ORDER=ANALYSIS.\n"
            syntax += "EXECUTE.\n"
        
        # 4. تحليل العلاقات بين المتغيرات
        if continuous_vars and categorical_vars:
            syntax += "\n* Means comparison by categories\n"
            syntax += f"MEANS TABLES={continuous_vars[0]} BY {categorical_vars[0]}\n"
            syntax += "  /CELLS=MEAN COUNT STDDEV.\n"
            syntax += "EXECUTE.\n"
        
        return syntax

# ===== واجهة Streamlit =====

def main():
    # شريط جانبي
    with st.sidebar:
        st.header("📁 رفع الملفات")
        
        st.subheader("1. ملف البيانات")
        data_file = st.file_uploader(
            "رفع ملف البيانات (Excel/CSV)",
            type=['xls', 'xlsx', 'csv'],
            key="data_uploader"
        )
        
        st.markdown("---")
        
        st.subheader("2. ملف الأسئلة")
        questions_file = st.file_uploader(
            "رفع ملف الأسئلة (Word/Text)",
            type=['docx', 'doc', 'txt'],
            key="questions_uploader"
        )
        
        st.markdown("---")
        
        # خيارات متقدمة
        with st.expander("⚙️ خيارات متقدمة"):
            auto_detect = st.checkbox("التعرف التلقائي على الأنماط", value=True)
            generate_summary = st.checkbox("توليد تقرير ملخص", value=True)
            include_comments = st.checkbox("تضمين التعليقات التوضيحية", value=True)
        
        st.markdown("---")
        
        analyze_btn = st.button(
            "🧠 تحليل تلقائي كامل",
            type="primary",
            use_container_width=True
        )
    
    # المنطقة الرئيسية
    st.markdown("""
    ## 🎯 محلل SPSS الديناميكي
    
    ### 📋 المميزات:
    
    1. **ديناميكي بالكامل**: يحل أي أسئلة إحصائية مع أي بيانات
    2. **تخمين ذكي**: يتعرف على أنواع المتغيرات ومعانيها تلقائياً
    3. **تحليل تلقائي**: يحدد نوع التحليل المناسب لكل سؤال
    4. **دعم كامل**: يدعم جميع أنواع التحليلات الإحصائية الشائعة
    5. **توليد كود كامل**: يولد كود SPSS جاهز للتشغيل
    
    ### 📊 كيفية الاستخدام:
    1. **ارفع ملف البيانات** (Excel أو CSV)
    2. **ارفع ملف الأسئلة** (Word أو Text)
    3. **انقر على "تحليل تلقائي كامل"**
    4. **تحميل كود SPSS** الجاهز
    """)
    
    if data_file and analyze_btn:
        try:
            # تحميل البيانات
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(data_file.getvalue())
                data_path = tmp.name
            
            # قراءة البيانات
            if data_file.name.lower().endswith('.csv'):
                df = pd.read_csv(data_path)
            else:
                df = pd.read_excel(data_path)
            
            os.unlink(data_path)
            
            # معالجة ملف الأسئلة
            questions_text = ""
            if questions_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp:
                    tmp.write(questions_file.getvalue())
                    questions_path = tmp.name
                
                if questions_file.name.lower().endswith(('.docx', '.doc')):
                    try:
                        doc = Document(questions_path)
                        questions_text = "\n".join([para.text for para in doc.paragraphs])
                    except:
                        st.warning("⚠️ تعذر قراءة ملف Word، جاري معالجة كملف نصي")
                        with open(questions_path, 'r', encoding='utf-8', errors='ignore') as f:
                            questions_text = f.read()
                else:
                    with open(questions_path, 'r', encoding='utf-8', errors='ignore') as f:
                        questions_text = f.read()
                
                os.unlink(questions_path)
                st.success(f"✅ تم تحميل {len(questions_text.split())} كلمة من ملف الأسئلة")
            else:
                st.info("ℹ️ لم يتم رفع ملف أسئلة، سيتم إنشاء أسئلة افتراضية")
                questions_text = ""
            
            # إنشاء المحلل
            with st.spinner("🔍 جاري تحليل البيانات والأسئلة..."):
                analyzer = DynamicSPSSAnalyzer(df, questions_text)
                
                # عرض المعلومات
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("المتغيرات", len(df.columns))
                with col2:
                    st.metric("الحالات", len(df))
                with col3:
                    st.metric("الأسئلة", len(analyzer.questions))
                
                # عرض تحليل المتغيرات
                with st.expander("📋 تحليل المتغيرات"):
                    var_data = []
                    for var_name, info in analyzer.variable_info.items():
                        row = {
                            'المتغير': var_name,
                            'المعنى': info.get('inferred_meaning', 'unknown'),
                            'النوع': info['stat_type'],
                            'المستوى': info['measurement_level'],
                            'القيم الفريدة': info['n_unique']
                        }
                        var_data.append(row)
                    st.table(pd.DataFrame(var_data))
                
                # عرض الأسئلة وتحليلها
                with st.expander("📝 تحليل الأسئلة"):
                    if analyzer.questions:
                        for q in analyzer.questions:
                            st.markdown(f"**{q['number']}. {q['text']}**")
                            st.caption(f"📊 النوع: {q['detected_type']}")
                            st.caption(f"⚙️ الطريقة: {q['analysis_method']}")
                            if q['variables']:
                                st.caption(f"🔧 المتغيرات: {', '.join(q['variables'])}")
                            st.markdown("---")
                    else:
                        st.info("لم يتم العثور على أسئلة في الملف")
                
                # توليد كود SPSS
                st.markdown("---")
                st.subheader("⚙️ توليد كود SPSS الديناميكي")
                
                with st.spinner("🔄 جاري توليد الحل الكامل..."):
                    spss_code = analyzer.generate_spss_syntax()
                    
                    # عرض الكود
                    st.code(spss_code, language='spss')
                    
                    # تحميل الكود
                    st.download_button(
                        label="💾 تحميل ملف SPSS (.sps)",
                        data=spss_code,
                        file_name="Dynamic_SPSS_Solution.sps",
                        mime="text/plain",
                        use_container_width=True
                    )
                    
                    # عرض إحصائيات عن الكود
                    lines_count = spss_code.count('\n')
                    char_count = len(spss_code)
                    
                    st.info(f"""
                    **إحصائيات الكود المتولد:**
                    - 📏 عدد الأسطر: {lines_count}
                    - 🔤 عدد الحروف: {char_count}
                    - ❓ عدد الأسئلة: {len(analyzer.questions)}
                    - ✅ الحالة: جاهز للتشغيل في SPSS
                    """)
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")
    
    elif not data_file and analyze_btn:
        st.warning("⚠️ يرجى رفع ملف البيانات أولاً")
    
    else:
        # عرض أمثلة
        with st.expander("🔍 أمثلة على أنواع البيانات المدعومة"):
            st.markdown("""
            ### مثال 1: بيانات البنوك
            ```
            X1 = Account Balance
            X2 = ATM Transactions
            X3 = Services Used
            X4 = Debit Card (0=No, 1=Yes)
            X5 = Interest (0=No, 1=Yes)
            X6 = City (1,2,3,4)
            ```
            
            ### مثال 2: بيانات البيسبول
            ```
            Team, League, Built Year, Stadium Size, Salary, Attendance, Wins
            ```
            
            ### مثال 3: بيانات OECD
            ```
            Country, G7 Member, Area, Population, GDP, Labor Force, Region
            ```
            
            ### مثال 4: بيانات الاستبيان
            ```
            Gender, Race, Salary, Region, Happiness, Age, Education, Occupation
            ```
            """)

if __name__ == "__main__":
    main()
