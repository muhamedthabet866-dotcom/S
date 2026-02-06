import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# إعداد واجهة التطبيق
st.set_page_config(page_title="MBA SPSS Master Solver", layout="wide")

st.title("🎓 المحرك الذكي لتوليد SPSS Syntax")
st.markdown("تحويل أسئلة الامتحانات إلى أكواد طبقاً لمنهج د. محمد عبد السلام")

# --- الإعدادات الجانبية ---
with st.sidebar:
    st.header("📂 1. البيانات والمنهج")
    # رفع ملف البيانات الأساسي (Data Set)
    data_file = st.file_uploader("ارفع ملف بيانات الإكسيل (XLSX)", type=['xlsx'])
    
    # رابط ملف المنهج من GitHub (قاعدة القواعد)
    # ملاحظة: سأزودك بتنسيق هذا الملف لترفه على حسابك
    RULES_URL = "https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/spss_rules.xlsx"
    st.info("سيتم جلب قواعد المنهج تلقائياً من GitHub")

# --- الصناديق الحوارية المطلوبة ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚙️ صندوق المتغيرات (Mapping)")
    v_mapping = st.text_area(
        "أدخل تعريف المتغيرات كما في الامتحان:",
        placeholder="X1=Team\nX2=League\nX5=Salary...",
        height=300
    )

with col2:
    st.subheader("📝 صندوق أسئلة الامتحان")
    questions_input = st.text_area(
        "الصق الأسئلة هنا (مثال: Draw a bar chart for average salary):",
        height=300
    )

# --- محرك التحليل والمقارنة ---
def generate_syntax(questions, mapping, rules_df):
    syntax_output = []
    # تحويل الـ Mapping إلى قاموس ليسهل استبداله
    mapping_dict = {}
    for line in mapping.split('\n'):
        if '=' in line:
            parts = line.split('=')
            mapping_dict[parts[1].strip().lower()] = parts[0].strip().upper()

    # تقسيم الأسئلة ومعالجتها
    for q in questions.split('\n'):
        if q.strip():
            found = False
            # مقارنة السؤال مع ملف المنهج (Rules)
            for _, rule in rules_df.iterrows():
                if rule['Keyword'].lower() in q.lower():
                    # استخراج الكود من المنهج وتعبئته بالمتغيرات الصحيحة
                    template = rule['Syntax_Template']
                    # منطق لاستبدال الكلمات بالرموز (مثل Salary بـ X5)
                    for word, code in mapping_dict.items():
                        if word in q.lower():
                            template = template.replace(f"{{var}}", code)
                    
                    syntax_output.append(f"* Question: {q}\n{template}\n")
                    found = True
                    break
            if not found:
                syntax_output.append(f"* Question: {q}\n* [Manual Check Required - No Rule Matched]\n")
    
    return "\n".join(syntax_output)

if st.button("🚀 توليد كود Syntax المنهج"):
    if v_mapping and questions_input:
        try:
            # جلب ملف المنهج من GitHub
            response = requests.get(RULES_URL)
            rules_df = pd.read_excel(BytesIO(response.content))
            
            # توليد الكود
            final_code = generate_syntax(questions_input, v_mapping, rules_df)
            
            st.success("تم توليد الكود بنجاح!")
            st.code(final_code, language="spss")
            
        except Exception as e:
            st.error(f"يرجى التأكد من رفع ملف المنهج على GitHub بشكل صحيح. الخطأ: {e}")
