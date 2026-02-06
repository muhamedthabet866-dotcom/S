import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# إعداد الصفحة
st.set_page_config(page_title="MBA SPSS Solver - Eng. Mohamed", layout="wide")

st.title("🎓 المحرك الذكي لمنهج SPSS (v26)")
st.subheader("تطوير المهندس محمد - خاص بطلاب الـ MBA")

# --- الإعدادات وجلب المنهج من GitHub ---
# استبدل هذا الرابط برابط الـ Raw الخاص بك بعد رفع ملف spss_rules.xlsx
GITHUB_RAW_URL = "https://github.com/muhamedthabet866-dotcom/S/raw/refs/heads/main/spss_rules.xlsx"

@st.cache_data
def load_rules(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_excel(BytesIO(response.content))
        return None
    except Exception:
        return None

rules_df = load_rules(GITHUB_RAW_URL)

# --- واجهة المستخدم ---
st.info("تأكد من إدخال المتغيرات بنفس التنسيق المذكور في أسفل ورقة الامتحان (مثلاً: X5=Salary)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⚙️ صندوق المتغيرات (Mapping)")
    mapping_input = st.text_area(
        "أدخل المتغيرات هنا:", 
        placeholder="X1=Team\nX2=League\nX5=Salary...",
        height=300
    )

with col2:
    st.markdown("### 📝 صندوق أسئلة الامتحان")
    questions_input = st.text_area(
        "الصق الأسئلة هنا:", 
        placeholder="Draw a bar chart for average salary...\nTest the normality of population...",
        height=300
    )

# --- زر التنفيذ ---
if st.button("🚀 توليد كود SPSS Syntax"):
    if not mapping_input.strip() or not questions_input.strip():
        st.warning("⚠️ يرجى ملء صندوق المتغيرات وصندوق الأسئلة أولاً.")
    else:
        # 1. معالجة صندوق المتغيرات (Mapping) بشكل آمن لتجنب أخطاء التقسيم
        mapping_dict = {}
        lines = mapping_input.split('\n')
        for line in lines:
            line = line.strip()
            if '=' in line:
                try:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        # تنظيف الكود (مثل X1) والاسم (مثل Team)
                        code = parts[0].strip().upper()
                        name = parts[1].strip().lower()
                        mapping_dict[name] = code
                except Exception:
                    continue

        # 2. توليد الكود بناءً على القواعد
        if rules_df is not None:
            final_syntax = [
                "* Generated for Eng. Mohamed.",
                "SET SEED=1234567.",
                "PRESERVE.",
                "SET DECIMAL=DOT.\n"
            ]
            
            questions = questions_input.split('\n')
            for q in questions:
                q = q.strip()
                if not q: continue
                
                matched = False
                # البحث في ملف القواعد المجلوب من GitHub
                for _, rule in rules_df.iterrows():
                    keyword = str(rule['Keyword']).lower()
                    if keyword in q.lower():
                        syntax_template = str(rule['Syntax_Template'])
                        
                        # استبدال المتغيرات الذكي بناءً على الكلمات الموجودة في السؤال
                        # نقوم بترتيب الكلمات من الأطول للأقصر لتجنب استبدال جزء من كلمة
                        sorted_names = sorted(mapping_dict.keys(), key=len, reverse=True)
                        
                        current_syntax = syntax_template
                        for name in sorted_names:
                            if name in q.lower():
                                code = mapping_dict[name]
                                # استبدال {var} أو {group} بالكود المناسب
                                current_syntax = current_syntax.replace("{var}", code).replace("{group}", code)
                        
                        final_syntax.append(f"* Question: {q}")
                        final_syntax.append(f"{current_syntax}")
                        final_syntax.append("EXECUTE.\n")
                        matched = True
                        break
                
                if not matched:
                    final_syntax.append(f"* Question: {q}")
                    final_syntax.append("* [!] لم يتم العثور على قاعدة مطابقة لهذا السؤال في ملف المنهج.")
                    final_syntax.append("EXECUTE.\n")

            # عرض النتائج
            st.success("✅ تم تحليل الأسئلة وتوليد الكود!")
            st.code("\n".join(final_syntax), language="spss")
            
            # زر تحميل الملف
            st.download_button(
                label="📥 تحميل ملف Syntax (.sps)",
                data="\n".join(final_syntax),
                file_name="MBA_Solver_Output.sps",
                mime="text/plain"
            )
        else:
            st.error("❌ لم يتمكن البرنامج من الاتصال بملف المنهج على GitHub. يرجى التأكد من الرابط أو رفع الملف.")

# --- قسم المساعدة بناءً على ملفاتك ---
with st.expander("💡 مساعدة في المتغيرات (بناءً على Data Sets)"):
    st.write("**Data Set 2 (Baseball):** X2=League, X5=Salary, X11=Surface") [cite: 16]
    st.write("**Data Set 3 (OECD):** X2=G7 Member, X3=Total area, X4=Population") [cite: 34]
    st.write("**Data Set 4 (Survey):** X1=Gender, X3=Salary, X5=General happiness") [cite: 55]
