import pandas as pd
import docx
import re
import os
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class SPSSv26SyntaxGenerator:
    def __init__(self, excel_path: str, word_path: str):
        """
        تهيئة مولد كود SPSS v26
        """
        self.excel_path = excel_path
        self.word_path = word_path
        self.dataset_name = os.path.basename(excel_path).split('.')[0]
        self.data = self.load_excel_data()
        self.questions = self.extract_questions()
        self.variable_map = self.create_variable_mapping()
        
    def load_excel_data(self) -> pd.DataFrame:
        """تحميل البيانات من Excel"""
        try:
            data = pd.read_excel(self.excel_path, sheet_name=0)
            
            # تنظيف أسماء الأعمدة
            data.columns = [str(col).strip() for col in data.columns]
            
            # تحليل أنواع البيانات
            self.data_types = {}
            for col in data.columns:
                if data[col].dtype == 'object':
                    self.data_types[col] = 'STRING'
                elif len(data[col].unique()) < 10:
                    self.data_types[col] = 'CATEGORICAL'
                else:
                    self.data_types[col] = 'SCALE'
            
            return data
        except Exception as e:
            print(f"Error loading Excel: {e}")
            return pd.DataFrame()
    
    def extract_questions(self) -> List[Dict]:
        """استخراج وتنظيم الأسئلة من ملف Word"""
        questions = []
        try:
            doc = docx.Document(self.word_path)
            current_question = None
            
            for para in doc.paragraphs:
                text = para.text.strip()
                
                # تحديد إذا كان هذا سؤالاً مرقماً
                if re.match(r'^\d+[\.\)]\s*', text):
                    if current_question:
                        questions.append(current_question)
                    
                    # استخراج رقم السؤال
                    match = re.match(r'^(\d+)[\.\)]\s*(.*)', text)
                    if match:
                        q_num = int(match.group(1))
                        q_text = match.group(2)
                        current_question = {
                            'number': q_num,
                            'text': q_text,
                            'full_text': text
                        }
                elif current_question and text:
                    # إضافة النص التالي للسؤال الحالي
                    current_question['full_text'] += " " + text
                    
            # إضافة السؤال الأخير
            if current_question:
                questions.append(current_question)
                
        except Exception as e:
            print(f"Error reading Word file: {e}")
        
        return questions
    
    def create_variable_mapping(self) -> Dict:
        """إنشاء خريطة للمتغيرات مع تعريفاتها"""
        variable_map = {}
        
        # تحليل أسماء الأعمدة من البيانات
        for col in self.data.columns:
            var_info = {
                'name': col,
                'label': col,
                'type': self.data_types.get(col, 'SCALE'),
                'values': {}
            }
            
            # إذا كان متغير فئوي، استخراج القيم الفريدة
            if var_info['type'] == 'CATEGORICAL':
                unique_vals = self.data[col].dropna().unique()[:10]  # أول 10 قيم فقط
                for val in unique_vals:
                    var_info['values'][str(val)] = f"Value {val}"
            
            variable_map[col] = var_info
        
        return variable_map
    
    def generate_dataset_setup(self) -> str:
        """إنشاء كود لإعداد مجموعة البيانات"""
        syntax = "* === SPSS v26 Dataset Setup ===\n"
        syntax += f"* File: {self.dataset_name}\n"
        syntax += f"* Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n"
        
        # تعريف المتغيرات
        syntax += "DATASET NAME DataSet1 WINDOW=FRONT.\n"
        syntax += "DATASET ACTIVATE DataSet1.\n\n"
        
        # إضافة تسميات للمتغيرات
        syntax += "* Variable Labels\n"
        for var_name, var_info in self.variable_map.items():
            syntax += f'VARIABLE LABELS {var_name} "{var_info["label"]}".\n'
        
        syntax += "\n"
        
        # تحديد أنواع المتغيرات
        syntax += "* Define Variable Types\n"
        for var_name, var_info in self.variable_map.items():
            if var_info['type'] == 'SCALE':
                syntax += f'VARIABLE LEVEL {var_name} (SCALE).\n'
            elif var_info['type'] in ['CATEGORICAL', 'STRING']:
                syntax += f'VARIABLE LEVEL {var_name} (NOMINAL).\n'
        
        syntax += "\n* Value Labels for Categorical Variables\n"
        for var_name, var_info in self.variable_map.items():
            if var_info['type'] == 'CATEGORICAL' and var_info['values']:
                syntax += f'VALUE LABELS {var_name}\n'
                for val, label in var_info['values'].items():
                    syntax += f'  {val} "{label}"\n'
                syntax += ".\n"
        
        syntax += "\nEXECUTE.\n"
        syntax += "*" * 60 + "\n\n"
        
        return syntax
    
    def generate_frequency_table(self, variables: List[str], question_text: str) -> str:
        """إنشاء جدول تكراري"""
        syntax = f"* Frequency Table: {question_text[:50]}...\n"
        syntax += "FREQUENCIES VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /BARCHART FREQ\n"
        syntax += "  /PIECHART FREQ\n"
        syntax += "  /ORDER=ANALYSIS.\n"
        syntax += "EXECUTE.\n\n"
        
        return syntax
    
    def generate_descriptive_stats(self, variables: List[str], question_text: str) -> str:
        """إنشاء إحصاءات وصفية"""
        syntax = f"* Descriptive Statistics: {question_text[:50]}...\n"
        syntax += "DESCRIPTIVES VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /SAVE\n"
        syntax += "  /STATISTICS=MEAN STDDEV MIN MAX SKEWNESS SESKEW KURTOSIS SEKURT.\n"
        syntax += "EXECUTE.\n\n"
        
        # جداول تفصيلية
        for var in variables:
            syntax += f"EXAMINE VARIABLES={var}\n"
            syntax += "  /COMPARE VARIABLE\n"
            syntax += "  /PLOT=BOXPLOT HISTOGRAM NPPLOT\n"
            syntax += "  /STATISTICS=NONE\n"
            syntax += "  /CINTERVAL 95\n"
            syntax += "  /MISSING=LISTWISE\n"
            syntax += "  /NOTOTAL.\n\n"
        
        return syntax
    
    def generate_bar_chart(self, variables: List[str], question_text: str) -> str:
        """إنشاء رسم بياني عمودي باستخدام Chart Builder (الطريقة المفضلة في v26)"""
        if len(variables) < 2:
            syntax = f"* Bar Chart: {question_text[:50]}...\n"
            syntax += "GGRAPH\n"
            syntax += f"  /GRAPHDATASET NAME=\"graphdataset\" VARIABLES={variables[0]}\n"
            syntax += "  /GRAPHSPEC SOURCE=INLINE.\n"
            syntax += "BEGIN GPL\n"
            syntax += f"  SOURCE: s=userSource(id(\"graphdataset\"))\n"
            syntax += f"  DATA: {variables[0]}=col(source(s), name(\"{variables[0]}\"))\n"
            syntax += "  GUIDE: axis(dim(1), label(\"Categories\"))\n"
            syntax += "  GUIDE: axis(dim(2), label(\"Frequency\"))\n"
            syntax += "  ELEMENT: interval(position(summary.count(bin.rect({variables[0]}))))\n"
            syntax += "END GPL.\n"
            syntax += "EXECUTE.\n\n"
        else:
            syntax = f"* Clustered Bar Chart: {question_text[:50]}...\n"
            syntax += f"GGRAPH\n"
            syntax += f"  /GRAPHDATASET NAME=\"graphdataset\" VARIABLES={variables[0]} {variables[1]}\n"
            syntax += "  /GRAPHSPEC SOURCE=INLINE.\n"
            syntax += "BEGIN GPL\n"
            syntax += f"  SOURCE: s=userSource(id(\"graphdataset\"))\n"
            syntax += f"  DATA: {variables[0]}=col(source(s), name(\"{variables[0]}\"), unit.category())\n"
            syntax += f"  DATA: {variables[1]}=col(source(s), name(\"{variables[1]}\"), unit.category())\n"
            syntax += f"  DATA: count=col(source(s), name(\"COUNT\"), unit.count())\n"
            syntax += "  COORD: rect(dim(1,2), cluster(3,0))\n"
            syntax += "  GUIDE: axis(dim(3), label(\"Categories\"))\n"
            syntax += "  GUIDE: axis(dim(2), label(\"Frequency\"))\n"
            syntax += "  GUIDE: legend(aesthetic(aesthetic.color.interior), label(\"Group\"))\n"
            syntax += "  SCALE: cat(dim(3), include(\"0\", \"1\"))\n"
            syntax += f"  ELEMENT: interval(position({variables[0]}*count*{variables[1]}), color.interior({variables[1]}))\n"
            syntax += "END GPL.\n"
            syntax += "EXECUTE.\n\n"
        
        return syntax
    
    def generate_pie_chart(self, variables: List[str], question_text: str) -> str:
        """إنشاء رسم بياني دائري"""
        syntax = f"* Pie Chart: {question_text[:50]}...\n"
        syntax += "GGRAPH\n"
        syntax += f"  /GRAPHDATASET NAME=\"graphdataset\" VARIABLES={variables[0]}\n"
        syntax += "  /GRAPHSPEC SOURCE=INLINE.\n"
        syntax += "BEGIN GPL\n"
        syntax += f"  SOURCE: s=userSource(id(\"graphdataset\"))\n"
        syntax += f"  DATA: {variables[0]}=col(source(s), name(\"{variables[0]}\"), unit.category())\n"
        syntax += f"  DATA: count=col(source(s), name(\"COUNT\"), unit.count())\n"
        syntax += "  COORD: polar.theta(start(0))\n"
        syntax += "  GUIDE: axis(dim(1))\n"
        syntax += "  GUIDE: legend(aesthetic(aesthetic.color.interior))\n"
        syntax += f"  ELEMENT: interval(position(summary.percent(count)), color.interior({variables[0]}), shape.interior(shape.symbol))\n"
        syntax += "END GPL.\n"
        syntax += "EXECUTE.\n\n"
        
        return syntax
    
    def generate_confidence_intervals(self, variables: List[str], question_text: str) -> str:
        """إنشاء فترات ثقة"""
        syntax = f"* Confidence Intervals: {question_text[:50]}...\n"
        
        for var in variables:
            syntax += f"* 95% CI for {var}\n"
            syntax += f"EXAMINE VARIABLES={var}\n"
            syntax += "  /PLOT NONE\n"
            syntax += "  /STATISTICS DESCRIPTIVES\n"
            syntax += "  /CINTERVAL 95\n"
            syntax += "  /MISSING LISTWISE.\n\n"
            
            syntax += f"* 99% CI for {var}\n"
            syntax += f"EXAMINE VARIABLES={var}\n"
            syntax += "  /PLOT NONE\n"
            syntax += "  /STATISTICS DESCRIPTIVES\n"
            syntax += "  /CINTERVAL 99\n"
            syntax += "  /MISSING LISTWISE.\n\n"
        
        return syntax
    
    def generate_t_test(self, variables: List[str], question_text: str) -> str:
        """إنشاء اختبار t"""
        syntax = f"* T-Test: {question_text[:50]}...\n"
        
        # استخراج القيمة المرجعية من نص السؤال
        numbers = re.findall(r'\d+', question_text)
        test_value = numbers[0] if numbers else "0"
        
        # اختبار عينة واحدة
        if 'equal' in question_text.lower() or 'يساوي' in question_text.lower():
            syntax += f"T-TEST\n"
            syntax += f"  /TESTVAL={test_value}\n"
            syntax += f"  /MISSING=ANALYSIS\n"
            syntax += f"  /VARIABLES={variables[0] if variables else 'VAR001'}\n"
            syntax += f"  /CRITERIA=CI(.95).\n\n"
        
        # اختبار عينتين مستقلتين
        elif 'difference' in question_text.lower() and len(variables) >= 2:
            syntax += f"T-TEST GROUPS={variables[0]}\n"
            syntax += f"  /VARIABLES={variables[1]}\n"
            syntax += f"  /MISSING=ANALYSIS\n"
            syntax += f"  /CRITERIA=CI(.95).\n\n"
        
        return syntax
    
    def generate_anova(self, variables: List[str], question_text: str) -> str:
        """إنشاء تحليل ANOVA"""
        if len(variables) < 2:
            return "* Insufficient variables for ANOVA\n\n"
        
        syntax = f"* ANOVA: {question_text[:50]}...\n"
        syntax += f"ONEWAY {variables[1]} BY {variables[0]}\n"
        syntax += "  /STATISTICS DESCRIPTIVES HOMOGENEITY\n"
        syntax += "  /MISSING ANALYSIS\n"
        syntax += "  /POSTHOC=TUKEY ALPHA(0.05).\n\n"
        
        return syntax
    
    def generate_correlation(self, variables: List[str], question_text: str) -> str:
        """إنشاء تحليل الارتباط"""
        syntax = f"* Correlation Analysis: {question_text[:50]}...\n"
        syntax += "CORRELATIONS\n"
        syntax += "  /VARIABLES="
        syntax += " ".join(variables) + "\n"
        syntax += "  /PRINT=TWOTAIL NOSIG\n"
        syntax += "  /MISSING=PAIRWISE.\n\n"
        
        # مصفوفة الانتشار
        syntax += "GRAPH\n"
        syntax += "  /SCATTERPLOT(MATRIX)="
        syntax += " ".join(variables) + "\n"
        syntax += "  /MISSING=LISTWISE.\n\n"
        
        return syntax
    
    def generate_regression(self, variables: List[str], question_text: str) -> str:
        """إنشاء تحليل الانحدار"""
        if len(variables) < 2:
            return "* Insufficient variables for regression\n\n"
        
        syntax = f"* Regression Analysis: {question_text[:50]}...\n"
        
        # تحديد المتغير التابع (Y)
        dependent_var = variables[0]
        independent_vars = variables[1:]
        
        syntax += f"REGRESSION\n"
        syntax += f"  /MISSING LISTWISE\n"
        syntax += f"  /STATISTICS COEFF OUTS R ANOVA\n"
        syntax += f"  /CRITERIA=PIN(.05) POUT(.10)\n"
        syntax += f"  /NOORIGIN\n"
        syntax += f"  /DEPENDENT {dependent_var}\n"
        syntax += f"  /METHOD=ENTER {' '.join(independent_vars)}.\n\n"
        
        return syntax
    
    def detect_analysis_type(self, question_text: str) -> str:
        """تحديد نوع التحليل المطلوب"""
        text_lower = question_text.lower()
        
        # قاموس أنواع التحليل مع الكلمات المفتاحية
        analysis_patterns = {
            'frequency': ['frequency table', 'جدول تكراري', 'توزيع تكراري'],
            'descriptive': ['mean', 'median', 'mode', 'standard deviation', 'مقاييس'],
            'bar_chart': ['bar chart', 'رسم بياني عمودي', 'مخطط عمودي'],
            'pie_chart': ['pie chart', 'رسم دائري', 'مخطط دائري'],
            'histogram': ['histogram', 'مدرج تكراري'],
            'confidence': ['confidence interval', 'فترة ثقة'],
            'ttest': ['test the hypothesis', 't-test', 'اختبار الفرضية'],
            'anova': ['anova', 'تحليل التباين', 'significant difference'],
            'correlation': ['correlation', 'ارتباط'],
            'regression': ['regression', 'انحدار', 'linear model'],
            'normality': ['normality', 'empirical rule', 'chebycheve'],
            'outliers': ['outliers', 'extreme value', 'القيم المتطرفة']
        }
        
        for analysis_type, keywords in analysis_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return analysis_type
        
        return 'descriptive'  # إفتراضي
    
    def extract_variables_from_question(self, question_text: str) -> List[str]:
        """استخراج المتغيرات المذكورة في السؤال"""
        found_vars = []
        
        # البحث عن أسماء المتغيرات في السؤال
        for var_name in self.variable_map.keys():
            var_lower = var_name.lower()
            question_lower = question_text.lower()
            
            # البحث بالاسم الكامل
            if var_lower in question_lower:
                found_vars.append(var_name)
            # البحث بالأسماء الشائعة
            elif any(keyword in var_lower for keyword in ['salary', 'age', 'gender', 'race']):
                if any(keyword in question_lower for keyword in ['salary', 'age', 'gender', 'race']):
                    found_vars.append(var_name)
        
        # إذا لم يتم العثور على متغيرات، استخدام الأعمدة الأولى
        if not found_vars and len(self.data.columns) > 0:
            found_vars = list(self.data.columns[:min(3, len(self.data.columns))])
        
        return found_vars
    
    def process_all_questions(self) -> str:
        """معالجة جميع الأسئلة وإنشاء كود SPSS كامل"""
        if not self.questions:
            return "* No questions found in the document\n"
        
        # بدء كود SPSS
        spss_syntax = self.generate_dataset_setup()
        
        spss_syntax += "* === Analysis for Each Question ===\n\n"
        
        for question in self.questions:
            q_num = question['number']
            q_text = question['text']
            full_text = question['full_text']
            
            spss_syntax += f"* Question {q_num}: {q_text}\n"
            
            # تحديد نوع التحليل
            analysis_type = self.detect_analysis_type(full_text)
            
            # استخراج المتغيرات
            variables = self.extract_variables_from_question(full_text)
            
            spss_syntax += f"* Analysis Type: {analysis_type}\n"
            spss_syntax += f"* Variables: {variables}\n"
            spss_syntax += "*" * 50 + "\n"
            
            # توليد الكود بناءً على نوع التحليل
            if analysis_type == 'frequency':
                spss_syntax += self.generate_frequency_table(variables, q_text)
            elif analysis_type == 'descriptive':
                spss_syntax += self.generate_descriptive_stats(variables, q_text)
            elif analysis_type == 'bar_chart':
                spss_syntax += self.generate_bar_chart(variables, q_text)
            elif analysis_type == 'pie_chart':
                spss_syntax += self.generate_pie_chart(variables, q_text)
            elif analysis_type == 'confidence':
                spss_syntax += self.generate_confidence_intervals(variables, q_text)
            elif analysis_type == 'ttest':
                spss_syntax += self.generate_t_test(variables, full_text)
            elif analysis_type == 'anova':
                spss_syntax += self.generate_anova(variables, full_text)
            elif analysis_type == 'correlation':
                spss_syntax += self.generate_correlation(variables, q_text)
            elif analysis_type == 'regression':
                spss_syntax += self.generate_regression(variables, q_text)
            else:
                spss_syntax += f"* No specific syntax for analysis type: {analysis_type}\n"
                spss_syntax += f"DESCRIPTIVES VARIABLES={' '.join(variables[:3])}\n"
                spss_syntax += "  /STATISTICS=MEAN STDDEV MIN MAX.\n\n"
            
            spss_syntax += "\n"
        
        # إضافة قسم للتنظيف
        spss_syntax += "* === Cleanup and Save ===\n"
        spss_syntax += "DATASET CLOSE ALL.\n"
        spss_syntax += f'SAVE OUTFILE="{self.dataset_name}_analyzed.sav"\n'
        spss_syntax += "  /COMPRESSED.\n"
        spss_syntax += "EXECUTE.\n"
        
        return spss_syntax
    
    def save_spss_syntax(self, syntax: str, output_path: str = None):
        """حفظ كود SPSS في ملف"""
        if output_path is None:
            output_path = f"SPSS_v26_{self.dataset_name}_Syntax.sps"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(syntax)
        
        print(f"SPSS syntax saved to: {output_path}")
        return output_path
    
    def generate_output_summary(self) -> Dict:
        """إنشاء ملخص للتحليل"""
        return {
            'dataset': self.dataset_name,
            'questions_count': len(self.questions),
            'variables_count': len(self.data.columns),
            'data_types': self.data_types,
            'generated_file': f"SPSS_v26_{self.dataset_name}_Syntax.sps"
        }


class BatchSPSSGenerator:
    """معالج دفعات لجميع مجموعات البيانات"""
    
    def __init__(self, data_question_pairs: List[Tuple[str, str]]):
        self.pairs = data_question_pairs
        self.results = []
    
    def process_all(self):
        """معالجة جميع أزواج البيانات والأسئلة"""
        print("=== Batch Processing for SPSS v26 ===\n")
        
        for data_file, question_file in self.pairs:
            if os.path.exists(data_file) and os.path.exists(question_file):
                print(f"Processing: {data_file}")
                
                try:
                    # إنشاء مولد لكل مجموعة بيانات
                    generator = SPSSv26SyntaxGenerator(data_file, question_file)
                    
                    # معالجة الأسئلة
                    spss_syntax = generator.process_all_questions()
                    
                    # حفظ ملف SPSS
                    output_file = generator.save_spss_syntax(spss_syntax)
                    
                    # جمع النتائج
                    summary = generator.generate_output_summary()
                    summary['status'] = 'Success'
                    summary['output_file'] = output_file
                    
                    self.results.append(summary)
                    
                    print(f"  ✓ Generated: {output_file}")
                    print(f"  Questions: {summary['questions_count']}")
                    print(f"  Variables: {summary['variables_count']}\n")
                    
                except Exception as e:
                    print(f"  ✗ Error: {e}\n")
                    self.results.append({
                        'dataset': os.path.basename(data_file),
                        'status': 'Failed',
                        'error': str(e)
                    })
            else:
                print(f"✗ File not found: {data_file} or {question_file}\n")
        
        return self.results
    
    def generate_summary_report(self):
        """إنشاء تقرير ملخص"""
        report_file = "SPSS_v26_Batch_Summary.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("SPSS v26 Batch Processing Summary\n")
            f.write("=" * 50 + "\n\n")
            
            success_count = sum(1 for r in self.results if r.get('status') == 'Success')
            f.write(f"Total Datasets: {len(self.results)}\n")
            f.write(f"Successfully Processed: {success_count}\n")
            f.write(f"Failed: {len(self.results) - success_count}\n\n")
            
            for result in self.results:
                f.write(f"Dataset: {result.get('dataset', 'Unknown')}\n")
                f.write(f"Status: {result.get('status', 'Unknown')}\n")
                
                if result.get('status') == 'Success':
                    f.write(f"Output File: {result.get('output_file', 'N/A')}\n")
                    f.write(f"Questions: {result.get('questions_count', 0)}\n")
                    f.write(f"Variables: {result.get('variables_count', 0)}\n")
                else:
                    f.write(f"Error: {result.get('error', 'Unknown error')}\n")
                
                f.write("-" * 40 + "\n\n")
        
        print(f"Summary report saved to: {report_file}")
        return report_file


# ===== وظائف مساعدة =====

def create_data_question_pairs(base_path="."):
    """إنشاء أزواج البيانات والأسئلة تلقائياً"""
    import glob
    
    # البحث عن ملفات البيانات
    data_files = sorted(glob.glob(os.path.join(base_path, "Data set *.xls")))
    
    # البحث عن ملفات الأسئلة
    question_files = []
    for data_file in data_files:
        dataset_num = os.path.basename(data_file).split()[2].split('.')[0]
        question_pattern = os.path.join(base_path, f"*data set {dataset_num}*.doc")
        found = glob.glob(question_pattern)
        if found:
            question_files.append(found[0])
        else:
            question_files.append("")
    
    # إنشاء الأزواج
    pairs = []
    for data_file, question_file in zip(data_files, question_files):
        if question_file:  # فقط إذا كان هناك ملف أسئلة
            pairs.append((data_file, question_file))
    
    return pairs


def generate_single_dataset_example():
    """مثال لتوليد كود لمجموعة بيانات واحدة"""
    # مثال مع Data set 2
    generator = SPSSv26SyntaxGenerator(
        "Data set 2.xls",
        "SPSS questioins For data set 2.doc"
    )
    
    # عرض معلومات عن البيانات
    print(f"Dataset: {generator.dataset_name}")
    print(f"Variables: {list(generator.data.columns)}")
    print(f"Data Types: {generator.data_types}")
    print(f"Questions Found: {len(generator.questions)}\n")
    
    # توليد كود SPSS
    spss_code = generator.process_all_questions()
    
    # حفظ الكود
    output_file = generator.save_spss_syntax(spss_code)
    
    # عرض جزء من الكود المتولد
    print("\n=== Sample Generated Code ===")
    sample_lines = spss_code.split('\n')[:30]
    print('\n'.join(sample_lines))
    print("...\n")
    
    return generator


# ===== الوظيفة الرئيسية =====

def main():
    """الدالة الرئيسية لتشغيل البرنامج"""
    import sys
    
    print("SPSS v26 Syntax Generator")
    print("=" * 50)
    
    # خيارات التشغيل
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = input("Enter mode (batch/single): ").strip().lower()
    
    if mode == 'batch':
        # معالجة دفعة لجميع الملفات
        pairs = create_data_question_pairs()
        
        if not pairs:
            print("No data-question pairs found!")
            return
        
        print(f"Found {len(pairs)} dataset-question pairs")
        
        batch_processor = BatchSPSSGenerator(pairs)
        results = batch_processor.process_all()
        batch_processor.generate_summary_report()
        
    elif mode == 'single':
        # معالجة مجموعة بيانات واحدة
        dataset_num = input("Enter dataset number (1-4): ").strip()
        
        data_file = f"Data set {dataset_num}.xls"
        question_file = f"SPSS questioins For data set {dataset_num}.doc"
        
        if not os.path.exists(data_file):
            question_file = f"SPSS questions For data set {dataset_num}.doc"
        
        if os.path.exists(data_file) and os.path.exists(question_file):
            generator = SPSSv26SyntaxGenerator(data_file, question_file)
            spss_code = generator.process_all_questions()
            output_file = generator.save_spss_syntax(spss_code)
            
            print(f"\nSPSS syntax generated successfully!")
            print(f"Output file: {output_file}")
        else:
            print(f"Files not found: {data_file} or {question_file}")
    
    else:
        print("Invalid mode. Use 'batch' or 'single'")


# ===== مثال للاستخدام المباشر =====

if __name__ == "__main__":
    # لتشغيل في وضع الدفعة
    # main()
    
    # أو لتجربة مجموعة بيانات واحدة
    print("=== SPSS v26 Syntax Generator Example ===\n")
    
    # مثال مع Data set 2
    example_generator = generate_single_dataset_example()
    
    # عرض عينة من الأسئلة المعالجة
    print("\n=== Sample Questions Processed ===")
    for i, question in enumerate(example_generator.questions[:5], 1):
        print(f"{i}. {question['text'][:80]}...")
        analysis_type = example_generator.detect_analysis_type(question['full_text'])
        variables = example_generator.extract_variables_from_question(question['full_text'])
        print(f"   Type: {analysis_type}, Variables: {variables}\n")
