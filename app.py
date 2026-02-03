# أضف هذا المنطق داخل دالة توليد السينتاكس في app.py

# ... (بعد كتابة رأس الملف) ...

for p in paragraphs:
    p_low = p.lower()
    
    # تحسين منطق Split File للسؤال 17
    if "each gender in each region" in p_low:
        syntax.append("* Scientific Justification: Subgroup analysis requires splitting the file.")
        syntax.append("SORT CASES BY x4 x1.\nSPLIT FILE LAYERED BY x4 x1.")
        syntax.append("DESCRIPTIVES VARIABLES=x3 x9 x7 x8 /STATISTICS=MEAN STDDEV MIN MAX.")
        syntax.append("SPLIT FILE OFF.")

    # تحسين اختبارات الفرضيات
    elif "test the hypothesis" in p_low:
        if "35000" in p_low:
            syntax.append("T-TEST /TESTVAL=35000 /VARIABLES=x3.")
        elif "gender" in p_low or "male" in p_low:
            syntax.append("T-TEST GROUPS=x1(1 2) /VARIABLES=x3.")
        elif "region" in p_low or "race" in p_low:
            # استخدام ONEWAY للمقارنة بين أكثر من مجموعتين (Chapter 6)
            var_target = "x3" if "salary" in p_low else "x5"
            group_var = "x4" if "region" in p_low else "x2"
            syntax.append(f"ONEWAY {var_target} BY {group_var} /STATISTICS DESCRIPTIVES /POSTHOC=TUKEY.")

    # تحسين الارتباط الترتيبي (Spearman)
    elif "correlation" in p_low and ("happiness" in p_low or "occupation" in p_low):
        syntax.append("* Scientific Justification: Spearman is used for ordinal data (Happiness/Occupation).")
        syntax.append("NONPAR CORR /VARIABLES=x5 x11 /PRINT=SPEARMAN.")

    # تحسين الرسوم الدائرية (Pie Charts)
    elif "pie chart" in p_low and "sum of salaries" in p_low:
        syntax.append("GRAPH /PIE=SUM(x3) BY x11 /TITLE='Total Salaries by Occupation'.")
