import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# إعداد الصفحة لتناسب المهندس محمد
st.set_page_config(page_title="MBA SPSS Solver v3.0", layout="wide")

st.title("🎓 المحرك الذكي المطور لمنهج SPSS")
st.markdown("---")

# --- إعدادات GitHub ---
# تأكد من رفع ملف spss_rules.xlsx على حسابك ووضع الرابط هنا
GITHUB_RAW_URL = "https://github.com/muhamedthabet866-dotcom/S/raw/refs/heads/main/spss_rules.xlsx"

@st.cache_data
def load_rules(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return pd.read_excel(BytesIO(response.content))
        return None
    except:
        return None

rules_df = load_rules(GITHUB_RAW_URL)

# --- الواجهة الرسومية ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚙️ تعريف المتغيرات (Mapping)")
    # القيمة الافتراضية بناءً على Data Set 1 لسهولة التجربة
    mapping_input = st.text_area("أدخل المتغيرات (مثال: X1=account balance):", 
        value="X1=account balance\nX2=ATM transactions\nX4=debit card\nX5=interest\nX6=city", 
        height=300)

with col2:
    st.subheader("📝 أسئلة الامتحان")
    questions_input = st.text_area("الصق الأسئلة هنا:", height=300)

# --- محرك التحليل المطور ---
if st.button("🚀 توليد كود SPSS Syntax المنهجي"):
    if not questions_input.strip():
        st.warning("⚠️ يرجى لصق الأسئلة أولاً.")
    elif rules_df is None:
        st.error("❌ فشل في جلب المنهج من GitHub. تحقق من الرابط.")
    else:
        # 1. بناء قاموس المتغيرات
        mapping_dict = {}
        for line in mapping_input.split('\n'):
            if '=' in line:
                parts = line.split('=')
                mapping_dict[parts[1].strip().lower()] = parts[0].strip().upper()
        
        # ترتيب الكلمات من الأطول للأقصر لتفادي أخطاء الاستبدال الجزئي
        sorted_var_names = sorted(mapping_dict.keys(), key=len, reverse=True)

        final_syntax = ["* Generated for Eng. Mohamed - MBA SPSS Solver.", "SET DECIMALS=DOT.\n"]

        # 2. تقسيم الأسئلة بشكل ذكي (حسب السطر أو الترقيم)
        # هذا يمنع تقسيم الجملة الواحدة لعدة أسطر
        raw_questions = re.split(r'\n(?=\d+[\.\)])|\n', questions_input)
        
        for q in raw_questions:
            q = q.strip()
            if not q or len(q) < 5: continue # تجاهل الأسطر الفارغة أو القصيرة جداً
            
            # تنظيف السؤال من الترقيم (1. أو 2.)
            clean_q = re.sub(r'^\d+[\.\)\s]+', '', q).lower()
            
            matched = False
            # البحث عن القاعدة (ترتيب تنازلي حسب طول الكلمة المفتاحية لضمان الدقة)
            sorted_rules = rules_df.copy()
            sorted_rules['key_len'] = sorted_rules['Keyword'].str.len()
            sorted_rules = sorted_rules.sort_values('key_len', ascending=False)

            for _, rule in sorted_rules.iterrows():
                keyword = str(rule['Keyword']).lower().strip()
                
                if keyword in clean_q:
                    template = str(rule['Syntax_Template'])
                    
                    # البحث عن جميع المتغيرات المذكورة في هذا السؤال
                    found_vars = []
                    for name in sorted_var_names:
                        if name in clean_q:
                            found_vars.append(mapping_dict[name])
                    
                    if found_vars:
                        # إزالة التكرار والحفاظ على الترتيب
                        unique_vars = []
                        [unique_vars.append(v) for v in found_vars if v not in unique_vars]
                        
                        # دمج المتغيرات في نص واحد (X1 X2 X3)
                        var_str = " ".join(unique_vars)
                        
                        # تطبيق الاستبدال في القالب
                        current_syntax = template.replace("{var}", var_str)
                        
                        # منطق خاص للرسوم البيانية التي تحتاج متغير تقسيم (Group)
                        if "{group}" in current_syntax:
                            # نفترض أن آخر متغير في السؤال هو متغير التقسيم (مثل City أو Gender)
                            group_var = unique_vars[-1] if unique_vars else ""
                            current_syntax = current_syntax.replace("{group}", group_var)

                        final_syntax.append(f"* Question: {q}")
                        final_syntax.append(f"{current_syntax}\nEXECUTE.")
                        matched = True
                        break
            
            if not matched:
                final_syntax.append(f"* Question: {q}\n* [!] لم يتم العثور على قاعدة مطابقة. تأكد من وجود '{q[:15]}...' في ملف المنهج.")

        # عرض النتيجة النهائية
        st.success("✅ اكتمل توليد الكود!")
        st.code("\n".join(final_syntax), language="spss")
        
        st.download_button(
            label="📥 تحميل ملف .sps",
            data="\n".join(final_syntax),
            file_name="MBA_Final_Solution.sps",
            mime="text/plain"
        )

# --- إرشادات للمهندس محمد بناءً على الملفات المرفقة ---
with st.expander("📚 إرشادات لضمان دقة الحل"):
    st.write("1. **الكلمات المفتاحية:** تأكد أن ملف الإكسيل يحتوي على كلمات مثل `frequency table`, `mean`, `bar chart`[cite: 57, 60, 62].")
    st.write("2. **الـ Mapping:** البرنامج يبحث عن الكلمة بالكامل، لذا اكتب `account balance` وليس `balance` فقط إذا كان هذا هو المكتوب في السؤال[cite: 58, 60, 61].")
    st.write("3. **الرسوم البيانية:** البرنامج مصمم ليتعرف على متغيرات المقارنة تلقائياً إذا وجدت في السؤال[cite: 62, 63].")
