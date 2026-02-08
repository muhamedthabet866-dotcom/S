import streamlit as st
import pandas as pd
import numpy as np
import re
import base64
from datetime import datetime
from collections import OrderedDict
import hashlib

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="SPSS Code Generator - Intelligent Version",
    page_icon="📊",
    layout="wide"
)

st.title("📊 مولد أكواد SPSS الذكي")
st.markdown("### يتعرف على المتغيرات من الأسئلة ويولد أكواد دقيقة لكل سؤال")

class IntelligentSPSSGenerator:
    def __init__(self):
        self.processed_questions = OrderedDict()
        self.variable_mapping = self._create_variable_mapping()
        self.question_types = {
            'descriptive': ['mean', 'average', 'median', 'mode', 'standard deviation', 'variance', 'descriptive', 'calculate', 'compute'],
            'frequency': ['frequency', 'distribution', 'count', 'table', 'percentage', 'percent', 'proportion'],
            't_test': ['t-test', 't test', 'compare means', 'independent samples', 'paired'],
            'anova': ['anova', 'analysis of variance', 'f-test', 'one-way', 'two-way'],
            'correlation': ['correlation', 'relationship', 'association', 'correlate', 'relationship between'],
            'regression': ['regression', 'predict', 'linear model', 'multiple regression'],
            'chi_square': ['chi-square', 'chi squared', 'contingency', 'association categorical'],
            'graph': ['graph', 'chart', 'histogram', 'bar chart', 'pie chart', 'scatter', 'plot', 'draw'],
            'confidence': ['confidence interval', 'ci', '95%', '99%', 'interval', 'construct the confidence'],
            'normality': ['normality', 'normal distribution', 'shapiro-wilk', 'kolmogorov', 'empirical rule', 'chebyshev'],
            'outliers': ['outliers', 'extreme values', 'unusual observations', 'extreme value', 'determine the outliers'],
            'group_comparison': ['by group', 'for each', 'compare groups', 'between groups', 'for each city', 'by city'],
            'recode': ['recode', 'categorize', 'group into', 'create classes', 'classify', 'suitable number of classes'],
            'transform': ['transform', 'compute', 'create variable', 'new variable', 'calculate']
        }
    
    def _create_variable_mapping(self):
        """إنشاء قاموس لربط أسماء المتغيرات الشائعة"""
        return {
            # مصطلحات شائعة في الأسئلة الإحصائية
            'account': ['X1', 'balance', 'account_balance'],
            'balance': ['X1', 'account_balance'],
            'atm': ['X2', 'transactions', 'atm_transactions'],
            'transaction': ['X2', 'atm', 'transactions'],
            'service': ['X3', 'other_services', 'services'],
            'debit': ['X4', 'debit_card', 'card'],
            'card': ['X4', 'debit_card'],
            'interest': ['X5', 'interest_received'],
            'city': ['X6', 'location', 'city_location'],
            'location': ['X6', 'city'],
            
            # مصطلحات عامة
            'income': ['X1', 'salary', 'revenue'],
            'salary': ['X1', 'income'],
            'age': ['age_var'],
            'gender': ['gender_var', 'sex'],
            'education': ['edu_var', 'education_level'],
            'score': ['score_var', 'test_score'],
            'price': ['price_var', 'cost'],
            'quantity': ['quantity_var', 'amount'],
            'rate': ['rate_var', 'percentage'],
            'category': ['cat_var', 'group']
        }
    
    def analyze_dataset(self, df):
        """تحليل شامل للبيانات وإنشاء تسميات ذكية"""
        analysis = {
            'variables': {},
            'summary': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_vars': [],
                'categorical_vars': [],
                'text_vars': [],
                'column_names': list(df.columns)
            },
            'suggested_labels': {}
        }
        
        for column in df.columns:
            col_data = df[column]
            var_info = {
                'name': column,
                'type': 'unknown',
                'missing': int(col_data.isna().sum()),
                'missing_percent': round(col_data.isna().sum() / len(df) * 100, 2),
                'unique_values': int(col_data.nunique()),
                'values': []
            }
            
            try:
                # محاولة تحويل إلى رقم
                numeric_data = pd.to_numeric(col_data.dropna())
                var_info['type'] = 'numeric'
                var_info['min'] = float(numeric_data.min())
                var_info['max'] = float(numeric_data.max())
                var_info['mean'] = float(numeric_data.mean())
                var_info['std'] = float(numeric_data.std())
                var_info['median'] = float(numeric_data.median())
                
                if var_info['unique_values'] <= 10:
                    var_info['subtype'] = 'categorical_numeric'
                    var_info['values'] = sorted([float(x) for x in numeric_data.unique()])
                    analysis['summary']['categorical_vars'].append(column)
                else:
                    var_info['subtype'] = 'continuous'
                    analysis['summary']['numeric_vars'].append(column)
                    
            except:
                # متغير نصي
                var_info['type'] = 'text'
                unique_vals = list(col_data.dropna().unique())
                var_info['values'] = unique_vals[:10]
                
                if var_info['unique_values'] <= 15:
                    var_info['subtype'] = 'categorical_text'
                    analysis['summary']['categorical_vars'].append(column)
                else:
                    var_info['subtype'] = 'free_text'
                    analysis['summary']['text_vars'].append(column)
            
            # إنشاء تسمية مقترحة للمتغير
            suggested_label = self._suggest_variable_label(column, var_info)
            analysis['suggested_labels'][column] = suggested_label
            
            analysis['variables'][column] = var_info
        
        return analysis
    
    def _suggest_variable_label(self, column_name, var_info):
        """اقتراح تسمية ذكية للمتغير بناءً على اسمه وخصائصه"""
        column_lower = column_name.lower()
        
        # إذا كان المتغير له اسم شائع
        if 'x1' in column_lower or column_name == 'X1':
            return 'Account Balance ($)'
        elif 'x2' in column_lower or column_name == 'X2':
            return 'ATM Transactions'
        elif 'x3' in column_lower or column_name == 'X3':
            return 'Other Services'
        elif 'x4' in column_lower or column_name == 'X4':
            return 'Debit Card Holder'
        elif 'x5' in column_lower or column_name == 'X5':
            return 'Interest Received'
        elif 'x6' in column_lower or column_name == 'X6':
            return 'City Location'
        
        # اقتراح بناءً على نوع البيانات
        if var_info['subtype'] == 'continuous':
            if var_info['mean'] > 1000:
                return f'{column_name} (Large Values)'
            else:
                return f'{column_name} (Continuous)'
        elif var_info['subtype'] == 'categorical_numeric':
            if var_info['unique_values'] == 2:
                return f'{column_name} (Binary: 0/1)'
            else:
                return f'{column_name} (Categorical)'
        elif var_info['subtype'] == 'categorical_text':
            return f'{column_name} (Categories)'
        
        return column_name.replace('_', ' ').title()
    
    def detect_variables_in_question(self, question, df_columns, data_analysis):
        """كشف ذكي للمتغيرات في السؤال"""
        question_lower = question.lower()
        detected_vars = []
        
        # الخطوة 1: البحث المباشر عن أسماء الأعمدة
        for column in df_columns:
            col_lower = column.lower()
            if (col_lower in question_lower or 
                f' {col_lower} ' in f' {question_lower} ' or
                question_lower.startswith(col_lower) or
                question_lower.endswith(col_lower)):
                detected_vars.append(column)
        
        # الخطوة 2: استخدام قاموس الربط
        for keyword, possible_vars in self.variable_mapping.items():
            if keyword in question_lower:
                for possible_var in possible_vars:
                    if possible_var in df_columns and possible_var not in detected_vars:
                        detected_vars.append(possible_var)
        
        # الخطوة 3: البحث عن مصطلحات مفتاحية
        key_terms = {
            'account balance': ['X1'],
            'balance': ['X1'],
            'atm transaction': ['X2'],
            'transaction': ['X2'],
            'debit card': ['X4'],
            'interest': ['X5'],
            'city': ['X6'],
            'location': ['X6'],
            'mean': data_analysis['summary']['numeric_vars'][:2] if data_analysis['summary']['numeric_vars'] else [],
            'average': data_analysis['summary']['numeric_vars'][:2] if data_analysis['summary']['numeric_vars'] else [],
            'frequency': data_analysis['summary']['categorical_vars'][:3] if data_analysis['summary']['categorical_vars'] else [],
            'histogram': data_analysis['summary']['numeric_vars'][:2] if data_analysis['summary']['numeric_vars'] else [],
            'bar chart': data_analysis['summary']['categorical_vars'][:1] + data_analysis['summary']['numeric_vars'][:1] 
                         if data_analysis['summary']['categorical_vars'] and data_analysis['summary']['numeric_vars'] else [],
            'pie chart': data_analysis['summary']['categorical_vars'][:1] if data_analysis['summary']['categorical_vars'] else [],
            'confidence interval': data_analysis['summary']['numeric_vars'][:1] if data_analysis['summary']['numeric_vars'] else []
        }
        
        for term, vars_list in key_terms.items():
            if term in question_lower and vars_list:
                for var in vars_list:
                    if var not in detected_vars:
                        detected_vars.append(var)
        
        # إزالة التكرارات
        return list(OrderedDict.fromkeys(detected_vars))
    
    def classify_question(self, question):
        """تصنيف دقيق للسؤال مع تحديد متطلباته"""
        question_lower = question.lower()
        classifications = []
        
        for q_type, keywords in self.question_types.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', question_lower):
                    classifications.append(q_type)
                    break
        
        # تحسين التصنيفات
        if 'frequency' in classifications and 'table' in question_lower:
            classifications.append('frequency_table')
        
        if 'graph' in classifications:
            if 'histogram' in question_lower:
                classifications.append('histogram')
            if 'bar' in question_lower and 'chart' in question_lower:
                classifications.append('bar_chart')
            if 'pie' in question_lower and 'chart' in question_lower:
                classifications.append('pie_chart')
            if 'scatter' in question_lower:
                classifications.append('scatter_plot')
        
        if 'confidence' in classifications:
            if '95%' in question_lower:
                classifications.append('ci_95')
            if '99%' in question_lower:
                classifications.append('ci_99')
        
        if not classifications:
            classifications.append('general_analysis')
        
        return list(OrderedDict.fromkeys(classifications))
    
    def generate_spss_for_question(self, q_num, question, df, data_analysis):
        """توليد كود SPSS دقيق ومخصص للسؤال"""
        
        # كشف المتغيرات
        detected_vars = self.detect_variables_in_question(
            question, 
            data_analysis['summary']['column_names'],
            data_analysis
        )
        
        # تصنيف السؤال
        classifications = self.classify_question(question)
        
        # إنشاء بصمة فريدة
        fingerprint = self._create_question_fingerprint(question, detected_vars, classifications)
        
        # التحقق من التكرار
        if fingerprint in self.processed_questions:
            similar_q = self.processed_questions[fingerprint]
            return None, f"تم معالجة سؤال مشابه (السؤال {similar_q['number']})"
        
        # حفظ البصمة
        self.processed_questions[fingerprint] = {
            'number': q_num,
            'question': question[:100],
            'variables': detected_vars,
            'types': classifications,
            'fingerprint': fingerprint
        }
        
        # توليد الكود
        code_lines = []
        code_lines.append(f"* {'='*70}")
        code_lines.append(f"* QUESTION {q_num}: {question[:80]}{'...' if len(question) > 80 else ''}")
        code_lines.append(f"* Classification: {', '.join(classifications)}")
        
        if detected_vars:
            var_labels = [data_analysis['suggested_labels'].get(v, v) for v in detected_vars]
            code_lines.append(f"* Variables: {', '.join([f'{v} ({l})' for v, l in zip(detected_vars[:3], var_labels[:3])])}")
            if len(detected_vars) > 3:
                code_lines.append(f"* ... and {len(detected_vars) - 3} more variables")
        
        code_lines.append(f"* {'='*70}\n")
        
        # توليد التحليلات المحددة
        analysis_code = self._generate_specific_analysis(
            q_num, question, detected_vars, classifications, data_analysis
        )
        
        code_lines.append(analysis_code)
        code_lines.append("EXECUTE.")
        code_lines.append("")
        
        return '\n'.join(code_lines), None
    
    def _create_question_fingerprint(self, question, detected_vars, classifications):
        """إنشاء بصمة فريدة للسؤال"""
        # تبسيط السؤال للمقارنة
        simple_question = re.sub(r'\d+', '#', question.lower())
        simple_question = re.sub(r'\s+', ' ', simple_question).strip()
        
        components = [
            '|'.join(sorted(classifications)),
            '|'.join(sorted(detected_vars)),
            simple_question[:50]
        ]
        
        fingerprint_string = '@@@'.join(components)
        return hashlib.md5(fingerprint_string.encode()).hexdigest()[:10]
    
    def _generate_specific_analysis(self, q_num, question, detected_vars, classifications, data_analysis):
        """توليد تحليل محدد بناءً على السؤال"""
        question_lower = question.lower()
        analysis_lines = []
        
        # إذا لم يتم اكتشاف متغيرات، استخدام متغيرات ذكية
        if not detected_vars:
            # محاولة تخمين المتغيرات المناسبة
            if 'account balance' in question_lower:
                detected_vars = ['X1']
            elif 'atm' in question_lower or 'transaction' in question_lower:
                detected_vars = ['X2']
            elif 'debit card' in question_lower:
                detected_vars = ['X4']
            elif 'interest' in question_lower:
                detected_vars = ['X5']
            elif 'city' in question_lower:
                detected_vars = ['X6']
            else:
                # استخدام متغيرات حسب النوع
                if 'frequency' in classifications:
                    detected_vars = data_analysis['summary']['categorical_vars'][:3]
                elif 'descriptive' in classifications:
                    detected_vars = data_analysis['summary']['numeric_vars'][:2]
                elif 'histogram' in classifications:
                    detected_vars = data_analysis['summary']['numeric_vars'][:2]
                else:
                    detected_vars = data_analysis['summary']['column_names'][:3]
        
        # توليد التحليلات بناءً على التصنيفات
        for q_type in classifications:
            if q_type == 'descriptive':
                if detected_vars:
                    vars_str = ' '.join(detected_vars[:3])
                    analysis_lines.append(f"* Descriptive statistics")
                    analysis_lines.append(f"FREQUENCIES VARIABLES={vars_str}")
                    analysis_lines.append("  /FORMAT=NOTABLE")
                    analysis_lines.append("  /STATISTICS=MEAN MEDIAN MODE MINIMUM MAXIMUM RANGE VARIANCE STDDEV SKEWNESS SESKEW.")
                    analysis_lines.append("")
            
            elif q_type == 'frequency_table':
                categorical_vars = [v for v in detected_vars 
                                  if data_analysis['variables'].get(v, {}).get('subtype') in 
                                  ['categorical_numeric', 'categorical_text']]
                
                if not categorical_vars:
                    categorical_vars = data_analysis['summary']['categorical_vars'][:3]
                
                if categorical_vars:
                    vars_str = ' '.join(categorical_vars[:3])
                    analysis_lines.append(f"* Frequency tables")
                    analysis_lines.append(f"FREQUENCIES VARIABLES={vars_str}")
                    analysis_lines.append("  /ORDER=ANALYSIS")
                    analysis_lines.append("  /BARCHART.")
                    analysis_lines.append("")
            
            elif q_type == 'histogram':
                numeric_vars = [v for v in detected_vars 
                              if data_analysis['variables'].get(v, {}).get('subtype') == 'continuous']
                
                if not numeric_vars:
                    numeric_vars = data_analysis['summary']['numeric_vars'][:2]
                
                for var in numeric_vars[:2]:
                    analysis_lines.append(f"* Histogram for {var}")
                    analysis_lines.append(f"GRAPH /HISTOGRAM={var}")
                    analysis_lines.append(f"  /TITLE='Histogram of {data_analysis['suggested_labels'].get(var, var)}'.")
                    analysis_lines.append("")
            
            elif q_type == 'bar_chart':
                if len(detected_vars) >= 2:
                    # افتراض أن الأول كمي والثاني فئوي
                    analysis_lines.append(f"* Bar chart")
                    analysis_lines.append(f"GRAPH /BAR(SIMPLE)=MEAN({detected_vars[0]}) BY {detected_vars[1]}")
                    analysis_lines.append(f"  /TITLE='Average {data_analysis['suggested_labels'].get(detected_vars[0], detected_vars[0])} by {data_analysis['suggested_labels'].get(detected_vars[1], detected_vars[1])}'.")
                    analysis_lines.append("")
                elif detected_vars:
                    # استخدام متغير فئوي للرسم البياني
                    categorical_vars = [v for v in detected_vars 
                                      if data_analysis['variables'].get(v, {}).get('subtype') in 
                                      ['categorical_numeric', 'categorical_text']]
                    if categorical_vars:
                        var = categorical_vars[0]
                        analysis_lines.append(f"* Bar chart for {var}")
                        analysis_lines.append(f"GRAPH /BAR(SIMPLE)=PCT BY {var}")
                        analysis_lines.append(f"  /TITLE='Percentage Distribution of {data_analysis['suggested_labels'].get(var, var)}'.")
                        analysis_lines.append("")
            
            elif q_type == 'pie_chart':
                categorical_vars = [v for v in detected_vars 
                                  if data_analysis['variables'].get(v, {}).get('subtype') in 
                                  ['categorical_numeric', 'categorical_text']]
                
                if categorical_vars:
                    var = categorical_vars[0]
                    analysis_lines.append(f"* Pie chart for {var}")
                    analysis_lines.append(f"GRAPH /PIE=PCT BY {var}")
                    analysis_lines.append(f"  /TITLE='Pie Chart: {data_analysis['suggested_labels'].get(var, var)}'.")
                    analysis_lines.append("")
            
            elif q_type == 'group_comparison':
                if 'city' in question_lower and detected_vars:
                    group_var = 'X6' if 'X6' in data_analysis['summary']['column_names'] else detected_vars[0]
                    analysis_vars = [v for v in detected_vars if v != group_var][:2]
                    
                    if analysis_vars:
                        vars_str = ' '.join(analysis_vars)
                        analysis_lines.append(f"* Analysis by {group_var}")
                        analysis_lines.append(f"SORT CASES BY {group_var}.")
                        analysis_lines.append(f"SPLIT FILE LAYERED BY {group_var}.")
                        analysis_lines.append(f"FREQUENCIES VARIABLES={vars_str}")
                        analysis_lines.append("  /FORMAT=NOTABLE")
                        analysis_lines.append("  /STATISTICS=MEAN MEDIAN MODE MIN MAX.")
                        analysis_lines.append("SPLIT FILE OFF.")
                        analysis_lines.append("")
            
            elif q_type in ['ci_95', 'ci_99', 'confidence']:
                numeric_vars = [v for v in detected_vars 
                              if data_analysis['variables'].get(v, {}).get('subtype') == 'continuous']
                
                if not numeric_vars:
                    numeric_vars = data_analysis['summary']['numeric_vars'][:1]
                
                for var in numeric_vars[:1]:
                    if '99%' in question_lower or q_type == 'ci_99':
                        analysis_lines.append(f"* 99% Confidence Interval for {var}")
                        analysis_lines.append(f"EXAMINE VARIABLES={var}")
                        analysis_lines.append("  /STATISTICS DESCRIPTIVES")
                        analysis_lines.append("  /CINTERVAL 99")
                        analysis_lines.append("  /PLOT NONE.")
                    else:
                        analysis_lines.append(f"* 95% Confidence Interval for {var}")
                        analysis_lines.append(f"EXAMINE VARIABLES={var}")
                        analysis_lines.append("  /STATISTICS DESCRIPTIVES")
                        analysis_lines.append("  /CINTERVAL 95")
                        analysis_lines.append("  /PLOT NONE.")
                    analysis_lines.append("")
            
            elif q_type == 'normality':
                numeric_vars = [v for v in detected_vars 
                              if data_analysis['variables'].get(v, {}).get('subtype') == 'continuous']
                
                if not numeric_vars:
                    numeric_vars = data_analysis['summary']['numeric_vars'][:1]
                
                for var in numeric_vars[:1]:
                    analysis_lines.append(f"* Normality test for {var}")
                    analysis_lines.append(f"EXAMINE VARIABLES={var}")
                    analysis_lines.append("  /PLOT NPPLOT")
                    analysis_lines.append("  /STATISTICS DESCRIPTIVES.")
                    analysis_lines.append("ECHO 'Check Shapiro-Wilk test: If Sig. > 0.05, data is normal (use Empirical Rule).'.")
                    analysis_lines.append("ECHO 'If Sig. < 0.05, data is not normal (use Chebyshev Rule).'.")
                    analysis_lines.append("")
            
            elif q_type == 'outliers':
                numeric_vars = [v for v in detected_vars 
                              if data_analysis['variables'].get(v, {}).get('subtype') == 'continuous']
                
                if not numeric_vars:
                    numeric_vars = data_analysis['summary']['numeric_vars'][:1]
                
                for var in numeric_vars[:1]:
                    analysis_lines.append(f"* Outlier detection for {var}")
                    analysis_lines.append(f"EXAMINE VARIABLES={var}")
                    analysis_lines.append("  /PLOT BOXPLOT")
                    analysis_lines.append("  /STATISTICS DESCRIPTIVES.")
                    analysis_lines.append("ECHO 'Outliers are points beyond the whiskers in the boxplot.'.")
                    analysis_lines.append("ECHO 'Extreme values are marked with * or o in the output.'.")
                    analysis_lines.append("")
            
            elif q_type == 'recode':
                if 'account balance' in question_lower or 'X1' in detected_vars:
                    analysis_lines.append(f"* Recoding Account Balance (X1) into classes")
                    analysis_lines.append(f"RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_Classes.")
                    analysis_lines.append(f"VALUE LABELS X1_Classes 1 '0-500' 2 '501-1000' 3 '1001-1500' 4 '1501-2000' 5 'Over 2000'.")
                    analysis_lines.append(f"FREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.")
                    analysis_lines.append("")
                
                elif 'atm' in question_lower or 'transaction' in question_lower or 'X2' in detected_vars:
                    analysis_lines.append(f"* Recoding ATM Transactions (X2) using K-rule")
                    analysis_lines.append(f"RECODE X2 (2 thru 5=1) (6 thru 9=2) (10 thru 13=3) (14 thru 17=4) (18 thru 21=5) (22 thru 25=6) INTO X2_Krule.")
                    analysis_lines.append(f"VALUE LABELS X2_Krule 1 '2-5' 2 '6-9' 3 '10-13' 4 '14-17' 5 '18-21' 6 '22-25'.")
                    analysis_lines.append(f"FREQUENCIES VARIABLES=X2_Krule.")
                    analysis_lines.append("")
        
        # إذا لم يتم إنشاء أي تحليل، إنشاء تحليل عام
        if not analysis_lines:
            if detected_vars:
                vars_str = ' '.join(detected_vars[:3])
                analysis_lines.append(f"* General analysis for variables: {vars_str}")
                analysis_lines.append(f"DESCRIPTIVES VARIABLES={vars_str}")
                analysis_lines.append("  /STATISTICS=MEAN STDDEV MIN MAX.")
            else:
                analysis_lines.append("* No specific analysis generated. Check variable detection.")
        
        return '\n'.join(analysis_lines)
    
    def generate_spss_header(self, df, data_analysis, filename):
        """توليد رأس كود SPSS ذكي"""
        header = f"""* =========================================================================
* SPSS SYNTAX FILE - INTELLIGENT GENERATION
* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Data File: {filename}
* Rows: {data_analysis['summary']['total_rows']}
* Variables: {data_analysis['summary']['total_columns']}
* =========================================================================

* DATA DEFINITION AND SETUP
"""
        
        # تعريف تسميات المتغيرات الذكية
        var_labels = []
        for var_name, suggested_label in data_analysis['suggested_labels'].items():
            var_labels.append(f"{var_name} '{suggested_label}'")
        
        header += "VARIABLE LABELS\n    " + " /".join(var_labels) + ".\n\n"
        
        # تسميات القيم للمتغيرات الفئوية
        value_labels = []
        for var_name, var_info in data_analysis['variables'].items():
            if var_info['subtype'] in ['categorical_numeric', 'categorical_text']:
                if var_info['unique_values'] <= 10:
                    line = f"    /{var_name} "
                    
                    if var_name == 'X4':
                        line += "0 'No' 1 'Yes'"
                    elif var_name == 'X5':
                        line += "0 'No' 1 'Yes'"
                    elif var_name == 'X6':
                        line += "1 'City 1' 2 'City 2' 3 'City 3' 4 'City 4'"
                    elif var_info['subtype'] == 'categorical_numeric':
                        for val in var_info['values'][:10]:
                            line += f"{int(val)} 'Category {int(val)}' "
                    else:
                        for i, val in enumerate(var_info['values'][:5], 1):
                            truncated_val = str(val)[:20]
                            line += f"{i} '{truncated_val}' "
                    
                    value_labels.append(line)
        
        if value_labels:
            header += "VALUE LABELS\n"
            header += "\n".join(value_labels)
            header += ".\n\n"
        
        header += "EXECUTE.\n\n"
        header += "* =========================================================================\n"
        header += "* QUESTION ANALYSIS SECTION\n"
        header += "* =========================================================================\n\n"
        
        return header
    
    def create_download_link(self, content, filename, btn_text="📥 تنزيل"):
        """إنشاء رابط تحميل"""
        b64 = base64.b64encode(content.encode()).decode()
        return f'<a href="data:file/txt;base64,{b64}" download="{filename}" style="text-decoration: none; padding: 10px 20px; background-color: #4CAF50; color: white; border-radius: 5px; font-weight: bold;">{btn_text} {filename}</a>'

# التطبيق الرئيسي
def main():
    st.sidebar.title("⚙️ إعدادات المولد الذكي")
    
    # خيارات متقدمة
    st.sidebar.subheader("خيارات الكشف الذكي")
    enable_smart_detection = st.sidebar.checkbox("تفعيل الكشف الذكي عن المتغيرات", value=True)
    auto_suggest_labels = st.sidebar.checkbox("اقتراح تسميات ذكية", value=True)
    prevent_duplicates = st.sidebar.checkbox("منع التحليلات المكررة", value=True)
    
    st.sidebar.subheader("تفاصيل الإخراج")
    include_comments = st.sidebar.checkbox("إضافة تعليقات توضيحية", value=True)
    show_variable_info = st.sidebar.checkbox("عرض معلومات المتغيرات", value=True)
    
    # إنشاء المولد
    generator = IntelligentSPSSGenerator()
    
    # القسم الرئيسي
    st.markdown("### 📁 تحميل الملفات")
    
    # تحميل الملفات
    col1, col2 = st.columns(2)
    
    with col1:
        data_file = st.file_uploader(
            "ملف البيانات (Excel/CSV)",
            type=['xlsx', 'xls', 'csv'],
            key="data_uploader"
        )
    
    with col2:
        questions_file = st.file_uploader(
            "ملف الأسئلة (TXT)",
            type=['txt'],
            key="questions_uploader"
        )
    
    if data_file and questions_file:
        try:
            # قراءة البيانات
            if data_file.name.endswith('.csv'):
                df = pd.read_csv(data_file, encoding='utf-8')
            else:
                df = pd.read_excel(data_file)
            
            # قراءة الأسئلة
            questions_text = questions_file.getvalue().decode('utf-8')
            
            # تحليل البيانات
            with st.spinner("جارٍ تحليل البيانات..."):
                data_analysis = generator.analyze_dataset(df)
            
            st.success(f"✅ تم تحليل البيانات بنجاح")
            
            # عرض لوحة المعلومات
            with st.expander("📊 لوحة معلومات البيانات", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("الصفوف", data_analysis['summary']['total_rows'])
                with col2:
                    st.metric("المتغيرات", data_analysis['summary']['total_columns'])
                with col3:
                    st.metric("المتغيرات الكمية", len(data_analysis['summary']['numeric_vars']))
                with col4:
                    st.metric("المتغيرات الفئوية", len(data_analysis['summary']['categorical_vars']))
                
                st.write("**المتغيرات مع التسميات المقترحة:**")
                for var_name, suggested_label in list(data_analysis['suggested_labels'].items())[:10]:
                    var_info = data_analysis['variables'][var_name]
                    st.write(f"- **{var_name}**: {suggested_label} ({var_info['type']}, قيم فريدة: {var_info['unique_values']})")
                
                if len(data_analysis['suggested_labels']) > 10:
                    st.write(f"... و {len(data_analysis['suggested_labels']) - 10} متغيرات أخرى")
            
            # معالجة الأسئلة
            questions = []
            lines = questions_text.split('\n')
            current_q = ""
            
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+[\.\)]', line) or re.match(r'^\d+\.\s+', line):
                    if current_q:
                        questions.append(current_q.strip())
                    current_q = line
                elif current_q and line and not line.startswith('*'):
                    current_q += " " + line
            
            if current_q:
                questions.append(current_q.strip())
            
            # تصفية الأسئلة الفارغة
            questions = [q for q in questions if q and len(q) > 5]
            
            st.info(f"📋 تم تحليل {len(questions)} سؤال")
            
            # عرض تحليل الأسئلة
            with st.expander("🔍 تحليل مفصل للأسئلة", expanded=True):
                for i, q in enumerate(questions[:15], 1):
                    detected_vars = generator.detect_variables_in_question(
                        q, 
                        data_analysis['summary']['column_names'],
                        data_analysis
                    )
                    classifications = generator.classify_question(q)
                    
                    st.write(f"**السؤال {i}:**")
                    st.write(f"{q[:120]}{'...' if len(q) > 120 else ''}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if classifications:
                            st.caption(f"**الأنواع:** {', '.join(classifications)}")
                    with col2:
                        if detected_vars:
                            var_labels = [data_analysis['suggested_labels'].get(v, v) for v in detected_vars[:3]]
                            st.caption(f"**المتغيرات المكتشفة:** {', '.join([f'{v} ({l})' for v, l in zip(detected_vars[:3], var_labels[:3])])}")
                    
                    st.write("---")
                
                if len(questions) > 15:
                    st.write(f"... و {len(questions) - 15} أسئلة أخرى")
            
            # زر توليد الكود
            st.markdown("---")
            if st.button("🚀 توليد كود SPSS الذكي", type="primary", use_container_width=True):
                
                with st.spinner(f"جارٍ توليد أكواد SPSS لـ {len(questions)} سؤال..."):
                    
                    # توليد الرأس
                    spss_code = generator.generate_spss_header(df, data_analysis, data_file.name)
                    
                    # معالجة كل سؤال
                    processed_count = 0
                    skipped_count = 0
                    skipped_details = []
                    
                    progress_bar = st.progress(0)
                    
                    for i, question in enumerate(questions, 1):
                        progress_bar.progress(i / len(questions))
                        
                        question_code, skip_reason = generator.generate_spss_for_question(
                            i, question, df, data_analysis
                        )
                        
                        if question_code:
                            spss_code += question_code
                            processed_count += 1
                        else:
                            skipped_count += 1
                            skipped_details.append(f"السؤال {i}: {skip_reason}")
                    
                    # إضافة تذييل
                    spss_code += f"""* =========================================================================
* END OF INTELLIGENT ANALYSIS
* Total Questions: {len(questions)}
* Successfully Processed: {processed_count}
* Skipped (to avoid duplicates): {skipped_count}
* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* =========================================================================
"""
                    
                    # عرض النتائج
                    st.success(f"✅ تم معالجة {processed_count} سؤال بنجاح")
                    
                    if skipped_details:
                        st.warning(f"⚠️ تم تخطي {skipped_count} سؤال لتجنب التكرار")
                        with st.expander("تفاصيل الأسئلة المتخطاة"):
                            for detail in skipped_details:
                                st.write(detail)
                    
                    # عرض الكود الناتج
                    st.subheader("📋 كود SPSS الذكي النهائي")
                    
                    # خيارات العرض
                    show_full = st.checkbox("عرض الكود كاملاً", value=False)
                    
                    if show_full:
                        st.code(spss_code, language='text', height=600)
                    else:
                        code_lines = spss_code.split('\n')
                        preview_lines = code_lines[:200]
                        st.code('\n'.join(preview_lines), language='text')
                        
                        if len(code_lines) > 200:
                            st.info(f"عرض 200 سطر من أصل {len(code_lines)}. قم بتفعيل 'عرض الكود كاملاً' لرؤية الكود كاملاً.")
                    
                    # قسم التنزيل
                    st.markdown("---")
                    st.subheader("📥 تحميل الملفات الناتجة")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(generator.create_download_link(
                            spss_code, "SPSS_Intelligent_Analysis.sps", "📊"
                        ), unsafe_allow_html=True)
                    
                    with col2:
                        # إنشاء تقرير تحليل
                        report = f"""تقرير التحليل الذكي
========================
التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ملف البيانات: {data_file.name}
عدد الأسئلة: {len(questions)}
عدد الأسئلة المعالجة: {processed_count}
عدد الأسئلة المتخطاة: {skipped_count}

تفاصيل الأسئلة المعالجة:
"""
                        for i, (fingerprint, info) in enumerate(generator.processed_questions.items(), 1):
                            report += f"""
{i}. السؤال {info['number']}:
   - المحتوى: {info['question']}
   - المتغيرات: {', '.join(info['variables'])}
   - الأنواع: {', '.join(info['types'])}
"""
                        
                        st.markdown(generator.create_download_link(
                            report, "Analysis_Report.txt", "📄"
                        ), unsafe_allow_html=True)
                    
                    with col3:
                        # إنشاء دليل الاستخدام
                        guide = f"""دليل استخدام كود SPSS الذكي
============================
1. افتح برنامج SPSS
2. قم بتحميل ملف البيانات: {data_file.name}
3. انتقل إلى Window → Syntax Editor
4. الصق الكود المرفق
5. حدد الكود كاملاً (Ctrl+A)
6. اضغط F5 أو انقر على زر التشغيل

معلومات التحليل:
- تم معالجة {processed_count} سؤال
- تم توليد تحليلات مختلفة لكل سؤال
- تم استخدام التسميات الذكية للمتغيرات
- تم تجنب التكرار في التحليلات

نصائح:
- راجع النتائج في نافذة Output
- احفظ الملفات بعد التشغيل
- يمكنك تعديل الكود حسب احتياجك
"""
                        
                        st.markdown(generator.create_download_link(
                            guide, "User_Guide.txt", "📝"
                        ), unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")
    
    else:
        # واجهة الترحيب
        st.info("""
        ## 🎯 مرحباً بك في المولد الذكي لأكواد SPSS
        
        **المميزات الجديدة:**
        ✅ **كشف ذكي للمتغيرات** - يتعرف على "account balance" كـ X1
        ✅ **تسميات ذكية** - يضع تسميات مناسبة للمتغيرات
        ✅ **تحليل مخصص** - كل سؤال يحصل على تحليل مختلف
        ✅ **منع التكرار** - نظام بصمات يمنع التحليلات المكررة
        
        **كيفية الاستخدام:**
        1. **حمّل ملف البيانات** (مثل Data set 1.xlsx)
        2. **حمّل ملف الأسئلة** (ملف نصي بالأسئلة)
        3. **اضغط على زر التوليد الذكي**
        4. **حمل الملفات الناتجة**
        
        **المثال المدعوم:**
        - البيانات: ملف Excel بأعمدة X1, X2, X3, X4, X5, X6
        - الأسئلة: ملف نصي بأسئلة مثل:
          "Construct a frequency table for account balance"
          "Draw histogram for ATM transactions"
          "Calculate mean and standard deviation"
        """)

if __name__ == "__main__":
    main()
