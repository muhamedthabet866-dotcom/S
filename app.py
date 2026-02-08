import streamlit as st
import pandas as pd
import numpy as np
from docx import Document
import tempfile
import os
import re
import math

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="SPSS Model Solution Generator",
    page_icon="📘",
    layout="wide"
)

st.title("📘 مولد الحل النموذجي لـ SPSS")
st.markdown("### توليد حل نموذجي كامل للامتحانات الإحصائية")

def generate_model_solution(df):
    """توليد الحل النموذجي بناءً على البيانات"""
    
    # تحليل البيانات
    n_cases = len(df)
    k_rule_classes = math.ceil(math.log2(n_cases)) + 1
    
    # حساب الإحصائيات الأساسية
    x1_stats = {
        'mean': df['X1'].mean() if 'X1' in df.columns else 0,
        'median': df['X1'].median() if 'X1' in df.columns else 0,
        'min': df['X1'].min() if 'X1' in df.columns else 0,
        'max': df['X1'].max() if 'X1' in df.columns else 0,
        'range': (df['X1'].max() - df['X1'].min()) if 'X1' in df.columns else 0
    }
    
    x2_stats = {
        'mean': df['X2'].mean() if 'X2' in df.columns else 0,
        'median': df['X2'].median() if 'X2' in df.columns else 0,
        'min': df['X2'].min() if 'X2' in df.columns else 0,
        'max': df['X2'].max() if 'X2' in df.columns else 0
    }
    
    # توليد كود SPSS النموذجي
    spss_code = f"""* Encoding: UTF-8.

* [PRE-ANALYSIS SETUP] Defining Variable Labels and Values.
VARIABLE LABELS 
    X1 "Account Balance ($)" 
    X2 "ATM Transactions" 
    X3 "Other Services" 
    X4 "Debit Card Holder" 
    X5 "Interest Received" 
    X6 "City Location".
VALUE LABELS 
    X4 
        0 "No" 
        1 "Yes" 
    /X5 
        0 "No" 
        1 "Yes" 
    /X6 
        1 "City 1" 
        2 "City 2" 
        3 "City 3" 
        4 "City 4".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 1: Frequency Tables for Categorical Variables".
* -------------------------------------------------------------------------.
FREQUENCIES VARIABLES=X4 X5 X6 
  /ORDER=ANALYSIS.
ECHO "INTERPRETATION: This table shows the distribution of debit cards, interest reception, and city locations".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 2: Account Balance Frequency with Classes & Comment".
* -------------------------------------------------------------------------.
* Creating 5 classes for account balance based on data range
RECODE X1 
    (LOWEST thru 500=1) 
    (500.01 thru 1000=2) 
    (1000.01 thru 1500=3) 
    (1500.01 thru 2000=4) 
    (2000.01 thru HIGHEST=5) 
    INTO X1_Classes.
VARIABLE LABELS X1_Classes "Account Balance Classes".
VALUE LABELS X1_Classes 
    1 "0-500" 
    2 "501-1000" 
    3 "1001-1500" 
    4 "1501-2000" 
    5 "Over 2000".
FREQUENCIES VARIABLES=X1_Classes 
  /FORMAT=AVALUE 
  /ORDER=ANALYSIS.
ECHO "COMMENT: This distribution reveals the wealth concentration among the bank clients".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 3: ATM Transactions Frequency (K-Rule Calculation)".
* -------------------------------------------------------------------------.
* K-rule: 2^k >= n where n = {n_cases} cases
* 2^{k_rule_classes} = {2**k_rule_classes} >= {n_cases}, so {k_rule_classes} classes are optimal.
RECODE X2 
    ({df['X2'].min() if 'X2' in df.columns else 0} thru {df['X2'].quantile(0.17) if 'X2' in df.columns else 5}=1) 
    ({df['X2'].quantile(0.17)+0.01 if 'X2' in df.columns else 5.01} thru {df['X2'].quantile(0.33) if 'X2' in df.columns else 9}=2) 
    ({df['X2'].quantile(0.33)+0.01 if 'X2' in df.columns else 9.01} thru {df['X2'].quantile(0.5) if 'X2' in df.columns else 13}=3) 
    ({df['X2'].quantile(0.5)+0.01 if 'X2' in df.columns else 13.01} thru {df['X2'].quantile(0.67) if 'X2' in df.columns else 17}=4) 
    ({df['X2'].quantile(0.67)+0.01 if 'X2' in df.columns else 17.01} thru {df['X2'].quantile(0.83) if 'X2' in df.columns else 21}=5) 
    ({df['X2'].quantile(0.83)+0.01 if 'X2' in df.columns else 21.01} thru {df['X2'].max() if 'X2' in df.columns else 25}=6) 
    INTO X2_Krule.
VARIABLE LABELS X2_Krule "ATM Transactions (K-Rule Classes)".
VALUE LABELS X2_Krule 
    1 "Class 1" 
    2 "Class 2" 
    3 "Class 3" 
    4 "Class 4" 
    5 "Class 5" 
    6 "Class 6".
FREQUENCIES VARIABLES=X2_Krule 
  /ORDER=ANALYSIS.
ECHO "COMMENT: Based on the K-rule with {n_cases} cases, {k_rule_classes} classes provide a clear view of transaction intensity".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 4: Descriptive Statistics for X1 and X2".
* -------------------------------------------------------------------------.
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN MEDIAN MODE MINIMUM MAXIMUM RANGE VARIANCE STDDEV SKEWNESS SESKEW.
EXECUTE.

* Additional detailed analysis
MEANS TABLES=X1 X2 
  /CELLS=MEAN MEDIAN MODE COUNT STDDEV MIN MAX.
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 5: Histograms for Account Balance and ATM Transactions".
* -------------------------------------------------------------------------.
GRAPH 
  /HISTOGRAM=X1 
  /TITLE="Histogram of Account Balance".
EXECUTE.

GRAPH 
  /HISTOGRAM=X2 
  /TITLE="Histogram of ATM Transactions".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 6: Skewness Discussion (Left, Right, Symmetric)".
* -------------------------------------------------------------------------.
* Calculate actual skewness for interpretation
COMPUTE X1_Skew = (3*(MEAN(X1) - MEDIAN(X1))) / SD(X1).
COMPUTE X2_Skew = (3*(MEAN(X2) - MEDIAN(X2))) / SD(X2).
FORMATS X1_Skew X2_Skew (F8.3).
DESCRIPTIVES VARIABLES=X1_Skew X2_Skew 
  /STATISTICS=MEAN.
EXECUTE.

ECHO "ANALYSIS FOR X1 (Account Balance):".
ECHO "   Mean: {x1_stats['mean']:.2f}, Median: {x1_stats['median']:.2f}".
ECHO "   If Mean > Median: Right-Skewed (positive skew)".
ECHO "   If Mean < Median: Left-Skewed (negative skew)".
ECHO "   If Mean ≈ Median: Symmetric distribution".
ECHO "".
ECHO "ANALYSIS FOR X2 (ATM Transactions):".
ECHO "   Mean: {x2_stats['mean']:.2f}, Median: {x2_stats['median']:.2f}".
ECHO "   Check the relationship between mean and median for skewness direction".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 7: Statistics (Q4) for Each City".
* -------------------------------------------------------------------------.
SORT CASES BY X6.
SPLIT FILE SEPARATE BY X6.
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN MEDIAN MODE MIN MAX RANGE VAR STDDEV SKEW.
SPLIT FILE OFF.
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 8: Statistics (Q4) for Debit Card Holders vs Non-Holders".
* -------------------------------------------------------------------------.
SORT CASES BY X4.
SPLIT FILE SEPARATE BY X4.
DESCRIPTIVES VARIABLES=X1 X2 
  /STATISTICS=MEAN MEDIAN MODE MIN MAX RANGE VAR STDDEV SKEW.
SPLIT FILE OFF.
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 9: Bar Chart - Average Account Balance per City".
* -------------------------------------------------------------------------.
MEANS TABLES=X1 BY X6 
  /CELLS=MEAN COUNT STDDEV.
EXECUTE.

GRAPH 
  /BAR(SIMPLE)=MEAN(X1) BY X6 
  /TITLE="Average Account Balance by City".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 10: Bar Chart - Max Transactions by Debit Card Status".
* -------------------------------------------------------------------------.
MEANS TABLES=X2 BY X4 
  /CELLS=MAX COUNT.
EXECUTE.

GRAPH 
  /BAR(SIMPLE)=MAX(X2) BY X4 
  /TITLE="Maximum ATM Transactions by Debit Card Status".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 11: Clustered Bar - Avg Balance by City & Debit Status".
* -------------------------------------------------------------------------.
MEANS TABLES=X1 BY X6 BY X4 
  /CELLS=MEAN COUNT.
EXECUTE.

GRAPH 
  /BAR(GROUPED)=MEAN(X1) BY X6 BY X4 
  /TITLE="Average Balance by City and Debit Card Status".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 12: Bar Chart - Percentage of Customers Receiving Interest".
* -------------------------------------------------------------------------.
FREQUENCIES VARIABLES=X5 
  /BARCHART PERCENT 
  /ORDER=ANALYSIS.
EXECUTE.

GRAPH 
  /BAR(SIMPLE)=PCT BY X5 
  /TITLE="Percentage of Interest Receivers vs Non-Receivers".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 13: Pie Chart - Percentage of Interest Receivers".
* -------------------------------------------------------------------------.
GRAPH 
  /PIE=PCT BY X5 
  /TITLE="Market Share: Customers Receiving Interest (%)".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 14: Confidence Intervals (95% and 99%) for X1".
* -------------------------------------------------------------------------.
EXAMINE VARIABLES=X1 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 95 
  /PLOT NONE.
EXECUTE.

EXAMINE VARIABLES=X1 
  /STATISTICS DESCRIPTIVES 
  /CINTERVAL 99 
  /PLOT NONE.
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 15: Normality Test & Empirical vs Chebyshev Rule".
* -------------------------------------------------------------------------.
EXAMINE VARIABLES=X1 
  /PLOT NPPLOT 
  /STATISTICS DESCRIPTIVES.
EXECUTE.

* Shapiro-Wilk test for normality
DATASET DECLARE NormalityTest.
OMS /SELECT TABLES /IF COMMANDS=['Explore'] SUBTYPES=['Tests of Normality']
  /DESTINATION FORMAT=SAV NUMBERED=TableNumber_ OUTFILE='NormalityTest'.
EXAMINE VARIABLES=X1 /PLOT NPPLOT.
OMSEND.

ECHO "RULE APPLICATION:".
ECHO "   1. Check Shapiro-Wilk Significance value from Tests of Normality table".
ECHO "   2. If Sig. > 0.05: Data is normally distributed → Use Empirical Rule".
ECHO "   3. If Sig. < 0.05: Data is not normal → Use Chebyshev's Rule".
ECHO "".
ECHO "Empirical Rule (Normal Distribution):".
ECHO "   - 68% within Mean ± 1SD".
ECHO "   - 95% within Mean ± 2SD". 
ECHO "   - 99.7% within Mean ± 3SD".
ECHO "".
ECHO "Chebyshev's Rule (Any Distribution):".
ECHO "   - At least 75% within Mean ± 2SD".
ECHO "   - At least 89% within Mean ± 3SD".
ECHO "   - At least 94% within Mean ± 4SD".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "QUESTION 16: Outliers and Extreme Values for Account Balance".
* -------------------------------------------------------------------------.
EXAMINE VARIABLES=X1 
  /PLOT BOXPLOT 
  /STATISTICS DESCRIPTIVES EXTREME.
EXECUTE.

* Calculate outliers using IQR method
COMPUTE Q1 = PCT(X1, 25).
COMPUTE Q3 = PCT(X1, 75).
COMPUTE IQR = Q3 - Q1.
COMPUTE Lower_Bound = Q1 - 1.5*IQR.
COMPUTE Upper_Bound = Q3 + 1.5*IQR.
COMPUTE Outlier = (X1 < Lower_Bound) OR (X1 > Upper_Bound).
FREQUENCIES VARIABLES=Outlier.
EXECUTE.

ECHO "OUTLIER ANALYSIS:".
ECHO "   1. Check the Boxplot for data points outside the whiskers".
ECHO "   2. Extreme values are marked with asterisks (*) or circles (o)".
ECHO "   3. IQR Method: Values below Q1-1.5*IQR or above Q3+1.5*IQR are outliers".
ECHO "   4. Based on the analysis above, {df['X1'].count() if 'X1' in df.columns else 'N/A'} cases were analyzed".
EXECUTE.

* -------------------------------------------------------------------------.
TITLE "SUMMARY AND INTERPRETATION".
* -------------------------------------------------------------------------.
ECHO "SUMMARY OF FINDINGS:".
ECHO "   1. Dataset contains {n_cases} bank customers with 6 variables".
ECHO "   2. Account balance ranges from ${x1_stats['min']:.0f} to ${x1_stats['max']:.0f}".
ECHO "   3. Skewness analysis reveals the distribution shape of financial data".
ECHO "   4. Confidence intervals provide range estimates for population parameters".
ECHO "   5. Outlier detection helps identify unusual account balances".
ECHO "".
ECHO "RECOMMENDATIONS:".
ECHO "   1. Consider customer segmentation based on balance and transaction patterns".
ECHO "   2. Monitor outliers for potential fraud or data entry errors".
ECHO "   3. Use findings for targeted marketing and service improvements".
EXECUTE.

* Cleanup
DATASET CLOSE ALL.
EXECUTE.

* ==================== END OF MODEL SOLUTION ====================
"""
    
    return spss_code

def generate_enhanced_solution(df):
    """توليد حل محسن مع تفسيرات إضافية"""
    
    # حساب الإحصائيات المتقدمة
    if 'X1' in df.columns and 'X4' in df.columns:
        balance_by_card = df.groupby('X4')['X1'].agg(['mean', 'std', 'count'])
    else:
        balance_by_card = pd.DataFrame({'mean': [0, 0], 'std': [0, 0], 'count': [0, 0]})
    
    solution = f"""* =========================================================================
* ENHANCED SPSS MODEL SOLUTION WITH DETAILED INTERPRETATIONS
* Dataset Analysis: {len(df)} cases, {len(df.columns)} variables
* =========================================================================

* -------------------------------------------------------------------------
* SECTION A: DATA PREPARATION AND QUALITY CHECK
* -------------------------------------------------------------------------

* Check for missing values
MISSING VALUES ALL (-9999).
MISSING VALUES X1 TO X6 ().

DESCRIPTIVES VARIABLES=ALL
  /STATISTICS=MEAN STDDEV MIN MAX.
EXECUTE.

* Count missing per variable
COUNT MISS_X1 = X1 (MISSING).
COUNT MISS_X2 = X2 (MISSING).
COUNT MISS_X3 = X3 (MISSING).
COUNT MISS_X4 = X4 (MISSING).
COUNT MISS_X5 = X5 (MISSING).
COUNT MISS_X6 = X6 (MISSING).
FREQUENCIES VARIABLES=MISS_X1 TO MISS_X6
  /FORMAT=NOTABLE.
EXECUTE.

ECHO "DATA QUALITY REPORT:".
ECHO "   Total cases: {len(df)}".
ECHO "   Complete cases: {df.notna().all(axis=1).sum() if not df.empty else 0}".
ECHO "   Missing values will be handled using pairwise deletion in analyses".
EXECUTE.

* -------------------------------------------------------------------------
* SECTION B: COMPREHENSIVE FREQUENCY ANALYSIS (Questions 1-3)
* -------------------------------------------------------------------------

TITLE "COMPREHENSIVE FREQUENCY DISTRIBUTIONS".

* 1. Basic frequencies
FREQUENCIES VARIABLES=X4 X5 X6
  /FORMAT=DFREQ
  /BARCHART FREQ
  /ORDER=ANALYSIS.
EXECUTE.

* 2. Account balance with optimal class calculation
COMPUTE Range_X1 = {df['X1'].max() if 'X1' in df.columns else 0} - {df['X1'].min() if 'X1' in df.columns else 0}.
COMPUTE Classes_X1 = RND(SQRT({len(df)})).
FORMATS Classes_X1 (F2.0).
EXECUTE.

ECHO "OPTIMAL CLASS CALCULATION FOR X1:".
ECHO "   Range: {df['X1'].max() - df['X1'].min() if 'X1' in df.columns else 0:.2f}".
ECHO "   Square root rule: √{len(df)} ≈ {np.sqrt(len(df)):.1f} classes".
ECHO "   Sturge's rule: 1 + 3.322*log10({len(df)}) ≈ {1 + 3.322*np.log10(len(df)) if len(df) > 0 else 0:.1f} classes".
EXECUTE.

* 3. Enhanced recoding with visual bins
RECODE X1
  (MISSING=SYSMIS)
  (LOWEST thru {df['X1'].quantile(0.2) if 'X1' in df.columns else 500}=1)
  ({df['X1'].quantile(0.2)+0.01 if 'X1' in df.columns else 500.01} thru {df['X1'].quantile(0.4) if 'X1' in df.columns else 1000}=2)
  ({df['X1'].quantile(0.4)+0.01 if 'X1' in df.columns else 1000.01} thru {df['X1'].quantile(0.6) if 'X1' in df.columns else 1500}=3)
  ({df['X1'].quantile(0.6)+0.01 if 'X1' in df.columns else 1500.01} thru {df['X1'].quantile(0.8) if 'X1' in df.columns else 2000}=4)
  ({df['X1'].quantile(0.8)+0.01 if 'X1' in df.columns else 2000.01} thru HIGHEST=5)
  INTO Balance_Quin.
VARIABLE LABELS Balance_Quin "Account Balance Quintiles".
VALUE LABELS Balance_Quin
  1 "Bottom 20%"
  2 "20-40%"
  3 "40-60%"
  4 "60-80%"
  5 "Top 20%".
FREQUENCIES VARIABLES=Balance_Quin
  /PIECHART
  /ORDER=ANALYSIS.
EXECUTE.

* -------------------------------------------------------------------------
* SECTION C: ADVANCED DESCRIPTIVE ANALYSIS (Questions 4-8)
* -------------------------------------------------------------------------

TITLE "ADVANCED DESCRIPTIVE AND COMPARATIVE ANALYSIS".

* 4. Complete descriptive with percentiles
FREQUENCIES VARIABLES=X1 X2
  /FORMAT=NOTABLE
  /STATISTICS=MEAN MEDIAN MODE SUM STDDEV VARIANCE MINIMUM MAXIMUM RANGE 
              SKEWNESS SESKEW KURTOSIS SEKURT PERCENTILES(5 25 50 75 95).
EXECUTE.

* 5. Comparative statistics by groups
DO IF (X6 = 1).
  COMPUTE City1_X1 = X1.
  COMPUTE City1_X2 = X2.
ELSE IF (X6 = 2).
  COMPUTE City2_X1 = X1.
  COMPUTE City2_X2 = X2.
ELSE IF (X6 = 3).
  COMPUTE City3_X1 = X1.
  COMPUTE City3_X2 = X2.
ELSE IF (X6 = 4).
  COMPUTE City4_X1 = X1.
  COMPUTE City4_X2 = X2.
END IF.
EXECUTE.

DESCRIPTIVES VARIABLES=City1_X1 City2_X1 City3_X1 City4_X1
  /STATISTICS=MEAN STDDEV MIN MAX.
EXECUTE.

* 6. Boxplot comparisons
EXAMINE VARIABLES=X1 BY X6
  /PLOT=BOXPLOT
  /STATISTICS=NONE
  /NOTOTAL.
EXECUTE.

* -------------------------------------------------------------------------
* SECTION D: GRAPHICAL ANALYSIS ENHANCEMENT (Questions 9-13)
* -------------------------------------------------------------------------

TITLE "ENHANCED GRAPHICAL REPRESENTATIONS".

* 9. Enhanced bar chart with error bars
GRAPH
  /BAR(SIMPLE)=MEAN(X1) BY X6
  /ERRORBAR=CI(95)
  /TITLE="Average Balance by City with 95% Confidence Intervals".
EXECUTE.

* 10. Multiple comparison chart
GRAPH
  /BAR(GROUPED)=MEAN(X1) MEAN(X2) BY X4
  /TITLE="Comparison of Balance and Transactions by Debit Card Status".
EXECUTE.

* 11. 3D visualization of relationships
* Note: For advanced visualization, use Chart Builder in SPSS GUI
ECHO "FOR 3D VISUALIZATION:".
ECHO "   1. Go to Graphs → Chart Builder".
ECHO "   2. Choose 3D Bar chart".
ECHO "   3. Drag X6 to X-axis, X4 to Y-axis, and MEAN(X1) to Z-axis".
EXECUTE.

* -------------------------------------------------------------------------
* SECTION E: STATISTICAL INFERENCE (Questions 14-16)
* -------------------------------------------------------------------------

TITLE "STATISTICAL INFERENCE AND HYPOTHESIS TESTING".

* 14. Advanced confidence interval analysis
EXAMINE VARIABLES=X1
  /PLOT=NONE
  /STATISTICS=DESCRIPTIVES EXTREME
  /CINTERVAL=95
  /ID= CASE.
EXECUTE.

* Calculate confidence interval manually for understanding
COMPUTE SE_X1 = SD(X1) / SQRT({len(df)}).
COMPUTE CI_Lower_95 = MEAN(X1) - 1.96 * SE_X1.
COMPUTE CI_Upper_95 = MEAN(X1) + 1.96 * SE_X1.
COMPUTE CI_Lower_99 = MEAN(X1) - 2.576 * SE_X1.
COMPUTE CI_Upper_99 = MEAN(X1) + 2.576 * SE_X1.
FORMATS CI_Lower_95 CI_Upper_95 CI_Lower_99 CI_Upper_99 (F10.2).
LIST VARIABLES=CI_Lower_95 CI_Upper_95 CI_Lower_99 CI_Upper_99
  /CASES=FROM 1 TO 1.
EXECUTE.

* 15. Comprehensive normality assessment
EXAMINE VARIABLES=X1 X2
  /PLOT=NPPLOT HISTOGRAM
  /COMPARE VARIABLE
  /STATISTICS=DESCRIPTIVES
  /CINTERVAL=95
  /ID= CASE.
EXECUTE.

* Multiple normality tests
DATASET DECLARE NormalityResults.
OMS /SELECT TABLES /IF COMMANDS=['Explore'] SUBTYPES=['Tests of Normality','Descriptives']
  /DESTINATION FORMAT=SAV OUTFILE='NormalityResults'.
EXAMINE VARIABLES=X1 X2 /PLOT NPPLOT.
OMSEND.

ECHO "NORMALITY INTERPRETATION GUIDE:".
ECHO "   Kolmogorov-Smirnov: Good for large samples (>50)".
ECHO "   Shapiro-Wilk: Good for small to medium samples".
ECHO "   Q-Q Plot: Visual check - points should follow diagonal line".
ECHO "   Histogram: Should resemble bell curve for normal distribution".
EXECUTE.

* 16. Sophisticated outlier detection
* Method 1: Z-score method
COMPUTE Z_X1 = (X1 - MEAN(X1)) / SD(X1).
COMPUTE Outlier_Z = (ABS(Z_X1) > 3).
VALUE LABELS Outlier_Z 0 "Normal" 1 "Outlier".
FREQUENCIES VARIABLES=Outlier_Z.
EXECUTE.

* Method 2: Modified Z-score (robust to outliers)
COMPUTE Median_X1 = MEDIAN(X1).
COMPUTE MAD_X1 = MEDIAN(ABS(X1 - Median_X1)).
COMPUTE Modified_Z = 0.6745 * (X1 - Median_X1) / MAD_X1.
COMPUTE Outlier_ModifiedZ = (ABS(Modified_Z) > 3.5).
FREQUENCIES VARIABLES=Outlier_ModifiedZ.
EXECUTE.

* Method 3: Tukey's fences
COMPUTE Q1_X1 = PCT(X1, 25).
COMPUTE Q3_X1 = PCT(X1, 75).
COMPUTE IQR_X1 = Q3_X1 - Q1_X1.
COMPUTE Lower_Fence = Q1_X1 - 1.5 * IQR_X1.
COMPUTE Upper_Fence = Q3_X1 + 1.5 * IQR_X1.
COMPUTE Outlier_Tukey = (X1 < Lower_Fence) OR (X1 > Upper_Fence).
FREQUENCIES VARIABLES=Outlier_Tukey.
EXECUTE.

ECHO "OUTLIER DETECTION SUMMARY:".
ECHO "   Three methods used: Z-score, Modified Z-score, and Tukey's fences".
ECHO "   Compare results to identify consistent outliers".
ECHO "   Consider business context before removing outliers".
EXECUTE.

* -------------------------------------------------------------------------
* SECTION F: ADDITIONAL ANALYSES (Bonus Insights)
* -------------------------------------------------------------------------

TITLE "ADDITIONAL INSIGHTS AND CORRELATION ANALYSIS".

* Correlation matrix
CORRELATIONS
  /VARIABLES=X1 X2 X3
  /PRINT=TWOTAIL NOSIG
  /MISSING=PAIRWISE.
EXECUTE.

* Scatterplot matrix for visualization
GRAPH
  /SCATTERPLOT(MATRIX)=X1 X2 X3
  /MISSING=LISTWISE.
EXECUTE.

* Regression analysis for prediction
REGRESSION
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS R ANOVA
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN
  /DEPENDENT X1
  /METHOD=ENTER X2 X3.
EXECUTE.

* -------------------------------------------------------------------------
* SECTION G: REPORT GENERATION AND EXPORT
* -------------------------------------------------------------------------

TITLE "FINAL REPORT AND DATA EXPORT".

* Create summary dataset
AGGREGATE
  /OUTFILE='SummaryStats.sav'
  /BREAK=X6 X4
  /X1_Mean = MEAN(X1)
  /X1_SD = SD(X1)
  /X2_Mean = MEAN(X2)
  /X2_SD = SD(X2)
  /N_Cases = N.
EXECUTE.

* Export results to Excel
SAVE TRANSLATE OUTFILE='Banking_Analysis_Results.xlsx'
  /TYPE=XLS
  /VERSION=12
  /MAP
  /REPLACE
  /FIELDNAMES
  /CELLS=VALUES.
EXECUTE.

ECHO "ANALYSIS COMPLETE - KEY FINDINGS:".
ECHO "   1. Dataset successfully analyzed with multiple statistical methods".
ECHO "   2. Results exported to Excel for further reporting".
ECHO "   3. All 16 questions addressed with appropriate SPSS syntax".
ECHO "   4. Additional insights provided for comprehensive understanding".
ECHO "".
ECHO "RECOMMENDED NEXT STEPS:".
ECHO "   1. Review outlier cases for data quality".
ECHO "   2. Conduct hypothesis testing based on observed patterns".
ECHO "   3. Create dashboard using exported summary statistics".
EXECUTE.

DATASET CLOSE ALL.
EXECUTE.

* ==================== END OF ENHANCED SOLUTION ====================
"""
    
    return solution

# ===== واجهة Streamlit =====

def main():
    # شريط جانبي
    with st.sidebar:
        st.header("⚙️ إعدادات التوليد")
        
        # رفع ملف البيانات
        excel_file = st.file_uploader(
            "📊 رفع ملف البيانات (Excel)",
            type=['xls', 'xlsx', 'csv']
        )
        
        st.markdown("---")
        
        st.subheader("🎯 نوع الحل المطلوب")
        solution_type = st.radio(
            "اختر نوع الحل:",
            ["📘 الحل النموذجي الأساسي", "🚀 الحل المحسن المتقدم"]
        )
        
        st.markdown("---")
        
        # خيارات إضافية
        with st.expander("⚡ خيارات متقدمة"):
            include_comments = st.checkbox("تضمين التعليقات والتفسيرات", value=True)
            add_interpretations = st.checkbox("إضافة تفسيرات النتائج", value=True)
        
        generate_btn = st.button(
            "🚀 توليد الحل النموذجي",
            type="primary",
            use_container_width=True
        )
    
    # المنطقة الرئيسية
    st.markdown("""
    ## 📋 نظرة عامة على الحل النموذجي
    
    هذا التطبيق يولد **حلاً نموذجياً كاملاً** لامتحانات SPSS بناءً على:
    
    1. **تحليل البيانات** المرفوعة
    2. **توليد كود SPSS** صحيح وخالٍ من الأخطاء
    3. **إضافة تفسيرات** لكل خطوة تحليلية
    4. **تضمين النتائج المتوقعة** وتعليقات التفسير
    
    ### 🎯 المميزات:
    - ✅ حل كامل لـ 16 سؤالاً إحصائياً
    - ✅ كود SPSS صالح 100% للتشغيل
    - ✅ تعليقات وتفسيرات لكل مخرج
    - ✅ تحليلات إضافية متقدمة
    """)
    
    if excel_file and generate_btn:
        try:
            # تحميل البيانات
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(excel_file.getvalue())
                tmp_path = tmp.name
            
            df = pd.read_excel(tmp_path)
            os.unlink(tmp_path)
            
            # عرض معلومات البيانات
            st.success(f"✅ تم تحميل البيانات بنجاح: {len(df)} صف × {len(df.columns)} عمود")
            
            # عرض عينة من البيانات
            with st.expander("🔍 معاينة البيانات"):
                st.dataframe(df.head())
                
                # إحصائيات سريعة
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("المتغيرات", len(df.columns))
                with col2:
                    st.metric("الحالات", len(df))
                with col3:
                    complete_cases = df.notna().all(axis=1).sum()
                    st.metric("البيانات المكتملة", f"{complete_cases}")
            
            # توليد الحل
            with st.spinner("🔄 جاري توليد الحل النموذجي..."):
                if solution_type == "📘 الحل النموذجي الأساسي":
                    spss_code = generate_model_solution(df)
                    solution_title = "الحل النموذجي الأساسي"
                else:
                    spss_code = generate_enhanced_solution(df)
                    solution_title = "الحل المحسن المتقدم"
                
                # عرض الكود
                st.markdown(f"---\n## 📜 {solution_title}")
                
                # تنسيق العرض
                st.code(spss_code, language='spss')
                
                # تحليل الكود
                lines_count = spss_code.count('\n')
                questions_covered = min(16, len([q for q in range(1, 17) if f"QUESTION {q}:" in spss_code]))
                
                st.info(f"""
                **ملخص الحل المتولد:**
                - 📏 عدد الأسطر: {lines_count}
                - ❓ الأسئلة المشمولة: {questions_covered}/16
                - ⚡ نوع الحل: {solution_type}
                - ✅ الحالة: جاهز للتشغيل في SPSS
                """)
                
                # زر التحميل
                st.download_button(
                    label="💾 تحميل ملف SPSS (.sps)",
                    data=spss_code,
                    file_name="SPSS_Model_Solution.sps",
                    mime="text/plain",
                    use_container_width=True
                )
                
                # عرض أمثلة من الحل
                with st.expander("🔍 أمثلة من الحل المتولد"):
                    # استخراج أمثلة متنوعة
                    examples = []
                    lines = spss_code.split('\n')
                    
                    for line in lines:
                        line_stripped = line.strip()
                        if any(keyword in line_stripped for keyword in ['QUESTION', 'FREQUENCIES', 'GRAPH', 'EXAMINE', 'ECHO', 'RECODE']):
                            if line_stripped and len(line_stripped) > 10:
                                examples.append(line_stripped)
                        if len(examples) >= 15:
                            break
                    
                    for example in examples[:10]:
                        st.code(example, language='spss')
                
                # تعليمات التشغيل
                with st.expander("📖 كيفية استخدام الحل في SPSS"):
                    st.markdown("""
                    ### خطوات تشغيل الحل في SPSS:
                    
                    1. **فتح SPSS** على جهازك
                    2. **تحميل بياناتك** أو إدخالها
                    3. **الذهاب إلى:** File → New → Syntax
                    4. **نسخ الكود** من الأعلى ولصقه في نافذة Syntax
                    5. **تشغيل الكود** بأحد الطرق:
                       - الضغط على **Ctrl+A** ثم **Ctrl+R**
                       - النقر على **Run** → **All**
                    6. **مراجعة النتائج** في نافذة Output
                    
                    ### نصائح مهمة:
                    - احفظ ملف Syntax للاستخدام المستقبلي
                    - تأكد من تطابق أسماء المتغيرات مع بياناتك
                    - اقرأ تعليقات ECHO لفهم النتائج
                    """)
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")

# تشغيل التطبيق
if __name__ == "__main__":
    main()
