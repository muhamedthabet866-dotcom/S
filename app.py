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
    page_title="Advanced SPSS Code Generator",
    page_icon="📊",
    layout="wide"
)

st.title("📊 مولد أكواد SPSS المتقدم")
st.markdown("### برنامج ذكي يعالج جميع الأسئلة ويولّد كود فريد لكل سؤال")

class AdvancedSPSSGenerator:
    def __init__(self):
        self.processed_questions = OrderedDict()
        self.variable_analysis_cache = {}
        self.question_types = {
            'descriptive': ['mean', 'average', 'median', 'mode', 'standard deviation', 'variance', 'descriptive'],
            'frequency': ['frequency', 'distribution', 'count', 'table', 'percentage', 'percent'],
            't_test': ['t-test', 't test', 'compare means', 'independent samples', 'paired'],
            'anova': ['anova', 'analysis of variance', 'f-test', 'one-way', 'two-way'],
            'correlation': ['correlation', 'relationship', 'association', 'correlate'],
            'regression': ['regression', 'predict', 'linear model', 'multiple regression'],
            'chi_square': ['chi-square', 'chi squared', 'contingency', 'association categorical'],
            'graph': ['graph', 'chart', 'histogram', 'bar chart', 'pie chart', 'scatter', 'plot'],
            'confidence': ['confidence interval', 'ci', '95%', '99%', 'interval'],
            'normality': ['normality', 'normal distribution', 'shapiro-wilk', 'kolmogorov'],
            'outliers': ['outliers', 'extreme values', 'unusual observations'],
            'group_comparison': ['by group', 'for each', 'compare groups', 'between groups'],
            'recode': ['recode', 'categorize', 'group into', 'create classes', 'classify'],
            'transform': ['transform', 'compute', 'create variable', 'new variable', 'calculate']
        }
    
    def analyze_dataset(self, df):
        """تحليل شامل للبيانات"""
        analysis = {
            'variables': {},
            'summary': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_vars': [],
                'categorical_vars': [],
                'text_vars': []
            }
        }
        
        for column in df.columns:
            col_data = df[column]
            var_info = {
                'name': column,
                'type': 'unknown',
                'missing': int(col_data.isna().sum()),
                'missing_percent': round(col_data.isna().sum() / len(df) * 100, 2),
                'unique_values': int(col_data.nunique())
            }
            
            try:
                # محاولة تحويل إلى رقم
                numeric_data = pd.to_numeric(col_data.dropna())
                var_info['type'] = 'numeric'
                var_info['min'] = float(numeric_data.min())
                var_info['max'] = float(numeric_data.max())
                var_info['mean'] = float(numeric_data.mean())
                var_info['std'] = float(numeric_data.std())
                
                if var_info['unique_values'] <= 10:
                    var_info['subtype'] = 'categorical_numeric'
                    var_info['values'] = sorted(numeric_data.unique())
                    analysis['summary']['categorical_vars'].append(column)
                else:
                    var_info['subtype'] = 'continuous'
                    analysis['summary']['numeric_vars'].append(column)
                    
            except:
                # متغير نصي
                var_info['type'] = 'text'
                if var_info['unique_values'] <= 15:
                    var_info['subtype'] = 'categorical_text'
                    var_info['values'] = list(col_data.dropna().unique())[:10]
                    analysis['summary']['categorical_vars'].append(column)
                else:
                    var_info['subtype'] = 'free_text'
                    analysis['summary']['text_vars'].append(column)
            
            analysis['variables'][column] = var_info
        
        return analysis
    
    def extract_variables_from_text(self, text, variable_names):
        """استخراج المتغيرات من النص بدقة"""
        text_lower = text.lower()
        detected_vars = []
        
        for var in variable_names:
            var_lower = var.lower()
            
            # طرق مختلفة للكشف عن المتغيرات
            patterns = [
                f'\\b{var_lower}\\b',  # الكلمة كاملة
                f'{var_lower}\\s+',    # متبوع بمسافة
                f'\\s+{var_lower}\\b',  # مسبوق بمسافة
                var_lower.replace('_', ' '),  # مع underscores
            ]
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected_vars.append(var)
                    break
            
            # أيضا التحقق من أجزاء الاسم
            if '_' in var:
                parts = var_lower.split('_')
                if any(part in text_lower for part in parts if len(part) > 2):
                    detected_vars.append(var)
        
        # إزالة التكرارات مع الحفاظ على الترتيب
        return list(OrderedDict.fromkeys(detected_vars))
    
    def classify_question(self, question):
        """تصنيف السؤال بدقة مع تحديد الأنواع الفرعية"""
        question_lower = question.lower()
        classifications = []
        
        for q_type, keywords in self.question_types.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', question_lower):
                    classifications.append(q_type)
                    break
        
        # كشف الأنواع الخاصة
        if 'graph' in classifications:
            if 'histogram' in question_lower:
                classifications.append('histogram')
            if 'bar' in question_lower and 'chart' in question_lower:
                classifications.append('bar_chart')
            if 'pie' in question_lower:
                classifications.append('pie_chart')
            if 'scatter' in question_lower:
                classifications.append('scatter_plot')
        
        return list(OrderedDict.fromkeys(classifications)) if classifications else ['general_analysis']
    
    def generate_question_fingerprint(self, question, detected_vars, classifications):
        """إنشاء بصمة فريدة للسؤال لمنع التكرار"""
        components = [
            ' '.join(sorted(classifications)),
            ' '.join(sorted(detected_vars)),
            re.sub(r'\s+', ' ', question.lower()).strip()
        ]
        
        fingerprint_string = '|'.join(components)
        return hashlib.md5(fingerprint_string.encode()).hexdigest()[:8]
    
    def generate_spss_for_question(self, q_num, question, df, data_analysis):
        """توليد كود SPSS خاص ومختلف لكل سؤال"""
        
        # استخراج المتغيرات
        variable_names = list(df.columns)
        detected_vars = self.extract_variables_from_text(question, variable_names)
        
        # تصنيف السؤال
        classifications = self.classify_question(question)
        
        # إنشاء بصمة السؤال
        fingerprint = self.generate_question_fingerprint(question, detected_vars, classifications)
        
        # التحقق من عدم تكرار السؤال
        if fingerprint in self.processed_questions:
            similar_q = self.processed_questions[fingerprint]
            return None, f"السؤال مشابه للسؤال {similar_q['number']}. تم تجنبه لمنع التكرار."
        
        # حفظ البصمة
        self.processed_questions[fingerprint] = {
            'number': q_num,
            'question': question[:100],
            'variables': detected_vars,
            'types': classifications
        }
        
        # توليد الكود
        code_lines = []
        code_lines.append(f"* {'='*70}")
        code_lines.append(f"* QUESTION {q_num}: {question[:80]}{'...' if len(question) > 80 else ''}")
        code_lines.append(f"* Types: {', '.join(classifications)}")
        if detected_vars:
            code_lines.append(f"* Variables detected: {', '.join(detected_vars)}")
        code_lines.append(f"* {'='*70}\n")
        
        # إضافة تعليق تحليلي
        code_lines.append(f"* ANALYSIS FOR QUESTION {q_num}")
        
        # توليد كود بناءً على التصنيفات
        if not detected_vars:
            # إذا لم يتم اكتشاف متغيرات
            code_lines.append("* No specific variables detected in question.")
            code_lines.append("* Running general descriptive analysis on all variables.")
            code_lines.append("DESCRIPTIVES VARIABLES=ALL")
            code_lines.append("  /STATISTICS=MEAN STDDEV MIN MAX.\n")
        
        else:
            # معالجة كل نوع من التحليلات
            processed_commands = []
            
            for q_type in classifications:
                if q_type == 'descriptive':
                    if detected_vars:
                        vars_str = ' '.join(detected_vars[:5])
                        cmd = f"DESCRIPTIVES VARIABLES={vars_str}"
                        cmd += "\n  /STATISTICS=MEAN STDDEV MIN MAX SEMEAN KURTOSIS SKEWNESS."
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
                    
                elif q_type == 'frequency':
                    categorical_vars = [v for v in detected_vars 
                                      if data_analysis['variables'].get(v, {}).get('subtype') in 
                                      ['categorical_numeric', 'categorical_text']]
                    if categorical_vars:
                        vars_str = ' '.join(categorical_vars[:5])
                        cmd = f"FREQUENCIES VARIABLES={vars_str}"
                        cmd += "\n  /ORDER=ANALYSIS"
                        cmd += "\n  /BARCHART"
                        cmd += "\n  /PIECHART."
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
                    
                elif q_type == 'histogram':
                    numeric_vars = [v for v in detected_vars 
                                  if data_analysis['variables'].get(v, {}).get('subtype') == 'continuous']
                    for var in numeric_vars[:3]:
                        cmd = f"GRAPH /HISTOGRAM(NORMAL)={var}"
                        cmd += f"\n  /TITLE='Histogram of {var}'."
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
                
                elif q_type == 'bar_chart':
                    if len(detected_vars) >= 2:
                        # افتراض أن الأول هو المتغير الكمي والثاني هو الفئوي
                        cmd = f"GRAPH /BAR(SIMPLE)=MEAN({detected_vars[0]}) BY {detected_vars[1]}"
                        cmd += f"\n  /TITLE='Average {detected_vars[0]} by {detected_vars[1]}'."
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
                
                elif q_type == 't_test':
                    if len(detected_vars) >= 2:
                        # افتراض أن الأول هو متغير المجموعة
                        group_var = detected_vars[0]
                        test_vars = ' '.join(detected_vars[1:3])
                        cmd = f"T-TEST GROUPS={group_var}"
                        cmd += f"\n  /VARIABLES={test_vars}"
                        cmd += "\n  /CRITERIA=CI(.95)."
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
                
                elif q_type == 'correlation':
                    if len(detected_vars) >= 2:
                        vars_str = ' '.join(detected_vars[:4])
                        cmd = f"CORRELATIONS /VARIABLES={vars_str}"
                        cmd += "\n  /PRINT=TWOTAIL NOSIG."
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
                
                elif q_type == 'regression':
                    if len(detected_vars) >= 2:
                        dv = detected_vars[0]
                        iv_list = ' '.join(detected_vars[1:4])
                        cmd = f"REGRESSION"
                        cmd += f"\n  /DEPENDENT {dv}"
                        cmd += f"\n  /METHOD=ENTER {iv_list}."
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
                
                elif q_type == 'confidence':
                    for var in detected_vars[:2]:
                        if '95%' in question.lower():
                            cmd = f"EXAMINE VARIABLES={var}"
                            cmd += "\n  /CINTERVAL 95"
                            cmd += "\n  /PLOT NONE."
                        elif '99%' in question.lower():
                            cmd = f"EXAMINE VARIABLES={var}"
                            cmd += "\n  /CINTERVAL 99"
                            cmd += "\n  /PLOT NONE."
                        else:
                            cmd = f"EXAMINE VARIABLES={var}"
                            cmd += "\n  /CINTERVAL 95"
                            cmd += "\n  /PLOT NONE."
                        
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
                
                elif q_type == 'normality':
                    for var in detected_vars[:2]:
                        cmd = f"EXAMINE VARIABLES={var}"
                        cmd += "\n  /PLOT NPPLOT"
                        cmd += "\n  /STATISTICS DESCRIPTIVES."
                        if cmd not in processed_commands:
                            code_lines.append(cmd)
                            processed_commands.append(cmd)
            
            # إذا لم يتم إنشاء أي أوامر
            if not processed_commands:
                vars_str = ' '.join(detected_vars[:3])
                code_lines.append(f"DESCRIPTIVES VARIABLES={vars_str}")
                code_lines.append("  /STATISTICS=MEAN STDDEV MIN MAX.")
        
        code_lines.append("EXECUTE.")
        code_lines.append("")  # سطر فارغ لفصل الأسئلة
        
        return '\n'.join(code_lines), None
    
    def generate_spss_header(self, df, data_analysis, filename):
        """توليد رأس كود SPSS"""
        header = f"""* =========================================================================
* SPSS SYNTAX FILE
* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Data File: {filename}
* Rows: {data_analysis['summary']['total_rows']}
* Variables: {data_analysis['summary']['total_columns']}
* =========================================================================

* DATA DEFINITION AND SETUP
"""
        
        # تعريف المتغيرات
        var_labels = []
        for var_name, var_info in data_analysis['variables'].items():
            label = var_name.replace('_', ' ').title()
            var_labels.append(f"{var_name} '{label}'")
        
        header += "VARIABLE LABELS\n    " + " /".join(var_labels) + ".\n\n"
        
        # تسميات القيم للمتغيرات الفئوية
        value_labels = []
        for var_name, var_info in data_analysis['variables'].items():
            if var_info['subtype'] in ['categorical_numeric', 'categorical_text']:
                if var_info.get('values') and len(var_info['values']) <= 10:
                    line = f"    /{var_name} "
                    if var_info['subtype'] == 'categorical_numeric':
                        for val in var_info['values']:
                            line += f"{val} 'Value {val}' "
                    else:
                        for i, val in enumerate(var_info['values'][:5], 1):
                            line += f"{i} '{val}' "
                    value_labels.append(line.strip())
        
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
    st.sidebar.title("⚙️ إعدادات التحليل")
    
    # خيارات التحليل
    st.sidebar.subheader("خيارات المعالجة")
    auto_detect_types = st.sidebar.checkbox("الكشف التلقائي عن أنواع المتغيرات", value=True)
    prevent_duplicates = st.sidebar.checkbox("منع تكرار التحليلات", value=True)
    include_comments = st.sidebar.checkbox("إضافة تعليقات توضيحية", value=True)
    
    st.sidebar.subheader("تخصيص الإخراج")
    output_format = st.sidebar.selectbox(
        "نوع الملف الناتج",
        ["SPSS Syntax (.sps)", "Text File (.txt)", "Word Document (.docx)"]
    )
    
    # إنشاء المولد
    generator = AdvancedSPSSGenerator()
    
    # القسم الرئيسي
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📁 تحميل الملفات")
    with col2:
        st.markdown("### ⚡ معالجة سريعة")
    
    # تحميل الملفات
    col1, col2 = st.columns(2)
    
    with col1:
        data_file = st.file_uploader(
            "ملف البيانات (Excel/CSV)",
            type=['xlsx', 'xls', 'csv'],
            help="يمكن أن يكون ملف Excel أو CSV يحتوي على البيانات"
        )
    
    with col2:
        questions_file = st.file_uploader(
            "ملف الأسئلة (TXT)",
            type=['txt'],
            help="ملف نصي يحتوي على الأسئلة، سؤال في كل سطر"
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
            data_analysis = generator.analyze_dataset(df)
            
            # عرض معلومات البيانات
            st.success(f"✅ تم تحميل البيانات بنجاح")
            
            # عرض لوحة التحكم
            with st.expander("📊 لوحة تحكم البيانات", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("عدد الصفوف", data_analysis['summary']['total_rows'])
                with col2:
                    st.metric("عدد المتغيرات", data_analysis['summary']['total_columns'])
                with col3:
                    st.metric("المتغيرات الكمية", len(data_analysis['summary']['numeric_vars']))
                
                st.write("**المتغيرات:**")
                for var_name, var_info in list(data_analysis['variables'].items())[:10]:
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**{var_name}**")
                    with col2:
                        st.write(f"{var_info['type']} ({var_info['subtype']})")
                    with col3:
                        st.write(f"قيم: {var_info['unique_values']}")
                
                if len(data_analysis['variables']) > 10:
                    st.write(f"... و {len(data_analysis['variables']) - 10} متغيرات أخرى")
            
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
            
            # معاينة الأسئلة
            with st.expander("👁️ معاينة الأسئلة وتحليلها"):
                for i, q in enumerate(questions[:10], 1):
                    classifications = generator.classify_question(q)
                    detected_vars = generator.extract_variables_from_text(q, list(df.columns))
                    
                    st.write(f"**السؤال {i}:**")
                    st.write(f"{q[:150]}{'...' if len(q) > 150 else ''}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if classifications:
                            st.caption(f"**التصنيفات:** {', '.join(classifications)}")
                    with col2:
                        if detected_vars:
                            st.caption(f"**المتغيرات:** {', '.join(detected_vars)}")
                    
                    st.write("---")
                
                if len(questions) > 10:
                    st.write(f"... و {len(questions) - 10} أسئلة أخرى")
            
            # زر المعالجة
            st.markdown("---")
            if st.button("🚀 معالجة جميع الأسئلة وتوليد الكود", type="primary", use_container_width=True):
                
                with st.spinner(f"جارٍ معالجة {len(questions)} سؤال..."):
                    
                    # توليد الرأس
                    spss_code = generator.generate_spss_header(df, data_analysis, data_file.name)
                    
                    # معالجة كل سؤال
                    skipped_questions = []
                    question_stats = {
                        'total': len(questions),
                        'processed': 0,
                        'skipped': 0
                    }
                    
                    progress_bar = st.progress(0)
                    
                    for i, question in enumerate(questions, 1):
                        # تحديث شريط التقدم
                        progress_bar.progress(i / len(questions))
                        
                        # توليد كود للسؤال
                        question_code, skip_reason = generator.generate_spss_for_question(
                            i, question, df, data_analysis
                        )
                        
                        if question_code:
                            spss_code += question_code
                            question_stats['processed'] += 1
                        else:
                            skipped_questions.append({
                                'number': i,
                                'question': question[:100],
                                'reason': skip_reason
                            })
                            question_stats['skipped'] += 1
                    
                    # إضافة تذييل
                    spss_code += f"""* =========================================================================
* END OF ANALYSIS
* Total Questions Processed: {question_stats['processed']}
* Duplicate Questions Skipped: {question_stats['skipped']}
* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* =========================================================================
"""
                    
                    # عرض النتائج
                    st.success(f"✅ تم معالجة {question_stats['processed']} سؤال بنجاح")
                    
                    if skipped_questions:
                        st.warning(f"⚠️ تم تخطي {question_stats['skipped']} سؤال لتجنب التكرار")
                        with st.expander("عرض الأسئلة المتخطاة"):
                            for skipped in skipped_questions:
                                st.write(f"**السؤال {skipped['number']}:** {skipped['question']}")
                                st.caption(f"السبب: {skipped['reason']}")
                    
                    # عرض الكود الناتج
                    st.subheader("📋 كود SPSS النهائي")
                    
                    # خيارات العرض
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        show_full = st.checkbox("عرض الكود كاملاً", value=False)
                    
                    # عرض الكود
                    if show_full:
                        st.code(spss_code, language='text', height=600)
                    else:
                        code_lines = spss_code.split('\n')
                        st.code('\n'.join(code_lines[:200]), language='text')
                        if len(code_lines) > 200:
                            st.info(f"يتم عرض 200 سطر من أصل {len(code_lines)}. قم بتفعيل 'عرض الكود كاملاً' لرؤية الكود كاملاً.")
                    
                    # قسم التنزيل
                    st.markdown("---")
                    st.subheader("📥 تحميل الملفات")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(generator.create_download_link(
                            spss_code, "SPSS_Analysis.sps", "📊"
                        ), unsafe_allow_html=True)
                    
                    with col2:
                        # إنشاء ملف تقرير
                        report = f"""تقرير تحليل SPSS
تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
الملف: {data_file.name}
عدد الأسئلة: {len(questions)}
عدد الأسئلة المعالجة: {question_stats['processed']}
عدد الأسئلة المتخطاة: {question_stats['skipped']}

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
                        # إنشاء ملف تعليمات
                        instructions = f"""تعليمات استخدام كود SPSS:
1. افتح برنامج SPSS
2. قم بتحميل ملف البيانات: {data_file.name}
3. افتح محرر الصيغ (Syntax Editor)
4. الصق الكود المرفق
5. حدد الكود كاملاً (Ctrl+A)
6. اضغط F5 أو انقر على زر التشغيل
7. افحص نافذة الإخراج (Output) للنتائج

ملاحظات:
- الكود يعالج {question_stats['processed']} سؤال
- تم تجنب تكرار {question_stats['skipped']} سؤال
- كل سؤال له تحليل فريد ومختلف
"""
                        
                        st.markdown(generator.create_download_link(
                            instructions, "Instructions.txt", "📝"
                        ), unsafe_allow_html=True)
                    
                    # عرض إحصائيات التحليل
                    with st.expander("📈 إحصائيات التحليل"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("الأسئلة المعالجة", question_stats['processed'])
                        with col2:
                            st.metric("المتغيرات المستخدمة", len(df.columns))
                        with col3:
                            st.metric("أنواع التحليلات", len(set([
                                t for q in generator.processed_questions.values() 
                                for t in q['types']
                            ])))
                        
                        # عرض توزيع أنواع الأسئلة
                        type_counts = {}
                        for q_info in generator.processed_questions.values():
                            for q_type in q_info['types']:
                                type_counts[q_type] = type_counts.get(q_type, 0) + 1
                        
                        st.write("**توزيع أنواع التحليلات:**")
                        for t_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                            st.write(f"- {t_type}: {count} سؤال")
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")
            st.exception(e)
    
    else:
        # واجهة الترحيب
        st.info("""
        ## 🎯 مرحباً بك في مولد أكواد SPSS المتقدم
        
        **المميزات الجديدة:**
        ✅ **معالجة جميع الأسئلة** - كل سؤال يحصل على تحليل فريد
        ✅ **منع التكرار** - نظام بصمات يمنع تكرار نفس التحليل
        ✅ **تحليل ذكي** - اكتشاف تلقائي للمتغيرات والأنواع
        ✅ **إحصائيات مفصلة** - تقارير عن الأسئلة المعالجة والمتخطاة
        
        **كيفية الاستخدام:**
        1. **حمّل ملف البيانات** (Excel أو CSV)
        2. **حمّل ملف الأسئلة** (ملف نصي)
        3. **اضغط على زر المعالجة**
        4. **حمل الملفات الناتجة**
        
        **البرنامج يتعامل مع:**
        - أي عدد من الأسئلة
        - أي تنسيق للبيانات
        - جميع أنواع التحليلات الإحصائية
        - اكتشاف تلقائي للمتغيرات المذكورة في الأسئلة
        """)
        
        # أمثلة توضيحية
        with st.expander("📚 أمثلة على تنسيق الأسئلة"):
            st.markdown("""
            ### مثال لمجموعة أسئلة متنوعة:
            ```
            1. احسب المتوسط والانحراف المعياري للعمر والدخل
            2. أنشئ جدولاً تكرارياً للنوع والمستوى التعليمي
            3. ارسم مخططاً شريطياً يوضح متوسط الدخل حسب النوع
            4. اختبر إذا كان هناك فرق في العمر بين الذكور والإناث
            5. افحص العلاقة بين سنوات الخبرة والدخل
            6. ارسم مخططاً مبعثراً للعمر مقابل الدخل
            7. أنشئ فترات ثقة 95% للدخل
            8. افحص توزيع العمر للتحقق من الطبيعي
            9. احسب الارتباط بين جميع المتغيرات الكمية
            10. حلل تأثير النوع والتعليم على الدخل
            ```
            
            **الملاحظة:** كل سؤال سوف يحصل على تحليل فريد ومختلف!
            """)
        
        # زر تجريبي
        if st.button("🔄 تشغيل مثال تجريبي", type="secondary"):
            # إنشاء بيانات تجريبية
            np.random.seed(42)
            sample_data = pd.DataFrame({
                'العمر': np.random.randint(20, 60, 50),
                'الدخل': np.random.normal(5000, 1500, 50),
                'النوع': np.random.choice(['ذكر', 'أنثى'], 50),
                'المستوى_التعليمي': np.random.choice(['ثانوي', 'بكالوريوس', 'ماجستير', 'دكتوراه'], 50),
                'سنوات_الخبرة': np.random.randint(1, 30, 50),
                'القسم': np.random.choice(['مبيعات', 'تكنولوجيا', 'موارد بشرية', 'مالية'], 50)
            })
            
            sample_questions = """1. احسب الإحصاءات الوصفية للعمر والدخل
2. أنشئ جداول تكرارية للنوع والمستوى التعليمي
3. ارسم مخططاً شريطياً لمتوسط الدخل حسب النوع
4. اختبر فرق العمر بين الذكور والإناث
5. افحص الارتباط بين العمر والدخل
6. ارسم مخططاً مبعثراً للعمر مقابل الدخل
7. احسب فترات ثقة 95% للدخل
8. افحص توزيع العمر
9. حلل تأثير النوع على الدخل
10. ارسم مخططاً صندوقياً للدخل حسب القسم"""
            
            st.success("تم تحميل المثال التجريبي بنجاح!")
            st.write("**البيانات التجريبية:**")
            st.dataframe(sample_data)
            st.write("**الأسئلة التجريبية:**")
            st.text(sample_questions)

if __name__ == "__main__":
    main()
