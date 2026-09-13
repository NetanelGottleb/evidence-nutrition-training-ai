import os
import streamlit as st
from google import genai
from google.genai import types

# הגדרות עמוד
st.set_page_config(
    page_title="עוזר תזונה ואימונים מבוסס ראיות ומחקרים",
    layout="wide"
)

# התאמת עיצוב RTL בעברית
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    .stTextInput input, .stTextArea textarea { direction: rtl; text-align: right; }
    .stChatMessage { direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { direction: rtl; text-align: right; }
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
    .source-box {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 10px 14px;
        border-radius: 6px;
        margin-top: 15px;
        font-size: 12px;
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

# 2. כותרת והצהרה משפטית
st.title("עוזר תזונה וכושר מבוסס ראיות ומחקרים קליניים")
st.caption("מנוע מענה המחובר בזמן אמת לספרות המחקרית ב-PubMed, מטא-אנליזות וניירות עמדה רשמיים")

st.markdown("""
<div class="disclaimer-box">
    <strong>הבהרה חשובה:</strong> כלי זה מיועד למטרות לימודיות והנגשת מדע בלבד. המידע והמקורות המובאים אינם מהווים ייעוץ רפואי, אבחון קליני, או תוכנית אישית מותאמת. לפני כל שינוי תזונתי או עומס אימונים יש להיוועץ באיש מקצוע מוסמך (רופא, דיאטן קליני או מאמן מוסמך).
</div>
""", unsafe_allow_html=True)

# 3. סרגל צד - מחשבון ומדרג הראיות
with st.sidebar:
    st.header("מחשבון חלבון יומי מבוסס ראיות")
    st.write("טווחים לפי עמדות ה-ISSN ומטא-אנליזות (Morton et al., 2018).")
    
    weight = st.number_input("משקל גוף (ק\"ג):", min_value=30.0, max_value=200.0, value=75.0, step=0.5)
    goal = st.selectbox(
        "מטרה עיקרית:",
        [
            "היפרטרופיה / עלייה במסת שריר (1.6 - 2.2 גרם/ק\"ג)",
            "שימור מסת שריר בגירעון קלורי / חיטוב (1.8 - 2.4 גרם/ק\"ג)",
            "ספורטאי סיבולת (1.2 - 1.6 גרם/ק\"ג)",
            "אוכלוסייה כללית / בריאות (0.8 - 1.2 גרם/ק\"ג)"
        ]
    )
    
    if "היפרטרופיה" in goal:
        low, high = 1.6, 2.2
    elif "חיטוב" in goal:
        low, high = 1.8, 2.4
    elif "סיבולת" in goal:
        low, high = 1.2, 1.6
    else:
        low, high = 0.8, 1.2
        
    p_low = round(weight * low)
    p_high = round(weight * high)
    
    st.success(f"טווח מומלץ: {p_low} - {p_high} גרם חלבון ביום.")
    st.caption(f"חלוקה אפקטיבית: 3-5 מנות של כ-{round(weight * 0.4)} גרם חלבון לארוחה.")
    
    st.markdown("---")
    st.subheader("מדרג הראיות המדעיות בכלי")
    st.markdown("""
    1. **מטא-אנליזות וסקירות שיטתיות** (רמת הראיה הגבוהה ביותר).
    2. **ניסויים קליניים מבוקרים (RCTs)** בבני אדם.
    3. **ניירות עמדה בינלאומיים** (ISSN, ACSM, AND).
    4. **מתודולוגיה מדעית ישראלית** (גיא שלמון, אשד לין, טל בן משה).
    """)

# 4. מנוע AI עם חיפוש ספרות מחקרית חי (Grounding)
SYSTEM_INSTRUCTION = """
אתה חוקר ומנגיש ידע מדעי בכיר בתחומי תזונת הספורט, פיזיולוגיית המאמץ והמטבוליזם.
בסיס הידע שלך מושתת באופן קשיח על מדרג הראיות המדעיות (Evidence Hierarchy), תוך עדיפות עליונה למטא-אנליזות, סקירות שיטתיות וניסויים קליניים מבוקרים (RCTs) שפורסמו בכתבי עת שפיטים.

עקרונות חובה במענה:
1. ציטוט ספרות ומחקרים אמיתיים:
   - בכל תשובה ציין את שמות החוקרים העיקריים ושנת הפרסום של מטא-אנליזות או מחקרי מפתח רלוונטיים (למשל: Morton et al. 2018 בנושא חלבון; Schoenfeld et al. 2017 בנושא נפח ותדירות; Aragon & Schoenfeld 2013 בנושא תזמון חלבון; Hall et al. בנושא מודלים מטבוליים ומאזן אנרגיה; עמדות ISSN ו-ACSM).
   - הקפד להבחין בבירור בין ממצאים שהוכחו במטא-אנליזות על בני אדם מאומנים, לבין השערות מנגנוניות או מחקרי עכברים.
2. ניתוח פיזיולוגי מנומק:
   - הסבר בקצרה את המנגנון הביולוגי (מתח מכני, מסלול mTOR, סינתזת חלבוני שריר MPS, מאזן חנקן, מאזן אנרגטי).
   - נתח והפרך מיתוסים נפוצים באמצעות נתוני הניסויים הקליניים (כגון מיתוס החלון האנבולי הצר, מיתוסי נזק מטבולי, ניקוי רעלים, או השמנה שאינה נובעת ממאזן קלורי).
3. מבנה התשובה:
   - מסקנה תמציתית וישימה (Takeaway).
   - הראיות המחקריות (פירוט מחקרי מפתח ומטא-אנליזות).
   - המנגנון הפיזיולוגי.
   - סייגים ומגבלות מחקריות (היכן חסר מידע או שיש שונות בינאישית).
4. החרגה רפואית:
   - ציין תמיד שמדובר בהנגשת מידע מדעי ולא בהמלצה רפואית פרטנית.
"""

def generate_response(prompt: str):
    try:
        client = genai.Client(api_key=api_key)
        # הפעלת חיפוש מחקרים חי בגוגל (Grounding)
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
            contents=prompt,
            config=config
        )
        
        reply_text = response.text if response.text else "לא התקבלה תשובה מהמודל."
        
        # חילוץ אוטומטי של מקורות ומאמרים מתוך תוצאות החיפוש
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

# 5. ניהול היסטוריית השיחה
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# כפתורי שאילתות מבוססות ספרות
st.write("שאילתות מדעיות לדוגמה:")
col1, col2, col3 = st.columns(3)
quick_query = None
with col1:
    if st.button("כמות חלבון אופטימלית: מה אומרות המטא-אנליזות?", use_container_width=True):
        quick_query = "מהי כמות החלבון היומית המרבית שממנה יש תועלת להיפרטרופיה לפי המטא-אנליזה של Morton 2018 וספרות עוקבת?"
with col2:
    if st.button("נפח שבועי מול עצימות: Schoenfeld 2017", use_container_width=True):
        quick_query = "כיצד מוגדר הקשר בין נפח האימון השבועי (מספר סטים לקבוצת שריר) לבין שיעור ההיפרטרופיה לפי הספרות של Schoenfeld?"
with col3:
    if st.button("קריאטין וספיגה: נייר עמדת ה-ISSN", use_container_width=True):
        quick_query = "מהן המסקנות העיקריות של נייר עמדת ה-ISSN לגבי יעילות, פרוטוקולי העמסה ובטיחות של קריאטין מונוהידראט?"

user_input = st.chat_input("שאל/י על מחקרים, מטא-אנליזות, פיזיולוגיה של המאמץ ותזונת ספורט...") or quick_query

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        with st.spinner("סורק ספרות מחקרית ומנתח נתונים קליניים..."):
            ai_reply, sources = generate_response(user_input)
            st.markdown(ai_reply)
            
            if sources:
                st.markdown("---")
                st.caption("מקורות ומאמרים מדעיים שנמצאו ברשת:")
                for title, uri in sources[:5]:
                    st.markdown(f"- [{title}]({uri})")
            
    # שמירה בהיסטוריה
    full_content = ai_reply
    if sources:
        full_content += "\n\n**מקורות שנסרקו:**\n" + "\n".join([f"- [{title}]({uri})" for title, uri in sources[:5]])
    st.session_state.chat_history.append({"role": "assistant", "content": full_content})
