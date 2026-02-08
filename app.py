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
    page_title="مولد أكواد SPSS المتقدم",
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
    .sub-header {
        font-size: 1.8rem;
        color: #1E40AF;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .section-box {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1.5rem;
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
    .arabic-text {
        direction: rtl;
        text-align: right;
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
            # إزالة التنسيق الزائد
            q = re.sub(r'\*\*', '', q)
            q = re.sub(r'\[.*?\]', '', q)
            q = q.strip()
            if q:
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
            code += """FREQUENCIES VARIABLES=X4 X5 X6 
  /ORDER=ANALYSIS 
  /BARCHART FREQ 
  /FORMAT=DFREQ.
* Interpretation: Shows distribution of debit card ownership, interest reception, and city locations.

"""
        
        # Q2: Account balance frequency table with classes
        elif q_num == 2 or ('account balance' in question_lower and 'frequency table' in question_lower):
            # حساب الحدود المناسبة
            if df is not None and 'X1' in df.columns:
                min_val = df['X1'].min()
                max_val = df['X1'].max()
                interval = (max_val - min_val) / 5
                code += f"""* Creating 5 classes for account balance
COMPUTE X1_Class = TRUNC((X1 - {min_val}) / {interval}) + 1.
RECODE X1_Class (1=1) (2=2) (3=3) (4=4) (5=5) (6=6) (7=7) (8=8) (9=9) (10=10).
VALUE LABELS X1_Class 
    1 '${min_val:.0f}-${min_val+interval:.0f}' 
    2 '${min_val+interval:.0f}-${min_val+2*interval:.0f}'
    3 '${min_val+2*interval:.0f}-${min_val+3*interval:.0f}'
    4 '${min_val+3*interval:.0f}-${min_val+4*interval:.0f}'
    5 '${min_val+4*interval:.0f}-${max_val:.0f}'.
FREQUENCIES VARIABLES=X1_Class 
  /ORDER=ANALYSIS 
  /BARCHART FREQ.
* Comment: This frequency distribution shows the concentration of account balances among customers.

"""
            else:
                code += """* Standard class intervals for account balance
RECODE X1 (0 thru 500=1) (501 thru 1000=2) (1001 thru 1500=3) (1501 thru 2000=4) (2001 thru HI=5) 
  INTO X1_Classes.
VALUE LABELS X1_Classes 
    1 '$0-500' 
    2 '$501-1000' 
    3 '$1001-1500' 
    4 '$1501-2000' 
    5 '>$2000'.
FREQUENCIES VARIABLES=X1_Classes /ORDER=ANALYSIS.
* Comment: Distribution reveals wealth concentration among bank clients.

"""
        
        # Q3: ATM transactions frequency (K-rule)
        elif q_num == 3 or ('atm transactions' in question_lower and 'frequency table' in question_lower):
            code += """* Using K-rule: 2^k >= n where n=60, so k=6 (2^6=64)
RECODE X2 (0 thru 4=1) (5 thru 8=2) (9 thru 12=3) (13 thru 16=4) (17 thru 20=5) (21 thru HI=6) 
  INTO X2_KClasses.
VALUE LABELS X2_KClasses 
    1 '0-4 transactions' 
    2 '5-8 transactions' 
    3 '9-12 transactions' 
    4 '13-16 transactions' 
    5 '17-20 transactions' 
    6 '21+ transactions'.
FREQUENCIES VARIABLES=X2_KClasses 
  /ORDER=ANALYSIS 
  /BARCHART FREQ.
* Comment: Based on K-rule, 6 classes provide optimal view of transaction intensity.

"""
        
        # Q4: Descriptive statistics
        elif q_num == 4 or ('mean' in question_lower and 'median' in question_lower and 'mode' in question_lower):
            code += """* Descriptive Statistics for Account Balance and ATM Transactions
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN SEMEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX 
  KURTOSIS SKEWNESS.

* Alternative with FREQUENCIES for Mode:
FREQUENCIES VARIABLES=X1 X2 
  /FORMAT=NOTABLE 
  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX SKEWNESS.

"""
        
        # Q5: Histograms
        elif q_num == 5 or ('histogram' in question_lower):
            code += """* Histogram for Account Balance with Normal Curve
GRAPH /HISTOGRAM(NORMAL)=X1 
  /TITLE='Histogram of Account Balance ($)'.

* Histogram for ATM Transactions
GRAPH /HISTOGRAM(NORMAL)=X2 
  /TITLE='Histogram of ATM Transactions'.

"""
        
        # Q6: Skewness discussion
        elif q_num == 6 or ('skewness' in question_lower and 'discuss' in question_lower):
            code += """* Skewness Analysis
EXAMINE VARIABLES=X1 X2 
  /PLOT=BOXPLOT HISTOGRAM NPPLOT 
  /STATISTICS=DESCRIPTIVES 
  /COMPARE VARIABLES.
* Interpretation: 
* 1. If Mean > Median → Right (Positive) Skew
* 2. If Mean < Median → Left (Negative) Skew  
* 3. If Mean ≈ Median → Symmetric Distribution
* 4. Skewness > 0 → Right Skew, Skewness < 0 → Left Skew

"""
        
        # Q7: Statistics by city
        elif q_num == 7:
            code += """* Descriptive Statistics for Each City
SORT CASES BY X6.
SPLIT FILE LAYERED BY X6.
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN MEDIAN STDDEV MIN MAX.
SPLIT FILE OFF.

"""
        
        # Q8: Statistics by debit card status
        elif q_num == 8:
            code += """* Descriptive Statistics by Debit Card Status
SORT CASES BY X4.
SPLIT FILE LAYERED BY X4.
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN MEDIAN STDDEV MIN MAX.
SPLIT FILE OFF.

"""
        
        # Q9: Bar chart - average balance by city
        elif q_num == 9 or ('bar chart' in question_lower and 'average account balance' in question_lower and 'each city' in question_lower):
            code += """* Bar Chart: Average Account Balance by City
GGRAPH
  /GRAPHDATASET NAME="graphdataset" VARIABLES=X6 MEAN(X1)[name="MEAN_X1"] 
  /GRAPHSPEC SOURCE=INLINE.
BEGIN GPL
  SOURCE: s=userSource(id("graphdataset"))
  DATA: X6=col(source(s), name("X6"), unit.category())
  DATA: MEAN_X1=col(source(s), name("MEAN_X1"))
  GUIDE: axis(dim(1), label("City"))
  GUIDE: axis(dim(2), label("Average Account Balance ($)"))
  ELEMENT: interval(position(X6*MEAN_X1))
END GPL.

* Simple bar chart alternative:
GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 
  /TITLE="Average Account Balance by City".

"""
        
        # Q10: Bar chart - max transactions by debit card
        elif q_num == 10 or ('bar chart' in question_lower and 'maximum number of transactions' in question_lower):
            code += """* Bar Chart: Maximum Transactions by Debit Card Status
GRAPH /BAR(SIMPLE)=MAX(X2) BY X4 
  /TITLE="Maximum ATM Transactions by Debit Card Status".

"""
        
        # Q11: Clustered bar chart
        elif q_num == 11 or ('bar chart' in question_lower and 'average account balance' in question_lower and 'debit card' in question_lower):
            code += """* Clustered Bar Chart: Average Balance by City and Debit Card Status
GGRAPH
  /GRAPHDATASET NAME="graphdataset" VARIABLES=X6 X4 MEAN(X1)[name="MEAN_X1"] 
  /GRAPHSPEC SOURCE=INLINE.
BEGIN GPL
  SOURCE: s=userSource(id("graphdataset"))
  DATA: X6=col(source(s), name("X6"), unit.category())
  DATA: X4=col(source(s), name("X4"), unit.category())
  DATA: MEAN_X1=col(source(s), name("MEAN_X1"))
  GUIDE: axis(dim(1), label("City"))
  GUIDE: axis(dim(2), label("Average Account Balance ($)"))
  GUIDE: legend(aesthetic(aesthetic.color.interior), label("Debit Card"))
  ELEMENT: interval.dodge(position(X6*MEAN_X1), color.interior(X4))
END GPL.

* Alternative clustered bar:
GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 
  /TITLE="Average Account Balance by City and Debit Card Status".

"""
        
        # Q12: Bar chart - percentage with interest
        elif q_num == 12 or ('bar chart' in question_lower and 'percentage' in question_lower and 'interest' in question_lower):
            code += """* Bar Chart: Percentage of Customers Receiving Interest
GRAPH /BAR(SIMPLE)=PCT BY X5 
  /TITLE="Percentage of Customers Receiving Interest".

"""
        
        # Q13: Pie chart - interest receivers
        elif q_num == 13 or ('pie chart' in question_lower and 'percentage' in question_lower and 'interest' in question_lower):
            code += """* Pie Chart: Percentage of Customers Receiving Interest
GRAPH /PIE=PCT BY X5 
  /TITLE="Percentage of Interest Receivers vs Non-Receivers".

"""
        
        # Q14: Confidence intervals
        elif q_num == 14 or ('confidence interval' in question_lower):
            code += """* 95% and 99% Confidence Intervals for Account Balance
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
            code += """* Normality Tests for Account Balance
EXAMINE VARIABLES=X1 
  /PLOT=NPPLOT 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 95.
  
* Shapiro-Wilk Test for Normality
DATASET DECLARE NormalityTest.
OMS /SELECT TABLES /IF COMMANDS=['Explore'] SUBTYPES=['Tests of Normality']
  /DESTINATION FORMAT=SAV NUMBERED=TableNumber_ 
  OUTFILE='NormalityTest' VIEWER=YES.
EXAMINE VARIABLES=X1 /PLOT NPPLOT.
OMSEND.

* Interpretation:
* 1. If Shapiro-Wilk Sig. > 0.05 → Data is normal → Apply Empirical Rule
* 2. If Shapiro-Wilk Sig. ≤ 0.05 → Data is not normal → Apply Chebyshev's Rule
* Empirical Rule: 68-95-99.7% within 1-2-3 SD from mean
* Chebyshev's Rule: At least (1-1/k²)% within k SD from mean

"""
        
        # Q16: Outliers detection
        elif q_num == 16 or ('outliers' in question_lower or 'extremes' in question_lower):
            code += """* Detecting Outliers and Extreme Values for Account Balance
EXAMINE VARIABLES=X1 
  /PLOT=BOXPLOT STEMLEAF 
  /STATISTICS=EXTREME 
  /COMPARE VARIABLES 
  /MISSING LISTWISE 
  /NOTOTAL.

* Identify specific outliers
COMPUTE Z_X1 = (X1 - MEAN(X1)) / SD(X1).
EXECUTE.
FREQUENCIES VARIABLES=Z_X1 
  /FORMAT=NOTABLE 
  /STATISTICS=MIN MAX 
  /HISTOGRAM NORMAL.
* Values with |Z-score| > 3 are considered extreme outliers

"""
        
        # For any other question, provide template
        else:
            # Identify what type of analysis is needed
            if 'bar chart' in question_lower:
                code += "* Bar chart analysis required.\n"
                code += "GRAPH /BAR(SIMPLE)=MEAN(Variable) BY CategoryVariable /TITLE='Your Title'.\n\n"
            elif 'pie chart' in question_lower:
                code += "* Pie chart analysis required.\n"
                code += "GRAPH /PIE=PCT BY CategoryVariable /TITLE='Your Title'.\n\n"
            elif 'histogram' in question_lower:
                code += "* Histogram analysis required.\n"
                code += "GRAPH /HISTOGRAM(NORMAL)=Variable /TITLE='Your Title'.\n\n"
            elif 'frequency' in question_lower:
                code += "* Frequency table analysis required.\n"
                code += "FREQUENCIES VARIABLES=Variable /ORDER=ANALYSIS /BARCHART FREQ.\n\n"
            else:
                code += f"* Analysis for: {question[:50]}...\n"
                code += "* Manual analysis required. Review question details.\n\n"
        
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
            code += """* Bar Chart: Average Salary by League
GRAPH /BAR(SIMPLE)=MEAN(x5) BY x2 
  /TITLE="Average Salary by League (American vs National)".

"""
        
        # Q2: Stadium size by team
        elif q_num == 2 or ('size of stadium' in question_lower):
            code += """* Bar Chart: Stadium Size for Each Team
GRAPH /BAR(SIMPLE)=MEAN(x4) BY x1 
  /TITLE="Stadium Capacity for Each Team" 
  /CATEGORY ORDER=ASCENDING.

"""
        
        # Q3: Salary and wins by team
        elif q_num == 3 or ('salary and number of wins' in question_lower):
            code += """* Grouped Bar Chart: Salary and Wins by Team
GGRAPH
  /GRAPHDATASET NAME="graphdataset" VARIABLES=x1 MEAN(x5)[name="SALARY"] MEAN(x7)[name="WINS"] 
  /GRAPHSPEC SOURCE=INLINE.
BEGIN GPL
  SOURCE: s=userSource(id("graphdataset"))
  DATA: x1=col(source(s), name("x1"), unit.category())
  DATA: SALARY=col(source(s), name("SALARY"))
  DATA: WINS=col(source(s), name("WINS"))
  TRANS: SALARY_scaled = eval(SALARY / 10)  # Scale for better visualization
  GUIDE: axis(dim(1), label("Team"))
  GUIDE: axis(dim(2), label("Values"))
  GUIDE: legend(aesthetic(aesthetic.color.interior), label("Metric"))
  ELEMENT: interval(position(x1*SALARY_scaled), color.interior(color.red))
  ELEMENT: interval(position(x1*WINS), color.interior(color.blue))
END GPL.

"""
        
        # Q4: Pie charts for errors and wins
        elif q_num == 4:
            code += """* Pie Chart 1: Average Errors by Stadium Age
RECODE x3 (LO thru 1990=1) (1991 thru HI=2) INTO Built_Era.
VALUE LABELS Built_Era 1 "Built ≤1990" 2 "Built >1990".
GRAPH /PIE=MEAN(x13) BY Built_Era 
  /TITLE="Average Errors by Stadium Construction Era".

* Pie Chart 2: Maximum Wins by Surface Type
GRAPH /PIE=MAX(x7) BY x11 
  /TITLE="Maximum Wins by Surface Type".

"""
        
        # Q5: Pie chart for labor force
        elif q_num == 5 and 'labor forth' in question_lower:
            code += """* Pie Chart: Average Labor Force by Region
GRAPH /PIE=MEAN(x10) BY x11 
  /TITLE="Average Labor Force by Region".

"""
        
        # Q6: Descriptive statistics
        elif q_num == 6 or ('mean' in question_lower and 'median' in question_lower and 'mode' in question_lower):
            code += """* Descriptive Statistics for Key Variables
DESCRIPTIVES VARIABLES=x4 x5 x6 x7 x8 x9 x10 x12 x13
  /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX 
  KURTOSIS SKEWNESS.

"""
        
        # Q7: Frequency tables for categorical
        elif q_num == 7:
            code += """* Frequency Tables for Categorical Variables
FREQUENCIES VARIABLES=x2 x11 
  /ORDER=ANALYSIS 
  /BARCHART FREQ 
  /PIECHART PERCENT.

"""
        
        # Q8: Frequency tables for continuous
        elif q_num == 8:
            code += """* Frequency Tables for Continuous Variables (with classes)
* Size classes
RECODE x4 (LO thru 40000=1) (40001 thru 50000=2) (50001 thru 60000=3) (60001 thru HI=4) INTO Size_Cat.
* Salary classes  
RECODE x5 (LO thru 40=1) (40.01 thru 60=2) (60.01 thru 80=3) (80.01 thru 100=4) (100.01 thru HI=5) INTO Salary_Cat.

FREQUENCIES VARIABLES=Size_Cat Salary_Cat 
  /ORDER=ANALYSIS 
  /BARCHART FREQ.

"""
        
        # Q9: Confidence intervals
        elif q_num == 9 or ('confidence interval' in question_lower):
            code += """* 95% and 99% Confidence Intervals
EXAMINE VARIABLES=x5 x6 x4 x7 x13
  /PLOT NONE 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 95 99 
  /MISSING LISTWISE.

"""
        
        # Q10: Normality tests
        elif q_num == 10 or ('normality' in question_lower):
            code += """* Normality Test for Salary
EXAMINE VARIABLES=x5 
  /PLOT=NPPLOT HISTOGRAM 
  /STATISTICS DESCRIPTIVES.
  
* Empirical Rule vs Chebyshev Rule
* If data is normal (Shapiro-Wilk p > 0.05): Use Empirical Rule (68-95-99.7)
* If data is not normal: Use Chebyshev Rule (at least 1-1/k² within k SD)

"""
        
        # Q11: Outliers detection
        elif q_num == 11 or ('outliers' in question_lower and 'attendance' in question_lower):
            code += """* Outlier Detection for Attendance
EXAMINE VARIABLES=x6 
  /PLOT=BOXPLOT 
  /STATISTICS=EXTREME 
  /MISSING LISTWISE 
  /NOTOTAL.

* Identifying extreme values (Tukey's method)
COMPUTE Q1_x6 = PCTILE(x6, 25).
COMPUTE Q3_x6 = PCTILE(x6, 75).
COMPUTE IQR_x6 = Q3_x6 - Q1_x6.
COMPUTE LowerBound = Q1_x6 - 1.5 * IQR_x6.
COMPUTE UpperBound = Q3_x6 + 1.5 * IQR_x6.
COMPUTE Outlier_x6 = (x6 < LowerBound) | (x6 > UpperBound).
EXECUTE.
FREQUENCIES VARIABLES=Outlier_x6.

"""
        
        # Q12-20: Hypothesis tests
        elif q_num >= 12 and q_num <= 20 and ('hypothesis' in question_lower or 'test' in question_lower):
            code += self.generate_hypothesis_test_code(q_num, question)
        
        else:
            code += f"* Analysis for question {q_num}\n"
            code += "* Review specific requirements for this question.\n\n"
        
        return code
    
    def generate_hypothesis_test_code(self, q_num, question):
        """توليد كود اختبارات الفرضيات لمجموعة البيانات 2"""
        code = ""
        question_lower = question.lower()
        
        # Q12: Test if average wins = 90
        if q_num == 12 or 'average number of wins is equal 90' in question_lower:
            code += """* One-Sample T-Test: H0: μ = 90 wins
T-TEST 
  /TESTVAL=90 
  /VARIABLES=x7 
  /MISSING=ANALYSIS 
  /CRITERIA=CI(.95).

"""
        
        # Q13: Test if average salary = 65M
        elif q_num == 13 or 'average salary is equal 65' in question_lower:
            code += """* One-Sample T-Test for Salary: H0: μ = $65M
T-TEST 
  /TESTVAL=65 
  /VARIABLES=x5 
  /MISSING=ANALYSIS 
  /CRITERIA=CI(.95).

"""
        
        # Q14: Compare salary between leagues
        elif q_num == 14 or 'no significance between the average salary of american and national teams' in question_lower:
            code += """* Independent T-Test: Salary by League
T-TEST GROUPS=x2(0 1) 
  /VARIABLES=x5 
  /MISSING=ANALYSIS 
  /CRITERIA=CI(.95).

"""
        
        # Q15: Compare stadium size by surface
        elif q_num == 15 or 'no significance difference between the size of the stadium that have natural surface' in question_lower:
            code += """* Independent T-Test: Stadium Size by Surface Type
T-TEST GROUPS=x11(0 1) 
  /VARIABLES=x4 
  /MISSING=ANALYSIS 
  /CRITERIA=CI(.95).

"""
        
        # Q16: Compare salary by stadium age
        elif q_num == 16 or 'no significance difference between the average salary of the teams built before and after 1990' in question_lower:
            code += """* Independent T-Test: Salary by Stadium Age
RECODE x3 (LO thru 1990=1) (1991 thru HI=2) INTO Built_1990.
T-TEST GROUPS=Built_1990(1 2) 
  /VARIABLES=x5 
  /MISSING=ANALYSIS 
  /CRITERIA=CI(.95).

"""
        
        # Q17: Compare ERA by win group
        elif q_num == 17 or 'no significant difference between the era of the teams who win more than 85 times' in question_lower:
            code += """* Independent T-Test: ERA by Win Group
RECODE x7 (LO thru 85=1) (86 thru HI=2) INTO Win_85.
T-TEST GROUPS=Win_85(1 2) 
  /VARIABLES=x8 
  /MISSING=ANALYSIS 
  /CRITERIA=CI(.95).

"""
        
        # Q18: ANOVA for HR by building period
        elif q_num == 18 or 'no significant difference between the hr of the teams built before 1950' in question_lower:
            code += """* One-Way ANOVA: Home Runs by Building Period
RECODE x3 (LO thru 1949=1) (1950 thru 1970=2) (1971 thru 1990=3) (1991 thru HI=4) INTO Build_Period.
ONEWAY x10 BY Build_Period 
  /STATISTICS DESCRIPTIVES HOMOGENEITY 
  /MISSING ANALYSIS 
  /POSTHOC=TUKEY LSD ALPHA(.05).

"""
        
        # Q19: Compare wins by salary threshold
        elif q_num == 19 or 'no significant difference between the number of wins of the teams of salary less than 70 millions' in question_lower:
            code += """* Independent T-Test: Wins by Salary Threshold
RECODE x5 (LO thru 69.99=1) (70 thru HI=2) INTO Salary_70.
T-TEST GROUPS=Salary_70(1 2) 
  /VARIABLES=x7 
  /MISSING=ANALYSIS 
  /CRITERIA=CI(.95).

"""
        
        # Q20: ANOVA for wins by salary category
        elif q_num == 20 or 'no significant difference between the number of wins of the teams of salary less than 40 million' in question_lower:
            code += """* One-Way ANOVA: Wins by Salary Category
RECODE x5 (LO thru 39.99=1) (40 thru 59.99=2) (60 thru 79.99=3) (80 thru HI=4) INTO Salary_Cat4.
ONEWAY x7 BY Salary_Cat4 
  /STATISTICS DESCRIPTIVES HOMOGENEITY 
  /MISSING ANALYSIS 
  /POSTHOC=TUKEY LSD ALPHA(.05).

"""
        
        return code

# تطبيق Streamlit
def main():
    app = SPSSProfessionalGenerator()
    
    st.title("📊 مولد أكواد SPSS الاحترافي")
    st.markdown('<div class="section-box arabic-text">', unsafe_allow_html=True)
    st.markdown("### 🚀 يولد أكواد SPSS كاملة مع جميع الرسوم البيانية والتحليلات")
    st.markdown("يتعامل مع جميع أنواع الأسئلة ويولد أكواد جاهزة للتنفيذ في SPSS")
    st.markdown('</div>', unsafe_allow_html=True)
    
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
            type=['xls', 'xlsx']
        )
        
        # رفع ملف الأسئلة
        questions_file = st.file_uploader(
            "رفع ملف الأسئلة (TXT أو DOC)",
            type=['txt', 'doc', 'docx']
        )
        
        if excel_file and questions_file:
            st.success("✅ تم رفع الملفين بنجاح")
    
    # المحتوى الرئيسي
    if excel_file and questions_file:
        try:
            # قراءة البيانات
            df = pd.read_excel(excel_file)
            
            # قراءة الأسئلة
            if questions_file.name.endswith('.txt'):
                questions_text = questions_file.getvalue().decode('utf-8')
            else:
                # للملفات الأخرى، نقرأ النص الخام
                questions_text = str(questions_file.getvalue())
            
            questions = app.parse_questions(questions_text)
            
            # عرض المعلومات
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("عدد الأسئلة", len(questions))
            with col2:
                st.metric("عدد المتغيرات", len(df.columns))
            with col3:
                st.metric("عدد الصفوف", len(df))
            
            # زر توليد الكود
            if st.button("🚀 توليد كود SPSS كامل", type="primary"):
                with st.spinner("جاري توليد الكود الاحترافي..."):
                    if dataset_num == 1:
                        spss_code = app.generate_dataset1_code(questions, df)
                    elif dataset_num == 2:
                        spss_code = app.generate_dataset2_code(questions, df)
                    else:
                        spss_code = "* Code generation for this dataset is under development.\n"
                    
                    app.generated_codes[dataset_num] = spss_code
                    
                    st.success(f"✅ تم توليد كود SPSS لـ {len(questions)} سؤال")
                    
                    # عرض الكود
                    st.markdown('<div class="code-header">كود SPSS المُنشأ</div>', unsafe_allow_html=True)
                    st.code(spss_code, language='text', height=500)
                    
                    # أزرار التنزيل
                    st.markdown("---")
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        st.markdown(app.create_download_link(spss_code, f"Syntax{dataset_num}_Complete.sps"), 
                                  unsafe_allow_html=True)
                    
                    with col_dl2:
                        if st.button("🔄 توليد كود جديد"):
                            st.rerun()
        
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")
    
    else:
        st.info("📤 يرجى رفع ملف Excel وملف الأسئلة لبدء التوليد")
        
        # عرض مثال
        with st.expander("📚 مثال على المخرجات المتوقعة"):
            st.code("""* مثال لكود SPSS كامل مع رسوم بيانية:
GRAPH /BAR(SIMPLE)=MEAN(X1) BY X6 
  /TITLE="Average Account Balance by City".

GRAPH /HISTOGRAM(NORMAL)=X1 
  /TITLE="Distribution of Account Balances".

T-TEST /TESTVAL=100 /VARIABLES=X1.

EXAMINE VARIABLES=X1 
  /PLOT=BOXPLOT 
  /STATISTICS=EXTREME.
""", language='text')

if __name__ == "__main__":
    main()
