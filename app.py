import streamlit as st
import pandas as pd
from docx import Document
import google.generativeai as genai
import io

# 1. إعداد واجهة البرمجة (API) لـ Gemini
# احصل على مفتاحك من https://aistudio.google.com/
genai.configure(api_key="ضع_مفتاحك_هنا_YOUR_API_KEY")

def ask_gemini_for_syntax(questions, data_summary):
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    You are an expert SPSS statistician for MBA students. 
    Analyze the following variables and questions to generate a professional SPSS Syntax (.sps).
    
    Variables and Context:
    {data_summary}
    
    Questions to solve:
    {questions}
    
    Requirements:
    1. Use VARIABLE LABELS and VALUE LABELS as per the context.
    2. For each question, provide the correct SPSS command (FREQUENCIES, GRAPH, T-TEST, ONEWAY, REGRESSION, etc.).
    3. Use Scientific Justification comments before each command.
    4. Follow the MBA standards of Dr. Mohamed A. Salam.
    5. Return ONLY the syntax code.
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- واجهة Streamlit ---
st.set_page_config(page_title="Gemini SPSS AI", layout="wide")
st.title("🤖 محرك SPSS الذكي المدعوم بـ Gemini")

col1, col2 = st.columns(2)
with col1:
    u_excel = st.file_uploader("1. ارفع ملف البيانات (Excel)", type=['xlsx', 'xls', 'csv'])
with col2:
    u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word)", type=['docx'])

if u_excel and u_word:
    # قراءة البيانات للحصول على المسميات
    df = pd.read_excel(u_excel) if not u_excel.name.endswith('.csv') else pd.read_csv(u_excel)
    data_summary = f"Columns in Excel: {df.columns.tolist()}\nFirst 5 rows: {df.head().to_string()}"
    
    # قراءة الأسئلة من الوورد
    doc = Document(io.BytesIO(u_word.read()))
    questions = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    
    if st.button("🚀 توليد السينتاكس بواسطة الذكاء الاصطناعي"):
        with st.spinner("Gemini يقوم بتحليل البيانات الآن..."):
            try:
                # إرسال المهمة لـ Gemini
                final_syntax = ask_gemini_for_syntax(questions, data_summary)
                
                st.success("✅ تم توليد السينتاكس بذكاء!")
                st.code(final_syntax, language='spss')
                
                st.download_button(
                    label="تحميل ملف الـ Syntax الذكي (.sps)",
                    data=final_syntax,
                    file_name="AI_Generated_Analysis.sps",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"حدث خطأ في الاتصال بـ Gemini: {e}")
