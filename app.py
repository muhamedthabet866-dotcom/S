import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import re
import math
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="SPSS Dynamic Solver v26",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 محلل SPSS الديناميكي - الإصدار 26")
st.markdown("### يحل أي امتحان إحصائي مع قراءة التعريفات من ملف الأسئلة")

class SPSSv26Solver:
    """محلل متكامل لـ SPSS v26 مع قراءة التعريفات من الأسئلة"""
    
    def __init__(self, df: pd.DataFrame, questions_text: str):
        self.df = df
        self.questions_text = questions_text
        self.variable_definitions = self._extract_variable_definitions()
        self.variable_info = self._analyze_variables_with_definitions()
        self.questions = self._parse_questions()
        
    def _extract_variable_definitions(self) -> Dict:
        """استخراج تعريفات المتغيرات من ملف الأسئلة"""
        definitions = {}
        
        # تحويل النص إلى سطور
        lines = self.questions_text.split('\n')
        
        # البحث عن قسم Where أو حيث
        start_where = False
        for line in lines:
            line = line.strip()
            line_lower = line.lower()
            
            # بداية قسم التعريفات
            if 'where:' in line_lower or 'حيث:' in line_lower:
                start_where = True
                continue
            
            # إذا كنا في قسم التعريفات
            if start_where and line:
                if '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        var = parts[0].strip().upper()
                        definition = parts[1].strip()
                        if var.startswith('X'):
                            definitions[var] = definition
                else:
                    # ربما انتهى قسم التعريفات
                    break
        
        # البحث عن تعريفات في النص كله
        for line in lines:
            line = line.strip()
            if '=' in line and ('X' in line or 'x' in line):
                # نمط X1 = تعريف
                match = re.match(r'([Xx]\d+)\s*=\s*(.+)', line)
                if match:
                    var = match.group(1).upper()
                    definition = match.group(2).strip()
                    definitions[var] = definition
        
        return definitions
    
    def _analyze_variables_with_definitions(self) -> Dict:
        """تحليل المتغيرات مع استخدام التعريفات من الأسئلة"""
        variable_info = {}
        
        for col in self.df.columns:
            col_str = str(col).strip().upper()
            var_data = self.df[col].dropna()
            
            info = {
                'name': col_str,
                'original_name': col_str,
                'dtype': str(self.df[col].dtype),
                'n_unique': len(var_data.unique()),
                'missing': self.df[col].isna().sum(),
                'total': len(self.df[col]),
                'unique_values': sorted(var_data.unique().tolist()) if len(var_data.unique()) <= 20 else []
            }
            
            # استخدام التعريف من الأسئلة إذا موجود
            if col_str in self.variable_definitions:
                info['definition'] = self.variable_definitions[col_str]
            else:
                # تخمين من أسماء الأعمدة الشائعة
                info['definition'] = self._guess_definition_from_name(col_str)
            
            # تحديد النوع الإحصائي
            if pd.api.types.is_numeric_dtype(self.df[col]):
                if info['n_unique'] <= 10:
                    info['stat_type'] = 'CATEGORICAL'
                    info['measurement_level'] = 'NOMINAL'
                else:
                    info['stat_type'] = 'CONTINUOUS'
                    info['measurement_level'] = 'SCALE'
                    if not var_data.empty:
                        info['stats'] = {
                            'mean': float(var_data.mean()),
                            'std': float(var_data.std()),
                            'min': float(var_data.min()),
                            'max': float(var_data.max()),
                            'median': float(var_data.median())
                        }
            else:
                info['stat_type'] = 'STRING'
                info['measurement_level'] = 'NOMINAL'
            
            # تسميات القيم بناءً على التعريف
            info['value_labels'] = self._generate_value_labels(col_str, info)
            
            variable_info[col_str] = info
        
        return variable_info
    
    def _guess_definition_from_name(self, var_name: str) -> str:
        """تخمين تعريف المتغير من اسمه"""
        var_lower = var_name.lower()
        
        guesses = {
            'x1': 'Account Balance in $',
            'x2': 'Number of ATM transactions',
            'x3': 'Number of other bank services used',
            'x4': 'Has a debit card (1=yes, 0=no)',
            'x5': 'Receive interest on the account (1=yes, 0=no)',
            'x6': 'City where banking is done',
            'account': 'Account balance',
            'balance': 'Account balance',
            'transaction': 'ATM transactions',
            'atm': 'ATM transactions',
            'debit': 'Debit card holder',
            'card': 'Debit card holder',
            'interest': 'Interest received',
            'city': 'City location',
            'salary': 'Salary in $',
            'team': 'Team name',
            'league': 'League (0=national, 1=american)',
            'built': 'Year stadium was built',
            'size': 'Stadium capacity',
            'attendance': 'Total attendance',
            'wins': 'Number of wins',
            'country': 'Country name',
            'population': 'Population in thousands',
            'area': 'Total area in thousand square km',
            'gdp': 'Gross Domestic Product',
            'happiness': 'General happiness level',
            'gender': 'Gender (1=male, 2=female)',
            'age': 'Age in years',
            'education': 'Years of education'
        }
        
        for key, value in guesses.items():
            if key in var_lower:
                return value
        
        return f'Variable {var_name}'
    
    def _generate_value_labels(self, var_name: str, info: Dict) -> Dict:
        """توليد تسميات القيم بناءً على التعريف"""
        labels = {}
        definition = info.get('definition', '').lower()
        
        if info['stat_type'] == 'CATEGORICAL' and info['unique_values']:
            for val in info['unique_values']:
                if isinstance(val, (int, float)):
                    # من التعريف
                    if 'debit card' in definition:
                        if val == 0:
                            labels[val] = "No"
                        elif val == 1:
                            labels[val] = "Yes"
                    elif 'interest' in definition:
                        if val == 0:
                            labels[val] = "No"
                        elif val == 1:
                            labels[val] = "Yes"
                    elif 'league' in definition:
                        if val == 0:
                            labels[val] = "National"
                        elif val == 1:
                            labels[val] = "American"
                    elif 'gender' in definition:
                        if val == 1:
                            labels[val] = "Male"
                        elif val == 2:
                            labels[val] = "Female"
                    elif 'city' in definition or 'location' in definition:
                        city_names = {1: "City A", 2: "City B", 3: "City C", 4: "City D"}
                        labels[val] = city_names.get(val, f"City {val}")
                    else:
                        labels[val] = f"Value {val}"
                else:
                    labels[val] = str(val)
        
        return labels
    
    def _parse_questions(self) -> List[Dict]:
        """تحليل الأسئلة مع استخراج دقيق"""
        questions = []
        
        # أنماط الأسئلة المرقمة
        patterns = [
            r'(\d+)\.\s+(.*?)(?=\n\d+\.|\n\n|$)',  # 1. سؤال
            r'(\d+)\)\s+(.*?)(?=\n\d+\)|\n\n|$)',  # 1) سؤال
            r'Q(\d+)[:\-]\s+(.*?)(?=\nQ\d+[:\.\-]|\n\n|$)',  # Q1: سؤال
        ]
        
        # استخدام re.DOTALL لجعل النقطة تطابق الأسطر الجديدة
        for pattern in patterns:
            matches = re.finditer(pattern, self.questions_text, re.IGNORECASE)
            for match in matches:
                try:
                    q_num = int(match.group(1).strip())
                    q_text = match.group(2).strip()
                    
                    # تنظيف النص
                    q_text = re.sub(r'\s+', ' ', q_text)
                    
                    if q_text and len(q_text) > 10:
                        questions.append({
                            'number': q_num,
                            'text': q_text[:150],
                            'full_text': q_text,
                            'type': self._detect_question_type(q_text),
                            'variables': self._extract_variables(q_text)
                        })
                except (ValueError, IndexError):
                    continue
        
        # إذا لم نجد أسئلة مرقمة، نبحث عن فقرات
        if not questions:
            lines = self.questions_text.split('\n')
            q_num = 1
            for line in lines:
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
                            'number': q_num,
                            'text': line[:150],
                            'full_text': line,
                            'type': self._detect_question_type(line),
                            'variables': self._extract_variables(line)
                        })
                        q_num += 1
        
        return sorted(questions, key=lambda x: x['number'])
    
    def _detect_question_type(self, text: str) -> str:
        """تحديد نوع السؤال"""
        text_lower = text.lower()
        
        types = {
            'frequency': ['frequency table', 'جدول تكراري', 'توزيع تكراري'],
            'descriptive': ['mean', 'median', 'mode', 'standard deviation', 'calculate', 'احسب'],
            'histogram': ['histogram', 'مدرج تكراري'],
            'bar_chart': ['bar chart', 'رسم بياني عمودي'],
            'pie_chart': ['pie chart', 'رسم دائري'],
            'confidence': ['confidence interval', 'فترة ثقة'],
            't_test': ['test the hypothesis', 'اختبار الفرضية', 't-test'],
            'anova': ['anova', 'تحليل التباين'],
            'correlation': ['correlation', 'ارتباط'],
            'regression': ['regression', 'انحدار'],
            'outliers': ['outliers', 'القيم المتطرفة'],
            'normality': ['normality', 'empirical rule', 'chebycheve']
        }
        
        for q_type, keywords in types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return q_type
        
        return 'descriptive'
    
    def _extract_variables(self, text: str) -> List[str]:
        """استخراج المتغيرات المذكورة في السؤال"""
        found_vars = []
        text_lower = text.lower()
        
        # البحث عن المتغيرات المذكورة في السؤال
        for var_name in self.variable_info.keys():
            var_lower = var_name.lower()
            
            # البحث بالاسم
            if var_lower in text_lower:
                found_vars.append(var_name)
            
            # البحث بالتعريف
            definition = self.variable_info[var_name].get('definition', '').lower()
            if definition:
                # تحقق من كلمات رئيسية في التعريف
                def_words = definition.split()
                for word in def_words[:3]:
                    if word and len(word) > 2 and word in text_lower:
                        found_vars.append(var_name)
                        break
        
        return list(set(found_vars))
    
    def generate_spss_v26_syntax(self) -> str:
        """توليد كود SPSS v26 متوافق"""
        
        syntax = f"""* =========================================================================
* SPSS v26 SYNTAX - COMPLETE EXAM SOLUTION
* Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
* Dataset: {len(self.df.columns)} variables, {len(self.df)} cases
* Questions: {len(self.questions)}
* =========================================================================

DATASET NAME ExamData WINDOW=FRONT.
DATASET ACTIVATE ExamData.

* -------------------------------------------------------------------------
* VARIABLE DEFINITIONS
* -------------------------------------------------------------------------

"""
        
        # تعريفات المتغيرات
        for var_name, info in self.variable_info.items():
            definition = info.get('definition', f'Variable {var_name}')
            syntax += f"VARIABLE LABELS {var_name} '{definition}'.\n"
            syntax += f"VARIABLE LEVEL {var_name} ({info['measurement_level']}).\n"
            
            if info['value_labels']:
                syntax += f"VALUE LABELS {var_name}\n"
                for val, label in info['value_labels'].items():
                    syntax += f"  {val} '{label}'\n"
                syntax += ".\n"
        
        syntax += "\nEXECUTE.\n"
        
        # إنشاء متغيرات مشتقة
        syntax += self._generate_derived_vars()
        
        # حل الأسئلة
        syntax += self._generate_question_solutions()
        
        # إنهاء
        syntax += """
* -------------------------------------------------------------------------
* SAVE AND CLEANUP
* -------------------------------------------------------------------------

SAVE OUTFILE='SPSS_Analysis_v26.sav'
  /COMPRESSED.
EXECUTE.

DATASET CLOSE ALL.
EXECUTE.

* ==================== END OF SYNTAX ====================
"""
        
        return syntax
    
    def _generate_derived_vars(self) -> str:
        """إنشاء متغيرات مشتقة"""
        syntax = "\n* -------------------------------------------------------------------------\n"
        syntax += "* DERIVED VARIABLES\n"
        syntax += "* -------------------------------------------------------------------------\n\n"
        
        # إنشاء فئات للبيانات المستمرة
        for var_name, info in self.variable_info.items():
            if info['stat_type'] == 'CONTINUOUS' and 'stats' in info:
                mean_val = info['stats']['mean']
                syntax += f"* Create categories for {var_name}\n"
                syntax += f"RECODE {var_name} (LOWEST thru {mean_val:.2f}=1) ({mean_val:.2f} thru HIGHEST=2) INTO {var_name}_Cat.\n"
                syntax += f"VARIABLE LABELS {var_name}_Cat '{var_name} Categories'.\n"
                syntax += f"VALUE LABELS {var_name}_Cat\n"
                syntax += f"  1 'Low (Below Mean)'\n"
                syntax += f"  2 'High (Above Mean)'\n"
                syntax += ".\n\n"
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def _generate_question_solutions(self) -> str:
        """توليد حلول للأسئلة"""
        if not self.questions:
            return "\n* No questions found in the text\n"
        
        syntax = "\n* -------------------------------------------------------------------------\n"
        syntax += "* QUESTION SOLUTIONS\n"
        syntax += "* -------------------------------------------------------------------------\n\n"
        
        for q in self.questions:
            syntax += self._solve_single_question(q)
        
        return syntax
    
    def _solve_single_question(self, question: Dict) -> str:
        """حل سؤال واحد"""
        q_num = question['number']
        q_text = question['text']
        q_type = question['type']
        variables = question['variables']
        
        syntax = f"* QUESTION {q_num}: {q_text}\n"
        
        # إذا لم توجد متغيرات، نستخدم المتغيرات المناسبة
        if not variables:
            if q_type == 'frequency':
                variables = [v for v, info in self.variable_info.items() 
                           if info['stat_type'] == 'CATEGORICAL'][:3]
            elif q_type == 'descriptive':
                variables = [v for v, info in self.variable_info.items() 
                           if info['stat_type'] == 'CONTINUOUS'][:2]
            elif q_type in ['histogram', 'bar_chart', 'pie_chart']:
                variables = list(self.variable_info.keys())[:2]
        
        if variables:
            syntax += f"* Variables: {', '.join(variables)}\n"
        
        # توليد الكود المناسب
        if q_type == 'frequency':
            if variables:
                syntax += f"FREQUENCIES VARIABLES={' '.join(variables)}\n"
                syntax += "  /BARCHART FREQ\n"
                syntax += "  /ORDER=ANALYSIS.\n"
        
        elif q_type == 'descriptive':
            if variables:
                syntax += f"DESCRIPTIVES VARIABLES={' '.join(variables)}\n"
                syntax += "  /STATISTICS=MEAN MEDIAN MODE STDDEV MIN MAX SKEWNESS SESKEW.\n"
        
        elif q_type == 'histogram':
            if variables:
                for var in variables[:2]:
                    if self.variable_info[var]['stat_type'] == 'CONTINUOUS':
                        syntax += f"GRAPH\n"
                        syntax += f"  /HISTOGRAM={var}\n"
                        syntax += f"  /TITLE='Histogram of {var}'.\n"
        
        elif q_type == 'bar_chart':
            if len(variables) >= 2:
                syntax += f"GRAPH\n"
                syntax += f"  /BAR(GROUPED)=MEAN({variables[1]}) BY {variables[0]}\n"
                syntax += f"  /TITLE='Bar Chart: {variables[1]} by {variables[0]}'.\n"
            elif variables:
                syntax += f"GRAPH\n"
                syntax += f"  /BAR(SIMPLE)=COUNT BY {variables[0]}\n"
                syntax += f"  /TITLE='Bar Chart of {variables[0]}'.\n"
        
        elif q_type == 'pie_chart':
            if variables:
                syntax += f"GRAPH\n"
                syntax += f"  /PIE=PCT BY {variables[0]}\n"
                syntax += f"  /TITLE='Pie Chart of {variables[0]}'.\n"
        
        elif q_type == 'confidence':
            if variables:
                for var in variables[:2]:
                    if self.variable_info[var]['stat_type'] == 'CONTINUOUS':
                        syntax += f"EXAMINE VARIABLES={var}\n"
                        syntax += "  /PLOT NONE\n"
                        syntax += "  /STATISTICS DESCRIPTIVES\n"
                        syntax += "  /CINTERVAL 95.\n"
                        syntax += f"EXAMINE VARIABLES={var}\n"
                        syntax += "  /PLOT NONE\n"
                        syntax += "  /STATISTICS DESCRIPTIVES\n"
                        syntax += "  /CINTERVAL 99.\n"
        
        elif q_type == 't_test':
            if len(variables) >= 2:
                syntax += f"T-TEST GROUPS={variables[0]}\n"
                syntax += f"  /VARIABLES={variables[1]}\n"
                syntax += f"  /CRITERIA=CI(.95).\n"
        
        elif q_type == 'outliers':
            if variables:
                for var in variables[:2]:
                    if self.variable_info[var]['stat_type'] == 'CONTINUOUS':
                        syntax += f"EXAMINE VARIABLES={var}\n"
                        syntax += "  /PLOT=BOXPLOT\n"
                        syntax += "  /STATISTICS=EXTREME\n"
                        syntax += "  /NOTOTAL.\n"
        
        else:
            # حل عام
            if variables:
                syntax += f"DESCRIPTIVES VARIABLES={' '.join(variables[:3])}\n"
                syntax += "  /STATISTICS=MEAN STDDEV MIN MAX.\n"
        
        syntax += "EXECUTE.\n\n"
        return syntax

# ===== واجهة Streamlit =====

def main():
    # شريط جانبي
    with st.sidebar:
        st.header("📁 رفع ملفات الامتحان")
        
        st.subheader("1. ملف البيانات")
        data_file = st.file_uploader(
            "رفع ملف Excel أو CSV",
            type=['xls', 'xlsx', 'csv'],
            key="data_file"
        )
        
        st.markdown("---")
        
        st.subheader("2. ملف الأسئلة")
        questions_file = st.file_uploader(
            "رفع ملف نصي أو Word (بدون python-docx)",
            type=['txt'],
            key="questions_file",
            help="يرجى حفظ ملف Word كملف نصي (.txt) أولاً"
        )
        
        st.markdown("---")
        
        if st.button("🚀 توليد الحل الكامل", type="primary", use_container_width=True):
            st.session_state['generate'] = True
        else:
            st.session_state['generate'] = False
    
    # المنطقة الرئيسية
    if not data_file:
        st.info("👈 ابدأ برفع ملف البيانات من الشريط الجانبي")
        
        with st.expander("📖 تعليمات الاستخدام"):
            st.markdown("""
            ### خطوات الاستخدام:
            
            1. **رفع ملف البيانات** (Excel أو CSV):
               - يجب أن يحتوي على البيانات الخام
               - الأسماء في الصف الأول
               - يمكن أن تكون أي بيانات إحصائية
            
            2. **رفع ملف الأسئلة** (ملف نصي .txt):
               - احفظ ملف Word كـ .txt أولاً
               - يجب أن يحتوي على الأسئلة الإحصائية
               - يمكن أن يحتوي على تعريفات المتغيرات
            
            3. **توليد الحل**:
               - سيقوم البرنامج بقراءة التعريفات من الأسئلة
               - سيحلل كل سؤال تلقائياً
               - سيولد كود SPSS v26 كامل
            
            ### كيفية حفظ ملف Word كـ .txt:
            1. افتح ملف Word
            2. انقر على "ملف" → "حفظ باسم"
            3. اختر "نص عادي (*.txt)"
            4. احفظ الملف
            
            ### مثال على ملف الأسئلة (ملف .txt):
            ```
            1. Construct frequency tables for categorical variables
            
            2. Calculate mean and standard deviation for account balance
            
            Where:
            X1 = Account Balance in $
            X2 = Number of ATM transactions
            X3 = Has a debit card (1=yes, 0=no)
            ```
            """)
    
    elif data_file and st.session_state.get('generate', False):
        try:
            # تحميل البيانات
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp:
                tmp.write(data_file.getvalue())
                data_path = tmp.name
            
            # تحديد نوع الملف وقراءته
            if data_file.name.lower().endswith('.csv'):
                df = pd.read_csv(data_path)
            else:  # Excel
                df = pd.read_excel(data_path)
            
            os.unlink(data_path)
            
            # تحميل الأسئلة
            questions_text = ""
            if questions_file:
                # قراءة الملف النصي
                questions_text = questions_file.getvalue().decode('utf-8', errors='ignore')
                st.success(f"✅ تم تحميل ملف الأسئلة ({len(questions_text.split())} كلمة)")
            else:
                st.info("ℹ️ لم يتم رفع ملف أسئلة، سيتم إنشاء أسئلة افتراضية")
            
            # إنشاء المحلل
            with st.spinner("🔍 جاري تحليل الملفات..."):
                solver = SPSSv26Solver(df, questions_text)
                
                st.success(f"✅ تم تحليل {len(df)} صف و {len(df.columns)} متغير")
                
                # عرض المعلومات
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("المتغيرات", len(df.columns))
                with col2:
                    st.metric("الحالات", len(df))
                with col3:
                    st.metric("الأسئلة", len(solver.questions))
                
                # عرض تعريفات المتغيرات
                with st.expander("📋 تعريفات المتغيرات المستخرجة"):
                    if solver.variable_definitions:
                        for var, definition in solver.variable_definitions.items():
                            st.markdown(f"**{var}**: {definition}")
                    else:
                        st.info("لم يتم العثور على تعريفات في ملف الأسئلة")
                        st.markdown("**التعريفات المقترحة:**")
                        for var_name, info in solver.variable_info.items():
                            st.markdown(f"**{var_name}**: {info.get('definition', 'N/A')}")
                
                # عرض البيانات
                with st.expander("🔍 معاينة البيانات"):
                    st.dataframe(df.head(10))
                    
                    # إحصائيات سريعة
                    st.markdown("**ملخص البيانات:**")
                    st.write(df.describe())
                
                # توليد كود SPSS
                st.markdown("---")
                st.subheader("⚙️ توليد كود SPSS v26")
                
                spss_code = solver.generate_spss_v26_syntax()
                
                # عرض الكود
                st.code(spss_code, language='spss')
                
                # تحميل الكود
                st.download_button(
                    label="💾 تحميل ملف SPSS (.sps)",
                    data=spss_code,
                    file_name="SPSS_v26_Solution.sps",
                    mime="text/plain",
                    use_container_width=True
                )
                
                # عرض تحليل الأسئلة
                with st.expander("📝 تحليل الأسئلة"):
                    if solver.questions:
                        for q in solver.questions:
                            st.markdown(f"**{q['number']}. {q['text']}**")
                            st.caption(f"النوع: {q['type']}")
                            if q['variables']:
                                st.caption(f"المتغيرات: {', '.join(q['variables'])}")
                            st.markdown("---")
                    else:
                        st.info("لم يتم العثور على أسئلة في الملف")
                
                # عرض أمثلة من الكود
                with st.expander("🔧 أمثلة من التحليلات المتولدة"):
                    lines = spss_code.split('\n')
                    examples = []
                    
                    keywords = ['FREQUENCIES', 'DESCRIPTIVES', 'GRAPH', 'EXAMINE', 'T-TEST', 
                              'CORRELATIONS', 'MEANS', 'RECODE', 'VARIABLE LABELS']
                    
                    for line in lines:
                        if any(keyword in line for keyword in keywords):
                            if line.strip() and len(line.strip()) > 10:
                                examples.append(line.strip())
                            if len(examples) >= 10:
                                break
                    
                    for example in examples:
                        st.code(example, language='spss')
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    elif not data_file and st.session_state.get('generate', False):
        st.warning("⚠️ يرجى رفع ملف البيانات أولاً")

if __name__ == "__main__":
    main()
