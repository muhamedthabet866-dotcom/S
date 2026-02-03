import streamlit as st
import pandas as pd
from docx import Document
import google.generativeai as genai
import io

# 1. إعداد ذكاء Gemini الاصطناعي
# احصل على مفتاحك مجاناً من: https://aistudio.google.com/
API_KEY = "ضع_مفتاح_الـ_API_الخاص_بك_هنا" 
genai.configure(api_key=API_KEY)

def ask_gemini_for_syntax(questions, data_context):
    """إرسال البيانات والأسئلة لـ Gemini لتوليد كود SPSS احترافي"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are a professional SPSS expert for MBA students. 
    Task: Generate a perfect SPSS Syntax (.sps) file based on the context below.
    
    Context (Excel Data Summary):
    {data_context}
    
    Questions (from Word File):
    {questions}
    
    Rules for Syntax:
    1. Identify X1, X2, etc., from the 'Where:' or 'Definitions' section in the questions.
    2. Use 'Scientific Justification' as a comment before every command.
    3. Use FREQUENCIES for categorical data.
    4. Use T-TEST (1-sample or independent) and ONEWAY ANOVA (with Post-Hoc Tukey) correctly.
    5. Use GRAPH /BAR or /PIE as requested (Mean, Max, or Count).
    6. Include 'VALUE LABELS' and 'VARIABLE LABELS' at the beginning.
    7. Return ONLY the SPSS syntax code, no extra text.
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- واجهة المستخدم (Streamlit UI) ---
st.set_page_config(page_title="MBA SPSS AI Expert", layout="wide")
st.title("🤖 خبير الإحصاء الذكي (Gemini AI Edition)")
st.markdown("قم برفع ملفاتك وسيقوم الذكاء الاصطناعي بكتابة الكود الإحصائي الكامل لك.")

# أزرار رفع الملفات
col1, col2 = st.columns(2)
with col1:
    u_excel = st.file_uploader("1. ارفع ملف الإكسيل (Data set)", type=['xlsx', 'xls', 'csv'])
with col2:
    u_word = st.file_uploader("2. ارفع ملف الأسئلة (Word .docx)", type=['docx'])

if u_excel and u_word:
    # معالجة بيانات الإكسيل
    if u_excel.name.endswith('.csv'):
        df = pd.read_csv(u_excel)
    else:
        df = pd.read_excel(u_excel)
    
    # تحضير سياق البيانات للذكاء الاصطناعي
    data_context = f"Columns: {df.columns.tolist()}\nFirst rows:\n{df.head(5).to_string()}"
    
    # معالجة ملف الوورد (نصوص وجداول)
    doc = Document(io.BytesIO(u_word.read()))
    questions_list = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                questions_list.append(cell.text)
    all_questions = "\n".join(questions_list)

    if st.button("🚀 حل الامتحان وتوليد السينتاكس"):
        if API_KEY == "AIzaSyBOoryKbkBskgLby5HlUUxtTPO8Oby8744":
            st.error("⚠️ خطأ: يرجى وضع API Key صالح في الكود أولاً.")
        else:
            with st.spinner("جاري تحليل البيانات والأسئلة بواسطة Gemini 1.5 Flash..."):
                try:
                    # طلب الحل من الذكاء الاصطناعي
                    final_syntax = ask_gemini_for_syntax(all_questions, data_context)
                    
                    st.success("✅ تم توليد الحل النموذجي بنجاح!")
                    st.code(final_syntax, language='spss')
                    
                    # زر تحميل الملف الناتج
                    st.download_button(
                        label="تحميل ملف السينتاكس الجاهز (.sps)",
                        data=final_syntax,
                        file_name="MBA_Final_Analysis.sps",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"حدث خطأ في الاتصال بالخادم: {e}")
