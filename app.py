import pandas as pd
import docx
import re
import os
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class SPSSQuestionAnalyzer:
    def __init__(self, excel_path: str, word_path: str):
        """
        تهيئة المحلل مع مسارات الملفات
        """
        self.excel_path = excel_path
        self.word_path = word_path
        self.dataset_name = os.path.basename(excel_path).split('.')[0]
        self.data = self.load_excel_data()
        self.questions = self.extract_questions()
        self.variable_definitions = self.extract_variable_definitions()
        
    def load_excel_data(self) -> pd.DataFrame:
        """تحميل البيانات من ملف Excel"""
        try:
            # محاولة قراءة الملف مع تحديد الورقة الأولى
            data = pd.read_excel(self.excel_path, sheet_name=0)
            return data
        except Exception as e:
            print(f"خطأ في تحميل ملف Excel: {e}")
            return None
    
    def extract_questions(self) -> List[str]:
        """استخراج الأسئلة من ملف Word"""
        questions = []
        try:
            doc = docx.Document(self.word_path)
            for para in doc.paragraphs:
                text = para.text.strip()
                # البحث عن الأسئلة المرقمة
                if re.match(r'^\d+[\.\)]\s+', text) or re.match(r'^\d+\.\s+', text):
                    questions.append(text)
                # إضافة النص إذا كان يحتوي على سؤال
                elif any(keyword in text.lower() for keyword in ['draw', 'construct', 'calculate', 'test', 'find']):
                    questions.append(text)
            return questions
        except Exception as e:
            print(f"خطأ في قراءة ملف Word: {e}")
            return []
    
    def extract_variable_definitions(self) -> Dict[str, str]:
        """استخراج تعريفات المتغيرات من نهاية ملف Word"""
        definitions = {}
        try:
            doc = docx.Document(self.word_path)
            for para in doc.paragraphs:
                text = para.text.strip()
                # البحث عن تعريفات المتغيرات (عادة تأتي في النهاية)
                if '=' in text and ('X' in text or 'x' in text):
                    parts = text.split('=')
                    if len(parts) >= 2:
                        var_name = parts[0].strip()
                        var_desc = parts[1].strip()
                        definitions[var_name] = var_desc
            return definitions
        except:
            return {}
    
    def detect_analysis_type(self, question: str) -> str:
        """تحديد نوع التحليل الإحصائي المطلوب"""
        question_lower = question.lower()
        
        # أنواع التحليل المختلفة
        analysis_types = {
            'bar_chart': ['bar chart', 'رسم بياني عمودي', 'مخطط عمودي'],
            'pie_chart': ['pie chart', 'رسم دائري', 'مخطط دائري'],
            'frequency': ['frequency table', 'جدول تكراري', 'توزيع تكراري'],
            'descriptive': ['mean', 'median', 'mode', 'standard deviation', 'مقاييس النزعة المركزية'],
            'confidence_interval': ['confidence interval', 'فترة ثقة'],
            'normality': ['normality', 'empirical rule', 'chebycheve', 'التوزيع الطبيعي'],
            'outliers': ['outliers', 'extreme value', 'القيم المتطرفة'],
            'hypothesis': ['test the hypothesis', 'اختبار الفرضية', 'null hypothesis'],
            'correlation': ['correlation', 'ارتباط'],
            'regression': ['regression', 'انحدار'],
            'histogram': ['histogram', 'مدرج تكراري'],
            'anova': ['anova', 'تحليل التباين']
        }
        
        for analysis_type, keywords in analysis_types.items():
            for keyword in keywords:
                if keyword in question_lower:
                    return analysis_type
        
        return 'unknown'
    
    def extract_variables_from_question(self, question: str) -> List[str]:
        """استخراج المتغيرات المذكورة في السؤال"""
        found_vars = []
        # البحث عن المتغيرات في السؤال (مثل X1, X2, salary, age, etc.)
        for col in self.data.columns:
            if isinstance(col, str):
                # البحث بأسماء المتغيرات
                if col.lower() in question.lower():
                    found_vars.append(col)
                # البحث برموز X
                elif f'x{col}' in question.lower() or f'X{col}' in question.lower():
                    found_vars.append(col)
        
        return found_vars
    
    def generate_spss_syntax(self, question: str, analysis_type: str, variables: List[str]) -> str:
        """إنشاء كود SPSS بناءً على نوع التحليل"""
        
        # رأس الكود
        syntax = f"* SPSS Syntax for: {question[:50]}...\n"
        syntax += f"* Dataset: {self.dataset_name}\n"
        syntax += f"* Analysis Type: {analysis_type}\n\n"
        
        if analysis_type == 'frequency':
            syntax += self.generate_frequency_syntax(variables)
        elif analysis_type == 'descriptive':
            syntax += self.generate_descriptive_syntax(variables)
        elif analysis_type == 'bar_chart':
            syntax += self.generate_barchart_syntax(variables, question)
        elif analysis_type == 'pie_chart':
            syntax += self.generate_piechart_syntax(variables, question)
        elif analysis_type == 'confidence_interval':
            syntax += self.generate_confidence_syntax(variables)
        elif analysis_type == 'hypothesis':
            syntax += self.generate_hypothesis_syntax(variables, question)
        elif analysis_type == 'correlation':
            syntax += self.generate_correlation_syntax(variables)
        elif analysis_type == 'histogram':
            syntax += self.generate_histogram_syntax(variables)
        elif analysis_type == 'normality':
            syntax += self.generate_normality_syntax(variables)
        elif analysis_type == 'outliers':
            syntax += self.generate_outliers_syntax(variables)
        else:
            syntax += "* No specific syntax generated for this question type.\n"
            syntax += "* Please check the question and analysis type.\n"
        
        return syntax
    
    def generate_frequency_syntax(self, variables: List[str]) -> str:
        """إنشاء كود لجدول التكرارات"""
        syntax = "FREQUENCIES VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /STATISTICS=MEAN MEDIAN MODE STDDEV MIN MAX RANGE\n"
        syntax += "  /ORDER=ANALYSIS.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_descriptive_syntax(self, variables: List[str]) -> str:
        """إنشاء كود للمقاييس الوصفية"""
        syntax = "DESCRIPTIVES VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /STATISTICS=MEAN MEDIAN MODE STDDEV MIN MAX RANGE VAR.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_barchart_syntax(self, variables: List[str], question: str) -> str:
        """إنشاء كود للرسم البياني العمودي"""
        syntax = "GGRAPH\n"
        syntax += "  /GRAPHDATASET NAME=\"graphdataset\" VARIABLES="
        
        if len(variables) >= 2:
            syntax += f"{variables[0]} {variables[1]}\n"
            syntax += "  /GRAPHSPEC SOURCE=INLINE.\n"
            syntax += "BEGIN GPL\n"
            syntax += f"  SOURCE: s=userSource(id(\"graphdataset\"))\n"
            syntax += f"  DATA: {variables[0]}=col(source(s), name(\"{variables[0]}\"))\n"
            syntax += f"  DATA: {variables[1]}=col(source(s), name(\"{variables[1]}\"), unit.category())\n"
            syntax += "  GUIDE: axis(dim(1), label(\"Variable\"))\n"
            syntax += "  GUIDE: axis(dim(2), label(\"Value\"))\n"
            syntax += "  ELEMENT: interval(position({variables[1]}*{variables[0]}))\n"
            syntax += "END GPL.\n"
        else:
            syntax += f"{variables[0]}\n"
            syntax += "  /GRAPHSPEC SOURCE=INLINE.\n"
            syntax += "BEGIN GPL\n"
            syntax += f"  SOURCE: s=userSource(id(\"graphdataset\"))\n"
            syntax += f"  DATA: {variables[0]}=col(source(s), name(\"{variables[0]}\"))\n"
            syntax += "  GUIDE: axis(dim(1), label(\"Variable\"))\n"
            syntax += "  GUIDE: axis(dim(2), label(\"Frequency\"))\n"
            syntax += f"  ELEMENT: interval(position({variables[0]}))\n"
            syntax += "END GPL.\n"
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_piechart_syntax(self, variables: List[str], question: str) -> str:
        """إنشاء كود للرسم البياني الدائري"""
        syntax = "GRAPH\n"
        syntax += "  /PIE=PCT BY "
        syntax += " ".join(variables) + "\n"
        syntax += "  /TITLE='Pie Chart'.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_confidence_syntax(self, variables: List[str]) -> str:
        """إنشاء كلفترة الثقة"""
        syntax = ""
        for var in variables:
            syntax += f"* 95% Confidence Interval for {var}\n"
            syntax += f"EXAMINE VARIABLES={var}\n"
            syntax += "  /PLOT NONE\n"
            syntax += "  /STATISTICS DESCRIPTIVES\n"
            syntax += f"  /CINTERVAL 95\n"
            syntax += "  /MISSING LISTWISE.\n\n"
            
            syntax += f"* 99% Confidence Interval for {var}\n"
            syntax += f"EXAMINE VARIABLES={var}\n"
            syntax += "  /PLOT NONE\n"
            syntax += "  /STATISTICS DESCRIPTIVES\n"
            syntax += f"  /CINTERVAL 99\n"
            syntax += "  /MISSING LISTWISE.\n\n"
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_hypothesis_syntax(self, variables: List[str], question: str) -> str:
        """إنشاء كود لاختبار الفرضيات"""
        syntax = ""
        
        # تحديد نوع الاختبار بناءً على السؤال
        if 'equal' in question.lower() or 'يساوي' in question.lower():
            test_value = self.extract_test_value(question)
            syntax += f"* One-Sample T-Test\n"
            syntax += f"T-TEST\n"
            syntax += f"  /TESTVAL={test_value}\n"
            syntax += f"  /MISSING=ANALYSIS\n"
            syntax += f"  /VARIABLES={variables[0] if variables else 'VAR001'}\n"
            syntax += f"  /CRITERIA=CI(.95).\n"
        elif 'difference' in question.lower() or 'اختلاف' in question.lower():
            if len(variables) >= 2:
                syntax += f"* Independent Samples T-Test\n"
                syntax += f"T-TEST GROUPS={variables[0]}(1 0)\n"
                syntax += f"  /VARIABLES={variables[1]}\n"
                syntax += f"  /MISSING=ANALYSIS\n"
                syntax += f"  /CRITERIA=CI(.95).\n"
            else:
                syntax += "* Need at least two variables for difference test\n"
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_correlation_syntax(self, variables: List[str]) -> str:
        """إنشاء كود لمعامل الارتباط"""
        syntax = "CORRELATIONS\n"
        syntax += "  /VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /PRINT=TWOTAIL NOSIG\n"
        syntax += "  /MISSING=PAIRWISE.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_histogram_syntax(self, variables: List[str]) -> str:
        """إنشاء كود للمدرج التكراري"""
        syntax = "GRAPH\n"
        syntax += "  /HISTOGRAM="
        syntax += " ".join(variables) + "\n"
        syntax += "  /TITLE='Histogram'.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_normality_syntax(self, variables: List[str]) -> str:
        """إنشاء كود لفحص normality"""
        syntax = ""
        for var in variables:
            syntax += f"* Normality test for {var}\n"
            syntax += f"EXAMINE VARIABLES={var}\n"
            syntax += "  /PLOT HISTOGRAM NPPLOT\n"
            syntax += "  /COMPARE GROUP\n"
            syntax += "  /STATISTICS DESCRIPTIVES\n"
            syntax += "  /CINTERVAL 95\n"
            syntax += "  /MISSING LISTWISE\n"
            syntax += "  /NOTOTAL.\n\n"
        
        syntax += "EXECUTE.\n"
        return syntax
    
    def generate_outliers_syntax(self, variables: List[str]) -> str:
        """إنشاء كود للكشف عن القيم المتطرفة"""
        syntax = "EXAMINE VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /PLOT BOXPLOT\n"
        syntax += "  /COMPARE GROUP\n"
        syntax += "  /STATISTICS DESCRIPTIVES\n"
        syntax += "  /CINTERVAL 95\n"
        syntax += "  /MISSING LISTWISE\n"
        syntax += "  /NOTOTAL.\n"
        syntax += "EXECUTE.\n"
        return syntax
    
    def extract_test_value(self, question: str) -> str:
        """استخراج قيمة الاختبار من السؤال"""
        # البحث عن أرقام في السؤال
        numbers = re.findall(r'\d+', question)
        if numbers:
            return numbers[0]
        return "0"
    
    def process_all_questions(self) -> Dict[int, Dict[str, Any]]:
        """معالجة جميع الأسئلة"""
        results = {}
        
        print(f"=== معالجة ملف: {self.dataset_name} ===\n")
        print(f"عدد الأسئلة: {len(self.questions)}\n")
        print(f"المتغيرات في البيانات: {list(self.data.columns)}\n")
        
        for i, question in enumerate(self.questions, 1):
            print(f"السؤال {i}: {question[:100]}...")
            
            # تحديد نوع التحليل
            analysis_type = self.detect_analysis_type(question)
            print(f"  نوع التحليل: {analysis_type}")
            
            # استخراج المتغيرات
            variables = self.extract_variables_from_question(question)
            print(f"  المتغيرات المستخرجة: {variables}")
            
            # إنشاء كود SPSS
            spss_syntax = self.generate_spss_syntax(question, analysis_type, variables)
            
            # حفظ النتائج
            results[i] = {
                'question': question,
                'analysis_type': analysis_type,
                'variables': variables,
                'spss_syntax': spss_syntax
            }
            
            print(f"  تم إنشاء كود SPSS\n")
        
        return results
    
    def save_syntax_to_file(self, results: Dict[int, Dict[str, Any]], output_path: str):
        """حفظ كود SPSS في ملف"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"* SPSS Syntax File\n")
            f.write(f"* Generated from: {self.dataset_name}\n")
            f.write(f"* Date: {pd.Timestamp.now()}\n")
            f.write(f"* Total Questions: {len(results)}\n")
            f.write("*" * 80 + "\n\n")
            
            for i, result in results.items():
                f.write(f"* Question {i}: {result['question'][:100]}...\n")
                f.write(f"* Analysis Type: {result['analysis_type']}\n")
                f.write(f"* Variables: {result['variables']}\n")
                f.write("-" * 60 + "\n")
                f.write(result['spss_syntax'])
                f.write("\n" + "=" * 80 + "\n\n")
        
        print(f"تم حفظ ملف SPSS Syntax في: {output_path}")


class SPSSGeneratorManager:
    """مدير لمعالجة جميع مجموعات البيانات"""
    
    def __init__(self, data_files: List[str], question_files: List[str]):
        self.data_files = data_files
        self.question_files = question_files
    
    def generate_all_syntax(self):
        """إنشاء كود SPSS لجميع مجموعات البيانات"""
        all_results = {}
        
        for data_file, question_file in zip(self.data_files, self.question_files):
            if os.path.exists(data_file) and os.path.exists(question_file):
                analyzer = SPSSQuestionAnalyzer(data_file, question_file)
                results = analyzer.process_all_questions()
                
                # حفظ النتائج في ملف
                output_file = f"SPSS_Syntax_{analyzer.dataset_name}.sps"
                analyzer.save_syntax_to_file(results, output_file)
                
                all_results[analyzer.dataset_name] = results
            else:
                print(f"ملف مفقود: {data_file} أو {question_file}")
        
        return all_results
    
    def generate_summary_report(self, all_results: Dict[str, Any]):
        """إنشاء تقرير ملخص"""
        report_file = "SPSS_Syntax_Summary.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("تقرير ملخص لجميع ملفات SPSS Syntax\n")
            f.write("=" * 60 + "\n\n")
            
            total_questions = 0
            for dataset_name, results in all_results.items():
                f.write(f"مجموعة البيانات: {dataset_name}\n")
                f.write(f"عدد الأسئلة: {len(results)}\n")
                f.write("-" * 40 + "\n")
                
                for q_num, result in results.items():
                    f.write(f"  السؤال {q_num}: {result['analysis_type']}\n")
                    f.write(f"    المتغيرات: {result['variables']}\n")
                
                f.write("\n")
                total_questions += len(results)
            
            f.write(f"إجمالي الأسئلة المعالجة: {total_questions}\n")
            f.write(f"عدد مجموعات البيانات: {len(all_results)}\n")
        
        print(f"تم حفظ التقرير الملخص في: {report_file}")


# ===== الاستخدام الرئيسي للبرنامج =====

def main():
    """الدالة الرئيسية لتشغيل البرنامج"""
    
    # تعريف مسارات الملفات
    data_files = [
        "Data set 1.xls",
        "Data set 2.xls", 
        "Data set 3.xls",
        "Data set 4.xls"
    ]
    
    question_files = [
        "SPSS questions For data set 1.doc",
        "SPSS questioins For data set 2.doc",
        "SPSS questioins For data set 3.doc",
        "SPSS questioins For data set 4 .doc"
    ]
    
    # إنشاء مدير المعالجة
    manager = SPSSGeneratorManager(data_files, question_files)
    
    # توليد كود SPSS لجميع الملفات
    print("=== بدء توليد كود SPSS Syntax ===")
    all_results = manager.generate_all_syntax()
    
    # إنشاء تقرير ملخص
    manager.generate_summary_report(all_results)
    
    print("\n=== اكتمل توليد الكود بنجاح ===")
    print("ملفات SPSS Syntax المتولدة:")
    for data_file in data_files:
        dataset_name = os.path.basename(data_file).split('.')[0]
        print(f"  - SPSS_Syntax_{dataset_name}.sps")


# ===== مثال لمعالجة سؤال محدد =====

def process_single_dataset():
    """معالجة مجموعة بيانات واحدة كمثال"""
    
    # استخدام Data set 2 كمثال
    analyzer = SPSSQuestionAnalyzer("Data set 2.xls", "SPSS questioins For data set 2.doc")
    
    # معالجة سؤال محدد
    sample_question = "Draw a bar chart that shows the average salary for American and national teams."
    
    print(f"السؤال المثال: {sample_question}")
    
    # تحليل السؤال
    analysis_type = analyzer.detect_analysis_type(sample_question)
    variables = analyzer.extract_variables_from_question(sample_question)
    syntax = analyzer.generate_spss_syntax(sample_question, analysis_type, variables)
    
    print(f"نوع التحليل: {analysis_type}")
    print(f"المتغيرات: {variables}")
    print(f"\nكود SPSS المتولد:\n")
    print(syntax)


if __name__ == "__main__":
    # لتشغيل البرنامج الكامل
    main()
    
    # أو لتشغيل مثال واحد
    # process_single_dataset()
