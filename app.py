import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="SPSS Master Solver", layout="wide")

st.title("🚀 المحرك الذكي المطور (تعامل مع قوائم المتغيرات)")

# --- الجانب الأيسر: الإعدادات ---
with st.sidebar:
    st.header("📂 1. البيانات والمرجع")
    # ارفع ملف "SPSS_Master_Guide_Template.csv" الذي أنشأته لك
    guide_file = st.file_uploader("ارفع ملف الدليل (Excel/CSV)", type=['csv', 'xlsx'])
    
    st.header("⚙️ 2. الـ Mapping (الربط)")
    st.info("اكتب اسم المتغير في السؤال = اسمه في ملفك")
    # هنا تضع المتغيرات المطلوبة في السؤال
    v_mapping = st.text_area("مثال:\nVars=X2 X3 X4\nTarget=X1", 
                               value="Vars=X2 X3 X4\nTarget=X1", height=150)

# تحويل الـ Mapping لقاموس
mapping_dict = {}
for line in v_mapping.split('\n'):
    if '=' in line:
        k, v = line.split('=')
        mapping_dict[k.strip()] = v.strip()

# --- الجانب الأيمن: حل الأسئلة ---
st.header("📝 خطوة 3: الصق سؤال الامتحان")
q_input = st.text_area("مثال: Construct a frequency table for debit card, interest, and city", height=150)

if st.button("🚀 توليد كود SPSS الآن"):
    if guide_file and q_input:
        # قراءة الدليل
        df_guide = pd.read_csv(guide_file) if guide_file.name.endswith('csv') else pd.read_excel(guide_file)
        
        # البحث عن الكلمة المفتاحية في السؤال
        found = False
        for _, row in df_guide.iterrows():
            keyword = str(row['Keyword']).lower()
            if keyword in q_input.lower():
                syntax = str(row['Syntax'])
                
                # استبدال الـ Placeholders بالقيم من الـ Mapping
                # هذا الجزء سيبدل [Vars] بـ X2 X3 X4 دفعة واحدة
                for key, val in mapping_dict.items():
                    syntax = syntax.replace(f"[{key}]", val)
                
                st.success(f"✅ تم اكتشاف نوع التحليل: {row['Category']}")
                st.code(f"* Solution for: {keyword}\n" + syntax + "\nEXECUTE.", language="spss")
                found = True
                break
        
        if not found:
            st.error("❌ لم أجد كلمة مفتاحية في الدليل تطابق سؤالك. يرجى إضافة 'frequency' في ملف الدليل.")
    else:
        st.warning("يرجى رفع ملف الدليل وكتابة السؤال.")
