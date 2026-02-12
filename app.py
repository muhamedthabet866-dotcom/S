import streamlit as st
import pandas as pd
import re
import docx2txt
from io import StringIO

# -----------------------------------------------------------------------------
# 1. قاموس المرادفات (السر في فهم الأسئلة المختلفة)
# هذا القاموس يربط كلمات السؤال بمفاتيح ملف القواعد الخاص بك
# -----------------------------------------------------------------------------
KEYWORD_MAPPING = {
    # كلمات السؤال (عربي/إنجليزي)  ->  اسم القاعدة في ملف CSV
    'frequency': 'frequency table',
    'frequencies': 'frequency table',
    'count': 'frequency table',
    'distribution': 'frequency table',
    'تكرار': 'frequency table',
    'توزيع': 'frequency table',
    
    'mean': 'mean, median, mode',
    'average': 'mean, median, mode',
    'descriptive': 'mean, median, mode',
    'summary': 'mean, median, mode',
    'متوسط': 'mean, median, mode',
    'وصف': 'mean, median, mode',

    'bar': 'bar chart',
    'أعمدة': 'bar chart',
    
    'pie': 'pie chart',
    'دائرة': 'pie chart',

    'correlation': 'correlation',
    'relationship': 'correlation',
    'associate': 'correlation',
    'pearson': 'correlation',
    'ارتباط': 'correlation',
    'علاقة': 'correlation',

    'regression': 'regression',
    'predict': 'regression',
    'impact': 'regression',
    'effect': 'regression',
    'انحدار': 'regression',
    'تأثير': 'regression',
    'تنبؤ': 'regression',

    't-test': 'significant difference (2 groups)',
    'compare two': 'significant difference (2 groups)',
    'difference between': 'significant difference (2 groups)',
    'فروق': 'significant difference (2 groups)',
    'مجموعتين': 'significant difference (2 groups)',

    'anova': 'significant difference (>2 groups)',
    'f-test': 'significant difference (>2 groups)',
    'analysis of variance': 'significant difference (>2 groups)',
    'more than two': 'significant difference (>2 groups)',
    
    'normal': 'normality',
    'shapiro': 'normality',
    'طبيعي': 'normality'
}

# -----------------------------------------------------------------------------
# 2. فئة المحرك الذكي
# -----------------------------------------------------------------------------
class IntelligentSPSSGenerator:
    def __init__(self, rules_df, data_df):
        self.rules_df = rules_df
        # تنظيف مفاتيح القواعد لتكون سهلة البحث
        self.rules_df['Keyword'] = self.rules_df['Keyword'].astype(str).str.strip()
        self.df = data_df
        self.columns = list(data_df.columns) if data_df is not None else []

    def detect_variables(self, text):
        """استخراج أسماء الأعمدة من النص"""
        found = []
        # ترتيب الأعمدة حسب الطول (الأطول أولاً) لتجنب الأخطاء
        sorted_cols = sorted(self.columns, key=len, reverse=True)
        
        for col in sorted_cols:
            # بحث غير حساس لحالة الأحرف (Case Insensitive)
            pattern = re.escape(str(col))
            if re.search(pattern, text, re.IGNORECASE):
                found.append(col)
        
        # إزالة التكرارات مع الحفاظ على الترتيب
        return list(dict.fromkeys(found))

    def map_question_to_rule(self, text):
        """تحويل نص السؤال إلى مفتاح القاعدة المناسب"""
        text_lower = text.lower()
        
        # 1. البحث في قاموس المرادفات (الطريقة الذكية)
        for user_word, csv_key in KEYWORD_MAPPING.items():
            if user_word in text_lower:
                # التحقق من أن المفتاح موجود فعلاً في ملف CSV المرفوع
                if csv_key in self.rules_df['Keyword'].values:
                    return csv_key
        
        # 2. إذا فشل القاموس، نحاول البحث المباشر في ملف القواعد
        for keyword in self.rules_df['Keyword']:
            if keyword.lower() in text_lower:
                return keyword
                
        return None

    def fill_template(self, syntax_template, found_vars):
        """تعبئة القالب بالمتغيرات المكتشفة"""
        code = syntax_template
        
        # تجهيز المتغيرات
        var_list = " ".join(found_vars) if found_vars else "[MISSING_VAR]"
        var1 = found_vars[0] if len(found_vars) > 0 else "[VAR1]"
        var2 = found_vars[1] if len(found_vars) > 1 else "[VAR2]"
        
        # محاولة ذكية لتحديد المتغير المستقل والتابع (للإنحدار واختبار ت)
        # نفترض عادةً أن المتغير الفئوي (Categorical) هو الـ Group
        group_var = "[GROUP]"
        test_var = "[TEST_VAR]"
        
        if len(found_vars) >= 2:
            # استراتيجية بسيطة: المتغير الذي يحتوي قيم فريدة قليلة (مثل الجنس) هو المجموعة
            # وبقية المتغيرات هي المتغيرات الرقمية
            if self.df is not None:
                for v in found_vars:
                    if self.df[v].nunique() < 10: # رقم اعتباطي للمتغير الفئوي
                        group_var = v
                    else:
                        test_var = v
            else:
                # بدون بيانات نفترض الترتيب: (رقمي، فئوي)
                test_var = var1
                group_var = var2

        # استبدال العناصر النائبة (Placeholders) في القالب
        # التبديلات العامة
        code = code.replace("{var}", var_list)
        code = code.replace("{vars}", var_list)
        
        # التبديلات المحددة
        code = code.replace("{var1}", var1)
        code = code.replace("{var2}", var2)
        code = code.replace("{group}", group_var)
        code = code.replace("{cat_var}", group_var) # تسمية بديلة
        code = code.replace("{num_var}", test_var) # تسمية بديلة
        
        # تبديلات الانحدار (Regression)
        code = code.replace("{y}", var1) # نفترض الأول هو التابع
        code = code.replace("{x}", var2)
        code = code.replace("{x_list}", " ".join(found_vars[1:]) if len(found_vars)>1 else "[INDEP_VARS]")

        return code

    def generate_syntax(self, question, q_num):
        """توليد الكود النهائي للسؤال"""
        # 1. تحديد نوع التحليل
        rule_key = self.map_question_to_rule(question)
        
        # 2. تحديد المتغيرات
        vars_found = self.detect_variables(question)
        
        header = f"""
* ----------------------------------------------------------------.
* QUESTION {q_num}: {question[:60]}...
* DETECTED VARS: {vars_found}
"""
        if not rule_key:
            return header + f"* ERROR: ANALYSIS NOT RECOGNIZED. Try words like 'mean', 'frequency', 'test'.\n"
        
        header += f"* MATCHED RULE: {rule_key}\n* ----------------------------------------------------------------.\n"
        
        # 3. جلب القالب وتعبئته
        row = self.rules_df[self.rules_df['Keyword'] == rule_key].iloc[0]
        template = row['Syntax_Template']
        final_code = self.fill_template(template, vars_found)
        
        return header + final_code + "\n"

# -----------------------------------------------------------------------------
# 3. واجهة التطبيق
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="SPSS Smart Wizard", layout="wide")
    st.title("🧙‍♂️ معالج SPSS الذكي (Smart Wizard)")
    st.info("💡 هذا الإصدار يستخدم الذكاء لربط كلماتك (مثل 'Average') بقواعد الملف (مثل 'mean, median, mode').")

    col1, col2 = st.columns(2)
    
    # تحميل الملفات
    with col1:
        st.subheader("1. ملف القواعد (Rules)")
        rules_file = st.file_uploader("Upload spss_rules.csv", type=['csv'])
        
        st.subheader("2. ملف البيانات (Excel)")
        data_file = st.file_uploader("Upload Excel Data", type=['xlsx', 'xls'])

    with col2:
        st.subheader("3. ملف الأسئلة (Word/Txt)")
        q_file = st.file_uploader("Upload Questions", type=['docx', 'txt'])

    # زر التشغيل
    if st.button("🚀 تحليل وتوليد الكود") and rules_file and data_file and q_file:
        try:
            # قراءة الملفات
            rules_df = pd.read_csv(rules_file)
            data_df = pd.read_excel(data_file)
            
            # قراءة الأسئلة
            if q_file.name.endswith('.docx'):
                q_text = docx2txt.process(q_file)
            else:
                q_text = q_file.getvalue().decode("utf-8")

            # تهيئة المعالج
            wizard = IntelligentSPSSGenerator(rules_df, data_df)
            
            # تقسيم الأسئلة (افتراض أن السؤال يبدأ برقم)
            questions = [q.strip() for q in re.split(r'\n(?=\d+[\.\)]|Q\d+)', q_text) if len(q.strip()) > 5]

            full_syntax = "* Encoding: UTF-8.\n"
            
            # حلقة التوليد
            for i, q in enumerate(questions, 1):
                # تنظيف النص من الأرقام
                clean_q = re.sub(r'^(\d+[\.\)]|Q\d+)\s*', '', q)
                full_syntax += wizard.generate_syntax(clean_q, i)

            # عرض النتيجة
            st.success("✅ تم التوليد بنجاح!")
            st.code(full_syntax, language="spss")
            
            # تحميل
            st.download_button(
                "📥 تحميل ملف Syntax (.sps)",
                full_syntax,
                "Smart_Output.sps"
            )

        except Exception as e:
            st.error(f"❌ حدث خطأ: {e}")

if __name__ == "__main__":
    main()
