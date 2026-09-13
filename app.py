import os
from datetime import date
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# הגדרות עמוד
st.set_page_config(
    page_title="מערכת תזונה, אימונים ומעקב מבוססת ראיות",
    layout="wide"
)

# ביטול מוחלט של חיצי מספרים והתאמת עיצוב RTL
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    .stTextInput input, .stTextArea textarea { direction: rtl; text-align: right; }
    .stChatMessage { direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { direction: rtl; text-align: right; }
    
    /* הסתרת כל החיצים וכפתורי הפלוס/מינוס בשדות קלט */
    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
    }
    input[type=number] {
        -moz-appearance: textfield !important;
    }
    button[data-testid="stNumberInputStepUp"],
    button[data-testid="stNumberInputStepDown"],
    div[data-testid="stNumberInputStepUp"],
    div[data-testid="stNumberInputStepDown"] {
        display: none !important;
    }

    .disclaimer-box {
        background-color: #fff3cd;
        border-right: 5px solid #ffeeba;
        padding: 12px 16px;
        border-radius: 4px;
        color: #856404;
        font-size: 13px;
        margin-bottom: 20px;
        line-height: 1.4;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 1. אבטחת מפתח API
api_key = (
    st.secrets.get("GEMINI_API_KEY")
    or st.secrets.get("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
)

if not api_key:
    st.error("שגיאה: מפתח API אינו מוגדר בהגדרות הסודיות (Secrets).")
    st.stop()

# 2. כותרת והבהרה משפטית
st.title("מערכת תזונה, כושר ומעקב מבוססת ראיות")
st.markdown("""
<div class="disclaimer-box">
    <strong>הבהרה חשובה:</strong> כלי זה מיועד למטרות לימודיות והנגשת מדע בלבד. החישובים, התפריטים וההמלצות אינם מהווים ייעוץ רפואי או תזונתי אישי ואינם תחליף לרופא או דיאטן קליני מוסמך.
</div>
""", unsafe_allow_html=True)

# 3. חלוקה ללשוניות
tab_calc, tab_tracker, tab_chat = st.tabs([
    "מחשבון קלוריות ומאקרו מותאם אישית",
    "יומן ומעקב שקילות ואימונים",
    "צ'אט ייעוץ מבוסס ספרות מחקרית"
])

# ==========================================
# לשונית 1: מחשבון קלוריות ומאקרו
# ==========================================
with tab_calc:
    st.subheader("תכנון קלורי ומאקרו-נוטריאנטים אישי")
    st.caption("הקלד את הנתונים ישירות בתיבות הטקסט (ללא חיצים)")
    
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1:
        gender = st.selectbox("מין ביולוגי:", ["גבר", "אישה"])
    with col_in2:
        age_input = st.text_input("גיל (שנים):", value="22")
    with col_in3:
        weight_input = st.text_input("משקל (ק\"ג):", value="75.0")
    with col_in4:
        height_input = st.text_input("גובה (ס\"מ):", value="175")
        
    # המרת ערכים בצורה בטוחה
    try:
        user_weight = float(weight_input.strip())
    except (ValueError, AttributeError):
        user_weight = 75.0
        
    try:
        user_height = float(height_input.strip())
    except (ValueError, AttributeError):
        user_height = 175.0
        
    try:
        age = int(age_input.strip())
    except (ValueError, AttributeError):
        age = 22
        
    col_in5, col_in6 = st.columns(2)
    with col_in5:
        activity = st.selectbox(
            "רמת פעילות שבועית:",
            [
                "יושבני (עבודה משרדית, ללא אימונים)",
                "פעילות קלה (1-3 אימונים בשבוע)",
                "פעילות בינונית (3-5 אימונים בשבוע)",
                "פעילות גבוהה (6-7 אימונים עצימים בשבוע)",
                "ספורטאי תחרותי / עבודה פיזית מאומצת"
            ]
        )
    with col_in6:
        diet_goal = st.selectbox(
            "יעד תזונתי:",
            [
                "שימור מסת שריר בחיטוב (גירעון מתון של כ-400 קלוריות)",
                "שמירה על משקל קיים (מאזן ניטרלי)",
                "בניית מסת שריר מתונה / מסה נקייה (עודף של כ-250 קלוריות)",
                "עלייה מואצת במסה (עודף של כ-500 קלוריות)"
            ]
        )
        
    # חישוב BMR
    if gender == "גבר":
        bmr = (10 * user_weight) + (6.25 * user_height) - (5 * age) + 5
    else:
        bmr = (10 * user_weight) + (6.25 * user_height) - (5 * age) - 161
        
    activity_factors = {
        "יושבני (עבודה משרדית, ללא אימונים)": 1.2,
        "פעילות קלה (1-3 אימונים בשבוע)": 1.375,
        "פעילות בינונית (3-5 אימונים בשבוע)": 1.55,
        "פעילות גבוהה (6-7 אימונים עצימים בשבוע)": 1.725,
        "ספורטאי תחרותי / עבודה פיזית מאומצת": 1.9
    }
    tdee = bmr * activity_factors[activity]
    
    if "גירעון" in diet_goal:
        target_calories = tdee - 400
        protein_per_kg = 2.0
    elif "עודף של כ-250" in diet_goal:
        target_calories = tdee + 250
        protein_per_kg = 1.8
    elif "עודף של כ-500" in diet_goal:
        target_calories = tdee + 500
        protein_per_kg = 1.8
    else:
        target_calories = tdee
        protein_per_kg = 1.8
        
    protein_g = round(user_weight * protein_per_kg)
    protein_kcal = protein_g * 4
    
    fat_kcal = target_calories * 0.25
    fat_g = round(fat_kcal / 9)
    
    carbs_kcal = max(0, target_calories - (protein_kcal + fat_kcal))
    carbs_g = round(carbs_kcal / 4)
    
    st.markdown("---")
    st.subheader("תוצאות ההקצאה היומית:")
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("סך קלוריות מומלץ", f"{round(target_calories)} קק\"ל")
    with m_col2:
        st.metric("חלבון יומי", f"{protein_g} גרם", f"{round(protein_kcal)} קלוריות")
    with m_col3:
        st.metric("שומן יומי", f"{fat_g} גרם", f"{round(fat_kcal)} קלוריות")
    with m_col4:
        st.metric("פחמימות יומיות", f"{carbs_g} גרם", f"{round(carbs_kcal)} קלוריות")
        
    st.info(f"המלצת חלוקה לארוחות: כ-3 עד 4 ארוחות יומיות, כאשר כל ארוחה מכילה לפחות {round(protein_g / 3.5)} גרם חלבון להבטחת גירוי מסלול mTOR וסינתזת חלבוני שריר.")

# ==========================================
# לשונית 2: יומן מעקב ושקילות
# ==========================================
with tab_tracker:
    st.subheader("יומן מעקב שקילות ואימונים")
    st.caption("הקלדה ידנית ישירה ללא כפתורי חצים")
    
    if "tracker_data" not in st.session_state:
        st.session_state.tracker_data = []
        
    with st.form("add_log_form", clear_on_submit=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            log_date = st.date_input("תאריך:", value=date.today())
        with f_col2:
            log_weight_input = st.text_input("משקל בוקר (ק\"ג):", value=f"{user_weight:.1f}")
        with f_col3:
            log_calories_input = st.text_input("צריכה קלורית משוערת:", value=f"{round(target_calories)}")
        with f_col4:
            log_workout = st.text_input("אימון שבוצע / קבוצת שריר:", placeholder="למשל: רגליים וכתפיים, RIR 1-2")
            
        submitted = st.form_submit_button("הוסף רשומה ליומן")
        if submitted:
            try:
                parsed_weight = float(log_weight_input.strip())
            except ValueError:
                parsed_weight = user_weight
            try:
                parsed_cals = int(log_calories_input.strip())
            except ValueError:
                parsed_cals = round(target_calories)
                
            st.session_state.tracker_data.append({
                "תאריך": str(log_date),
                "משקל (ק\"ג)": parsed_weight,
                "קלוריות": parsed_cals,
                "הערות אימון": log_workout if log_workout else "ללא פירוט"
            })
            st.success("הרשומה נוספה בהצלחה.")
            
    if st.session_state.tracker_data:
        df_logs = pd.DataFrame(st.session_state.tracker_data)
        st.dataframe(df_logs, use_container_width=True)
        
        csv_data = df_logs.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="הורד יומן מעקב לקובץ Excel / CSV",
            data=csv_data,
            file_name=f"fitness_tracker_{date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.write("אין עדיין רשומות ביומן המעקב. הוסף רשומה בטופס למעלה.")

# ==========================================
# לשונית 3: צ'אט מחקרים וראיות
# ==========================================
with tab_chat:
    st.subheader("שאלות ותשובות מבוססות מחקרים ופיזיולוגיה")
    
    SYSTEM_INSTRUCTION = """
אתה מומחה בכיר ומנגיש ידע בתחומי תזונת הספורט, פיזיולוגיית המאמץ והמטבוליזם.
בסיס הידע שלך מושתת על מדרג הראיות המדעיות (Evidence Hierarchy), תוך עדיפות למטא-אנליזות, סקירות שיטתיות ו-RCTs שפיטים, לצד המתודולוגיות של מנגישי הידע מבוססי הראיות בישראל (גיא שלמון, אשד לין, טל בן משה).

עקרונות המענה:
1. שלב תמיד בין תזונה לאימונים:
   - היפרטרופיה ועומס: מתח מכני, RIR/RPE, נפח שבועי אפקטיבי (10-20 סטים לשריר), זמני מנוחה מספקים (2-3 דקות בתרגילים מורכבים).
   - תזונה ומאזן אנרגיה: קלוריות יומיות, חלבון מבוסס משקל גוף, חלוקת חלבון סביב אימונים, הידרציה, תוספים בדרג A (קריאטין, קפאין).
2. ציטוט מחקרי מפתח: ציין שמות חוקרים ושנת פרסום (Morton et al. 2018, Schoenfeld et al. 2017, Aragon & Schoenfeld 2013, ניירות עמדה של ISSN ו-ACSM).
3. החרגה רפואית: המידע הינו לימודי בלבד ולא תחליף לייעוץ פרטני.
"""

    def generate_ai_reply(prompt_text: str):
        try:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                safety_settings=[
                    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                ]
            )
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt_text,
                config=config
            )
            
            reply_text = response.text if response.text else "לא התקבלה תשובה מהמודל."
            sources = []
            if response.candidates and response.candidates[0].grounding_metadata:
                gm = response.candidates[0].grounding_metadata
                if hasattr(gm, "grounding_chunks") and gm.grounding_chunks:
                    for chunk in gm.grounding_chunks:
                        if hasattr(chunk, "web") and chunk.web:
                            title = chunk.web.title or "מאמר מדעי / מקור מקוון"
                            uri = chunk.web.uri
                            if uri and uri not in [s[1] for s in sources]:
                                sources.append((title, uri))
            return reply_text, sources
        except Exception as e:
            return f"אירעה שגיאה בעיבוד הנתונים ({e}). אנא נסה שוב מאוחר יותר.", []

    if "chat_history_v2" not in st.session_state:
        st.session_state.chat_history_v2 = []

    for msg in st.session_state.chat_history_v2:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    chat_query = st.chat_input("שאל/י על אימונים, תזונת ספורט, קריאטין, מסה, חיטוב ומחקרים...")
    if chat_query:
        st.session_state.chat_history_v2.append({"role": "user", "content": chat_query})
        with st.chat_message("user"):
            st.markdown(chat_query)
            
        with st.chat_message("assistant"):
            with st.spinner("סורק ספרות מחקרית ומנתח נתונים..."):
                reply_out, sources_out = generate_ai_reply(chat_query)
                st.markdown(reply_out)
                
                if sources_out:
                    st.markdown("---")
                    st.caption("מקורות ומחקרים שנמצאו ברשת:")
                    for s_title, s_uri in sources_out[:5]:
                        st.markdown(f"- [{s_title}]({s_uri})")
                        
        final_history_text = reply_out
        if sources_out:
            final_history_text += "\n\n**מקורות שנסרקו:**\n" + "\n".join([f"- [{s_title}]({s_uri})" for s_title, s_uri in sources_out[:5]])
        st.session_state.chat_history_v2.append({"role": "assistant", "content": final_history_text})
