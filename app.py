import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import base64
from datetime import datetime

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
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #F59E0B;
        margin-bottom: 1rem;
    }
    .spss-code {
        background-color: #1E293B;
        color: #E2E8F0;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        overflow-x: auto;
        white-space: pre-wrap;
        direction: ltr;
        font-size: 12px;
        line-height: 1.3;
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
    .stButton>button:hover {
        background-color: #1D4ED8;
    }
    .arabic-text {
        direction: rtl;
        text-align: right;
    }
    .code-header {
        background-color: #1E293B;
        color: white;
        padding: 10px;
        border-radius: 5px 5px 0 0;
        font-family: monospace;
        font-size: 14px;
    }
    .variable-table {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class AdvancedSPSSGenerator:
    def __init__(self):
        self.uploaded_files = {}
        self.generated_codes = {}
        self.variable_mapping = {}
        
    def create_download_link(self, content, filename):
        """إنشاء رابط تحميل للملف"""
        b64 = base64.b64encode(content.encode()).decode()
        return f'<a href="data:file/txt;base64,{b64}" download="{filename}" style="color: #3B82F6; text-decoration: none; font-weight: bold;">📥 {filename}</a>'
    
    def parse_questions(self, text_content):
        """تحليل النص لاستخراج الأسئلة بدقة"""
        questions = []
        lines = text_content.split('\n')
        current_q = ""
        in_question = False
        
        for line in lines:
            line = line.strip()
            
            # البحث عن سؤال مرقم
            if re.match(r'^\d+[\.\)]', line) or re.match(r'^\[\d+\]', line):
                if current_q:
                    questions.append(current_q.strip())
                current_q = line
                in_question = True
            elif in_question and line and not line.startswith('*') and not line.startswith('['):
                current_q += " " + line
            elif line == "" and in_question:
                in_question = False
        
        if current_q:
            questions.append(current_q.strip())
        
        return questions
    
    def analyze_variables(self, df):
        """تحليل المتغيرات لتحديد أنواعها"""
        variable_info = {
            'categorical': [],
            'continuous': [],
            'binary': [],
            'nominal': [],
            'ordinal': []
        }
        
        for col in df.columns:
            # محاولة تحديد نوع المتغير
            unique_vals = df[col].nunique()
            dtype = df[col].dtype
            
            if dtype == 'object' or unique_vals <= 10:
                variable_info['categorical'].append(col)
                if unique_vals == 2:
                    variable_info['binary'].append(col)
            else:
                variable_info['continuous'].append(col)
        
        return variable_info
    
    def generate_header(self, dataset_name, questions_count):
        """إنشاء رأس ملف SPSS"""
        header = f"""* Encoding: UTF-8.
* =========================================================================.
* SPSS Syntax for {dataset_name} Analysis
* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Total Questions Analyzed: {questions_count}
* Software: Compatible with IBM SPSS Statistics V26+
* =========================================================================.

"""
        return header
    
    def generate_variable_labels(self, df, dataset_num):
        """توليد تسميات المتغيرات بناءً على نوع مجموعة البيانات"""
        code = "* --- [VARIABLE AND VALUE LABELING] --- .\n"
        code += "* Scientific Justification: Proper labeling ensures that the output is readable\n"
        code += "* and that categorical variables are correctly interpreted during analysis.\n\n"
        
        if dataset_num == 1:
            code += """VARIABLE LABELS 
    X1 "Account Balance ($)" X2 "Number of ATM Transactions" X3 "Number of Other Bank Services Used" 
    X4 "Has a Debit Card" X5 "Receives Interest on the Account" X6 "City where Banking is Done".\n"""
            code += """VALUE LABELS X4 0 "No" 1 "Yes" /X5 0 "No" 1 "Yes" 
    /X6 1 "City 1" 2 "City 2" 3 "City 3" 4 "City 4".\n\n"""
        
        elif dataset_num == 2:
            code += """VARIABLE LABELS 
    x1 "Team Name" x2 "League" x3 "Year Built" x4 "Stadium Size" 
    x5 "Salary ($M)" x6 "Attendance" x7 "Wins" x8 "ERA" x9 "Batting Average" 
    x10 "Home Runs" x11 "Surface Type" x12 "Stolen Bases" x13 "Errors".\n"""
            code += """VALUE LABELS x2 0 "National League" 1 "American League"
    /x11 0 "Natural Surface" 1 "Artificial Surface".\n\n"""
        
        elif dataset_num == 3:
            code += """VARIABLE LABELS 
    x1 "Country" x2 "G7 Member" x3 "Total Area (000 sq km)" x4 "Population (000)" 
    x5 "Population Over 65%" x6 "Exchange Rate per USD" x7 "GDP (Billions USD)" 
    x8 "Energy Use (MTOE)" x9 "Manufacturing Index" x10 "Total Labor Force" x11 "Region".\n"""
            code += """VALUE LABELS x2 0 "Non-G7" 1 "G7 Member"
    /x11 1 "Far East" 2 "Europe" 3 "North America".\n\n"""
        
        elif dataset_num == 4:
            code += """VARIABLE LABELS 
    x1 "Gender" x2 "Race" x3 "Salary" x4 "Region" x5 "General Happiness" 
    x6 "Is Life Exciting" x7 "Brothers/Sisters" x8 "Children" x9 "Age" 
    x10 "Highest Year of School" x11 "Occupation" x12 "Most Important Problem".\n"""
            code += """VALUE LABELS x1 1 "Male" 2 "Female" 
    /x2 1 "White" 2 "Black" 3 "Others"
    /x4 1 "North East" 2 "South East" 3 "West"
    /x5 1 "Very Happy" 2 "Pretty Happy" 3 "Not Too Happy"
    /x6 1 "Exciting" 2 "Routine" 3 "Dull"
    /x11 1 "Managerial" 2 "Technical" 3 "Farming" 4 "Service" 5 "Production" 6 "Marketing"
    /x12 1 "Health" 2 "Financial" 3 "Family" 4 "Legal" 5 "Personal" 6 "Service" 7 "Miscellaneous".\n\n"""
        
        code += "EXECUTE.\n\n"
        return code
    
    def generate_frequency_tables(self, question, df, dataset_num):
        """توليد كود جداول التكرار"""
        code = f"* -------------------------------------------------------------------------.\n"
        code += f"TITLE \"{question}\".\n"
        code += f"* -------------------------------------------------------------------------.\n"
        
        if dataset_num == 1:
            code += "FREQUENCIES VARIABLES=X4 X5 X6 /ORDER=ANALYSIS.\n"
            code += "ECHO \"INTERPRETATION: This table shows the distribution of debit cards, interest reception, and city locations\".\n\n"
        
        elif dataset_num == 2:
            code += "FREQUENCIES VARIABLES=x2 x11 /ORDER=ANALYSIS.\n\n"
        
        elif dataset_num == 4:
            code += "FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.\n"
            code += "* Scientific Justification: Frequency tables summarize categorical variable distribution.\n\n"
        
        return code
    
    def generate_descriptive_stats(self, question, df, dataset_num):
        """توليد كود الإحصاءات الوصفية"""
        code = f"* -------------------------------------------------------------------------.\n"
        code += f"TITLE \"{question}\".\n"
        code += f"* -------------------------------------------------------------------------.\n"
        
        if dataset_num == 1:
            code += "FREQUENCIES VARIABLES=X1 X2 \n"
            code += "  /FORMAT=NOTABLE \n"
            code += "  /STATISTICS=MEAN MEDIAN MODE MINIMUM MAXIMUM RANGE VARIANCE STDDEV SKEWNESS SESKEW.\n\n"
        
        elif dataset_num == 2:
            code += "FREQUENCIES VARIABLES=x4 x5 x6 x7 x8 x9 x10 x12 x13\n"
            code += "  /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE STDDEV VARIANCE RANGE MIN MAX.\n\n"
        
        elif dataset_num == 4:
            code += "FREQUENCIES VARIABLES=x3 x9 x7 x8 \n"
            code += "  /FORMAT=NOTABLE \n"
            code += "  /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.\n\n"
        
        return code
    
    def generate_bar_charts(self, question, df, dataset_num):
        """توليد كود الرسوم البيانية"""
        code = f"* -------------------------------------------------------------------------.\n"
        code += f"TITLE \"{question}\".\n"
        code += f"* -------------------------------------------------------------------------.\n"
        
        if 'average salary' in question.lower() and 'american' in question.lower():
            code += "GRAPH /BAR(SIMPLE)=MEAN(x5) BY x2 /TITLE=\"Average Salary by League\".\n\n"
        
        elif 'size of stadium' in question.lower():
            code += "GRAPH /BAR(SIMPLE)=MEAN(x4) BY x1 /TITLE=\"Stadium Capacity per Team\".\n\n"
        
        elif 'salary and number of wins' in question.lower():
            code += "GRAPH /BAR(GROUPED)=MEAN(x5) MEAN(x7) BY x1 /TITLE=\"Comparison: Salary vs Wins\".\n\n"
        
        elif 'number of respondent' in question.lower() and 'region' in question.lower():
            code += "GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE='Number of Respondents by Region'.\n\n"
        
        elif 'average salary of respondents' in question.lower():
            code += "GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE='Average Salary by Region'.\n\n"
        
        elif 'average number of children' in question.lower():
            code += "GRAPH /BAR(SIMPLE)=MEAN(x8) BY x2 /TITLE='Average Children by Race'.\n\n"
        
        else:
            code += "* Bar chart code template:\n"
            code += "* GRAPH /BAR(SIMPLE)=MEAN(Variable) BY Category /TITLE='Your Title'.\n\n"
        
        return code
    
    def generate_pie_charts(self, question, df, dataset_num):
        """توليد كود الرسوم الدائرية"""
        code = f"* -------------------------------------------------------------------------.\n"
        code += f"TITLE \"{question}\".\n"
        code += f"* -------------------------------------------------------------------------.\n"
        
        if 'average number of errors' in question.lower() and '1990' in question.lower():
            code += "* Q4: Recoding Year Built for pie chart\n"
            code += "RECODE x3 (LO thru 1990=1) (1991 thru HI=2) INTO Built_90.\n"
            code += "VALUE LABELS Built_90 1 \"Built In/Before 1990\" 2 \"Built After 1990\".\n"
            code += "GRAPH /PIE=MEAN(x13) BY Built_90 /TITLE=\"Avg Errors by Stadium Construction Era\".\n\n"
        
        elif 'maximum number of wins' in question.lower() and 'surface' in question.lower():
            code += "GRAPH /PIE=MAX(x7) BY x11 /TITLE=\"Max Wins by Surface Type\".\n\n"
        
        elif 'sum of salaries' in question.lower() and 'occupation' in question.lower():
            code += "GRAPH /PIE=SUM(x3) BY x11 /TITLE='Sum of Salaries by Occupation'.\n\n"
        
        elif 'percentage of male and female' in question.lower():
            code += "GRAPH /PIE=COUNT BY x1 /TITLE='Gender Percentage'.\n\n"
        
        else:
            code += "* Pie chart code template:\n"
            code += "* GRAPH /PIE=MEAN(Variable) BY Category /TITLE='Your Title'.\n\n"
        
        return code
    
    def generate_confidence_intervals(self, question, df, dataset_num):
        """توليد كود فترات الثقة"""
        code = f"* -------------------------------------------------------------------------.\n"
        code += f"TITLE \"{question}\".\n"
        code += f"* -------------------------------------------------------------------------.\n"
        
        if dataset_num == 1:
            code += "EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 95 /PLOT NONE.\n"
            code += "EXAMINE VARIABLES=X1 /STATISTICS DESCRIPTIVES /CINTERVAL 99 /PLOT NONE.\n\n"
        
        elif dataset_num == 2:
            code += "EXAMINE VARIABLES=x5 x6 x4 x7 x13\n"
            code += "  /PLOT BOXPLOT NPPLOT /CINTERVAL 95 /STATISTICS DESCRIPTIVES.\n"
            code += "EXAMINE VARIABLES=x5 x6 x4 x7 x13 /CINTERVAL 99 /STATISTICS DESCRIPTIVES.\n\n"
        
        elif dataset_num == 4:
            code += "EXAMINE VARIABLES=x3 x9 BY x4 /STATISTICS DESCRIPTIVES /CINTERVAL 95 /PLOT NONE.\n"
            code += "EXAMINE VARIABLES=x3 x9 BY x4 /STATISTICS DESCRIPTIVES /CINTERVAL 99 /PLOT NONE.\n\n"
        
        return code
    
    def generate_hypothesis_tests(self, question, df, dataset_num):
        """توليد كود اختبارات الفرضيات"""
        code = f"* -------------------------------------------------------------------------.\n"
        code += f"TITLE \"{question}\".\n"
        code += f"* -------------------------------------------------------------------------.\n"
        
        question_lower = question.lower()
        
        # مجموعة البيانات 2
        if dataset_num == 2:
            if 'average number of wins is equal 90' in question_lower:
                code += "T-TEST /TESTVAL=90 /VARIABLES=x7.\n\n"
            
            elif 'average salary is equal 65' in question_lower:
                code += "T-TEST /TESTVAL=65 /VARIABLES=x5.\n\n"
            
            elif 'no significance between the average salary of american and national teams' in question_lower:
                code += "T-TEST GROUPS=x2(0 1) /VARIABLES=x5.\n\n"
            
            elif 'no significance difference between the size of the stadium' in question_lower and 'surface' in question_lower:
                code += "T-TEST GROUPS=x11(0 1) /VARIABLES=x4.\n\n"
            
            elif 'no significance difference between the average salary of the teams built before and after 1990' in question_lower:
                code += "* First, recode the year variable\n"
                code += "RECODE x3 (LO thru 1990=1) (1991 thru HI=2) INTO Built_90.\n"
                code += "VALUE LABELS Built_90 1 \"Built In/Before 1990\" 2 \"Built After 1990\".\n"
                code += "T-TEST GROUPS=Built_90(1 2) /VARIABLES=x5.\n\n"
            
            elif 'no significant difference between the era' in question_lower and 'wins' in question_lower:
                code += "* Recode wins for ERA analysis\n"
                code += "RECODE x7 (LO thru 85=1) (85.01 thru HI=2) INTO Win_Group_85.\n"
                code += "VALUE LABELS Win_Group_85 1 \"Wins <= 85\" 2 \"Wins > 85\".\n"
                code += "T-TEST GROUPS=Win_Group_85(1 2) /VARIABLES=x8.\n\n"
            
            elif 'no significant difference between the hr' in question_lower and 'built before 1950' in question_lower:
                code += "* Categorize building year into four periods\n"
                code += "RECODE x3 (LO thru 1949=1) (1950 thru 1970=2) (1971 thru 1990=3) (1991 thru HI=4) INTO Year_Groups.\n"
                code += "VALUE LABELS Year_Groups 1 \"Before 1950\" 2 \"1950-1970\" 3 \"1971-1990\" 4 \"1991 & More\".\n"
                code += "ONEWAY x10 BY Year_Groups /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).\n\n"
            
            elif 'no significant difference between the number of wins of the teams of salary less than 70' in question_lower:
                code += "* Recode salary for wins comparison\n"
                code += "RECODE x5 (LO thru 69.99=1) (70 thru HI=2) INTO Sal_Group_70.\n"
                code += "VALUE LABELS Sal_Group_70 1 \"Salary < 70M\" 2 \"Salary >= 70M\".\n"
                code += "T-TEST GROUPS=Sal_Group_70(1 2) /VARIABLES=x7.\n\n"
            
            elif 'no significant difference between the number of wins of the teams of salary' in question_lower and '80 million' in question_lower:
                code += "* Categorize salary into four levels\n"
                code += "RECODE x5 (LO thru 39.99=1) (40 thru 59.99=2) (60 thru 79.99=3) (80 thru HI=4) INTO Salary_Cat_4.\n"
                code += "VALUE LABELS Salary_Cat_4 1 \"< 40M\" 2 \"40-60M\" 3 \"60-80M\" 4 \"> 80M\".\n"
                code += "ONEWAY x7 BY Salary_Cat_4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY ALPHA(0.05).\n\n"
        
        # مجموعة البيانات 4
        elif dataset_num == 4:
            if 'average salary is equal 35000' in question_lower:
                code += "T-TEST /TESTVAL=35000 /VARIABLES=x3.\n\n"
            
            elif 'average age in the north east and south east regions equal 45' in question_lower:
                code += "TEMPORARY.\n"
                code += "SELECT IF (x4 = 1 OR x4 = 2).\n"
                code += "T-TEST /TESTVAL=45 /VARIABLES=x9.\n\n"
            
            elif 'no significant difference between the average general happiness of the north east and south east' in question_lower:
                code += "T-TEST GROUPS=x4(1 2) /VARIABLES=x5.\n\n"
            
            elif 'no significant difference between the average number of children of east and west region' in question_lower:
                code += "RECODE x4 (1 2=1) (3=2) INTO Region_EW.\n"
                code += "T-TEST GROUPS=Region_EW(1 2) /VARIABLES=x8.\n\n"
            
            elif 'no significant difference between the average general happiness of people of age over and under 50' in question_lower:
                code += "RECODE x9 (LO THRU 50=1) (50.01 THRU HI=2) INTO Age_50.\n"
                code += "T-TEST GROUPS=Age_50(1 2) /VARIABLES=x5.\n\n"
            
            elif 'no significant difference between the average numbers of children of black and white people' in question_lower:
                code += "T-TEST GROUPS=x2(1 2) /VARIABLES=x8.\n\n"
            
            elif 'no significant difference between the average general happiness of white people of ages greater than 45' in question_lower:
                code += "TEMPORARY.\n"
                code += "SELECT IF (x2 = 1).\n"
                code += "RECODE x9 (LO THRU 45=1) (45.01 THRU HI=2) INTO Age_45_W.\n"
                code += "T-TEST GROUPS=Age_45_W(1 2) /VARIABLES=x5.\n\n"
            
            elif 'no significant difference between the average salary of the different regions' in question_lower:
                code += "ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES.\n\n"
            
            elif 'no significant difference between the average general happiness for the different race' in question_lower:
                code += "ONEWAY x5 BY x2 /STATISTICS DESCRIPTIVES.\n\n"
        
        return code
    
    def generate_correlation_regression(self, question, df, dataset_num):
        """توليد كود الارتباط والانحدار"""
        code = f"* -------------------------------------------------------------------------.\n"
        code += f"TITLE \"{question}\".\n"
        code += f"* -------------------------------------------------------------------------.\n"
        
        question_lower = question.lower()
        
        if dataset_num == 4:
            if 'correlation between salary and the age' in question_lower:
                code += "CORRELATIONS /VARIABLES=x3 x9.\n\n"
            
            elif 'correlation between general happiness and occupation' in question_lower:
                code += "NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.\n\n"
            
            elif 'linear regression model' in question_lower and 'general happiness' in question_lower:
                code += """REGRESSION
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS R ANOVA COLLIN
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN 
  /DEPENDENT x5
  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.\n\n"""
        
        return code
    
    def generate_special_analysis(self, question, df, dataset_num):
        """توليد كود للتحليلات الخاصة"""
        code = f"* -------------------------------------------------------------------------.\n"
        code += f"TITLE \"{question}\".\n"
        code += f"* -------------------------------------------------------------------------.\n"
        
        question_lower = question.lower()
        
        if dataset_num == 1:
            if 'frequency table that has a suitable number of classes' in question_lower and 'account balance' in question_lower:
                code += """RECODE X1 (0 thru 500=1) (500.01 thru 1000=2) (1000.01 thru 1500=3) (1500.01 thru 2000=4) (2000.01 thru HI=5) INTO X1_Classes.
VALUE LABELS X1_Classes 1 "0-500" 2 "501-1000" 3 "1001-1500" 4 "1501-2000" 5 "Over 2000".
FREQUENCIES VARIABLES=X1_Classes /FORMAT=AVALUE.
ECHO "COMMENT: This distribution reveals the wealth concentration among the bank clients".\n\n"""
            
            elif 'frequency table that has an appropriate number of classes' in question_lower and 'atm transactions' in question_lower:
                code += """* K-rule: 2^k >= 60. For n=60, 2^6=64, so 6 classes are optimal.
RECODE X2 (2 thru 5=1) (6 thru 9=2) (10 thru 13=3) (14 thru 17=4) (18 thru 21=5) (22 thru 25=6) INTO X2_Krule.
VALUE LABELS X2_Krule 1 "2-5" 2 "6-9" 3 "10-13" 4 "14-17" 5 "18-21" 6 "22-25".
FREQUENCIES VARIABLES=X2_Krule.
ECHO "COMMENT: Based on the K-rule, 6 classes provide a clear view of transaction intensity".\n\n"""
            
            elif 'skewness of the distribution' in question_lower:
                code += """ECHO "ANALYSIS: Compare Mean and Median from Q4. If Mean > Median, it is Right-Skewed".
ECHO "If Mean < Median, it is Left-Skewed. Negative Skewness indicates most values are high".\n\n"""
            
            elif 'answer question number 4 for each city' in question_lower:
                code += """SORT CASES BY X6.
SPLIT FILE SEPARATE BY X6.
FREQUENCIES VARIABLES=X1 X2 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE MIN MAX RANGE VAR STDDEV SKEW.
SPLIT FILE OFF.\n\n"""
            
            elif 'answer question number 4 for customers who have debit card or not' in question_lower:
                code += """SORT CASES BY X4.
SPLIT FILE SEPARATE BY X4.
FREQUENCIES VARIABLES=X1 X2 /FORMAT=NOTABLE /STATISTICS=MEAN MEDIAN MODE MIN MAX RANGE VAR STDDEV SKEW.
SPLIT FILE OFF.\n\n"""
            
            elif 'maximum number of transactions for customer who have debit card' in question_lower:
                code += "GRAPH /BAR(SIMPLE)=MAX(X2) BY X4 /TITLE=\"Maximum ATM Transactions by Debit Card Status\".\n\n"
            
            elif 'average account balance for each city for the customers who have debit card' in question_lower:
                code += "GRAPH /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 /TITLE=\"Avg Balance by City and Card Status\".\n\n"
            
            elif 'percentage of customers who receive interest on the account' in question_lower:
                code += "GRAPH /BAR(SIMPLE)=PCT BY X5 /TITLE=\"Percentage of Interest Receivers vs Non-Receivers\".\n\n"
            
            elif 'pie chart to show the percentage of customers who receive an interest or not' in question_lower:
                code += "GRAPH /PIE=PCT BY X5 /TITLE=\"Market Share: Customers Receiving Interest (%)\".\n\n"
            
            elif 'normality of the data apply the empirical rule or chebycheve rule' in question_lower:
                code += """EXAMINE VARIABLES=X1 /PLOT NPPLOT /STATISTICS NONE.
ECHO "RULE: If Shapiro-Wilk Sig > 0.05, apply Empirical Rule. If < 0.05, use Chebyshev".\n\n"""
            
            elif 'outliers and the extremes value for the account balance' in question_lower:
                code += """EXAMINE VARIABLES=X1 /PLOT BOXPLOT /STATISTICS DESCRIPTIVES.
ECHO "ANALYSIS: Check the Boxplot for data points outside the whiskers to find outliers".\n\n"""
        
        return code
    
    def generate_dataset_specific_code(self, dataset_num, questions, df):
        """توليد كود خاص بمجموعة البيانات"""
        full_code = self.generate_header(f"Data Set {dataset_num}", len(questions))
        full_code += self.generate_variable_labels(df, dataset_num)
        
        # معالجة كل سؤال
        for i, question in enumerate(questions, 1):
            question_lower = question.lower()
            
            # تحديد نوع السؤال وتوليد الكود المناسب
            if 'frequency table' in question_lower and ('categorical' in question_lower or 'discrete' in question_lower):
                full_code += self.generate_frequency_tables(f"QUESTION {i}: {question[:50]}...", df, dataset_num)
            
            elif 'mean' in question_lower or 'median' in question_lower or 'standard deviation' in question_lower:
                full_code += self.generate_descriptive_stats(f"QUESTION {i}: {question[:50]}...", df, dataset_num)
            
            elif 'bar chart' in question_lower:
                full_code += self.generate_bar_charts(f"QUESTION {i}: {question[:50]}...", df, dataset_num)
            
            elif 'pie chart' in question_lower:
                full_code += self.generate_pie_charts(f"QUESTION {i}: {question[:50]}...", df, dataset_num)
            
            elif 'confidence interval' in question_lower:
                full_code += self.generate_confidence_intervals(f"QUESTION {i}: {question[:50]}...", df, dataset_num)
            
            elif 'hypothesis' in question_lower or 'test' in question_lower:
                full_code += self.generate_hypothesis_tests(f"QUESTION {i}: {question[:50]}...", df, dataset_num)
            
            elif 'correlation' in question_lower or 'regression' in question_lower:
                full_code += self.generate_correlation_regression(f"QUESTION {i}: {question[:50]}...", df, dataset_num)
            
            else:
                # التحليلات الخاصة
                full_code += self.generate_special_analysis(f"QUESTION {i}: {question[:50]}...", df, dataset_num)
        
        return full_code

# إنشاء تطبيق Streamlit
def main():
    app = AdvancedSPSSGenerator()
    
    # عنوان التطبيق
    st.markdown('<h1 class="main-header">📊 مولد أكواد SPSS المتقدم</h1>', unsafe_allow_html=True)
    st.markdown('<div class="section-box arabic-text">', unsafe_allow_html=True)
    st.markdown("### 🚀 مولد أكواد SPSS احترافي - نفس مستوى Syntax2.sps و Syntax3.sps و Syntax4.sps")
    st.markdown("يقوم بتحليل الأسئلة وإنشاء أكواد SPSS متطابقة مع النماذج المرفوعة")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown("## ⚙️ الإعدادات المتقدمة")
        st.markdown('<div class="warning-box arabic-text">', unsafe_allow_html=True)
        st.info("""
        **🎯 مميزات الإصدار المتقدم:**
        1. يدعم جميع مجموعات البيانات (1-4)
        2. يولد أكواد بنفس جودة النماذج المرفوعة
        3. يتضمن التعليقات العلمية (Scientific Justification)
        4. يدعم RECODE, T-TEST, ANOVA, REGRESSION
        5. يضيف تسميات المتغيرات تلقائياً
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("## 📊 تحديد مجموعة البيانات")
        dataset_num = st.selectbox(
            "اختر رقم مجموعة البيانات",
            [1, 2, 3, 4],
            format_func=lambda x: f"Data Set {x}"
        )
        
        st.markdown("## 📁 حالة الملفات")
        if 'excel' in app.uploaded_files:
            st.success(f"✅ {app.uploaded_files['excel']['name']}")
        if 'word' in app.uploaded_files:
            st.success(f"✅ {app.uploaded_files['word']['name']}")
        
        st.markdown("---")
        st.markdown("### ⚡ خيارات سريعة")
        if st.button("🔄 مسح كل شيء", use_container_width=True):
            app.uploaded_files = {}
            app.generated_codes = {}
            st.rerun()
    
    # علامات التبويب الرئيسية
    tab1, tab2, tab3 = st.tabs(["📤 تحميل الملفات", "⚡ توليد الأكواد", "📊 معاينة البيانات"])
    
    with tab1:
        st.markdown('<div class="sub-header arabic-text">تحميل البيانات والأسئلة</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### 📊 ملف Excel (Data Set {dataset_num})")
            excel_file = st.file_uploader(
                f"اختر ملف Excel لمجموعة البيانات {dataset_num}",
                type=['xls', 'xlsx'],
                key=f"excel_{dataset_num}"
            )
            
            if excel_file is not None:
                try:
                    df = pd.read_excel(excel_file)
                    st.success(f"✅ تم تحميل {excel_file.name} ({len(df)} صف، {len(df.columns)} عمود)")
                    
                    # تحليل المتغيرات
                    var_info = app.analyze_variables(df)
                    
                    with st.expander("🔍 تحليل المتغيرات"):
                        st.write(f"**عدد المتغيرات:** {len(df.columns)}")
                        st.write(f"**متغيرات فئوية:** {len(var_info['categorical'])}")
                        st.write(f"**متغيرات مستمرة:** {len(var_info['continuous'])}")
                        st.write(f"**متغيرات ثنائية:** {len(var_info['binary'])}")
                        
                        st.write("**أسماء الأعمدة:**")
                        for col in df.columns:
                            dtype = df[col].dtype
                            unique = df[col].nunique()
                            st.write(f"- {col}: {dtype} (فريد: {unique})")
                    
                    app.uploaded_files['excel'] = {
                        'name': excel_file.name,
                        'data': df,
                        'dataset_num': dataset_num,
                        'var_info': var_info
                    }
                    
                except Exception as e:
                    st.error(f"❌ خطأ في تحميل Excel: {str(e)}")
        
        with col2:
            st.markdown("### 📝 ملف الأسئلة")
            word_file = st.file_uploader(
                "اختر ملف الأسئلة (Word أو Text)",
                type=['txt', 'doc', 'docx'],
                key=f"word_{dataset_num}"
            )
            
            if word_file is not None:
                try:
                    # قراءة الملف
                    if word_file.name.endswith('.txt'):
                        text_content = word_file.getvalue().decode('utf-8')
                    else:
                        # لملفات Word، نستخدم قراءة النص البسيطة
                        text_content = str(word_file.getvalue())
                    
                    questions = app.parse_questions(text_content)
                    
                    st.success(f"✅ تم تحليل {len(questions)} سؤال")
                    
                    with st.expander("📋 معاينة الأسئلة"):
                        for i, q in enumerate(questions[:10], 1):
                            st.write(f"**{i}.** {q[:100]}..." if len(q) > 100 else f"**{i}.** {q}")
                        if len(questions) > 10:
                            st.write(f"... و{len(questions)-10} أسئلة أخرى")
                    
                    app.uploaded_files['word'] = {
                        'name': word_file.name,
                        'questions': questions,
                        'content': text_content
                    }
                    
                except Exception as e:
                    st.error(f"❌ خطأ في تحليل الأسئلة: {str(e)}")
    
    with tab2:
        st.markdown('<div class="sub-header arabic-text">توليد أكواد SPSS</div>', unsafe_allow_html=True)
        
        if 'excel' not in app.uploaded_files or 'word' not in app.uploaded_files:
            st.warning("⚠️ يرجى تحميل ملف Excel وملف الأسئلة أولاً")
        else:
            # عرض معلومات البيانات
            df = app.uploaded_files['excel']['data']
            questions = app.uploaded_files['word']['questions']
            dataset_num = app.uploaded_files['excel']['dataset_num']
            
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("عدد الأسئلة", len(questions))
            with col_info2:
                st.metric("عدد المتغيرات", len(df.columns))
            with col_info3:
                st.metric("عدد الصفوف", len(df))
            
            # زر التوليد
            col_gen1, col_gen2 = st.columns([1, 3])
            
            with col_gen1:
                generate_button = st.button(
                    f"🚀 توليد كود Data Set {dataset_num}",
                    use_container_width=True,
                    type="primary"
                )
                
                if generate_button:
                    with st.spinner("🔄 جاري توليد كود SPSS المتقدم..."):
                        # توليد الكود
                        spss_code = app.generate_dataset_specific_code(dataset_num, questions, df)
                        
                        # حفظ الكود
                        app.generated_codes[f'dataset_{dataset_num}'] = spss_code
                        
                        st.success(f"✅ تم توليد كود SPSS لـ {len(questions)} سؤال")
            
            with col_gen2:
                if f'dataset_{dataset_num}' in app.generated_codes:
                    st.markdown("### 📋 كود SPSS المُنشأ")
                    
                    # عرض الكود مع إمكانية النسخ
                    st.markdown('<div class="code-header">SPSS Syntax Code</div>', unsafe_allow_html=True)
                    st.code(app.generated_codes[f'dataset_{dataset_num}'], language='text')
                    
                    # أزرار الإجراءات
                    st.markdown("---")
                    col_actions1, col_actions2, col_actions3 = st.columns(3)
                    
                    with col_actions1:
                        st.markdown(app.create_download_link(
                            app.generated_codes[f'dataset_{dataset_num}'],
                            f"Syntax{dataset_num}_Advanced.sps"
                        ), unsafe_allow_html=True)
                    
                    with col_actions2:
                        if st.button("📋 نسخ الكود", use_container_width=True):
                            st.success("الكود جاهز للنسخ (استخدم زر التنزيل للنسخة الكاملة)")
                    
                    with col_actions3:
                        if st.button("🆕 توليد جديد", use_container_width=True):
                            del app.generated_codes[f'dataset_{dataset_num}']
                            st.rerun()
    
    with tab3:
        st.markdown('<div class="sub-header arabic-text">معاينة البيانات والمتغيرات</div>', unsafe_allow_html=True)
        
        if 'excel' in app.uploaded_files:
            df = app.uploaded_files['excel']['data']
            dataset_num = app.uploaded_files['excel']['dataset_num']
            
            # عرض عينة من البيانات
            st.markdown("### 👁️ معاينة البيانات")
            st.dataframe(df.head(20), use_container_width=True)
            
            # عرض إحصائيات
            st.markdown("### 📈 الإحصاءات الأساسية")
            
            tab_stats1, tab_stats2, tab_stats3 = st.tabs(["وصفية", "أنواع البيانات", "القيم المفقودة"])
            
            with tab_stats1:
                if st.button("عرض الإحصاءات الوصفية"):
                    st.dataframe(df.describe(), use_container_width=True)
            
            with tab_stats2:
                dtype_summary = pd.DataFrame({
                    'المتغير': df.columns,
                    'النوع': df.dtypes.values,
                    'القيم الفريدة': [df[col].nunique() for col in df.columns],
                    'القيم المفقودة': [df[col].isnull().sum() for col in df.columns]
                })
                st.dataframe(dtype_summary, use_container_width=True)
            
            with tab_stats3:
                missing_data = df.isnull().sum()
                missing_percent = (missing_data / len(df)) * 100
                missing_df = pd.DataFrame({
                    'القيم المفقودة': missing_data,
                    'النسبة المئوية': missing_percent.round(2)
                })
                missing_df = missing_df[missing_df['القيم المفقودة'] > 0]
                
                if len(missing_df) > 0:
                    st.dataframe(missing_df, use_container_width=True)
                else:
                    st.success("🎉 لا توجد قيم مفقودة في البيانات!")
            
            # عرض العلاقات بين المتغيرات
            st.markdown("### 🔗 علاقات المتغيرات")
            
            if len(df.select_dtypes(include=[np.number]).columns) >= 2:
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                
                col_rel1, col_rel2 = st.columns(2)
                with col_rel1:
                    x_var = st.selectbox("المتغير X", num_cols, key="x_var_preview")
                with col_rel2:
                    y_var = st.selectbox("المتغير Y", num_cols, key="y_var_preview")
                
                if x_var != y_var:
                    chart_type = st.selectbox("نوع الرسم", ["مبعثر", "خطي", "عمودي"])
                    
                    try:
                        if chart_type == "مبعثر":
                            st.scatter_chart(df[[x_var, y_var]].dropna())
                        elif chart_type == "خطي":
                            st.line_chart(df[[x_var, y_var]].dropna())
                        elif chart_type == "عمودي":
                            st.bar_chart(df[[x_var, y_var]].dropna())
                    except:
                        st.warning("تعذر إنشاء الرسم مع البيانات المحددة")
        
        else:
            st.info("📥 يرجى تحميل ملف Excel أولاً")
    
    # عرض النماذج المرجعية
    with st.expander("📚 النماذج المرجعية (Syntax Files)"):
        st.markdown("""
        **النماذج التي تم الاقتداء بها:**
        
        1. **Syntax2.sps** - Major League Baseball Analysis
           - تحليل شامل لمجموعة البيانات 2
           - يتضمن T-TEST, ANOVA, RECODE متقدم
           - تسميات متغيرات مفصلة
        
        2. **Syntax3.sps** - Banking Data Analysis  
           - تحليل البيانات المصرفية
           - استخدام K-rule لتصنيف البيانات
           - فترات ثقة وتحليل تشتت
        
        3. **Syntax4.sps** - Social Survey Analysis
           - تحليل استبيان اجتماعي
           - تحليل انحدار خطي متعدد
           - اختبارات ارتباط غير بارامترية
        
        **مميزات المولد الحالي:**
        - يولد أكواد بنفس الجودة
        - يضيف التعليقات العلمية
        - يدعم جميع أنواع التحليلات
        - متوافق مع SPSS V26+
        """)
    
    # تذييل الصفحة
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;' class='arabic-text'>
        <p>مولد أكواد SPSS المتقدم | نفس جودة Syntax2.sps, Syntax3.sps, Syntax4.sps</p>
        <p>© 2024 - تم التطوير لإنشاء أكواد SPSS احترافية تلقائياً</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
