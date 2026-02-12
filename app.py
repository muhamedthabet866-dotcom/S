import streamlit as st
import pandas as pd
import docx2txt
import re
from io import StringIO

class DynamicSPSSSolver:
    def __init__(self, df=None):
        self.df = df
        self.columns = list(df.columns) if df is not None else []
        
        # قاموس الكلمات الدالة (عربي وإنجليزي) لربطها بأوامر SPSS
        self.keywords_map = {
            'frequencies': {
                'keywords': ['frequency', 'frequencies', 'count', 'distribution', 'تكرار', 'توزيع', 'عدد', 'فئات'],
                'syntax': 'FREQUENCIES VARIABLES={vars} /ORDER=ANALYSIS.'
            },
            'descriptives': {
                'keywords': ['mean', 'average', 'std', 'deviation', 'min', 'max', 'summary', 'متوسط', 'انحراف', 'أكبر قيمة', 'أقل قيمة', 'وصف'],
                'syntax': 'DESCRIPTIVES VARIABLES={vars} /STATISTICS=MEAN STDDEV MIN MAX.'
            },
            'histogram': {
                'keywords': ['histogram', 'hist', 'مدرج', 'هيستوجرام'],
                'syntax': 'GRAPH /HISTOGRAM={vars}.'
            },
            'barchart': {
                'keywords': ['bar', 'chart', 'bars', 'أعمدة', 'بياني'],
                'syntax': 'GRAPH /BAR(SIMPLE)=COUNT BY {vars}.'
            },
            'normality': {
                'keywords': ['normality', 'shapiro', 'normal distribution', 'طبيعي', 'توزيع طبيعي'],
                'syntax': 'EXAMINE VARIABLES={vars} /PLOT NPPLOT /STATISTICS NONE.'
            },
            'correlation': {
                'keywords': ['correlation', 'relationship', 'relate', 'pearson', 'ارتباط', 'علاقة'],
                'syntax': 'CORRELATIONS /VARIABLES={vars} /PRINT=TWOTAIL NOSIG.'
            },
             'ttest': {
                'keywords': ['t-test', 'compare means', 'difference', 'significant', 'فروق', 'ت تيست', 'اختبار ت'],
                'syntax': 'T-TEST GROUPS={group_var}(0 1) /MISSING=ANALYSIS /VARIABLES={vars} /CRITERIA=CI(.95).'
            }
        }

    def extract_text(self, uploaded_file):
        """قراءة النص سواء كان Word أو Text"""
        if uploaded_file.name.endswith('.docx'):
            return docx2txt.process(uploaded_file)
        elif uploaded_file.name.endswith('.txt'):
            return uploaded_file.getvalue().decode("utf-8")
        else:
            return ""

    def parse_questions(self, text):
        """تقسيم النص إلى قائمة أسئلة"""
        lines = text.split('\n')
        questions = []
        current_q = ""
        # نمط للبحث عن بداية السؤال (رقم ثم نقطة أو قوس)
        q_pattern = r'^(\d+[\.\)]|Q\d+|س\d+)'
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if re.match(q_pattern, line, re.IGNORECASE):
                if current_q:
                    questions.append(current_q.strip())
                current_q = line
            elif current_q:
                current_q += " " + line
                
        if current_q:
            questions.append(current_q.strip())
        return questions

    def detect_variables(self, question_text):
        """البحث عن أسماء أعمدة الإكسل داخل نص السؤال"""
        found_vars = []
        # ترتيب الأعمدة حسب الطول (الأطول أولاً) لتجنب أخطاء المطابقة الجزئية
        sorted_cols = sorted(self.columns, key=len, reverse=True)
        
        for col in sorted_cols:
            # تنظيف اسم العمود والنص للمقارنة (تجاهل حالة الأحرف)
            # نستخدم \b للتأكد أنها كلمة كاملة
            pattern = r'\b' + re.escape(str(col)) + r'\b'
            if re.search(pattern, question_text, re.IGNORECASE):
                found_vars.append(col)
        
        return found_vars

    def generate_syntax_for_question(self, question_text, q_num):
        """المحرك الرئيسي: يحلل السؤال ويكتب الكود"""
        
        # 1. تحديد المتغيرات
        detected_vars = self.detect_variables(question_text)
        vars_str = " ".join(detected_vars) if detected_vars else "[VARIABLE_MISSING]"
        
        # 2. تحديد نوع التحليل بناءً على الكلمات المفتاحية
        selected_syntax = ""
        analysis_type = "Unknown"
        
        for key, logic in self.keywords_map.items():
            for keyword in logic['keywords']:
                if keyword.lower() in question_text.lower():
                    # حالة خاصة للارتباط تحتاج متغيرين على الأقل
                    if key == 'correlation' and len(detected_vars) < 2:
                        continue
                        
                    selected_syntax = logic['syntax'].replace('{vars}', vars_str)
                    
                    # حالة خاصة لـ T-Test (يحتاج متغير تجميع ومتغير تابع)
                    if key == 'ttest' and len(detected_vars) >= 2:
                        # نفترض أن المتغير الأول هو التابع والثاني هو المجموعات (تقريب)
                        selected_syntax = selected_syntax.replace('{group_var}', detected_vars[-1])
                        selected_syntax = selected_syntax.replace('{vars}', " ".join(detected_vars[:-1]))
                    
                    analysis_type = key
                    break
            if selected_syntax:
                break
        
        # إذا لم يتم التعرف على السؤال
        if not selected_syntax:
            selected_syntax = f"* Could not detect analysis type for: {vars_str}.\n* Please check keywords (mean, freq, plot...)."

        # تجميع الكود النهائي للسؤال
        final_block = f"""
* --------------------------------------------------.
* QUESTION {q_num}: {question_text[:50]}...
* Detected Analysis: {analysis_type} | Detected Vars: {vars_str}
* --------------------------------------------------.
{selected_syntax}
"""
        return final_block

    def generate_full_script(self, questions):
        """تجميع الملف بالكامل"""
        
        # رأس الملف: تعريف المتغيرات من الإكسل تلقائياً
        header = """* Encoding: UTF-8.
* AUTOMATED VARIABLE DEFINITION FROM EXCEL.
"""
        # توليد كود لتعريف المتغيرات بناء على أعمدة الإكسل
        if self.columns:
            header += "VARIABLE LABELS\n"
            for col in self.columns:
                header += f'    {col} "{col}"\n'
            header += ".\n\n"

        body = ""
        for i, q in enumerate(questions, 1):
            body += self.generate_syntax_for_question(q, i)
            
        return header + body

# --- واجهة التطبيق ---
def main():
    st.set_page_config(page_title="Dynamic SPSS Solver", layout="wide")
    st.title("🤖 المحلل الذكي للامتحانات (Dynamic SPSS Solver)")
    st.markdown("""
    **كيف يعمل هذا النظام؟**
    1. ارفع ملف البيانات (Excel) ليقرأ البرنامج أسماء المتغيرات (مثال: Age, Income, Gender).
    2. ارفع ملف الأسئلة (Word/Txt).
    3. سيقوم البرنامج بقراءة كل سؤال، والبحث عن اسم المتغير بداخله، ثم كتابة الكود المناسب تلقائياً.
    
    ⚠️ **شرط مهم:** يجب أن يحتوي نص السؤال على **اسم العمود** كما هو مكتوب في ملف الإكسل (أو جزء منه).
    """)

    col1, col2 = st.columns(2)
    
    # 1. رفع البيانات
    with col1:
        st.subheader("1. ملف البيانات (Excel)")
        data_file = st.file_uploader("Upload Excel", type=['xlsx', 'xls'])
    
    df = None
    if data_file:
        try:
            df = pd.read_excel(data_file)
            st.success(f"✅ تم تحميل البيانات. الأعمدة المكتشفة: {list(df.columns)}")
            with st.expander("معاينة البيانات"):
                st.dataframe(df.head(3))
        except Exception as e:
            st.error(f"خطأ في ملف البيانات: {e}")

    # 2. رفع الأسئلة
    with col2:
        st.subheader("2. ملف الأسئلة (Word/Txt)")
        q_file = st.file_uploader("Upload Questions", type=['docx', 'txt'])

    # 3. المعالجة
    if df is not None and q_file is not None:
        solver = DynamicSPSSSolver(df)
        
        # استخراج النصوص
        text_content = solver.extract_text(q_file)
        questions = solver.parse_questions(text_content)
        
        st.info(f"🔍 تم العثور على {len(questions)} سؤال.")
        
        if st.button("⚡ توليد الحل (Generate Syntax)"):
            full_syntax = solver.generate_full_script(questions)
            
            st.subheader("📝 الكود المولد:")
            st.code(full_syntax, language="spss")
            
            st.download_button(
                label="💾 تحميل ملف Syntax (.sps)",
                data=full_syntax,
                file_name="Dynamic_Solution.sps",
                mime="text/plain"
            )
            
            st.markdown("---")
            st.warning("""
            **ملاحظات للتصحيح:**
            - إذا ظهر `[VARIABLE_MISSING]`، فهذا يعني أن اسم المتغير في السؤال يختلف عن اسم العمود في الإكسل.
            - تأكد أن أسماء الأعمدة في الإكسل باللغة الإنجليزية لنتائج أفضل في SPSS.
            """)

if __name__ == "__main__":
    main()
