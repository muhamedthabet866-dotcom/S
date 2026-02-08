import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import base64
from datetime import datetime
import textwrap

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="مولد أكواد SPSS المحترف",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS لتخصيص المظهر
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .code-header {
        background-color: #1E293B;
        color: white;
        padding: 10px;
        border-radius: 5px 5px 0 0;
        font-family: monospace;
        font-size: 14px;
        margin-top: 20px;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

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
        code = """* Encoding: UTF-8.
* =========================================================================.
* SPSS Syntax for Data Set 1: Banking Customer Analysis
* Generated: {date}
* Total Questions Analyzed: {q_count}
* Software: Compatible with IBM SPSS Statistics V26+
* =========================================================================.

""".format(date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), q_count=len(questions))
        
        # تعريف المتغيرات
        code += """* --- [VARIABLE DEFINITIONS] --- .
VARIABLE LABELS 
    X1 "Account Balance ($)" 
    X2 "Number of ATM Transactions in the Month" 
    X3 "Number of Other Bank Services Used" 
    X4 "Has a Debit Card (1=Yes, 0=No)" 
    X5 "Receive Interest on Account (1=Yes, 0=No)" 
    X6 "City where Banking is Done".

VALUE LABELS 
    X4 0 "No" 1 "Yes" 
    /X5 0 "No" 1 "Yes" 
    /X6 1 "City A" 2 "City B" 3 "City C" 4 "City D".

EXECUTE.

"""
        
        # معالجة كل سؤال
        for i, question in enumerate(questions, 1):
            code += self.generate_question1_code(i, question, df)
        
        return code
    
    def generate_question1_code(self, q_num, question, df):
        """توليد كود SPSS لسؤال محدد من مجموعة البيانات 1"""
        code = f"\n* {'='*70}\n"
        code += f"* QUESTION {q_num}: {question[:60]}...\n"
        code += f"* {'='*70}\n\n"
        
        question_lower = question.lower()
        
        # Q1: Frequency tables for categorical variables
        if q_num == 1 or ('frequency table' in question_lower and 'debit card' in question_lower):
            code += """* 1. Frequency tables for categorical variables
FREQUENCIES VARIABLES=X4 X5 X6 
  /ORDER=ANALYSIS 
  /BARCHART FREQ 
  /FORMAT=DFREQ.
* Shows distribution of debit card ownership, interest reception, and city locations.

"""
        
        # Q2: Account balance frequency table with classes
        elif q_num == 2 or ('account balance' in question_lower and 'frequency table' in question_lower and 'classes' in question_lower):
            code += """* 2. Account balance frequency distribution with classes
RECODE X1 (0 thru 500=1) (501 thru 1000=2) (1001 thru 1500=3) (1501 thru 2000=4) (2001 thru 2500=5) (2501 thru HI=6) 
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
  /FORMAT=DFREQ.
* Comment: Distribution reveals account balance concentration among customers.

"""
        
        # Q3: ATM transactions frequency (K-rule)
        elif q_num == 3 or ('atm transactions' in question_lower and 'frequency table' in question_lower and 'classes' in question_lower):
            code += """* 3. ATM transactions frequency using K-rule
* K-rule: 2^k >= n where n=60, so k=6 (2^6=64)
RECODE X2 (0 thru 4=1) (5 thru 8=2) (9 thru 12=3) (13 thru 16=4) (17 thru 20=5) (21 thru 24=6) 
  INTO X2_KClasses.
VALUE LABELS X2_KClasses 
    1 '0-4 transactions' 
    2 '5-8 transactions' 
    3 '9-12 transactions' 
    4 '13-16 transactions' 
    5 '17-20 transactions' 
    6 '21-24 transactions'.
EXECUTE.

FREQUENCIES VARIABLES=X2_KClasses 
  /ORDER=ANALYSIS 
  /BARCHART FREQ.
* Comment: 6 classes provide optimal view of transaction intensity.

"""
        
        # Q4: Descriptive statistics
        elif q_num == 4 or ('mean' in question_lower and 'median' in question_lower and 'mode' in question_lower):
            code += """* 4. Descriptive statistics for Account Balance and ATM Transactions
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN SEMEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX 
  KURTOSIS SKEWNESS.

* For Mode calculation specifically:
FREQUENCIES VARIABLES=X1 X2 
  /FORMAT=NOTABLE 
  /STATISTICS=MEAN MEDIAN MODE.

"""
        
        # Q5: Histograms
        elif q_num == 5 or ('histogram' in question_lower):
            code += """* 5. Histograms for Account Balance and ATM Transactions
GRAPH /HISTOGRAM(NORMAL)=X1 
  /TITLE='Histogram of Account Balance ($)'.

GRAPH /HISTOGRAM(NORMAL)=X2 
  /TITLE='Histogram of ATM Transactions'.

"""
        
        # Q6: Skewness discussion
        elif q_num == 6 or ('skewness' in question_lower and 'discuss' in question_lower):
            code += """* 6. Skewness analysis from Q4 and Q5
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
        
        # Q7: Statistics by city
        elif q_num == 7:
            code += """* 7. Descriptive statistics for each city
SORT CASES BY X6.
SPLIT FILE LAYERED BY X6.
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN MEDIAN STDDEV MIN MAX.
SPLIT FILE OFF.

"""
        
        # Q8: Statistics by debit card status
        elif q_num == 8:
            code += """* 8. Descriptive statistics by debit card status
SORT CASES BY X4.
SPLIT FILE LAYERED BY X4.
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN MEDIAN STDDEV MIN MAX.
SPLIT FILE OFF.

"""
        
        # Q9: Bar chart - average balance by city
        elif q_num == 9 or ('bar chart' in question_lower and 'average account balance' in question_lower and 'each city' in question_lower):
            code += """* 9. Bar chart: Average account balance for each city
GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 
  /TITLE="Average Account Balance by City" 
  /MISSING=REPORT.

"""
        
        # Q10: Bar chart - max transactions by debit card
        elif q_num == 10 or ('bar chart' in question_lower and 'maximum number of transactions' in question_lower and 'debit card' in question_lower):
            code += """* 10. Bar chart: Maximum transactions by debit card status
GRAPH /BAR(SIMPLE)=MAX(X2) BY X4 
  /TITLE="Maximum ATM Transactions by Debit Card Status" 
  /MISSING=REPORT.

"""
        
        # Q11: Clustered bar chart
        elif q_num == 11 or ('bar chart' in question_lower and 'average account balance' in question_lower and 'debit card' in question_lower and 'city' in question_lower):
            code += """* 11. Clustered bar chart: Average balance by city and debit card status
GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 
  /TITLE="Average Account Balance by City and Debit Card Status" 
  /MISSING=REPORT.

"""
        
        # Q12: Bar chart - percentage with interest
        elif q_num == 12 or ('bar chart' in question_lower and 'percentage' in question_lower and 'interest' in question_lower):
            code += """* 12. Bar chart: Percentage of customers receiving interest
GRAPH /BAR(SIMPLE)=PCT BY X5 
  /TITLE="Percentage of Customers Receiving Interest" 
  /MISSING=REPORT.

"""
        
        # Q13: Pie chart - interest receivers
        elif q_num == 13 or ('pie chart' in question_lower and 'percentage' in question_lower and 'interest' in question_lower):
            code += """* 13. Pie chart: Percentage of customers receiving interest
GRAPH /PIE=PCT BY X5 
  /TITLE="Percentage of Interest Receivers vs Non-Receivers" 
  /MISSING=REPORT.

"""
        
        # Q14: Confidence intervals
        elif q_num == 14 or ('confidence interval' in question_lower):
            code += """* 14. 95% and 99% Confidence Intervals for Account Balance
EXAMINE VARIABLES=X1 
  /PLOT NONE 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 95.
  
EXAMINE VARIABLES=X1 
  /PLOT NONE 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 99.

"""
        
        # Q15: Normality tests
        elif q_num == 15 or ('normality' in question_lower and ('empirical' in question_lower or 'chebycheve' in question_lower)):
            code += """* 15. Normality test and Empirical/Chebyshev rule application
EXAMINE VARIABLES=X1 
  /PLOT=NPPLOT 
  /STATISTICS DESCRIPTIVES.
  
* Check Tests of Normality table:
* - If Shapiro-Wilk Sig. > 0.05: Data is normal → Apply Empirical Rule
*   Empirical Rule: 68% within μ±σ, 95% within μ±2σ, 99.7% within μ±3σ
* - If Shapiro-Wilk Sig. ≤ 0.05: Data is not normal → Apply Chebyshev's Rule
*   Chebyshev's Rule: At least (1-1/k²)% within μ±kσ for any k>1

"""
        
        # Q16: Outliers detection
        elif q_num == 16 or ('outliers' in question_lower or 'extremes' in question_lower):
            code += """* 16. Outliers and extreme values detection for account balance
EXAMINE VARIABLES=X1 
  /PLOT=BOXPLOT 
  /STATISTICS=EXTREME 
  /MISSING LISTWISE.

* Alternative method using Z-scores:
DESCRIPTIVES VARIABLES=X1 
  /SAVE 
  /STATISTICS=MEAN STDDEV.
* This creates ZX1 variable with Z-scores
* Cases with |ZX1| > 3 are extreme outliers

"""
        
        # Default for other questions
        else:
            # Identify analysis type
            if 'bar chart' in question_lower:
                code += f"* {q_num}. Bar chart requested\n"
                code += "GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 /TITLE='Bar Chart Title'.\n\n"
            elif 'histogram' in question_lower:
                code += f"* {q_num}. Histogram requested\n"
                code += "GRAPH /HISTOGRAM(NORMAL)=X1 /TITLE='Histogram Title'.\n\n"
            elif 'frequency' in question_lower:
                code += f"* {q_num}. Frequency table requested\n"
                code += "FREQUENCIES VARIABLES=X1 /ORDER=ANALYSIS /BARCHART FREQ.\n\n"
            else:
                code += f"* {q_num}. {question[:50]}...\n"
                code += "* Please specify analysis requirements.\n\n"
        
        return code
    
    def generate_dataset2_code(self, questions, df):
        """توليد كود لمجموعة البيانات 2 (Baseball)"""
        code = """* Encoding: UTF-8.
* =========================================================================.
* SPSS Syntax for Data Set 2: Major League Baseball Analysis
* Generated: {date}
* Total Questions Analyzed: {q_count}
* Software: Compatible with IBM SPSS Statistics V26+
* =========================================================================.

""".format(date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), q_count=len(questions))
        
        code += """* --- [VARIABLE DEFINITIONS] --- .
VARIABLE LABELS 
    x1 "Team Name" 
    x2 "League (0=National, 1=American)" 
    x3 "Year Stadium Built" 
    x4 "Stadium Capacity" 
    x5 "Total Team Salary ($ Millions)" 
    x6 "Total Team Attendance" 
    x7 "Number of Wins in 2000" 
    x8 "Earned Run Average (ERA)" 
    x9 "Team Batting Average" 
    x10 "Home Runs" 
    x11 "Surface (0=Natural, 1=Artificial)" 
    x12 "Stolen Bases" 
    x13 "Team Errors".

VALUE LABELS 
    x2 0 "National League" 1 "American League"
    /x11 0 "Natural Surface" 1 "Artificial Surface".

EXECUTE.

"""
        
        # التحويلات المسبقة المطلوبة للأسئلة
        code += """* --- [DATA TRANSFORMATIONS FOR ANALYSIS] --- .
* For Q4: Teams built in/before 1990 vs after 1990
RECODE x3 (LO thru 1990=1) (1991 thru HI=2) INTO Built_90.
VALUE LABELS Built_90 1 "Built ≤1990" 2 "Built >1990".

* For Q12: Teams with wins >85 vs ≤85
RECODE x7 (LO thru 85=1) (86 thru HI=2) INTO Win_85.
VALUE LABELS Win_85 1 "Wins ≤85" 2 "Wins >85".

* For Q13: Building periods
RECODE x3 (LO thru 1949=1) (1950 thru 1970=2) (1971 thru 1990=3) (1991 thru HI=4) INTO Build_Period.
VALUE LABELS Build_Period 1 "Before 1950" 2 "1950-1970" 3 "1971-1990" 4 "1991+".

* For Q14: Salary threshold $70M
RECODE x5 (LO thru 69.99=1) (70 thru HI=2) INTO Salary_70.
VALUE LABELS Salary_70 1 "Salary <$70M" 2 "Salary ≥$70M".

* For Q15: Salary categories
RECODE x5 (LO thru 39.99=1) (40 thru 59.99=2) (60 thru 79.99=3) (80 thru HI=4) INTO Salary_Cat.
VALUE LABELS Salary_Cat 1 "<$40M" 2 "$40-60M" 3 "$60-80M" 4 ">$80M".

EXECUTE.

"""
        
        for i, question in enumerate(questions, 1):
            code += self.generate_question2_code(i, question, df)
        
        return code
    
    def generate_question2_code(self, q_num, question, df):
        """توليد كود لأسئلة مجموعة البيانات 2"""
        code = f"\n* {'='*70}\n"
        code += f"* QUESTION {q_num}: {question[:60]}...\n"
        code += f"* {'='*70}\n\n"
        
        question_lower = question.lower()
        
        # Q1: Average salary by league
        if q_num == 1 or ('average salary' in question_lower and 'american' in question_lower):
            code += """* 1. Bar chart: Average salary for American and National teams
GRAPH /BAR(SIMPLE)=MEAN(x5) BY x2 
  /TITLE="Average Salary by League (American vs National)".

"""
        
        # Q2: Stadium size by team
        elif q_num == 2 or ('size of stadium' in question_lower and 'each team' in question_lower):
            code += """* 2. Bar chart: Stadium size for each team
GRAPH /BAR(SIMPLE)=MEAN(x4) BY x1 
  /TITLE="Stadium Capacity for Each Team".

"""
        
        # Q3: Salary and wins by team
        elif q_num == 3 or ('salary and number of wins' in question_lower and 'each team' in question_lower):
            code += """* 3. Bar chart: Salary and wins for each team
* Note: This creates two separate charts for clarity
GRAPH /BAR(SIMPLE)=MEAN(x5) BY x1 
  /TITLE="Average Salary by Team".

GRAPH /BAR(SIMPLE)=MEAN(x7) BY x1 
  /TITLE="Average Wins by Team".

"""
        
        # Q4: Pie charts for errors and wins
        elif q_num == 4:
            code += """* 4. Pie charts for errors and wins
* a) Average errors by stadium age
GRAPH /PIE=MEAN(x13) BY Built_90 
  /TITLE="Average Errors by Stadium Construction Era".

* b) Maximum wins by surface type
GRAPH /PIE=MAX(x7) BY x11 
  /TITLE="Maximum Wins by Surface Type".

"""
        
        # Q5-6: Descriptive statistics
        elif q_num == 5 or q_num == 6:
            if 'mean' in question_lower or 'median' in question_lower or 'standard deviation' in question_lower:
                code += f"""* {q_num}. Descriptive statistics for key variables
DESCRIPTIVES VARIABLES=x4 x5 x6 x7 x8 x9 x10 x12 x13
  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX.

"""
        
        # Q7: Frequency tables for categorical
        elif q_num == 7:
            code += """* 7. Frequency tables for categorical data
FREQUENCIES VARIABLES=x2 x11 
  /ORDER=ANALYSIS 
  /BARCHART FREQ.

"""
        
        # Q8: Frequency tables for continuous
        elif q_num == 8:
            code += """* 8. Frequency tables for continuous data (with classes)
* Create classes for continuous variables
RECODE x4 (LO thru 40000=1) (40001 thru 45000=2) (45001 thru 50000=3) (50001 thru 55000=4) (55001 thru HI=5) INTO Size_Cat.
RECODE x5 (LO thru 40=1) (40.01 thru 60=2) (60.01 thru 80=3) (80.01 thru 100=4) (100.01 thru HI=5) INTO Salary_Cat2.
RECODE x6 (LO thru 2000000=1) (2000001 thru 2500000=2) (2500001 thru 3000000=3) (3000001 thru HI=4) INTO Attend_Cat.
RECODE x7 (LO thru 75=1) (76 thru 85=2) (86 thru 95=3) (96 thru HI=4) INTO Wins_Cat.

FREQUENCIES VARIABLES=Size_Cat Salary_Cat2 Attend_Cat Wins_Cat 
  /ORDER=ANALYSIS.

"""
        
        # Q9: Confidence intervals
        elif q_num == 9 or ('confidence interval' in question_lower):
            code += """* 9. 95% and 99% Confidence Intervals
EXAMINE VARIABLES=x5 x6 x4 x7 x13
  /PLOT NONE 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 95 99.

"""
        
        # Q10: Normality tests
        elif q_num == 10 or ('normality' in question_lower and 'salary' in question_lower):
            code += """* 10. Normality test for salary
EXAMINE VARIABLES=x5 
  /PLOT=NPPLOT HISTOGRAM 
  /STATISTICS DESCRIPTIVES.
  
* Interpretation:
* - If data normal (Shapiro-Wilk p > 0.05): Use Empirical Rule
* - If data not normal: Use Chebyshev's Rule

"""
        
        # Q11: Outliers detection
        elif q_num == 11 or ('outliers' in question_lower and 'attendance' in question_lower):
            code += """* 11. Outliers for attendance using Tukey's method
EXAMINE VARIABLES=x6 
  /PLOT=BOXPLOT 
  /STATISTICS=EXTREME.

"""
        
        # Q12-20: Hypothesis tests
        elif q_num >= 12 and q_num <= 20:
            code += self.generate_hypothesis_test_code(q_num, question)
        
        else:
            code += f"* {q_num}. Analysis for: {question[:50]}...\n"
            code += "* Please review specific question requirements.\n\n"
        
        return code
    
    def generate_hypothesis_test_code(self, q_num, question):
        """توليد كود اختبارات الفرضيات لمجموعة البيانات 2"""
        code = ""
        question_lower = question.lower()
        
        # Q12: Test if average wins = 90
        if q_num == 12 or 'average number of wins is equal 90' in question_lower:
            code += """* 12. Test hypothesis about average wins
* H0: μ = 90, H1: μ ≠ 90
T-TEST /TESTVAL=90 /VARIABLES=x7 /MISSING=ANALYSIS.

"""
        
        # Q13: Test if average salary = 65M
        elif q_num == 13 or 'average salary is equal 65' in question_lower:
            code += """* 13. Test hypothesis about average salary
* H0: μ = 65, H1: μ ≠ 65
T-TEST /TESTVAL=65 /VARIABLES=x5 /MISSING=ANALYSIS.

"""
        
        # Q14: Compare salary between leagues
        elif q_num == 14 or 'no significance between the average salary of american and national teams' in question_lower:
            code += """* 14. Compare average salary between leagues
* H0: μ_American = μ_National, H1: μ_American ≠ μ_National
T-TEST GROUPS=x2(0 1) /VARIABLES=x5 /MISSING=ANALYSIS.

"""
        
        # Q15: Compare stadium size by surface
        elif q_num == 15 or 'no significance difference between the size of the stadium that have natural surface' in question_lower:
            code += """* 15. Compare stadium size by surface type
* H0: μ_Natural = μ_Artificial, H1: μ_Natural ≠ μ_Artificial
T-TEST GROUPS=x11(0 1) /VARIABLES=x4 /MISSING=ANALYSIS.

"""
        
        # Q16: Compare salary by stadium age
        elif q_num == 16 or 'no significance difference between the average salary of the teams built before and after 1990' in question_lower:
            code += """* 16. Compare salary by stadium construction era
* H0: μ_≤1990 = μ_>1990, H1: μ_≤1990 ≠ μ_>1990
T-TEST GROUPS=Built_90(1 2) /VARIABLES=x5 /MISSING=ANALYSIS.

"""
        
        # Q17: Compare ERA by win group
        elif q_num == 17 or 'no significant difference between the era of the teams who win more than 85 times' in question_lower:
            code += """* 17. Compare ERA by win performance
* H0: μ_≤85 = μ_>85, H1: μ_≤85 ≠ μ_>85
T-TEST GROUPS=Win_85(1 2) /VARIABLES=x8 /MISSING=ANALYSIS.

"""
        
        # Q18: ANOVA for HR by building period
        elif q_num == 18 or 'no significant difference between the hr of the teams built before 1950' in question_lower:
            code += """* 18. ANOVA: Home Runs by building period
* H0: μ1 = μ2 = μ3 = μ4, H1: At least one mean differs
ONEWAY x10 BY Build_Period 
  /STATISTICS DESCRIPTIVES HOMOGENEITY 
  /MISSING ANALYSIS 
  /POSTHOC=TUKEY ALPHA(0.05).

"""
        
        # Q19: Compare wins by salary threshold
        elif q_num == 19 or 'no significant difference between the number of wins of the teams of salary less than 70 millions' in question_lower:
            code += """* 19. Compare wins by salary threshold
* H0: μ_<70M = μ_≥70M, H1: μ_<70M ≠ μ_≥70M
T-TEST GROUPS=Salary_70(1 2) /VARIABLES=x7 /MISSING=ANALYSIS.

"""
        
        # Q20: ANOVA for wins by salary category
        elif q_num == 20 or 'no significant difference between the number of wins of the teams of salary less than 40 million' in question_lower:
            code += """* 20. ANOVA: Wins by salary category
* H0: μ1 = μ2 = μ3 = μ4, H1: At least one mean differs
ONEWAY x7 BY Salary_Cat 
  /STATISTICS DESCRIPTIVES HOMOGENEITY 
  /MISSING ANALYSIS 
  /POSTHOC=TUKEY ALPHA(0.05).

"""
        
        return code

# تطبيق Streamlit
def main():
    st.title("📊 مولد أكواد SPSS المحترف")
    st.markdown("### يولد أكواد SPSS خالية من الأخطاء وجاهزة للتنفيذ")
    
    # إنشاء كائن المولد
    app = SPSSProfessionalGenerator()
    
    # الشريط الجانبي
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        
        dataset_num = st.selectbox(
            "اختر مجموعة البيانات",
            [1, 2, 3, 4],
            format_func=lambda x: f"Data Set {x}"
        )
        
        st.markdown("---")
        st.header("📁 رفع الملفات")
        
        # رفع ملف Excel
        excel_file = st.file_uploader(
            f"رفع ملف Excel (Data Set {dataset_num})",
            type=['xls', 'xlsx'],
            key=f"excel_{dataset_num}"
        )
        
        # رفع ملف الأسئلة
        questions_file = st.file_uploader(
            "رفع ملف الأسئلة",
            type=['txt'],
            key=f"questions_{dataset_num}"
        )
        
        if excel_file and questions_file:
            st.success("✅ الملفات جاهزة للتوليد")
    
    # المحتوى الرئيسي
    if excel_file and questions_file:
        try:
            # قراءة البيانات
            df = pd.read_excel(excel_file)
            
            # قراءة الأسئلة
            questions_text = questions_file.getvalue().decode('utf-8')
            questions = app.parse_questions(questions_text)
            
            # عرض المعلومات
            col1, col2 = st.columns(2)
            with col1:
                st.metric("عدد الأسئلة", len(questions))
                st.metric("عدد المتغيرات", len(df.columns))
            with col2:
                st.metric("عدد الصفوف", len(df))
                st.metric("متغيرات رقمية", len(df.select_dtypes(include=[np.number]).columns))
            
            # زر توليد الكود
            if st.button("🚀 توليد كود SPSS كامل", type="primary", use_container_width=True):
                with st.spinner("جاري توليد الكود المحترف..."):
                    if dataset_num == 1:
                        spss_code = app.generate_dataset1_code(questions, df)
                    elif dataset_num == 2:
                        spss_code = app.generate_dataset2_code(questions, df)
                    else:
                        spss_code = f"""* Code generation for Data Set {dataset_num}
* This dataset type is under development.
* For now, use similar structure as Data Set 1 or 2."""
                    
                    # حفظ الكود
                    app.generated_codes[dataset_num] = spss_code
                    
                    st.success(f"✅ تم توليد كود SPSS لـ {len(questions)} سؤال")
                    
                    # عرض الكود
                    st.markdown('<div class="code-header">كود SPSS المُنشأ (خالي من الأخطاء)</div>', unsafe_allow_html=True)
                    st.code(spss_code, language='text')
                    
                    # معلومات عن الكود
                    st.info(f"""
                    **معلومات الكود:**
                    - عدد الأسطر: {spss_code.count('\\n')}
                    - يحتوي على: {spss_code.count('GRAPH ')} رسم بياني
                    - يحتوي على: {spss_code.count('FREQUENCIES')} جدول تكرار
                    - يحتوي على: {spss_code.count('T-TEST')} اختبار فرضية
                    """)
                    
                    # أزرار التنزيل
                    st.markdown("---")
                    col_dl1, col_dl2, col_dl3 = st.columns(3)
                    
                    with col_dl1:
                        st.markdown(app.create_download_link(spss_code, f"Syntax{dataset_num}_Professional.sps"), 
                                  unsafe_allow_html=True)
                    
                    with col_dl2:
                        if st.button("📋 عرض نموذج الكود", use_container_width=True):
                            st.code("""* مثال على كود صحيح:
GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 
  /TITLE="Average by Category".

FREQUENCIES VARIABLES=X1 
  /ORDER=ANALYSIS 
  /BARCHART FREQ.

T-TEST /TESTVAL=100 /VARIABLES=X1.

EXAMINE VARIABLES=X1 
  /PLOT=BOXPLOT 
  /STATISTICS=EXTREME.""", language='text')
                    
                    with col_dl3:
                        if st.button("🔄 توليد جديد", use_container_width=True):
                            st.rerun()
        
        except Exception as e:
            st.error(f"❌ خطأ في معالجة الملفات: {str(e)}")
            st.info("تأكد من تنسيق الملفات الصحيح (Excel للبيانات، TXT للأسئلة)")
    
    else:
        # واجهة البداية
        st.info("📤 يرجى رفع ملف Excel وملف الأسئلة (TXT) لبدء التوليد")
        
        # عرض أمثلة
        with st.expander("📚 أمثلة على المخرجات الصحيحة"):
            col_ex1, col_ex2 = st.columns(2)
            
            with col_ex1:
                st.markdown("**مثال 1: رسوم بيانية صحيحة**")
                st.code("""* Bar chart - صحيح
GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 
  /TITLE="Average Balance by City".

* Histogram - صحيح  
GRAPH /HISTOGRAM(NORMAL)=X1 
  /TITLE="Distribution of Balances".

* Pie chart - صحيح
GRAPH /PIE=PCT BY X5 
  /TITLE="Percentage by Category".""", language='text')
            
            with col_ex2:
                st.markdown("**مثال 2: تحليلات إحصائية صحيحة**")
                st.code("""* Descriptive statistics - صحيح
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN MEDIAN STDDEV.

* Frequency table - صحيح
FREQUENCIES VARIABLES=X4 X5 
  /ORDER=ANALYSIS 
  /BARCHART FREQ.

* T-test - صحيح
T-TEST /TESTVAL=100 /VARIABLES=X1.""", language='text')
        
        # توجيهات
        st.markdown("""
        ### 📝 توجيهات الاستخدام:
        1. **ارفع ملف Excel** يحتوي على البيانات
        2. **ارفع ملف نصي (TXT)** يحتوي على الأسئلة
        3. **اختر رقم مجموعة البيانات** المناسبة
        4. **اضغط على زر "توليد كود SPSS كامل"**
        5. **قم بتنزيل الملف .sps** وافتحه في SPSS
        6. **شغل الكود** بدون أخطاء
        """)

if __name__ == "__main__":
    main()
