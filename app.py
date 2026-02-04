* Encoding: UTF-8.
SET DECIMAL=DOT.
* =================================================================.
* SPSS Comprehensive Solution for MBA Exam - Data Set 4
* Prepared for: Dr. Mohamed A. Salam
* =================================================================.

* --- [الخطوة 1: تعريف المتغيرات والقيم] --- .
VARIABLE LABELS 
  x1 "Gender" /x2 "Race" /x3 "Salary" /x4 "Region" /x5 "General Happiness" 
  /x6 "Is Life Exciting" /x7 "Number of Brothers/Sisters" /x8 "Number of Children" 
  /x9 "Age" /x10 "Schooling Years" /x11 "Occupation" /x12 "Most Important Problem".

VALUE LABELS x1 1 "Male" 2 "Female" 
 /x2 1 "White" 2 "Black" 3 "Other"
 /x4 1 "North East" 2 "South East" 3 "West"
 /x5 1 "Very Happy" 2 "Pretty Happy" 3 "Not Too Happy"
 /x11 1 "Managerial" 2 "Technical" 3 "Service" 4 "Others".
EXECUTE.

* --- [Q1] جداول التكرار للبيانات النوعية (الفصل 2) --- .
FREQUENCIES VARIABLES=x1 x2 x4 x5 x11 x12 /ORDER=ANALYSIS.

* --- [Q2-Q4] الرسوم البيانية (Bar Charts) --- .
* عدد المستجيبين حسب المنطقة.
GRAPH /BAR(SIMPLE)=COUNT BY x4 /TITLE="Number of Respondents by Region".
* متوسط الراتب حسب المنطقة.
GRAPH /BAR(SIMPLE)=MEAN(x3) BY x4 /TITLE="Average Salary by Region".
* متوسط عدد الأطفال حسب العرق (تصحيح الكود السابق).
GRAPH /BAR(SIMPLE)=MEAN(x8) BY x2 /TITLE="Average Children by Race".

* --- [Q5-Q6] الرسوم الدائرية (Pie Charts) --- .
* مجموع الرواتب لكل وظيفة.
GRAPH /PIE=SUM(x3) BY x11 /TITLE="Sum of Salaries by Occupation".
* نسبة الذكور والإناث (تصحيح الكود السابق: استخدام x1 بدلاً من x9).
GRAPH /PIE=COUNT BY x1 /TITLE="Gender Percentage".

* --- [Q7-Q8] البيانات المستمرة والإحصاء الوصفي (الفصل 2) --- .
* تقسيم الراتب والعمر لـ 5 فئات (حساب آلي بناءً على المدى المذكور 16950-135000).
RECODE x3 (LO THRU 40000=1) (40001 THRU 64000=2) (64001 THRU 88000=3) (88001 THRU 112000=4) (HI=5) INTO x3_CL.
RECODE x9 (LO THRU 32=1) (33 THRU 44=2) (45 THRU 56=3) (57 THRU 68=4) (HI=5) INTO x9_CL.
VARIABLE LABELS x3_CL "Salary Classes" /x9_CL "Age Classes".
FREQUENCIES VARIABLES=x3_CL x9_CL /FORMAT=NOTABLE.

* إيجاد المتوسط، الوسيط، المنوال، والانحراف المعياري.
FREQUENCIES VARIABLES=x3 x9 x7 x8 /FORMAT=NOTABLE 
 /STATISTICS=MEAN MEDIAN MODE STDDEV RANGE MIN MAX.

* --- [Q9-Q10] الاعتدالية والقيم المتطرفة (الفصل 2 & 7) --- .
EXAMINE VARIABLES=x3 x10 /PLOT BOXPLOT HISTOGRAM NPPLOT /STATISTICS DESCRIPTIVES.

* --- [Q11] التحليل المقسم حسب النوع والمنطقة (الفصل 4) --- .
SORT CASES BY x4 x1.
SPLIT FILE LAYERED BY x4 x1.
DESCRIPTIVES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN MEDIAN STDDEV.
SPLIT FILE OFF.

* --- [Q12] فترات الثقة 95% و 99% (الفصل 3) --- .
EXAMINE VARIABLES=x3 x9 BY x4 /STATISTICS DESCRIPTIVES /CINTERVAL 95 /PLOT NONE.
EXAMINE VARIABLES=x3 x9 BY x4 /STATISTICS DESCRIPTIVES /CINTERVAL 99 /PLOT NONE.

* --- [Q13-Q14] اختبارات تاء لعينة واحدة (الفصل 3) --- .
* هل متوسط الراتب يساوي 35000؟.
T-TEST /TESTVAL=35000 /VARIABLES=x3.
* هل متوسط العمر في منطقتي الشمال والجنوب الشرقي يساوي 45؟.
TEMPORARY.
SELECT IF (x4 = 1 OR x4 = 2).
T-TEST /TESTVAL=45 /VARIABLES=x9.

* --- [Q15-Q22] اختبارات الفروق (T-Test & ANOVA) (الفصل 4 & 6) --- .
* الفرق في السعادة بين الشمال والجنوب الشرقي (مجموعتين = T-Test).
T-TEST GROUPS=x4(1 2) /VARIABLES=x5.
* الفرق في عدد الأطفال بين الشرق والغرب.
RECODE x4 (1 2=1) (3=2) INTO Region_EW.
T-TEST GROUPS=Region_EW(1 2) /VARIABLES=x8.
* الفرق في الرواتب بين جميع المناطق (أكثر من مجموعتين = ANOVA).
ONEWAY x3 BY x4 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.
* الفرق في السعادة حسب العرق.
ONEWAY x5 BY x2 /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.

* --- [Q23-Q24] الارتباط (Correlation) (الفصل 8) --- .
* ارتباط بيرسون للراتب والعمر (كمي).
CORRELATIONS /VARIABLES=x3 x9 /PRINT=TWOTAIL NOSIG.
* ارتباط سبيرمان للسعادة والوظيفة (رتبي).
NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.

* --- [Q25] الانحدار الخطي المتعدد (الفصل 10) --- .
REGRESSION
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS R ANOVA COLLIN TOL
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN 
  /DEPENDENT x5
  /METHOD=ENTER x1 x2 x3 x4 x6 x7 x8 x9 x10 x11 x12.

EXECUTE.
