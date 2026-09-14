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
        margin-bottom: 12px;
        line-height: 1.5;
    }
    .menu-disclaimer {
        background-color: #e2e3e5;
        border-right: 4px solid #6c757d;
        padding: 10px 14px;
        border-radius: 4px;
        color: #383d41;
        font-size: 12px;
        margin-top: 15px;
        margin-bottom: 15px;
        line-height: 1.4;
    }
    .workout-box {
        background-color: #e8f4fd;
        border-right: 5px solid #2b7bb9;
        padding: 12px 16px;
        border-radius: 4px;
        color: #1a4971;
        font-size: 13px;
        margin-bottom: 15px;
        line-height: 1.5;
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

# 2. כותרת והבהרה משפטית מעוגנת בדין הישראלי
st.title("מערכת תזונה, כושר ומעקב מבוססת ראיות ומחקרים")

st.markdown("""
<div class="disclaimer-box">
    <strong>הבהרה משפטית ובריאותית חשובה (דין ישראלי):</strong><br>
    כלי זה מיועד למטרות לימודיות, מחקריות והעשרה בלבד, ואינו מהווה ייעוץ רפואי, אבחון קליני או תפריט תזונתי פרטני לפי <em>חוק הסדרת העיסוק במקצועות הבריאות, התשס"ח-2008</em>. 
    אין בשימוש במערכת כדי ליצור יחסי מטפל-מטופל, וחל איסור להסתמך על הפלטים כתחליף לבדיקה והתאמה אישית אצל רופא מוסמך או דיאטן קליני בעל רישיון משרד הבריאות. השימוש באפליקציה הוא על אחריותו הבלעדית של המשתמש.<br><br>
    שימוש באתר או באפליקציה זו מהווה הסכמה לתנאים, ככל והמשתמש לא מסכים לתנאים הינו מתכבד לצאת ולא להשתמש. נכתב בלשון זכר אך פונה לשני המינים יחדיו.
</div>
""", unsafe_allow_html=True)

with st.expander("קרא את כתב הוויתור המשפטי, תנאי השימוש והסרת האחריות המלאים"):
    st.markdown("""
<div dir="rtl" style="direction: rtl; text-align: right; line-height: 1.7; font-size: 14px;">
    <p style="margin: 6px 0;"><strong>1. מטרת המערכת:</strong> המערכת פועלת באמצעות בינה מלאכותית ונועדה להמחשת עקרונות תיאורטיים ומעשיים מבוססי-ראיות (Evidence-Based) בספרות המחקרית ובמתודולוגיות מנגישי הידע בישראל: קבוצת EVB תזונה וכושר, אתר קילוגרם ומייק בייקוב, גיא שלמון, אשד לין וטל בן משה.</p>
    <p style="margin: 6px 0;"><strong>2. היעדר יחסי מטפל-מטופל:</strong> השימוש במערכת אינו מהווה תחליף לטיפול תזונתי או רפואי ואינו יוצר יחסי דיאטן-מטופל או מאמן-מתאמן.</p>
    <p style="margin: 6px 0;"><strong>3. חובת בדיקה רפואית:</strong> חובה להיוועץ ברופא ובדיאטן קליני בעל רישיון משרד הבריאות בתוקף לפני כל שינוי בצריכת המזון, עומסי האימון או נטילת תוספים.</p>
    <p style="margin: 6px 0;"><strong>4. אוכלוסיות מיוחדות וקטינים:</strong> השימוש בקרב בני נוער (מתחת לגיל 18) מיועד למטרות לימודיות והעשרה בלבד ומחייב ליווי והסכמת הורים וכן פיקוח רפואי ותזונתי מוסמך. המערכת אינה מיועדת לנשים בהיריון/הנקה, אנשים עם מחלות רקע (סוכרת, דיסליפידמיה, מחלות כליה, לחץ דם) או עבר של הפרעות אכילה.</p>
    <p style="margin: 6px 0;"><strong>5. הסרת אחריות:</strong> המפעיל אינו נושא בכל אחריות לנזק ישיר או עקיף שייגרם מהסתמכות על חישובי המערכת או הצעות התפריט. השימוש הינו באחריות המשתמש בלבד.</p>
    <p style="margin: 6px 0;"><strong>6. סמכות שיפוט ייחודית:</strong> בכל מקרה של מחלוקת, טענה או תביעה הנוגעת לשימוש באתר, באפליקציה או בתכנים הנגזרים מהם, סמכות השיפוט הבלעדית והייחודית תהא נתונה אך ורק לבתי המשפט המוסמכים במחוז תל אביב-יפו, ועל כל עניין יחול הדין הישראלי בלבד.</p>
    <p style="margin: 6px 0;"><strong>7. שינויים בקוד ובהנחיות:</strong> היוצר שומר לעצמו את הזכות לשנות, להוסיף ולעדכן כראות עיניו מעת לעת את ההנחיות, התנאים, האלגוריתמים והקוד עצמו באתר ובאפליקציה, ללא צורך בהודעה מוקדמת או עדכון המשתמש, ומבלי שייכתב או יצוין באתר שנעשה עדכון. השינויים ייכנסו לתוקף מיד עם הטמעתם ויתגלו למשתמש בעת שימוש שוטף או רענון הדף/האפליקציה. חלה אחריות בלעדית על המשתמש לבדוק ולהתעדכן בשינויים ובתוספות.</p>
</div>
""", unsafe_allow_html=True)

# 3. חלוקה ללשוניות
tab_calc, tab_workout, tab_tracker, tab_chat = st.tabs([
    "מחשבון קלוריות ומחולל תפריט",
    "מחולל תוכניות אימון ונפח",
    "יומן ומעקב שקילות",
    "צ'אט ייעוץ ומחקרים"
])

# ==========================================
# לשונית 1: מחשבון ומחולל תפריט 3-5 ארוחות
# ==========================================
with tab_calc:
    st.subheader("1. תכנון קלורי ומאקרו-נוטריאנטים")
    st.caption("הזנה ישירה במקלדת (ללא חיצים) - מבוסס על עקרונות קבוצת EVB תזונה וכושר, אתר קילוגרם (מייק בייקוב), גיא שלמון, אשד לין, טל בן משה, ומותאם גם לבני נוער")
    
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1:
        gender = st.selectbox("מין ביולוגי:", ["גבר", "אישה"])
    with col_in2:
        age_input = st.text_input("גיל (שנים):", value="22", help="טווח גילאים פתוח (13 ומעלה). לגילאי נוער מופעלות התאמות גדילה ובטיחות.")
    with col_in3:
        weight_input = st.text_input('משקל (ק"ג):', value="75.0")
    with col_in4:
        height_input = st.text_input('גובה (ס"מ):', value="175")
        
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
        
    is_teen = age < 18
    if is_teen:
        st.info(f"מזוהה משתמש בגיל התבגרות ({age}). המערכת מחילה מקדמי גדילה, מקפידה על צפיפות נוטריאנטים ומגבילה גירעון אנרגטי למניעת פגיעה בהתפתחות.")

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
                "שימור מסת שריר בחיטוב (גירעון מתון ומבוקר)",
                "שמירה על משקל קיים (מאזן ניטרלי)",
                "בניית מסת שריר מתונה / מסה נקייה (עודף של כ-250 קלוריות)",
                "עלייה מואצת במסה (עודף של כ-500 קלוריות)"
            ]
        )
        
    # חישוב BMR לפי Mifflin-St Jeor עם תוספת אנרגטית לצורכי גדילה למתבגרים
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
    
    # תוספת צורכי גדילה והתפתחות למתבגרים (Schofield / FAO/WHO)
    growth_energy = 150 if is_teen else 0
    tdee = (bmr * activity_factors[activity]) + growth_energy
    
    if "גירעון" in diet_goal:
        if is_teen:
            # הגבלה מחמירה לגירעון קל מאוד בבני נוער (לא יותר מ-200 קק"ל ולא מתחת ל-BMR)
            deficit = min(200, max(0, tdee - bmr))
            target_calories = max(tdee - deficit, bmr)
            protein_per_kg = 1.8
            st.warning("שים לב: בגיל ההתבגרות גירעון קלורי אגרסיבי עלול לפגוע בגדילה לגובה, בצפיפות העצם ובמאזן ההורמונלי. הגירעון הוגבל לערך מתון מאוד.")
        else:
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
        protein_per_kg = 1.8 if not is_teen else 1.6
        
    protein_g = round(user_weight * protein_per_kg)
    protein_kcal = protein_g * 4
    
    fat_kcal = target_calories * 0.25
    fat_g = round(fat_kcal / 9)
    
    carbs_kcal = max(0, target_calories - (protein_kcal + fat_kcal))
    carbs_g = round(carbs_kcal / 4)
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("סך קלוריות יעד", f'{round(target_calories)} קק"ל')
    with m_col2:
        st.metric("חלבון יומי", f"{protein_g} גרם", f"{round(protein_kcal)} קלוריות")
    with m_col3:
        st.metric("שומן יומי", f"{fat_g} גרם", f"{round(fat_kcal)} קלוריות")
    with m_col4:
        st.metric("פחמימות יומיות", f"{carbs_g} גרם", f"{round(carbs_kcal)} קלוריות")
        
    st.markdown("---")
    st.subheader("2. מחולל שלד תפריט לדוגמה (3 עד 5 ארוחות)")
    st.caption("מבוסס על ערכי מאגר צמרת של משרד הבריאות, FoodsDictionary, אתר קילוגרם (מייק בייקוב), גיא שלמון, אשד לין, טל בן משה וקבוצת EVB תזונה וכושר")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        num_meals = st.selectbox("מספר ארוחות רצוי ביום:", ["3 ארוחות", "4 ארוחות", "5 ארוחות"], index=1)
    with col_m2:
        special_condition = st.text_input(
            "מגבלות, רגישויות או מצב בריאותי (אופציונלי):",
            placeholder="למשל: רגישות ללקטוז, צמחוני, כולסטרול גבוה, טרום סוכרת, כשרות"
        )
        
    def generate_menu_framework(cals, prot, fat, carbs, meals_count, condition, user_age, is_adolescent):
        system_menu_prompt = """
אתה דיאטן וחוקר תזונת ספורט בכיר הפועל בגישת Evidence-Based (מבוסס ראיות ומחקרים מדעיים).
הידע שלך מושתת על ניירות העמדה של משרד הבריאות הישראלי, עמותת "עתיד", ISSN, ACSM, לצד המתודולוגיות של מנגישי הידע בישראל:
- אתר "קילוגרם" (Kilogrm) ומייק בייקוב
- גיא שלמון (פורום הפייסבוק והעמוד האישי)
- אשד לין (מאמרים, הרצאות ותכנים מקצועיים מבוססי ראיות)
- טל בן משה (התכנים והעמוד האישי)
- קבוצת "EVB תזונה וכושר" בפייסבוק

תפקידך לבנות שלד תפריט לדוגמה בלבד (הצעה לימודית), המבוסס במדויק על ערכי הרכב מזונות אמינים מתוך מאגר "צמרת" של משרד הבריאות הישראלי, FoodsDictionary ו-USDA.

כללים מחייבים בבניית התפריט:
1. התאמת גיל והתפתחות:
   - אם מדובר במתבגר/נער (מתחת לגיל 18): הקפד על מקורות עשירים בסידן (מוצרי חלב / משקאות סויה מועשרים), ברזל, אבץ וצפיפות תזונתית גבוהה לתמיכה בצמיחה לגובה והתפתחות שלד ומוח. בשום אופן לא להמליץ על צמצום קלורי קיצוני.
2. דיוק בכמויות ומאגרים:
   - ציין לכל פריט מזון משקל מדויק בגרמים (או מ"ל) לצד מידה ביתית ברורה (כגון: 150 גרם חזה עוף מבושל = פילה בינוני; 60 גרם שיבולת שועל = כ-6 כפות).
   - הקפד שהסך הכללי של הארוחות יתכנס במדויק ליעדי הקלוריות והמאקרו שהוגדרו.
3. חלוקה לארוחות (3 עד 5 ארוחות):
   - פזר את החלבון שווה בשווה בין הארוחות (לפחות 25-40 גרם חלבון לארוחה לחציית סף הלאוצין ל-MPS).
   - כלול ארוחה ייעודית סביב האימון (Pre/Post Workout).
4. התייחסות רגועה ומעצימה למגבלות ומצבים בריאותיים:
   - אם צוינה רגישות, מחלה או מגבלה – התייחס אליה ברוגע ובטבעיות כהתאמה שגרתית ופשוטה.
5. מבנה התשובה:
   - טבלה או רשימה מסודרת לכל ארוחה: מזונות, כמויות, וחלוקת מאקרו.
   - סיכום יומי כולל של ערכים (סך קלוריות, חלבון, שומן, פחמימות, סיבים תזונתיים).
   - תווית החרגה בולטת המבהירה שמדובר בהצעה בלבד ויש להיוועץ באיש מקצוע מוסמך.
"""
        user_prompt = f"""
בנה שלד תפריט לדוגמה לפי הנתונים הבאים:
- גיל המתאמן: {user_age} ({'מתבגר/נוער - יש להתאים לגדילה' if is_adolescent else 'בוגר'})
- סך קלוריות יעד: {cals} קק"ל
- חלבון: {prot} גרם
- שומן: {fat} גרם
- פחמימות: {carbs} גרם
- מספר ארוחות: {meals_count}
- דגשים מיוחדים, רגישויות או רקע בריאותי: {condition if condition else 'ללא מגבלה מיוחדת'}
"""
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_menu_prompt,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    safety_settings=[
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    ]
                )
            )
            return response.text if response.text else "לא נוצר תפריט."
        except Exception as e:
            return f"אירעה שגיאה בבניית שלד התפריט ({e}). אנא נסה שוב."

    if st.button("בנה שלד תפריט לדוגמה", use_container_width=True):
        with st.spinner("מחשב כמויות ומחלק לארוחות לפי נתוני מאגר צמרת והנחיות משרד הבריאות..."):
            menu_output = generate_menu_framework(
                round(target_calories), protein_g, fat_g, carbs_g, num_meals, special_condition, age, is_teen
            )
            st.markdown("""
            <div class="menu-disclaimer">
                <strong>לידיעתך:</strong> שלד התפריט המוצג הינו הדגמה לימודית וחישובית בלבד על בסיס נתוני מאגר צמרת. אין לראות בו תפריט תזונתי מחייב או הוראה לפעולה, ואין בו כדי להחליף התאמה פרטנית על ידי דיאטן קליני מורשה כחוק.
            </div>
            """, unsafe_allow_html=True)
            st.markdown(menu_output)

# ==========================================
# לשונית 2: מחולל תוכניות אימון ונפח לפי מטרה
# ==========================================
with tab_workout:
    st.subheader("בניית תוכנית אימון מבוססת ראיות (Evidence-Based Volume & Periodization)")
    st.caption("מבוסס על עקרונות קבוצת EVB תזונה וכושר, אתר קילוגרם (מייק בייקוב), גיא שלמון, אשד לין, טל בן משה, וספרות ההיפרטרופיה (Schoenfeld, Helms, Israetel, Morton)")
    
    st.markdown("""
    <div class="workout-box">
        <strong>עקרונות המודול:</strong><br>
        התאמת נפח סטים שבועי לפי קבוצת שריר (MEV/MAV), קביעת פיצול אופטימלי (Split), ניהול עצימות וקרבה לכשל (RIR), והתאמה לגיל המתאמן (דגש בטיחותי וטכני לנוער) - ברוח המתודולוגיות של קבוצת EVB תזונה וכושר, אתר קילוגרם (מייק בייקוב), גיא שלמון, אשד לין וטל בן משה.
    </div>
    """, unsafe_allow_html=True)
    
    w_col1, w_col2, w_col3 = st.columns(3)
    with w_col1:
        workout_days = st.selectbox(
            "ימי אימון בשבוע:",
            ["2 ימים בשבוע", "3 ימים בשבוע", "4 ימים בשבוע", "5 ימים בשבוע", "6 ימים בשבוע"],
            index=1
        )
    with w_col2:
        training_goal = st.selectbox(
            "מטרת האימון המרכזית:",
            [
                "היפרטרופיה מקסימלית (בניית מסת שריר)",
                "שימור מסת שריר בחיטוב (שמירה על עצימות ונפח מותאם)",
                "פיתוח כוח בסיסי (כוח מרבי ותרגילי בסיס)"
            ]
        )
    with w_col3:
        experience_level = st.selectbox(
            "רמת מתאמן:",
            ["מתחיל (עד שנה של אימונים סדירים)", "בינוני (1-3 שנים)", "מתקדם (3+ שנים)"]
        )
        
    days_num = int(workout_days.split()[0])
    
    # המלצת פיצול אוטומטית לפי ימים
    if days_num <= 3:
        suggested_split = "Full Body (FBW - אימון גוף מלא בכל מפגש, תדירות שבועית גבוהה לכל שריר)"
    elif days_num == 4:
        suggested_split = "Upper / Lower (פלג גוף עליון / פלג גוף תחתון - 2 גירויים שבועיים לכל שריר)"
    elif days_num == 5:
        suggested_split = "Upper / Lower / Push / Pull / Legs או PPL + Upper/Lower"
    else:
        suggested_split = "Push / Pull / Legs (PPL מחזורי פעמיים בשבוע)"
        
    st.info(f"**מבנה פיצול מומלץ:** {suggested_split}")
    
    # חישוב נפח שבועי מומלץ (Weekly Set Volume)
    st.markdown("#### מדרג נפח שבועי מומלץ לקבוצות שריר (Weekly Sets):")
    
    if "שימור" in training_goal or "גירעון" in diet_goal:
        vol_chest = "8 - 12 סטים"
        vol_back = "10 - 14 סטים"
        vol_legs = "10 - 14 סטים"
        vol_shoulders = "6 - 10 סטים"
        vol_arms = "6 - 8 סטים (ישיר)"
        vol_note = "בגירעון קלורי נפח ההתאוששות (MRV) מוגבל; מתעדפים שמירה על משקלי עבודה (Intensity) ונפח סביב MEV/MV."
    elif "מתחיל" in experience_level:
        vol_chest = "10 - 12 סטים"
        vol_back = "10 - 14 סטים"
        vol_legs = "10 - 14 סטים"
        vol_shoulders = "6 - 10 סטים"
        vol_arms = "6 - 8 סטים (ישיר)"
        vol_note = "מתאמנים מתחילים מגיבים מעולה לנפח מתון סביב 10-12 סטים שבועיים לכל שריר גדול."
    else:
        vol_chest = "12 - 18 סטים"
        vol_back = "14 - 20 סטים"
        vol_legs = "14 - 20 סטים"
        vol_shoulders = "10 - 14 סטים"
        vol_arms = "8 - 12 סטים (ישיר)"
        vol_note = "נפח אופטימלי (MAV) להתקדמות מרבית, מחולק על פני 2-3 אימונים בשבוע."
        
    v_col1, v_col2, v_col3, v_col4, v_col5 = st.columns(5)
    v_col1.metric("חזה", vol_chest)
    v_col2.metric("גב", vol_back)
    v_col3.metric("רגליים", vol_legs)
    v_col4.metric("כתפיים", vol_shoulders)
    v_col5.metric("ידיים (ישיר)", vol_arms)
    st.caption(f"הנחיית נפח: {vol_note}")
    
    workout_notes = st.text_input(
        "דגשים מיוחדים לתוכנית (ציוד זמין, מגבלות תנועה, תרגילים מועדפים וכד'):",
        placeholder="למשל: חדר כושר מלא, ללא סקוואט חופשי עקב רגישות בגב, דגש על כתף צדית ויד קדמית"
    )
    
    def generate_workout_plan(days, goal, level, split_desc, user_age, is_adolescent, notes, target_cals):
        system_workout_prompt = """
אתה מאמן כושר בכיר ומומחה פיזיולוגיה מבוסס ראיות (Evidence-Based Strength & Hypertrophy Coach).
הפילוסופיה והמתודולוגיה שלך מושתתות על:
- אתר "קילוגרם" (Kilogrm) ומייק בייקוב (פרוגרסיב אוברלוד, תכנון תוכניות כוח והיפרטרופיה קלאסיות ומאוזנות)
- גיא שלמון (פיזיולוגיית המאמץ, פרופילי התנגדות, עקומת אורך-מתח ומניעת פציעות)
- אשד לין (עקרונות אימון והיפרטרופיה מבוססי מדע, ניהול עומסים והתאוששות)
- טל בן משה (בחירת תרגילים מותאמת ביומכנית, ניהול RIR ומתח מכני)
- קבוצת "EVB תזונה וכושר" (Evidence-Based)
- חוקרי מפתח עולמיים: Brad Schoenfeld, Eric Helms, Mike Israetel

כללי יסוד לבניית התוכנית:
1. התאמה לנוער (מתחת לגיל 18):
   - דגש קריטי על בטיחות, לימוד טכניקה מדויקת ושליטה מוטורית.
   - עבודה עם 2-3 RIR בתרגילים מורכבים (לא להגיע לכשל מוחלט בשום אופן).
   - שילוב תרגילים בטוחים ועקביים (משקולות יד, מכונות מודרכות, כבלים ומשקל גוף).
2. מבנה התוכנית:
   - חלק את התוכנית לימים ברורים (A, B, C...).
   - סדר תרגילים: תרגילים רב-מפרקיים מורכבים בראש האימון, תרגילי בידוד ומכונות בהמשך.
   - לכל תרגיל ציין: שם מדויק בעברית ובאנגלית, מספר סטים, טווח חזרות (למשל 6-8 לכוח, 8-12 להיפרטרופיה, 12-15 לבידוד), יעד RIR מדויק (Reps in Reserve), וזמן מנוחה בדקות.
3. ניהול התאוששות ופרוגרסיב אוברלוד:
   - הסבר קצר כיצד ליישם התקדמות עומסים משבוע לשבוע (הוספת חזרות/משקל).
   - המלצה על שבוע הפחתת עומס (Deload) לאחר 5-6 שבועות.
"""
        user_w_prompt = f"""
בנה תוכנית אימון מפורטת ומקצועית לפי המאפיינים הבאים:
- גיל המתאמן: {user_age} ({'נער/מתבגר - יש להדגיש בטיחות ו-RIR שמרני' if is_adolescent else 'בוגר'})
- ימי אימון בשבוע: {days}
- מטרת אימון מרכזית: {goal}
- רמת מתאמן: {level}
- מבנה פיצול מבוקש: {split_desc}
- סטטוס קלורי יומי: כ-{target_cals} קק"ל
- דגשים מיוחדים, אילוצים וציוד: {notes if notes else 'חדר כושר מאובזר סטנדרטי ללא מגבלות מיוחדות'}
"""
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_w_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_workout_prompt,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    safety_settings=[
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    ]
                )
            )
            return response.text if response.text else "לא נוצרה תוכנית אימון."
        except Exception as e:
            return f"אירעה שגיאה בבניית תוכנית האימון ({e}). אנא נסה שוב."

    if st.button("חולל תוכנית אימון מותאמת אישית", use_container_width=True):
        with st.spinner("בונה תוכנית אימון מבוססת ראיות ומחלקת עומסים..."):
            workout_output = generate_workout_plan(
                workout_days, training_goal, experience_level, suggested_split, age, is_teen, workout_notes, round(target_calories)
            )
            st.markdown(workout_output)

# ==========================================
# לשונית 3: יומן ומעקב שקילות ואימונים
# ==========================================
with tab_tracker:
    st.subheader("יומן מעקב שקילות ואימונים")
    st.caption("הקלדה ישירה ללא חיצים ומעקב שבועי על פי עקרונות המדידה והבקרה של קבוצת EVB, אתר קילוגרם (מייק בייקוב), גיא שלמון, אשד לין וטל בן משה")
    
    if "tracker_data" not in st.session_state:
        st.session_state.tracker_data = []
        
    with st.form("add_log_form", clear_on_submit=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            log_date = st.date_input("תאריך:", value=date.today())
        with f_col2:
            log_weight_input = st.text_input('משקל בוקר (ק"ג):', value=f"{user_weight:.1f}")
        with f_col3:
            log_calories_input = st.text_input("צריכה קלורית משוערת:", value=f"{round(target_calories)}")
        with f_col4:
            log_workout = st.text_input("אימון שבוצע / דגשים:", placeholder="למשל: אימון רגליים RIR 2, שתייה מספקת")
            
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
                'משקל (ק"ג)': parsed_weight,
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
# לשונית 4: צ'אט מחקרים וספרות
# ==========================================
with tab_chat:
    st.subheader("שאלות ותשובות מבוססות מחקרים ופיזיולוגיה")
    st.caption("מענה מבוסס מדרג הראיות המדעיות, מטא-אנליזות, ומתודולוגיות מנגישי הידע בישראל: קבוצת EVB תזונה וכושר, אתר קילוגרם (מייק בייקוב), גיא שלמון, אשד לין וטל בן משה")
    
    SYSTEM_INSTRUCTION = """
אתה מומחה בכיר ומנגיש ידע בתחומי תזונת הספורט, פיזיולוגיית המאמץ והמטבוליזם בגישת Evidence-Based.
בסיס הידע שלך מושתת על מדרג הראיות המדעיות (Evidence Hierarchy), תוך עדיפות למטא-אנליזות, סקירות שיטתיות ו-RCTs שפיטים, לצד המתודולוגיות של מנגישי הידע מבוססי הראיות בישראל:
- קבוצת הפייסבוק "EVB תזונה וכושר"
- אתר "קילוגרם" (Kilogrm), קבוצת הפייסבוק של מייק בייקוב והעמוד האישי שלו
- פורום הפייסבוק של גיא שלמון והעמוד המקצועי שלו
- אשד לין (התכנים והמאמרים המקצועיים בתזונת ספורט ואימונים מבוססי ראיות)
- העמוד האישי והתכנים המקצועיים של טל בן משה
- חוקרי מפתח בינלאומיים (Schoenfeld, Morton, Helms, Phillips, Aragon, ISSN, ACSM)

עקרונות המענה:
1. שלב תמיד בין תזונה לאימונים (מתח מכני, נפח שבועי, קלוריות, חלבון, מאזן נוזלים).
2. התאמת גיל: כאשר מתייחסים לבני נוער/מתבגרים (מתחת לגיל 18), הדגש צורכי גדילה, מניעת גירעון אנרגטי חריף, צריכת סידן/חלבון מספקת והקפדה על עבודה בטוחה עם RIR שמרני וללא כשל מוחלט.
3. ציטוט מחקרי מפתח: ציין שמות חוקרים ושנת פרסום (Morton et al. 2018, Schoenfeld et al. 2017, ניירות עמדה של ISSN ו-ACSM).
4. החרגה רפואית: המידע הינו לימודי בלבד ולא תחליף לייעוץ פרטני.
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
