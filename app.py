import streamlit as st
import pandas as pd
import numpy as np
import re
import base64
from datetime import datetime
import io

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="Universal SPSS Code Generator",
    page_icon="📊",
    layout="wide"
)

st.title("📊 مولد أكواد SPSS الشامل")
st.markdown("### برنامج ذكي لتوليد أكواد SPSS لأي امتحان إحصائي")

class UniversalSPSSGenerator:
    def __init__(self):
        self.analysis_templates = self._load_analysis_templates()
        self.variable_mapping = {}
    
    def _load_analysis_templates(self):
        """تحميل قوالب التحليل المختلفة"""
        return {
            'descriptive': {
                'title': 'الإحصاءات الوصفية',
                'syntax': 'DESCRIPTIVES VARIABLES={vars}\n  /STATISTICS=MEAN STDDEV MIN MAX.',
                'keywords': ['mean', 'average', 'median', 'mode', 'standard deviation', 'variance']
            },
            'frequency': {
                'title': 'الجداول التكرارية',
                'syntax': 'FREQUENCIES VARIABLES={vars}\n  /ORDER=ANALYSIS\n  /BARCHART.',
                'keywords': ['frequency', 'frequency table', 'distribution', 'count']
            },
            't_test': {
                'title': 'اختبار T',
                'syntax': 'T-TEST GROUPS={group_var}\n  /VARIABLES={test_vars}\n  /CRITERIA=CI(.95).',
                'keywords': ['t-test', 'compare means', 'independent samples', 'paired']
            },
            'anova': {
                'title': 'تحليل التباين (ANOVA)',
                'syntax': 'ONEWAY {dv} BY {iv}\n  /STATISTICS DESCRIPTIVES\n  /MISSING ANALYSIS.',
                'keywords': ['anova', 'analysis of variance', 'f-test', 'one-way']
            },
            'correlation': {
                'title': 'الارتباط',
                'syntax': 'CORRELATIONS\n  /VARIABLES={vars}\n  /PRINT=TWOTAIL NOSIG.',
                'keywords': ['correlation', 'relationship', 'association', 'correlate']
            },
            'regression': {
                'title': 'الانحدار',
                'syntax': 'REGRESSION\n  /DEPENDENT {dv}\n  /METHOD=ENTER {iv_list}.',
                'keywords': ['regression', 'predict', 'linear model', 'multiple regression']
            },
            'chi_square': {
                'title': 'اختبار مربع كاي',
                'syntax': 'CROSSTABS\n  /TABLES={var1} BY {var2}\n  /STATISTICS=CHISQ.',
                'keywords': ['chi-square', 'chi squared', 'contingency', 'association']
            },
            'graph': {
                'title': 'الرسوم البيانية',
                'syntax': 'GRAPH /{type}={vars}\n  /TITLE="{title}".',
                'keywords': ['graph', 'chart', 'histogram', 'bar chart', 'pie chart', 'scatter']
            },
            'confidence': {
                'title': 'فترات الثقة',
                'syntax': 'EXAMINE VARIABLES={var}\n  /CINTERVAL {level}\n  /PLOT NONE.',
                'keywords': ['confidence interval', 'ci', '95%', '99%', 'interval estimate']
            },
            'normality': {
                'title': 'اختبارات الطبيعية',
                'syntax': 'EXAMINE VARIABLES={var}\n  /PLOT NPPLOT\n  /STATISTICS NONE.',
                'keywords': ['normality', 'normal distribution', 'shapiro-wilk', 'kolmogorov']
            }
        }
    
    def analyze_data_structure(self, df):
        """تحليل هيكل البيانات وتحديد أنواع المتغيرات"""
        variable_info = {}
        
        for column in df.columns:
            col_data = df[column]
            
            # تحديد نوع المتغير
            try:
                numeric_check = pd.to_numeric(col_data.dropna())
                unique_count = col_data.nunique()
                
                if unique_count <= 10:
                    # إذا كان عدد القيم الفريدة قليل، قد يكون فئوي
                    variable_info[column] = {
                        'type': 'categorical',
                        'unique_values': unique_count,
                        'missing': col_data.isna().sum(),
                        'sample_values': list(col_data.dropna().unique())[:5]
                    }
                else:
                    # متغير كمي
                    variable_info[column] = {
                        'type': 'numeric',
                        'min': float(numeric_check.min()),
                        'max': float(numeric_check.max()),
                        'mean': float(numeric_check.mean()),
                        'missing': col_data.isna().sum()
                    }
            except:
                # متغير نصي
                variable_info[column] = {
                    'type': 'text',
                    'unique_values': col_data.nunique(),
                    'missing': col_data.isna().sum(),
                    'sample_values': list(col_data.dropna().unique())[:3]
                }
        
        return variable_info
    
    def detect_variables_from_question(self, question, variable_info):
        """اكتشاف المتغيرات المذكورة في السؤال"""
        detected_vars = []
        question_lower = question.lower()
        
        for var in variable_info.keys():
            var_lower = var.lower()
            
            # البحث عن اسم المتغير في السؤال
            if var_lower in question_lower:
                detected_vars.append(var)
            # البحث عن اختصارات شائعة
            elif any(term in question_lower for term in [f' {var} ', f'{var},', f'{var}.']):
                detected_vars.append(var)
        
        return detected_vars
    
    def classify_question(self, question):
        """تصنيف السؤال بناءً على محتواه"""
        question_lower = question.lower()
        
        # الكلمات المفتاحية لكل نوع من التحليلات
        classifications = []
        
        if any(keyword in question_lower for keyword in ['mean', 'average', 'median', 'mode', 'standard deviation', 'descriptive']):
            classifications.append('descriptive')
        
        if any(keyword in question_lower for keyword in ['frequency', 'distribution', 'count', 'table']):
            classifications.append('frequency')
        
        if any(keyword in question_lower for keyword in ['t-test', 't test', 'compare means', 'independent', 'paired']):
            classifications.append('t_test')
        
        if any(keyword in question_lower for keyword in ['anova', 'analysis of variance', 'f-test']):
            classifications.append('anova')
        
        if any(keyword in question_lower for keyword in ['correlation', 'relationship', 'association']):
            classifications.append('correlation')
        
        if any(keyword in question_lower for keyword in ['regression', 'predict', 'linear model']):
            classifications.append('regression')
        
        if any(keyword in question_lower for keyword in ['chi-square', 'chi square', 'contingency']):
            classifications.append('chi_square')
        
        if any(keyword in question_lower for keyword in ['graph', 'chart', 'histogram', 'bar', 'pie', 'scatter']):
            classifications.append('graph')
        
        if any(keyword in question_lower for keyword in ['confidence interval', 'ci', '95%', '99%']):
            classifications.append('confidence')
        
        if any(keyword in question_lower for keyword in ['normality', 'normal distribution', 'shapiro', 'kolmogorov']):
            classifications.append('normality')
        
        return classifications if classifications else ['general']
    
    def generate_spss_syntax(self, question, var_info, detected_vars, q_num):
        """توليد كود SPSS بناءً على السؤال والمتغيرات"""
        classifications = self.classify_question(question)
        syntax_lines = []
        comment_lines = []
        
        # عنوان السؤال
        title = f"* {'='*70}.\n* QUESTION {q_num}: {question[:60]}...\n* {'='*70}."
        syntax_lines.append(title)
        
        for classification in classifications:
            if classification == 'descriptive':
                if detected_vars:
                    vars_str = ' '.join(detected_vars[:3])
                    syntax = f"DESCRIPTIVES VARIABLES={vars_str}\n  /STATISTICS=MEAN STDDEV MIN MAX SEMEAN KURTOSIS SKEWNESS."
                    syntax_lines.append(syntax)
                    comment = f"* Descriptive statistics for: {vars_str}"
                    comment_lines.append(comment)
            
            elif classification == 'frequency':
                # البحث عن متغيرات فئوية
                categorical_vars = [v for v in detected_vars if var_info.get(v, {}).get('type') == 'categorical']
                if categorical_vars:
                    vars_str = ' '.join(categorical_vars[:3])
                    syntax = f"FREQUENCIES VARIABLES={vars_str}\n  /ORDER=ANALYSIS\n  /BARCHART\n  /PIECHART."
                    syntax_lines.append(syntax)
                    comment = f"* Frequency distribution for categorical variables: {vars_str}"
                    comment_lines.append(comment)
            
            elif classification == 't_test':
                if len(detected_vars) >= 2:
                    group_var = detected_vars[0]
                    test_vars = ' '.join(detected_vars[1:3])
                    syntax = f"T-TEST GROUPS={group_var}\n  /VARIABLES={test_vars}\n  /CRITERIA=CI(.95)\n  /MISSING=ANALYSIS."
                    syntax_lines.append(syntax)
                    comment = f"* T-test comparing {test_vars} by {group_var}"
                    comment_lines.append(comment)
            
            elif classification == 'anova':
                if len(detected_vars) >= 2:
                    dv = detected_vars[0]
                    iv = detected_vars[1]
                    syntax = f"ONEWAY {dv} BY {iv}\n  /STATISTICS DESCRIPTIVES HOMOGENEITY\n  /MISSING ANALYSIS\n  /POSTHOC=TUKEY ALPHA(0.05)."
                    syntax_lines.append(syntax)
                    comment = f"* One-way ANOVA: {dv} by {iv}"
                    comment_lines.append(comment)
            
            elif classification == 'correlation':
                if len(detected_vars) >= 2:
                    vars_str = ' '.join(detected_vars[:4])
                    syntax = f"CORRELATIONS\n  /VARIABLES={vars_str}\n  /PRINT=TWOTAIL NOSIG\n  /MISSING=PAIRWISE."
                    syntax_lines.append(syntax)
                    comment = f"* Correlation analysis between: {vars_str}"
                    comment_lines.append(comment)
            
            elif classification == 'regression':
                if len(detected_vars) >= 2:
                    dv = detected_vars[0]
                    iv_list = ' '.join(detected_vars[1:4])
                    syntax = f"REGRESSION\n  /MISSING LISTWISE\n  /STATISTICS COEFF OUTS R ANOVA\n  /CRITERIA=PIN(.05) POUT(.10)\n  /NOORIGIN\n  /DEPENDENT {dv}\n  /METHOD=ENTER {iv_list}."
                    syntax_lines.append(syntax)
                    comment = f"* Regression analysis: {dv} predicted by {iv_list}"
                    comment_lines.append(comment)
            
            elif classification == 'chi_square':
                if len(detected_vars) >= 2:
                    var1, var2 = detected_vars[:2]
                    syntax = f"CROSSTABS\n  /TABLES={var1} BY {var2}\n  /FORMAT=AVALUE TABLES\n  /STATISTICS=CHISQ PHI\n  /CELLS=COUNT EXPECTED."
                    syntax_lines.append(syntax)
                    comment = f"* Chi-square test of independence: {var1} × {var2}"
                    comment_lines.append(comment)
            
            elif classification == 'graph':
                if detected_vars:
                    # تحديد نوع الرسم البياني
                    if 'histogram' in question.lower():
                        for var in detected_vars[:2]:
                            if var_info.get(var, {}).get('type') == 'numeric':
                                syntax = f"GRAPH /HISTOGRAM(NORMAL)={var}\n  /TITLE='Histogram of {var}'."
                                syntax_lines.append(syntax)
                    elif 'bar' in question.lower():
                        if len(detected_vars) >= 2:
                            syntax = f"GRAPH /BAR(SIMPLE)=MEAN({detected_vars[0]}) BY {detected_vars[1]}\n  /TITLE='Bar Chart: {detected_vars[0]} by {detected_vars[1]}'."
                            syntax_lines.append(syntax)
                    elif 'scatter' in question.lower():
                        if len(detected_vars) >= 2:
                            syntax = f"GRAPH /SCATTERPLOT(BIVAR)={detected_vars[0]} WITH {detected_vars[1]}\n  /TITLE='Scatter Plot: {detected_vars[0]} vs {detected_vars[1]}'."
                            syntax_lines.append(syntax)
            
            elif classification == 'confidence':
                if detected_vars:
                    var = detected_vars[0]
                    if '95%' in question.lower():
                        syntax = f"EXAMINE VARIABLES={var}\n  /CINTERVAL 95\n  /PLOT NONE."
                    elif '99%' in question.lower():
                        syntax = f"EXAMINE VARIABLES={var}\n  /CINTERVAL 99\n  /PLOT NONE."
                    else:
                        syntax = f"EXAMINE VARIABLES={var}\n  /CINTERVAL 95\n  /PLOT NONE."
                    syntax_lines.append(syntax)
            
            elif classification == 'normality':
                if detected_vars:
                    var = detected_vars[0]
                    syntax = f"EXAMINE VARIABLES={var}\n  /PLOT NPPLOT\n  /STATISTICS DESCRIPTIVES."
                    syntax_lines.append(syntax)
            
            elif classification == 'general':
                if detected_vars:
                    vars_str = ' '.join(detected_vars[:3])
                    syntax = f"DESCRIPTIVES VARIABLES={vars_str}\n  /STATISTICS=MEAN STDDEV MIN MAX.\nFREQUENCIES VARIABLES={vars_str}\n  /ORDER=ANALYSIS."
                    syntax_lines.append(syntax)
                    comment = f"* General analysis for variables: {vars_str}"
                    comment_lines.append(comment)
        
        # إذا لم يتم اكتشاف أي متغيرات
        if not syntax_lines[1:]:  # إذا كان العنوان فقط
            syntax_lines.append("* Please specify which variables to analyze.")
            syntax_lines.append("DESCRIPTIVES VARIABLES=ALL\n  /STATISTICS=MEAN STDDEV.")
        
        # دمج التعليقات مع الصيغة
        if comment_lines:
            syntax_lines.insert(1, '\n'.join(comment_lines))
        
        return '\n'.join(syntax_lines) + '\n\n'
    
    def create_variable_labels(self, df):
        """إنشاء تسميات للمتغيرات"""
        labels = []
        for col in df.columns:
            # تحويل اسم المتغير إلى تسمية مقروءة
            label = col.replace('_', ' ').title()
            labels.append(f"{col} '{label}'")
        
        return "VARIABLE LABELS\n    " + " /".join(labels) + ".\n\n"
    
    def create_value_labels(self, df, var_info):
        """إنشاء تسميات القيم للمتغيرات الفئوية"""
        value_labels = []
        
        for var, info in var_info.items():
            if info['type'] == 'categorical' and info['unique_values'] <= 10:
                # محاولة إعطاء تسميات ذكية
                values = info['sample_values']
                labels_line = f"    /{var} "
                for i, val in enumerate(values[:5]):
                    if isinstance(val, (int, float)):
                        labels_line += f"{val} 'Value {val}' "
                    else:
                        labels_line += f"{i+1} '{val}' "
                value_labels.append(labels_line.strip())
        
        if value_labels:
            return "VALUE LABELS\n" + "\n".join(value_labels) + ".\n\n"
        return ""
    
    def parse_questions(self, text_content):
        """تحليل الأسئلة من ملف النص"""
        questions = []
        lines = text_content.split('\n')
        current_question = ""
        
        for line in lines:
            line = line.strip()
            
            # التعرف على بداية سؤال جديد
            if (re.match(r'^\d+[\.\)]', line) or 
                re.match(r'^Q\d+:', line, re.IGNORECASE) or
                re.match(r'^Question \d+:', line, re.IGNORECASE)):
                
                if current_question:
                    questions.append(current_question.strip())
                current_question = re.sub(r'^\d+[\.\)]\s*', '', line)
                current_question = re.sub(r'^Q\d+:\s*', '', current_question, flags=re.IGNORECASE)
                current_question = re.sub(r'^Question \d+:\s*', '', current_question, flags=re.IGNORECASE)
            
            elif current_question and line:
                current_question += " " + line
        
        if current_question:
            questions.append(current_question.strip())
        
        return [q for q in questions if q and len(q) > 5]

# التطبيق الرئيسي
def main():
    st.sidebar.title("⚙️ إعدادات المولد")
    
    # إضافة صورة أو شعار
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103655.png", width=100)
    
    # إعدادات التوليد
    st.sidebar.subheader("خيارات التوليد")
    include_comments = st.sidebar.checkbox("إضافة تعليقات توضيحية", value=True)
    auto_detect_vars = st.sidebar.checkbox("الكشف التلقائي عن المتغيرات", value=True)
    generate_all = st.sidebar.checkbox("توليد جميع أنواع التحليلات", value=False)
    
    st.sidebar.subheader("تنسيق الإخراج")
    output_format = st.sidebar.selectbox(
        "نوع الإخراج",
        ["SPSS Syntax (.sps)", "Text File (.txt)", "Both"]
    )
    
    generator = UniversalSPSSGenerator()
    
    # القسم الرئيسي
    st.markdown("---")
    
    # تحميل الملفات
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 تحميل ملف البيانات")
        data_file = st.file_uploader(
            "اختر ملف Excel أو CSV",
            type=['xlsx', 'xls', 'csv'],
            key="data_file"
        )
    
    with col2:
        st.subheader("📝 تحميل ملف الأسئلة")
        questions_file = st.file_uploader(
            "اختر ملف نصي للأسئلة",
            type=['txt', 'docx', 'pdf'],
            key="questions_file"
        )
    
    if data_file and questions_file:
        try:
            # قراءة البيانات
            if data_file.name.endswith('.csv'):
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            # قراءة الأسئلة
            if questions_file.name.endswith('.txt'):
                questions_text = questions_file.getvalue().decode('utf-8')
            else:
                # محاولة قراءة أنواع الملفات الأخرى
                questions_text = str(questions_file.getvalue())
            
            questions = generator.parse_questions(questions_text)
            
            # تحليل هيكل البيانات
            var_info = generator.analyze_data_structure(df)
            
            st.success(f"""
            ✅ تم تحميل البيانات بنجاح:
            - عدد الأسئلة: {len(questions)}
            - عدد المتغيرات: {len(df.columns)}
            - عدد الصفوف: {len(df)}
            """)
            
            # عرض معلومات البيانات
            with st.expander("📊 معاينة البيانات وتحليل المتغيرات"):
                tab1, tab2 = st.tabs(["معاينة البيانات", "تحليل المتغيرات"])
                
                with tab1:
                    st.dataframe(df.head(10))
                    st.caption(f"الأبعاد: {df.shape[0]} صف × {df.shape[1]} عمود")
                
                with tab2:
                    for var, info in list(var_info.items())[:10]:
                        st.write(f"**{var}**")
                        st.json(info, expanded=False)
                        st.write("---")
            
            # عرض الأسئلة
            with st.expander("📋 الأسئلة المحللة"):
                for i, q in enumerate(questions, 1):
                    classifications = generator.classify_question(q)
                    detected_vars = generator.detect_variables_from_question(q, var_info)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{i}.** {q}")
                    with col2:
                        st.caption(f"النوع: {', '.join(classifications)}")
                    
                    if detected_vars:
                        st.caption(f"المتغيرات المكتشفة: {', '.join(detected_vars)}")
                    
                    st.write("---")
            
            # زر توليد الكود
            st.markdown("---")
            if st.button("🚀 توليد كود SPSS", type="primary", use_container_width=True):
                with st.spinner("جارٍ توليد كود SPSS المتخصص..."):
                    
                    # إنشاء رأس الكود
                    header = f"""* ========================================================================
* SPSS SYNTAX GENERATED BY UNIVERSAL SPSS GENERATOR
* Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Dataset: {data_file.name}
* Questions: {len(questions)}
* Variables: {len(df.columns)}
* ========================================================================

* SETUP AND DATA DEFINITION
"""
                    
                    # إضافة تسميات المتغيرات
                    header += generator.create_variable_labels(df)
                    
                    # إضافة تسميات القيم
                    value_labels = generator.create_value_labels(df, var_info)
                    if value_labels:
                        header += value_labels
                    
                    header += "EXECUTE.\n\n"
                    
                    # توليد كود لكل سؤال
                    spss_code = header
                    
                    for i, question in enumerate(questions, 1):
                        detected_vars = generator.detect_variables_from_question(question, var_info)
                        question_code = generator.generate_spss_syntax(question, var_info, detected_vars, i)
                        spss_code += question_code
                    
                    # إضافة قسم الإخراج
                    spss_code += """* ========================================================================
* OUTPUT MANAGEMENT
* ========================================================================

* Save output to file
OUTPUT SAVE OUTFILE='SPSS_Output.spv'
  /KEEP=ALL.

* Save modified dataset
SAVE OUTFILE='Analyzed_Data.sav'
  /COMPRESSED.

* Clear output viewer (optional)
OUTPUT CLOSE ALL.
"""
                    
                    # عرض الكود
                    st.subheader("📋 كود SPSS النهائي")
                    
                    # خيارات عرض الكود
                    show_full = st.checkbox("عرض الكود كاملاً", value=False)
                    
                    if show_full:
                        st.code(spss_code, language='text')
                    else:
                        # عرض عينة من الكود
                        code_lines = spss_code.split('\n')
                        st.code('\n'.join(code_lines[:100]), language='text')
                        if len(code_lines) > 100:
                            st.info(f"عرض 100 سطر من أصل {len(code_lines)} سطر. تفعيل 'عرض الكود كاملاً' لرؤية الكود كاملاً.")
                    
                    # تحميل الملفات
                    st.markdown("---")
                    st.subheader("📥 تحميل الملفات")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # ملف SPSS Syntax
                        b64_sps = base64.b64encode(spss_code.encode()).decode()
                        href_sps = f'<a href="data:file/sps;base64,{b64_sps}" download="SPSS_Analysis.sps" style="text-decoration: none; padding: 10px 20px; background-color: #4CAF50; color: white; border-radius: 5px; font-weight: bold;">📥 تنزيل ملف SPSS (.sps)</a>'
                        st.markdown(href_sps, unsafe_allow_html=True)
                    
                    with col2:
                        # ملف نصي
                        b64_txt = base64.b64encode(spss_code.encode()).decode()
                        href_txt = f'<a href="data:file/txt;base64,{b64_txt}" download="Analysis_Code.txt" style="text-decoration: none; padding: 10px 20px; background-color: #2196F3; color: white; border-radius: 5px; font-weight: bold;">📥 تنزيل ملف نصي (.txt)</a>'
                        st.markdown(href_txt, unsafe_allow_html=True)
                    
                    with col3:
                        # ملف تعليمات
                        instructions = f"""# تعليمات استخدام كود SPSS
تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d')}
عدد الأسئلة: {len(questions)}

## خطوات التنفيذ:
1. افتح برنامج SPSS
2. قم بتحميل بياناتك (ملف البيانات الأصلي)
3. انتقل إلى Window → Syntax Editor
4. الصق الكود المرفق
5. حدد الكود كاملاً (Ctrl+A)
6. اضغط F5 أو انقر على Run (السهم الأخضر)

## ملاحظات مهمة:
- تأكد من تطابق أسماء المتغيرات
- قم بحفظ الملفات قبل البدء
- راجع الإخراج (Output) للنتائج
"""
                        b64_inst = base64.b64encode(instructions.encode()).decode()
                        href_inst = f'<a href="data:file/txt;base64,{b64_inst}" download="Instructions.txt" style="text-decoration: none; padding: 10px 20px; background-color: #FF9800; color: white; border-radius: 5px; font-weight: bold;">📥 تعليمات الاستخدام</a>'
                        st.markdown(href_inst, unsafe_allow_html=True)
                    
                    # نصائح وأفكار
                    with st.expander("💡 نصائح وتحسينات"):
                        st.markdown("""
                        ### لتحسين النتائج:
                        1. **تسمية المتغيرات بشكل واضح**: استخدم أسماء دالة على المحتوى
                        2. **تحديد المتغيرات في الأسئلة**: اذكر أسماء المتغيرات صراحة في الأسئلة
                        3. **التنظيم**: رتب الأسئلة بشكل منطقي
                        
                        ### للتحليلات المتقدمة:
                        - إذا كان السؤال عن مقارنة المجموعات، اذكر اسم متغير المجموعة
                        - إذا كان عن الارتباط، اذكر المتغيرين المراد قياس العلاقة بينهما
                        - إذا كان عن الانحدار، حدد المتغير التابع والمستقل
                        
                        ### أمثلة على صياغة الأسئلة:
                        - "احسب المتوسط والانحراف المعياري لمتغير الدخل (Income)"
                        - "ارسم مخططاً شريطياً يوضح توزيع النوع (Gender)"
                        - "اختبر إذا كان هناك فرق ذو دلالة في العمر (Age) بين المجموعتين (Group)"
                        """)
        
        except Exception as e:
            st.error(f"حدث خطأ: {str(e)}")
            st.exception(e)
    
    else:
        # واجهة الترحيب
        st.info("""
        ## 🎯 مرحباً بك في مولد أكواد SPSS الشامل
        
        **كيفية الاستخدام:**
        1. **قم بتحميل ملف البيانات** (Excel أو CSV)
        2. **قم بتحميل ملف الأسئلة** (ملف نصي)
        3. **اضغط على زر "توليد كود SPSS"**
        4. **حمل الملفات الناتجة**
        
        **المميزات:**
        - ✅ يدعم أي نوع من الامتحانات الإحصائية
        - ✅ يحلل البيانات تلقائياً
        - ✅ يتعرف على أنواع الأسئلة المختلفة
        - ✅ يكتشف المتغيرات المذكورة في الأسئلة
        - ✅ يولد كود SPSS جاهز للتنفيذ
        - ✅ يدعم جميع أنواع التحليلات الإحصائية
        
        **أنواع التحليلات المدعومة:**
        - الإحصاءات الوصفية
        - الجداول التكرارية
        - اختبارات T
        - تحليل التباين (ANOVA)
        - الارتباط والانحدار
        - اختبارات مربع كاي
        - الرسوم البيانية بأنواعها
        - فترات الثقة
        - اختبارات الطبيعية
        """)
        
        # أمثلة على تنسيق الأسئلة
        with st.expander("📚 أمثلة على تنسيق الأسئلة"):
            st.markdown("""
            ### مثال 1: أسئلة وصفية
            ```
            1. احسب المتوسط والانحراف المعياري للعمر والدخل
            2. أنشئ جدولاً تكرارياً للنوع والتعليم
            3. ارسم مخططاً شريطياً يوضح توزيع المناصب
            ```
            
            ### مثال 2: أسئلة استدلالية
            ```
            4. اختبر إذا كان هناك فرق في الراتب بين الذكور والإناث
            5. افحص العلاقة بين سنوات الخبرة والدخل
            6. حلل تأثير العمر والتعليم على الراتب
            ```
            
            ### مثال 3: أسئلة بيانية
            ```
            7. ارسم مخططاً دائرياً لتوزيع النوع
            8. أنشئ مخططاً مبعثراً للعلاقة بين العمر والدخل
            9. ارسم مخططاً صندوقياً للرواتب حسب القسم
            ```
            """)
        
        # مثال تجريبي
        with st.expander("🔬 جرب مثالاً تجريبياً"):
            if st.button("تحميل بيانات تجريبية"):
                # إنشاء بيانات تجريبية
                np.random.seed(42)
                sample_data = pd.DataFrame({
                    'Age': np.random.randint(20, 60, 100),
                    'Salary': np.random.normal(5000, 1500, 100),
                    'Gender': np.random.choice(['Male', 'Female'], 100),
                    'Education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], 100),
                    'Experience': np.random.randint(1, 30, 100),
                    'Department': np.random.choice(['Sales', 'IT', 'HR', 'Finance'], 100)
                })
                
                sample_questions = """1. Calculate descriptive statistics for Age and Salary
2. Create frequency tables for Gender and Education
3. Test if there is a significant difference in Salary between genders
4. Examine the relationship between Experience and Salary
5. Draw a bar chart showing average Salary by Department
6. Create a scatter plot of Age vs Salary
7. Perform regression analysis with Salary as dependent variable"""
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**البيانات التجريبية:**")
                    st.dataframe(sample_data.head())
                with col2:
                    st.write("**الأسئلة التجريبية:**")
                    st.text(sample_questions)

if __name__ == "__main__":
    main()
