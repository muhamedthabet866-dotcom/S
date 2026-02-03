import streamlit as st
import pandas as pd
from docx import Document
import google.generativeai as genai
import io

# 1. إعداد مفتاح API لـ Gemini
# تأكد من الحصول على المفتاح من https://aistudio.google.com/
API_KEY = "ضع_مفتاحك_هنا" 
genai.configure(api_key=API_KEY)

def ask_gemini_for_syntax(questions, data_summary):
    # استخدام الموديل الأحدث والأكثر استقراراً
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert SPSS statistician for MBA students. 
    Analyze the following variables and questions to generate a professional SPSS Syntax (.sps).
    
    Variables and Context:
    {data_summary}
    
    Questions to solve from the Word file:
    {questions}
    
    Requirements:
    1. Identify variables (X1, X2, etc.) based on the 'Where:' definitions in the text.
    2. For categorical data, use FREQUENCIES[cite: 6, 17].
    3. For mean comparisons, use T-TEST or ONEWAY ANOVA with TUKEY post-hoc[cite: 11, 30].
    4. For charts, use GRAPH /BAR or /PIE based on whether it asks for Average, Sum, or Percentage[cite: 1, 4, 18, 21].
    5. Ensure the syntax matches specific values (e.g., 90 wins, 35000 salary, or 600 area)[cite: 10, 11, 28].
    6. Include 'Scientific Justification' as a comment before each command.
    7. Return ONLY the syntax code.
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- واجهة Streamlit ---
st.set_page_config(page_title="Gemini SPSS AI", layout="wide")
st.title("🤖 محرك SPSS الذكي (Gemini 1.5 Flash)")

col1, col2 = st.columns(2)
with col1:
    u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
with col2:
    u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx'])

if u_excel and u_word:
    # قراءة ملخص البيانات لإرساله للذكاء الاصطناعي
    if u_excel.name.endswith('.csv'):
        df = pd.read_csv(u_excel)
    else:
        df = pd.read_excel(u_excel)
    
    data_summary = f"Columns in file: {df.columns.tolist()}\nFirst 3 rows for context:\n{df.head(3).to_string()}"
    
    # قراءة الأسئلة من الوورد
    try:
        doc = Document(io.BytesIO(u_word.read()))
        questions = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        # قراءة النصوص من الجداول أيضاً لضمان استخراج تعريفات المتغيرات (Where X1=...) 
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    questions += "\n" + cell.text
    except Exception as e:
        st.error(f"خطأ في قراءة ملف الوورد: {e}")
        questions = ""

    if st.button("🚀 توليد السينتاكس بواسطة الذكاء الاصطناعي"):
        if not API_KEY or API_KEY == "ضع_مفتاحك_هنا":
            st.warning("AIzaSyBOoryKbkBskgLby5HlUUxtTPO8Oby8744")
        elif not questions:
            st.warning("لم يتم العثور على أسئلة في ملف الوورد.")
        else:
            with st.spinner("Gemini يقوم بتحليل البيانات وتوليد الكود..."):
                try:
                    # طلب الكود من Gemini
                    final_syntax = ask_gemini_for_syntax(questions, data_summary)
                    
                    st.success("✅ تم توليد السينتاكس بنجاح!")
                    st.code(final_syntax, language='spss')
                    
                    st.download_button(
                        label="تحميل ملف الـ Syntax (.sps)",
                        data=final_syntax,
                        file_name="AI_Generated_Analysis.sps",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"حدث خطأ في الاتصال بـ Gemini: {e}")
                    st.info("تأكد من صحة مفتاح API ومن استخدام موديل gemini-1.5-flash.")
