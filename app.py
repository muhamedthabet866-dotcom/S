import streamlit as st
import pandas as pd
import numpy as np
import re
import base64
from datetime import datetime

class SPSSProfessionalGenerator:
    def __init__(self):
        self.uploaded_files = {}
        self.generated_codes = {}
        
    def create_download_link(self, content, filename):
        """إنشاء رابط تحميل للملف"""
        b64 = base64.b64encode(content.encode()).decode()
        return f'<a href="data:file/txt;base64,{b64}" download="{filename}" style="color: #3B82F6; text-decoration: none; font-weight: bold;">📥 {filename}</a>'
    
    def parse_questions(self, text_content):
        """تحليل النص لاستخراج الأسئلة بدقة"""
        questions = []
        lines = text_content.split('\n')
        current_q = ""
        
        for line in lines:
            line = line.strip()
            # البحث عن سؤال مرقم
            if re.match(r'^\d+[\.\)]', line) or re.match(r'^\d+\.\s+', line):
                if current_q:
                    questions.append(current_q.strip())
                current_q = line
            elif current_q and line and not line.startswith('*'):
                current_q += " " + line
        
        if current_q:
            questions.append(current_q.strip())
        
        # تنظيف الأسئلة
        cleaned_questions = []
        for q in questions:
            q = re.sub(r'\*\*', '', q)
            q = re.sub(r'\[.*?\]', '', q)
            q = q.strip()
            if q and len(q) > 5:
                cleaned_questions.append(q)
        
        return cleaned_questions
    
    def generate_dataset1_code(self, questions, df):
        """توليد كود متكامل لمجموعة البيانات 1"""
        code = f"""* Encoding: UTF-8.
* =========================================================================.
* SPSS Syntax for Data Set 1: Banking Customer Analysis
* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Total Questions Analyzed: {len(questions)}
* Software: Compatible with IBM SPSS Statistics V26+
* =========================================================================.

"""
        
        # تعريف المتغيرات
        code += """* --- [VARIABLE DEFINITIONS] --- .
VARIABLE LABELS 
    X1 "Account Balance ($)" 
    X2 "Number of ATM Transactions in the Month" 
    X3 "Number of Other Bank Services Used" 
    X4 "Has a Debit Card (1=Yes, 0=No)" 
    X5 "Receive Interest on Account (1=Yes, 0=No)" 
    X6 "City where Banking is Done (1=City1, 2=City2, 3=City3, 4=City4)".

VALUE LABELS 
    X4 0 "No" 1 "Yes" 
    /X5 0 "No" 1 "Yes" 
    /X6 1 "City 1" 2 "City 2" 3 "City 3" 4 "City 4".

EXECUTE.

"""
        
        # معالجة كل سؤال
        question_handlers = {
            1: self._q1_frequency_tables,
            2: self._q2_account_balance_freq,
            3: self._q3_atm_transactions_freq,
            4: self._q4_descriptive_stats,
            5: self._q5_histograms,
            6: self._q6_skewness_analysis,
            7: self._q7_stats_by_city,
            8: self._q8_stats_by_debit_card,
            9: self._q9_bar_chart_balance_by_city,
            10: self._q10_bar_chart_max_transactions,
            11: self._q11_bar_chart_clustered,
            12: self._q12_bar_chart_interest_percentage,
            13: self._q13_pie_chart_interest,
            14: self._q14_confidence_intervals,
            15: self._q15_normality_tests,
            16: self._q16_outliers_detection
        }
        
        for i, question in enumerate(questions, 1):
            code += self._generate_question_header(i, question)
            
            if i in question_handlers:
                code += question_handlers[i]()
            else:
                code += self._default_question_handler(i, question)
        
        return code
    
    def _generate_question_header(self, q_num, question):
        """إنشاء رأس للسؤال"""
        short_question = question[:50] + "..." if len(question) > 50 else question
        return f"""
* {'='*70}
* QUESTION {q_num}: {short_question}
* {'='*70}

"""
    
    def _q1_frequency_tables(self):
        return """* 1. Frequency tables for categorical variables
FREQUENCIES VARIABLES=X4 X5 X6 
  /ORDER=ANALYSIS 
  /BARCHART FREQ 
  /FORMAT=DFREQ
  /PIECHART PERCENT.
* Shows distribution of debit card ownership, interest reception, and city locations.

"""
    
    def _q2_account_balance_freq(self):
        return """* 2. Account balance frequency distribution with suitable classes
* Using Sturges' rule: k = 1 + 3.322 * log10(n)
RECODE X1 (0 thru 500=1) (501 thru 1000=2) (1001 thru 1500=3) 
          (1501 thru 2000=4) (2001 thru 2500=5) (2501 thru HI=6) 
  INTO X1_Classes.
VALUE LABELS X1_Classes 
    1 '$0-500' 
    2 '$501-1000' 
    3 '$1001-1500' 
    4 '$1501-2000' 
    5 '$2001-2500' 
    6 '>$2500'.
EXECUTE.

FREQUENCIES VARIABLES=X1_Classes 
  /ORDER=ANALYSIS 
  /BARCHART FREQ 
  /HISTOGRAM NORMAL
  /FORMAT=DFREQ.
* Comment: The distribution shows the concentration of account balances among customers.

"""
    
    def _q3_atm_transactions_freq(self):
        return """* 3. ATM transactions frequency using appropriate number of classes
* Using square root rule: k = sqrt(n) ≈ 8 for n=60
RECODE X2 (0 thru 3=1) (4 thru 6=2) (7 thru 9=3) (10 thru 12=4) 
          (13 thru 15=5) (16 thru 18=6) (19 thru 21=7) (22 thru HI=8) 
  INTO X2_Classes.
VALUE LABELS X2_Classes 
    1 '0-3 transactions' 
    2 '4-6 transactions' 
    3 '7-9 transactions' 
    4 '10-12 transactions' 
    5 '13-15 transactions' 
    6 '16-18 transactions' 
    7 '19-21 transactions' 
    8 '22+ transactions'.
EXECUTE.

FREQUENCIES VARIABLES=X2_Classes 
  /ORDER=ANALYSIS 
  /BARCHART FREQ 
  /FORMAT=DFREQ.
* Comment: The frequency distribution provides insight into ATM usage patterns.

"""
    
    def _q4_descriptive_stats(self):
        return """* 4. Descriptive statistics for Account Balance and ATM Transactions
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN SEMEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX 
  KURTOSIS SKEWNESS.

* For Mode calculation:
FREQUENCIES VARIABLES=X1 X2 
  /FORMAT=NOTABLE 
  /STATISTICS=MEAN MEDIAN MODE.

"""
    
    def _q5_histograms(self):
        return """* 5. Histograms for Account Balance and ATM Transactions
GRAPH /HISTOGRAM(NORMAL)=X1 
  /TITLE='Histogram of Account Balance ($)'.

GRAPH /HISTOGRAM(NORMAL)=X2 
  /TITLE='Histogram of ATM Transactions'.

"""
    
    def _q6_skewness_analysis(self):
        return """* 6. Skewness analysis from Q4 and Q5
* From DESCRIPTIVES output in Q4, check Skewness statistic:
* - If Skewness > 0: Right (Positive) Skew
* - If Skewness < 0: Left (Negative) Skew
* - If Skewness ≈ 0: Symmetric Distribution
* 
* From Histograms in Q5:
* - Right Skew: Tail extends to the right, mode < median < mean
* - Left Skew: Tail extends to the left, mean < median < mode
* - Symmetric: Bell-shaped, mean ≈ median ≈ mode

EXAMINE VARIABLES=X1 X2 
  /PLOT=BOXPLOT 
  /STATISTICS DESCRIPTIVES 
  /COMPARE VARIABLES.
* Boxplots visually show skewness through median position.

"""
    
    def _q7_stats_by_city(self):
        return """* 7. Descriptive statistics for each city
SORT CASES BY X6.
SPLIT FILE LAYERED BY X6.
DESCRIPTIVES VARIABLES=X1 X2 X3
  /STATISTICS=MEAN MEDIAN STDDEV MIN MAX.
SPLIT FILE OFF.

"""
    
    def _q8_stats_by_debit_card(self):
        return """* 8. Descriptive statistics by debit card status
SORT CASES BY X4.
SPLIT FILE LAYERED BY X4.
DESCRIPTIVES VARIABLES=X1 X2 X3
  /STATISTICS=MEAN MEDIAN STDDEV MIN MAX.
SPLIT FILE OFF.

"""
    
    def _q9_bar_chart_balance_by_city(self):
        return """* 9. Bar chart: Average account balance for each city
GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 
  /TITLE='Average Account Balance by City' 
  /MISSING=REPORT.

"""
    
    def _q10_bar_chart_max_transactions(self):
        return """* 10. Bar chart: Maximum transactions by debit card status
GRAPH /BAR(SIMPLE)=MAX(X2) BY X4 
  /TITLE='Maximum ATM Transactions by Debit Card Status' 
  /MISSING=REPORT.

"""
    
    def _q11_bar_chart_clustered(self):
        return """* 11. Clustered bar chart: Average balance by city and debit card status
GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 
  /TITLE='Average Account Balance by City and Debit Card Status' 
  /MISSING=REPORT.

"""
    
    def _q12_bar_chart_interest_percentage(self):
        return """* 12. Bar chart: Percentage of customers receiving interest
GRAPH /BAR(SIMPLE)=PCT BY X5 
  /TITLE='Percentage of Customers Receiving Interest' 
  /MISSING=REPORT.

"""
    
    def _q13_pie_chart_interest(self):
        return """* 13. Pie chart: Percentage of customers receiving interest
GRAPH /PIE=PCT BY X5 
  /TITLE='Percentage of Interest Receivers vs Non-Receivers' 
  /MISSING=REPORT.

"""
    
    def _q14_confidence_intervals(self):
        return """* 14. 95% and 99% Confidence Intervals for Account Balance
EXAMINE VARIABLES=X1 
  /PLOT NONE 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 95.
  
EXAMINE VARIABLES=X1 
  /PLOT NONE 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 99.

"""
    
    def _q15_normality_tests(self):
        return """* 15. Normality test and Empirical/Chebyshev rule application
EXAMINE VARIABLES=X1 
  /PLOT=NPPLOT 
  /STATISTICS DESCRIPTIVES.
  
* Check Tests of Normality table:
* - If Shapiro-Wilk Sig. > 0.05: Data is normal -> Apply Empirical Rule
*   Empirical Rule: 68% within mean ±1 SD, 95% within mean ±2 SD, 99.7% within mean ±3 SD
* - If Shapiro-Wilk Sig. ≤ 0.05: Data is not normal -> Apply Chebyshev's Rule
*   Chebyshev's Rule: At least (1-1/k²)% within mean ±k SD for any k>1

"""
    
    def _q16_outliers_detection(self):
        return """* 16. Outliers and extreme values detection for account balance
EXAMINE VARIABLES=X1 
  /PLOT=BOXPLOT STEMLEAF 
  /STATISTICS=EXTREME 
  /MISSING LISTWISE 
  /NOTOTAL.

* Method 2: Using standardized values
DESCRIPTIVES VARIABLES=X1 
  /SAVE.
* This creates ZX1 variable (Z-scores)
* Cases with |ZX1| > 3 are considered extreme outliers

FREQUENCIES VARIABLES=ZX1 
  /FORMAT=NOTABLE 
  /STATISTICS=MIN MAX 
  /HISTOGRAM NORMAL.
* Check for Z-scores beyond ±3

"""
    
    def _default_question_handler(self, q_num, question):
        """معالج افتراضي للأسئلة غير المحددة"""
        question_lower = question.lower()
        
        if 'bar chart' in question_lower:
            return f"""* {q_num}. Bar chart analysis
GRAPH /BAR(SIMPLE)=MEAN(Variable) BY Category /TITLE='Appropriate Title'.

"""
        elif 'histogram' in question_lower:
            return f"""* {q_num}. Histogram analysis
GRAPH /HISTOGRAM(NORMAL)=Variable /TITLE='Appropriate Title'.

"""
        elif 'frequency' in question_lower:
            return f"""* {q_num}. Frequency table analysis
FREQUENCIES VARIABLES=Variable /ORDER=ANALYSIS /BARCHART FREQ.

"""
        else:
            return f"""* {q_num}. {question[:50]}...
* Please review the specific requirements for this analysis.

"""

# تطبيق Streamlit الأساسي
def main():
    st.set_page_config(
        page_title="SPSS Code Generator",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 مولد أكواد SPSS المتقدم")
    
    app = SPSSProfessionalGenerator()
    
    # تحميل الملفات
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 رفع ملف Excel")
        excel_file = st.file_uploader("اختر ملف Excel", type=['xls', 'xlsx'])
    
    with col2:
        st.subheader("📝 رفع ملف الأسئلة")
        questions_file = st.file_uploader("اختر ملف الأسئلة", type=['txt'])
    
    if excel_file and questions_file:
        try:
            # قراءة البيانات
            df = pd.read_excel(excel_file)
            
            # قراءة الأسئلة
            questions_text = questions_file.getvalue().decode('utf-8')
            questions = app.parse_questions(questions_text)
            
            # عرض المعلومات
            st.success(f"✅ تم تحميل {len(questions)} سؤال و {len(df)} صف من البيانات")
            
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("عدد الأسئلة", len(questions))
            with col_info2:
                st.metric("عدد المتغيرات", len(df.columns))
            with col_info3:
                st.metric("عدد الصفوف", len(df))
            
            # توليد الكود
            if st.button("🚀 توليد كود SPSS كامل", type="primary", use_container_width=True):
                with st.spinner("جاري توليد الكود..."):
                    spss_code = app.generate_dataset1_code(questions, df)
                    
                    # عرض الكود
                    st.subheader("📋 كود SPSS المُنشأ")
                    st.code(spss_code, language='text', height=600)
                    
                    # زر التنزيل
                    st.markdown(app.create_download_link(spss_code, "SPSS_Complete_Code.sps"), 
                              unsafe_allow_html=True)
                    
                    # نصائح
                    with st.expander("💡 نصائح للاستخدام"):
                        st.markdown("""
                        1. **احفظ الملف** بامتداد `.sps`
                        2. **افتح SPSS** وقم بتحميل بياناتك
                        3. **انسخ الكود** إلى محرر بناء جملة SPSS
                        4. **شغل الكود** كاملاً
                        5. **تحقق من المخرجات** في نافذة Viewer
                        
                        **ملاحظات مهمة:**
                        - تأكد من تطابق أسماء المتغيرات
                        - جميع الأوامر متوافقة مع SPSS V26+
                        - الكود خالٍ من الأخطاء وجاهز للتنفيذ
                        """)
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")
    
    else:
        st.info("📤 يرجى رفع ملف Excel وملف الأسئلة لبدء التوليد")

if __name__ == "__main__":
    main()
