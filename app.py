import streamlit as st
import pandas as pd
import re
from io import StringIO
import docx2txt

# -----------------------------------------------------------------------------
# 1. تضمين بيانات ملف القواعد (لضمان عمل الكود حتى لو لم يرفع المستخدم الملف)
# -----------------------------------------------------------------------------
DEFAULT_RULES_CSV = """Keyword,Category,Syntax_Template
frequency,Descriptive,FREQUENCIES VARIABLES={vars} /ORDER=ANALYSIS.
count,Descriptive,FREQUENCIES VARIABLES={vars} /ORDER=ANALYSIS.
mean,Descriptive,DESCRIPTIVES VARIABLES={vars} /STATISTICS=MEAN STDDEV MIN MAX.
average,Descriptive,DESCRIPTIVES VARIABLES={vars} /STATISTICS=MEAN STDDEV MIN MAX.
median,Descriptive,FREQUENCIES VARIABLES={vars} /FORMAT=NOTABLE /STATISTICS=MEDIAN.
mode,Descriptive,FREQUENCIES VARIABLES={vars} /FORMAT=NOTABLE /STATISTICS=MODE.
std dev,Descriptive,DESCRIPTIVES VARIABLES={vars} /STATISTICS=STDDEV.
variance,Descriptive,DESCRIPTIVES VARIABLES={vars} /STATISTICS=VARIANCE.
range,Descriptive,DESCRIPTIVES VARIABLES={vars} /STATISTICS=RANGE.
histogram,Graphs,GRAPH /HISTOGRAM={vars}.
bar chart,Graphs,GRAPH /BAR(SIMPLE)=MEAN({num_var}) BY {cat_var}.
pie chart,Graphs,GRAPH /PIE=COUNT BY {cat_var}.
correlation,Relation,CORRELATIONS /VARIABLES={vars} /PRINT=TWOTAIL NOSIG.
relationship,Relation,CORRELATIONS /VARIABLES={vars} /PRINT=TWOTAIL NOSIG.
regression,Modeling,REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA /CRITERIA=PIN(.05) POUT(.10) /NOORIGIN /DEPENDENT {dep_var} /METHOD=ENTER {indep_vars}.
predict,Modeling,REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA /CRITERIA=PIN(.05) POUT(.10) /NOORIGIN /DEPENDENT {dep_var} /METHOD=ENTER {indep_vars}.
impact,Modeling,REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA /CRITERIA=PIN(.05) POUT(.10) /NOORIGIN /DEPENDENT {dep_var} /METHOD=ENTER {indep_vars}.
effect,Modeling,REGRESSION /MISSING LISTWISE /STATISTICS COEFF OUTS R ANOVA /CRITERIA=PIN(.05) POUT(.10) /NOORIGIN /DEPENDENT {dep_var} /METHOD=ENTER {indep_vars}.
t-test,T-Test,T-TEST GROUPS={cat_var}(1 2) /MISSING=ANALYSIS /VARIABLES={num_var} /CRITERIA=CI(.95).
difference between two,T-Test,T-TEST GROUPS={cat_var}(1 2) /MISSING=ANALYSIS /VARIABLES={num_var} /CRITERIA=CI(.95).
anova,ANOVA,ONEWAY {num_var} BY {cat_var} /STATISTICS DESCRIPTIVES /MISSING ANALYSIS /POSTHOC=TUKEY ALPHA(0.05).
difference among,ANOVA,ONEWAY {num_var} BY {cat_var} /STATISTICS DESCRIPTIVES /MISSING ANALYSIS /POSTHOC=TUKEY ALPHA(0.05).
normality,Testing,EXAMINE VARIABLES={vars} /PLOT BOXPLOT STEMLEAF NPPLOT /COMPARE GROUPS /STATISTICS DESCRIPTIVES /CINTERVAL 95 /MISSING LISTWISE /NOTOTAL.
test normal,Testing,EXAMINE VARIABLES={vars} /PLOT BOXPLOT STEMLEAF NPPLOT /COMPARE GROUPS /STATISTICS DESCRIPTIVES /CINTERVAL 95 /MISSING LISTWISE /NOTOTAL.
"""

# -----------------------------------------------------------------------------
# 2. فئة المعالجة الذكية (Smart Engine)
# -----------------------------------------------------------------------------
class SmartSPSSGenerator:
    def __init__(self, rules_df, data_df):
        self.rules = rules_df
        self.df = data_df
        self.columns = list(data_df.columns) if data_df is not None else []
        
        # تصنيف الأعمدة تلقائياً (رقمية vs نصية/فئوية)
        self.num_cols = []
        self.cat_cols = []
        if self.df is not None:
            for col in self.df.columns:
                if pd.api.types.is_numeric_dtype(self.df[col]) and self.df[col].nunique() > 10:
                    self.num_cols.append(col)
                else:
                    self.cat_cols.append(col)

    def find_mentioned_variables(self, text):
        """البحث عن المتغيرات الموجودة في النص ومطابقتها مع أعمدة الإكسل"""
        found = []
        text_lower = text.lower()
        
        # ترتيب الأعمدة حسب الطول (الأطول أولاً) لتجنب التطابق الجزئي الخاطئ
        sorted_cols = sorted(self.columns, key=len, reverse=True)
        
        for col in sorted_cols:
            # البحث عن اسم العمود ككلمة كاملة
            pattern = r'\b' + re.escape(str(col).lower()) + r'\b'
            if re.search(pattern, text_lower):
                found.append(col)
        
        return found

    def get_best_rule(self, text):
        """تحديد القاعدة المناسبة بناءً على الكلمات المفتاحية"""
        text_lower = text.lower()
        best_rule = None
        max_score = 0
        
        for idx, row in self.rules.iterrows():
            keyword = str(row['Keyword']).lower()
            if keyword in text_lower:
                # نعطي أولوية للكلمة الأطول (مثلاً "independent t-test" أفضل من "t-test")
                score = len(keyword)
                if score > max_score:
                    max_score = score
                    best_rule = row
        
        return best_rule

    def fill_template(self, template, found_vars):
        """تعبئة القالب بالمتغيرات المكتشفة بذكاء"""
        syntax = template
        
        # تصنيف المتغيرات المكتشفة
        found_num = [v for v in found_vars if v in self.num_cols]
        found_cat = [v for v in found_vars if v in self.cat_cols]
        
        # إذا لم نجد تصنيفاً دقيقاً، نعتبر الكل رقمي افتراضياً
        if not found_num and not found_cat:
            found_num = found_vars
        
        # 1. تعويض {vars} - قائمة عامة
        if "{vars}" in syntax:
            vars_str = " ".join(found_vars) if found_vars else "ALL_VARS"
            syntax = syntax.replace("{vars}", vars_str)
            
        # 2. تعويض {num_var} - متغير رقمي (مثل الراتب، العمر)
        if "{num_var}" in syntax:
            val = found_num[0] if found_num else (found_vars[0] if found_vars else "NUM_VAR")
            syntax = syntax.replace("{num_var}", val)

        # 3. تعويض {cat_var} - متغير فئوي/تجميعي (مثل الجنس، المدينة)
        if "{cat_var}" in syntax:
            val = found_cat[0] if found_cat else (found_vars[-1] if found_vars else "GROUP_VAR")
            syntax = syntax.replace("{cat_var}", val)
            
        # 4. تعويض {dep_var} و {indep_vars} للانحدار
        if "{dep_var}" in syntax:
            # افتراض: المتغير الأول هو التابع، والباقي مستقل
            dep = found_vars[0] if found_vars else "Y"
            indep = " ".join(found_vars[1:]) if len(found_vars) > 1 else "X"
            syntax = syntax.replace("{dep_var}", dep).replace("{indep_vars}", indep)
            
        return syntax

    def generate_syntax(self, question_text, q_num):
        """توليد الكود لسؤال واحد"""
        # 1. استخراج المتغيرات
        found_vars = self.find_mentioned_variables(question_text)
        
        # 2. تحديد القاعدة
        rule = self.get_best_rule(question_text)
        
        header = f"* --------------------------------------------------.\n* Q{q_num}: {question_text[:60]}...\n"
        
        if not rule is None:
            # 3. تعبئة القالب
            template = rule['Syntax_Template']
            
            # تنظيف القالب من أسماء المتغيرات القديمة إذا كانت موجودة في ملف القواعد
            # (نستبدل var, var1, group بـ {vars} و {cat_var} لتوحيد المعالجة)
            template = template.replace("{var}", "{vars}").replace("{group}", "{cat_var}")
            template = template.replace("{var1}", "{vars}").replace("{var2}", "") # Correlation usually takes list
            template = template.replace("{y}", "{dep_var}").replace("{x}", "{indep_vars}")
            template = template.replace("{x_list}", "{indep_vars}")

            code = self.fill_template(template, found_vars)
            
            # التحقق من وجود متغيرات
            if not found_vars:
                 header += f"* WARNING: No variables matched from Excel columns! Check spelling.\n"
            
            return header + code + "\n"
        else:
            return header + "* ANALYSIS NOT RECOGNIZED. Please check keywords in rules file.\n"

# -----------------------------------------------------------------------------
# 3. واجهة التطبيق
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="SPSS Smart Solver", layout="wide")
    st.title("🧠 المحلل الإحصائي الذكي (Smart SPSS Solver)")
    st.markdown("""
    هذا التطبيق يفهم سياق الأسئلة ويقوم بربطها بمتغيرات ملف الإكسل تلقائياً.
    1. يقرأ القواعد الإحصائية.
    2. يبحث عن أسماء الأعمدة (مثل `Income`, `Age`) داخل نص السؤال.
    3. يولد كود SPSS الصحيح بالمتغيرات الصحيحة.
    """)

    # إعداد ملف القواعد
    try:
        rules_df = pd.read_csv("spss_rules.csv")
    except:
        # استخدام القواعد الافتراضية إذا لم يوجد الملف
        rules_df = pd.read_csv(StringIO(DEFAULT_RULES_CSV))

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. ملف البيانات (Excel)")
        data_file = st.file_uploader("ارفع ملف الإكسل الذي يحتوي على البيانات", type=['xlsx', 'xls'])
    
    with col2:
        st.subheader("2. ملف الأسئلة (Word/Txt)")
        q_file = st.file_uploader("ارفع ملف الأسئلة", type=['docx', 'txt'])

    if data_file and q_file:
        try:
            # قراءة البيانات
            df = pd.read_excel(data_file)
            st.success(f"✅ تم تحميل البيانات. الأعمدة المكتشفة: {list(df.columns)}")
            
            # قراءة الأسئلة
            if q_file.name.endswith('.docx'):
                text = docx2txt.process(q_file)
            else:
                text = q_file.getvalue().decode("utf-8")
            
            # تقسيم الأسئلة
            questions = [q.strip() for q in re.split(r'\n(?=\d+[\.\)]|Q\d+)', text) if q.strip()]
            
            # المعالجة
            engine = SmartSPSSGenerator(rules_df, df)
            
            full_syntax = """* Encoding: UTF-8.
* Smart SPSS Syntax Generator.
* Generated based on uploaded Excel variables and Questions.

"""
            # تعريف المتغيرات (اختياري)
            full_syntax += "VARIABLE LABELS " + " ".join([f'{col} "{col}"' for col in df.columns]) + ".\n\n"

            for i, q in enumerate(questions, 1):
                # تنظيف نص السؤال من الأرقام في البداية
                clean_q = re.sub(r'^(\d+[\.\)]|Q\d+)\s*', '', q)
                full_syntax += engine.generate_syntax(clean_q, i)
            
            st.subheader("📝 الكود المولد (Syntax):")
            st.code(full_syntax, language="spss")
            
            st.download_button(
                "💾 تحميل ملف Syntax (.sps)",
                full_syntax,
                "Smart_Solution.sps",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"حدث خطأ: {str(e)}")
            st.write("التفاصيل:", e)

if __name__ == "__main__":
    main()
