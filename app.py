import re

# 1. محاكاة ملف القواعد (بدل قراءة ملف CSV)
RULES_DB = {
    "frequency": "FREQUENCIES VARIABLES={var} /ORDER=ANALYSIS.",
    "mean": "DESCRIPTIVES VARIABLES={var} /STATISTICS=MEAN STDDEV MIN MAX.",
    "t-test": "T-TEST GROUPS={group}(1 2) /MISSING=ANALYSIS /VARIABLES={var} /CRITERIA=CI(.95).",
    "correlation": "CORRELATIONS /VARIABLES={var1} {var2} /PRINT=TWOTAIL NOSIG.",
    "regression": "REGRESSION /DEPENDENT {dep} /METHOD=ENTER {indep}."
}

# 2. قاموس المرادفات (لجعل الكود ذكياً)
SYNONYMS = {
    "average": "mean", "summary": "mean", "متوسط": "mean",
    "count": "frequency", "distribution": "frequency", "تكرار": "frequency",
    "compare": "t-test", "difference": "t-test", "فروق": "t-test",
    "relationship": "correlation", "link": "correlation", "علاقة": "correlation",
    "predict": "regression", "impact": "regression", "تأثير": "regression"
}

def solve_one_question(question_text, available_columns):
    """
    دالة تأخذ نص السؤال وأسماء أعمدة الإكسل، وترجع كود SPSS
    """
    print(f"🔍 جاري تحليل السؤال: '{question_text}'")
    
    # أ) البحث عن المتغيرات (Variables Detection)
    found_vars = []
    for col in available_columns:
        # بحث غير حساس لحالة الأحرف
        if re.search(re.escape(col), question_text, re.IGNORECASE):
            found_vars.append(col)
    
    if not found_vars:
        return "❌ خطأ: لم يتم العثور على اسم أي عمود من الإكسل داخل السؤال."

    # ب) تحديد نوع الاختبار (Rule Detection)
    selected_rule_key = None
    question_lower = question_text.lower()
    
    # 1. البحث في المرادفات أولاً
    for word, key in SYNONYMS.items():
        if word in question_lower:
            selected_rule_key = key
            break
            
    # 2. إذا لم نجد، نبحث في القواعد مباشرة
    if not selected_rule_key:
        for key in RULES_DB:
            if key in question_lower:
                selected_rule_key = key
                break
    
    if not selected_rule_key:
        return "❌ خطأ: لم أفهم نوع التحليل المطلوب (حاول استخدام كلمات مثل average, test, plot)."

    # ج) تعبئة الكود (Template Filling)
    template = RULES_DB[selected_rule_key]
    syntax = template
    
    # منطق بسيط للتعبئة
    if selected_rule_key == "t-test":
        # نفترض أن المتغير الثاني هو الجروب (أو الأول إذا كان الوحيد فئوي)
        group_var = found_vars[1] if len(found_vars) > 1 else "GROUP_VAR"
        test_var = found_vars[0]
        syntax = syntax.replace("{group}", group_var).replace("{var}", test_var)
        
    elif selected_rule_key == "regression":
        dep_var = found_vars[0] # المتغير التابع
        indep_var = found_vars[1] if len(found_vars) > 1 else "INDEP_VAR"
        syntax = syntax.replace("{dep}", dep_var).replace("{indep}", indep_var)
        
    elif selected_rule_key == "correlation":
        var1 = found_vars[0]
        var2 = found_vars[1] if len(found_vars) > 1 else "VAR2"
        syntax = syntax.replace("{var1}", var1).replace("{var2}", var2)
        
    else: # mean, frequency
        syntax = syntax.replace("{var}", " ".join(found_vars))

    return f"* CODE GENERATED:\n{syntax}"

# --- تجربة الكود ---

# لنفترض أن هذه أعمدة ملف الإكسل
excel_columns = ["Income", "Gender", "Age", "Education"]

# سيناريو 1: سؤال عن المتوسط
q1 = "Calculate the average Income for employees."
print(solve_one_question(q1, excel_columns))
print("-" * 30)

# سيناريو 2: سؤال عن الفروق (T-Test)
q2 = "Is there a significant difference in Income based on Gender?"
print(solve_one_question(q2, excel_columns))
print("-" * 30)

# سيناريو 3: سؤال عربي
q3 = "ما هو تكرار متغير Education؟"
print(solve_one_question(q3, excel_columns))
