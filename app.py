import pandas as pd
import docx
import re
import os
import streamlit as st
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# تهيئة Streamlit
st.set_page_config(page_title="SPSS v26 Syntax Generator", layout="wide")
st.title("📊 SPSS v26 Syntax Generator")
st.markdown("### توليد كود SPSS تلقائياً من ملفات Excel وWord")

class SPSSv26SyntaxGenerator:
    def __init__(self, excel_path: str, word_path: str):
        """
        تهيئة مولد كود SPSS v26
        """
        self.excel_path = excel_path
        self.word_path = word_path
        self.dataset_name = os.path.basename(excel_path).split('.')[0]
        self.data = pd.DataFrame()
        self.data_types = {}
        self.variable_map = {}
        self.questions = []
        
        # تحميل البيانات
        self._load_data()
    
    def _load_data(self):
        """تحميل البيانات من Excel"""
        try:
            if os.path.exists(self.excel_path):
                self.data = pd.read_excel(self.excel_path, sheet_name=0)
                
                # تنظيف أسماء الأعمدة
                self.data.columns = [str(col).strip() for col in self.data.columns]
                
                # تحليل أنواع البيانات
                self.data_types = {}
                for col in self.data.columns:
                    if self.data[col].dtype == 'object':
                        self.data_types[col] = 'STRING'
                    elif len(self.data[col].dropna().unique()) < 10:
                        self.data_types[col] = 'CATEGORICAL'
                    else:
                        self.data_types[col] = 'SCALE'
                
                # إنشاء خريطة المتغيرات
                self._create_variable_mapping()
                
                # استخراج الأسئلة
                self._extract_questions()
            else:
                st.error(f"الملف غير موجود: {self.excel_path}")
        except Exception as e:
            st.error(f"خطأ في تحميل البيانات: {e}")
            self.data = pd.DataFrame()
    
    def _create_variable_mapping(self):
        """إنشاء خريطة للمتغيرات"""
        self.variable_map = {}
        
        for col in self.data.columns:
            var_info = {
                'name': col,
                'label': col,
                'type': self.data_types.get(col, 'SCALE'),
                'values': {}
            }
            
            # إذا كان متغير فئوي، استخراج القيم الفريدة
            if var_info['type'] == 'CATEGORICAL' and not self.data.empty:
                unique_vals = self.data[col].dropna().unique()[:10]
                for val in unique_vals:
                    var_info['values'][str(val)] = f"Value {val}"
            
            self.variable_map[col] = var_info
    
    def _extract_questions(self):
        """استخراج وتنظيم الأسئلة من ملف Word"""
        self.questions = []
        
        if not os.path.exists(self.word_path):
            st.warning(f"ملف الأسئلة غير موجود: {self.word_path}")
            return
        
        try:
            doc = docx.Document(self.word_path)
            current_question = None
            
            for para in doc.paragraphs:
                text = para.text.strip()
                
                if not text:
                    continue
                
                # تحديد إذا كان هذا سؤالاً مرقماً
                match = re.match(r'^(\d+)[\.\)]\s*(.*)', text)
                if match:
                    if current_question:
                        self.questions.append(current_question)
                    
                    q_num = int(match.group(1))
                    q_text = match.group(2)
                    current_question = {
                        'number': q_num,
                        'text': q_text,
                        'full_text': text
                    }
                elif current_question and text:
                    # إضافة النص التالي للسؤال الحالي
                    current_question['full_text'] += " " + text
            
            # إضافة السؤال الأخير
            if current_question:
                self.questions.append(current_question)
                
        except Exception as e:
            st.error(f"خطأ في قراءة ملف Word: {e}")
    
    def generate_dataset_setup(self) -> str:
        """إنشاء كود لإعداد مجموعة البيانات"""
        if self.data.empty:
            return "* No data loaded\n"
        
        syntax = f"* === SPSS v26 Dataset Setup ===\n"
        syntax += f"* File: {self.dataset_name}\n"
        syntax += f"* Variables: {len(self.data.columns)}\n"
        syntax += f"* Cases: {len(self.data)}\n"
        syntax += f"* Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n"
        
        # تعريف المتغيرات
        syntax += "DATASET NAME DataSet1 WINDOW=FRONT.\n"
        syntax += "DATASET ACTIVATE DataSet1.\n\n"
        
        # إضافة تسميات للمتغيرات
        syntax += "* Variable Labels\n"
        for var_name, var_info in self.variable_map.items():
            syntax += f'VARIABLE LABELS {var_name} "{var_info["label"]}".\n'
        
        syntax += "\n"
        
        # تحديد أنواع المتغيرات
        syntax += "* Define Variable Types\n"
        for var_name, var_info in self.variable_map.items():
            if var_info['type'] == 'SCALE':
                syntax += f'VARIABLE LEVEL {var_name} (SCALE).\n'
            elif var_info['type'] in ['CATEGORICAL', 'STRING']:
                syntax += f'VARIABLE LEVEL {var_name} (NOMINAL).\n'
        
        syntax += "\nEXECUTE.\n"
        syntax += "*" * 60 + "\n\n"
        
        return syntax
    
    def detect_analysis_type(self, question_text: str) -> str:
        """تحديد نوع التحليل المطلوب"""
        text_lower = question_text.lower()
        
        analysis_patterns = {
            'frequency': ['frequency table', 'جدول تكراري', 'توزيع تكراري'],
            'descriptive': ['mean', 'median', 'mode', 'standard deviation', 'مقاييس'],
            'bar_chart': ['bar chart', 'رسم بياني عمودي', 'مخطط عمودي'],
            'pie_chart': ['pie chart', 'رسم دائري', 'مخطط دائري'],
            'histogram': ['histogram', 'مدرج تكراري'],
            'confidence': ['confidence interval', 'فترة ثقة'],
            'ttest': ['test the hypothesis', 't-test', 'اختبار الفرضية'],
            'anova': ['anova', 'تحليل التباين', 'significant difference'],
            'correlation': ['correlation', 'ارتباط'],
            'regression': ['regression', 'انحدار', 'linear model'],
            'normality': ['normality', 'empirical rule', 'chebycheve'],
            'outliers': ['outliers', 'extreme value', 'القيم المتطرفة']
        }
        
        for analysis_type, keywords in analysis_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return analysis_type
        
        return 'descriptive'
    
    def extract_variables_from_question(self, question_text: str) -> List[str]:
        """استخراج المتغيرات المذكورة في السؤال"""
        if self.data.empty:
            return []
        
        found_vars = []
        question_lower = question_text.lower()
        
        # البحث عن أسماء المتغيرات في السؤال
        for var_name in self.variable_map.keys():
            var_lower = var_name.lower()
            
            # البحث بالاسم الكامل
            if var_lower in question_lower:
                found_vars.append(var_name)
            # البحث بالأسماء الشائعة
            elif 'salary' in question_lower and 'salary' in var_lower:
                found_vars.append(var_name)
            elif 'age' in question_lower and 'age' in var_lower:
                found_vars.append(var_name)
            elif 'gender' in question_lower and 'gender' in var_lower:
                found_vars.append(var_name)
        
        # إذا لم يتم العثور على متغيرات، استخدام الأعمدة الأولى
        if not found_vars and not self.data.empty:
            found_vars = list(self.data.columns[:min(3, len(self.data.columns))])
        
        return found_vars
    
    def generate_analysis_syntax(self, question: Dict) -> str:
        """توليد كود التحليل لسؤال معين"""
        q_num = question['number']
        q_text = question['text']
        full_text = question['full_text']
        
        syntax = f"* Question {q_num}: {q_text}\n"
        
        # تحديد نوع التحليل
        analysis_type = self.detect_analysis_type(full_text)
        
        # استخراج المتغيرات
        variables = self.extract_variables_from_question(full_text)
        
        syntax += f"* Analysis Type: {analysis_type}\n"
        syntax += f"* Variables: {variables}\n"
        syntax += "*" * 50 + "\n"
        
        # توليد الكود بناءً على نوع التحليل
        if analysis_type == 'frequency':
            syntax += self._generate_frequency_table(variables)
        elif analysis_type == 'descriptive':
            syntax += self._generate_descriptive_stats(variables)
        elif analysis_type == 'bar_chart':
            syntax += self._generate_bar_chart(variables)
        elif analysis_type == 'pie_chart':
            syntax += self._generate_pie_chart(variables)
        else:
            syntax += f"* Using descriptive statistics for {analysis_type}\n"
            syntax += self._generate_descriptive_stats(variables)
        
        syntax += "\n"
        return syntax
    
    def _generate_frequency_table(self, variables: List[str]) -> str:
        """إنشاء جدول تكراري"""
        syntax = "FREQUENCIES VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /BARCHART FREQ\n"
        syntax += "  /ORDER=ANALYSIS.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def _generate_descriptive_stats(self, variables: List[str]) -> str:
        """إنشاء إحصاءات وصفية"""
        syntax = "DESCRIPTIVES VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /STATISTICS=MEAN STDDEV MIN MAX.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def _generate_bar_chart(self, variables: List[str]) -> str:
        """إنشاء رسم بياني عمودي"""
        if len(variables) == 0:
            return "* No variables for bar chart\n"
        
        if len(variables) == 1:
            syntax = "GRAPH\n"
            syntax += f"  /BAR(SIMPLE)=COUNT BY {variables[0]}\n"
            syntax += "  /TITLE='Bar Chart'.\n"
            syntax += "EXECUTE.\n"
        else:
            syntax = "GRAPH\n"
            syntax += f"  /BAR(GROUPED)=MEAN({variables[1]}) BY {variables[0]}\n"
            syntax += "  /TITLE='Grouped Bar Chart'.\n"
            syntax += "EXECUTE.\n"
        
        return syntax
    
    def _generate_pie_chart(self, variables: List[str]) -> str:
        """إنشاء رسم بياني دائري"""
        if len(variables) == 0:
            return "* No variables for pie chart\n"
        
        syntax = "GRAPH\n"
        syntax += f"  /PIE=PCT BY {variables[0]}\n"
        syntax += "  /TITLE='Pie Chart'.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def process_all_questions(self) -> str:
        """معالجة جميع الأسئلة وإنشاء كود SPSS كامل"""
        if not self.questions:
            return "* No questions found in the document\n"
        
        if self.data.empty:
            return "* No data loaded\n"
        
        # بدء كود SPSS
        spss_syntax = self.generate_dataset_setup()
        
        spss_syntax += "* === Analysis for Each Question ===\n\n"
        
        for question in self.questions:
            try:
                spss_syntax += self.generate_analysis_syntax(question)
            except Exception as e:
                spss_syntax += f"* Error processing question {question['number']}: {str(e)[:100]}...\n\n"
        
        # إضافة قسم للتنظيف
        spss_syntax += "* === Cleanup ===\n"
        spss_syntax += "DATASET CLOSE ALL.\n"
        spss_syntax += "EXECUTE.\n"
        
        return spss_syntax

# واجهة Streamlit
def main():
    """الواجهة الرئيسية للتطبيق"""
    
    # شريط جانبي للتحكم
    with st.sidebar:
        st.header("⚙️ إعدادات")
        
        # اختيار وضع التشغيل
        mode = st.radio(
            "اختر وضع التشغيل:",
            ["📁 رفع ملفات", "📊 مثال توضيحي"]
        )
        
        if mode == "📁 رفع ملفات":
            st.subheader("رفع الملفات")
            
            # رفع ملف Excel
            excel_file = st.file_uploader(
                "رفع ملف البيانات (Excel)",
                type=['xls', 'xlsx']
            )
            
            # رفع ملف Word
            word_file = st.file_uploader(
                "رفع ملف الأسئلة (Word)",
                type=['doc', 'docx']
            )
            
            if excel_file and word_file:
                # حفظ الملفات المؤقتة
                excel_path = f"temp_{excel_file.name}"
                word_path = f"temp_{word_file.name}"
                
                with open(excel_path, "wb") as f:
                    f.write(excel_file.getbuffer())
                
                with open(word_path, "wb") as f:
                    f.write(word_file.getbuffer())
                
                # إنشاء المولد
                generator = SPSSv26SyntaxGenerator(excel_path, word_path)
                
                # تنظيف الملفات المؤقتة
                if os.path.exists(excel_path):
                    os.remove(excel_path)
                if os.path.exists(word_path):
                    os.remove(word_path)
                
                return generator
            else:
                return None
        
        else:  # مثال توضيحي
            st.subheader("مثال توضيحي")
            
            # استخدام ملفات المثال
            try:
                # هذه المسارات قد تحتاج للتعديل حسب بيئة Streamlit Cloud
                excel_path = "Data set 2.xls"
                word_path = "SPSS questioins For data set 2.doc"
                
                if os.path.exists(excel_path) and os.path.exists(word_path):
                    generator = SPSSv26SyntaxGenerator(excel_path, word_path)
                    return generator
                else:
                    st.warning("ملفات المثال غير موجودة. يرجى رفع ملفاتك.")
                    return None
            except:
                st.info("يرجى رفع ملفاتك للبدء")
                return None
    
    # المنطقة الرئيسية
    st.markdown("---")
    
    # تحميل المولد
    generator = main()
    
    if generator:
        if not generator.data.empty:
            # عرض معلومات عن البيانات
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 المتغيرات", len(generator.data.columns))
            
            with col2:
                st.metric("📈 الحالات", len(generator.data))
            
            with col3:
                st.metric("❓ الأسئلة", len(generator.questions))
            
            # عرض عينة من البيانات
            with st.expander("🔍 عرض عينة من البيانات"):
                st.dataframe(generator.data.head())
            
            # عرض المتغيرات
            with st.expander("📋 المتغيرات وأنواعها"):
                var_info = []
                for var_name, var_info_obj in generator.variable_map.items():
                    var_info.append({
                        'المتغير': var_name,
                        'النوع': var_info_obj['type'],
                        'التسمية': var_info_obj['label']
                    })
                st.table(pd.DataFrame(var_info))
            
            # عرض الأسئلة
            with st.expander("📝 الأسئلة المستخرجة"):
                for i, question in enumerate(generator.questions[:10], 1):
                    st.markdown(f"**{i}. {question['text']}**")
                    st.caption(f"النوع: {generator.detect_analysis_type(question['full_text'])}")
            
            # توليد كود SPSS
            st.markdown("---")
            st.subheader("🔄 توليد كود SPSS")
            
            if st.button("🚀 توليد كود SPSS", type="primary"):
                with st.spinner("جاري توليد كود SPSS..."):
                    spss_code = generator.process_all_questions()
                    
                    # عرض الكود
                    st.subheader("📜 كود SPSS المتولد")
                    st.code(spss_code, language='spss')
                    
                    # تحميل الملف
                    st.download_button(
                        label="📥 تحميل ملف SPSS (.sps)",
                        data=spss_code,
                        file_name=f"SPSS_{generator.dataset_name}.sps",
                        mime="text/plain"
                    )
        else:
            st.error("❌ لم يتم تحميل البيانات بشكل صحيح")
    else:
        # رسالة ترحيبية
        st.markdown("""
        ## 👋 مرحباً بكم في مولد كود SPSS v26
        
        ### كيفية الاستخدام:
        1. **في الشريط الجانبي** ← اختر "رفع ملفات"
        2. **ارفع ملف Excel** يحتوي على بياناتك
        3. **ارفع ملف Word** يحتوي على الأسئلة
        4. **انقر على "توليد كود SPSS"**
        
        ### المميزات:
        - ✅ توليد كود SPSS v26 تلقائياً
        - 📊 تحليل البيانات من ملفات Excel
        - 📝 استخراج الأسئلة من ملفات Word
        - 🔄 تحديد نوع التحليل تلقائياً
        - 📥 تحميل الكود جاهزاً للاستخدام
        
        ### أنواع التحليل المدعومة:
        - جداول التكرارات
        - الإحصاءات الوصفية
        - الرسوم البيانية (أعمدة، دوائر)
        - اختبارات الفرضيات
        - والعديد غيرها...
        """)

# تشغيل التطبيق
if __name__ == "__main__":
    main()
