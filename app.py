import os
from datetime import date
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="מערכת תזונה ואימונים מבוססת ראיות",
    layout="wide"
)

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
</style>
""", unsafe_allow_html=True)

api_key = (
    st.secrets.get("GEMINI_API_KEY")
    or st.secrets.get("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
)

if not api_key:
    st.error("שגיאה: מפתח API אינו מוגדר בהגדרות הסודיות (Secrets).")
    st.stop()

st.title("מערכת תזונה, כושר ומעקב מבוססת ראיות ומחקרים")

st.markdown("""
<div class="disclaimer-box">
    <strong>הבהרה משפטית ובריאותית חשובה (דין ישראלי):</strong><br>
    כלי זה מיועד למטרות לימודיות, מחקריות והעשרה בלבד, ואינו מהווה ייעוץ רפואי, אבחון קליני, תפריט תזונתי אישי לפי <em>חוק הסדרת העיסוק במקצועות הבריאות, התשס"ח-2008</em>, או מרשם אימון מוסמך. 
    אין בשימוש במערכת כדי ליצור יחסי מטפל-מטופל או מאמן-מתאמן. חל איסור להסתמך על הפלטים כתחליף לבדיקה והתאמה אישית אצל רופא מוסמך, דיאטן קליני בעל רישיון משרד הבריאות או מדריך כושר מוסמך. השימוש באפליקציה הוא על אחריותו הבלעדית של המשתמש.
</div>
""", unsafe_allow_html=True)

with st.expander("קרא את כתב הוויתור המשפטי, תנאי השימוש והסרת האחריות המלאים"):
    st.markdown("""
    1. **מטרת המערכת:** המערכת פועלת באמצעות בינה מלאכותית ונועדה להמחשת עקרונות תיאורטיים בלבד בספרות המחקרית ובשיטות המקובלות.
    2. **היעדר יחסי מטפל-מטופל:** השימוש במערכת אינו מהווה תחליף לטיפול תזונתי או הדרכת אימון אישית.
    3. **חובת בדיקה רפואית:** חובה להיוועץ ברופא, בדיאטן קליני מורשה ובמדריך מוסמך לפני כל שינוי בצריכת המזון, עומסי האימון או נטילת תוספים.
    4. **אוכלוסיות מיוחדות ונוער:** על מתאמנים צעירים (מתחת לגיל 18) לקבל ליווי והסכמת הורים/אנשי מקצוע. המערכת אינה מיועדת לנשים בהיריון/הנקה, או לאנשים עם מחלות רקע כרוניות והפרעות אכילה.
    5. **הסרת אחריות:** המפעיל אינו נושא בכל אחריות לנזק ישיר או עקיף שייגרם משימוש בחישובי המערכת או בתוכניות. השימוש הינו באחריות המשתמש בלבד.
    """)

tab_nutrition, tab_workout, tab_tracker, tab_chat = st.tabs([
    "מחשבון תזונה ותפריט לדוגמה",
    "מחולל תוכניות אימון חכם",
    "יומן ומעקב שקילות ואימונים",
    "צ'אט ייעוץ מבוסס ספרות ומומחים"
])

# ==========================================
# לשונית 1: מחשבון תזונה ותפריט לדוגמה
# ==========================================
with tab_nutrition:
    st.subheader("1. תכנון קלורי ומאקרו-נוטריאנטים אישי")
    st.caption("הזנה ישירה של נתונים במקלדת (ללא חיצים) - מותאם לנוער ומבוגרים")
    
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1:
        gender = st.selectbox("מין ביולוגי:", ["גבר", "אישה"])
    with col_in2:
        age_input = st.text_input("גיל (שנים):", value="17")
    with col_in3:
        weight_input = st.text_input("משקל (ק\"ג):", value="70.0")
    with col_in4:
        height_input = st.text_input("גובה (ס\"מ):", value="175")
        
    try:
        user_weight = float(weight_input.strip())
    except (ValueError, AttributeError):
        user_weight = 70.0
        
    try:
        user_height = float(height_input.strip())
    except (ValueError, AttributeError):
        user_height = 175.0
        
    try:
        age = int(age_input.strip())
    except (ValueError, AttributeError):
        age = 17
        
    col_in5, col_in6 = st.columns(2)
    with col_in5:
        activity = st.selectbox(
            "רמת פעילות שבועית:",
            [
                "יושבני (עבודה/לימודים בישיבה, ללא אימונים)",
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
                "שימור מסת שריר בחיטוב (גירעון מתון)",
                "שמירה על משקל קיים (מאזן ניטרלי)",
                "בניית מסת שריר מתונה / מסה נקייה (עודף מתון)",
                "עלייה במסה (עודף מוגבר)"
            ]
        )
        
    if gender == "גבר":
        bmr = (10 * user_weight) + (6.25 * user_height) - (5 * age) + 5
    else:
        bmr = (10 * user_weight) + (6.25 * user_height) - (5 * age) - 161
        
    activity_factors = {
        "יושבני (עבודה/לימודים בישיבה, ללא אימונים)": 1.2,
        "פעילות קלה (1-3 אימונים בשבוע)": 1.375,
        "פעילות בינונית (3-5 אימונים בשבוע)": 1.55,
        "פעילות גבוהה (6-7 אימונים עצימים בשבוע)": 1.725,
        "ספורטאי תחרותי / עבודה פיזית מאומצת": 1.9
    }
    tdee = bmr * activity_factors[activity]
    
    if age < 18:
        deficit_val = 250
        st.info("הערה מותאמת לגיל נוער: מומלץ להימנע מגירעונות קלוריים חריפים כדי לתמוך בצמיחה ובהתפתחות תקינה.")
    else:
        deficit_val = 400

    if "גירעון" in diet_goal:
        target_calories = tdee - deficit_val
        protein_per_kg = 2.0
    elif "עודף מתון" in diet_goal:
        target_calories = tdee + 250
        protein_per_kg = 1.8
    elif "עודף מוגבר" in diet_goal:
        target_calories = tdee + 450
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
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("סך קלוריות יעד", f"{round(target_calories)} קק\"ל")
    with m_col2:
        st.metric("חלבון יומי", f"{protein_g} גרם", f"{round(protein_kcal)} קלוריות")
    with m_col3:
        st.metric("שומן יומי", f"{fat_g} גרם", f"{round(fat_kcal)} קלוריות")
    with m_col4:
        st.metric("פחמימות יומיות", f"{carbs_g} גרם", f"{round(carbs_kcal)} קלוריות")
        
    st.markdown("---")
    st.subheader("2. מחולל שלד תפריט לדוגמה (3 עד 5 ארוחות)")
    st.caption("מבוסס על ערכי מאגר צמרת של משרד הבריאות, FoodsDictionary, USDA ועקרונות מבוססי ראיות")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        num_meals = st.selectbox("מספר ארוחות רצוי ביום:", ["3 ארוחות", "4 ארוחות", "5 ארוחות"], index=1)
    with col_m2:
        special_condition = st.text_input(
            "מגבלות, רגישויות או העדפות (אופציונלי):",
            placeholder="למשל: רגישות ללקטוז, כשר, צמחוני, טרום סוכרת"
        )
        
    def generate_menu_framework(cals, prot, fat, carbs, meals_count, condition, user_age):
        system_menu_prompt = f"""
אתה מומחה תזונה הפועל על פי גישה מבוססת ראיות (Evidence-Based Practice), בהשראת התכנים, הפוסטים והאתרים של:
- אשד לין (אתר, פוסטים ותכני אינסטגרם)
- קבוצת EVB תזונה וכושר בפייסבוק
- גיא שלמון (הפורום והעמוד הרשמי)
- טל בן משה (העמוד המקצועי)
- מייק בייקוב (אתר קילוגרם והקבוצה בפייסבוק)
בניית השלד נשענת על נתוני מאגר "צמרת" של משרד הבריאות הישראלי, FoodsDictionary ו-USDA.

הנחיות מחייבות:
1. גיל המתאמן: {user_age}. במידה והגיל מתחת ל-18, הקפד על אספקת סידן נאותה, צריכת אנרגיה שתומכת בהתפתחות וחלוקה מאוזנת.
2. כמויות ברורות: ציין גרמים מדויקים ומידות ביתיות לכל פריט (כפות, כוסות, יחידות).
3. חלוקה מבוססת מדע: פזר את החלבון באופן שווה בין הארוחות (סביב 25-40 גרם לארוחה).
4. גישה רגועה: אם צוינה רגישות או מצב בריאותי (כמו לקטוז, סוכרת, כשרות), הצג את ההתאמות כפשוטות ונגישות ללא דרמטיזציה.
5. הבהרה בסיום: ציין שמדובר בשלד לימודי להמחשה בלבד, המצריך בדיקה מול דיאטן קליני בעל רישיון.
"""
        user_prompt = f"""
בנה שלד תפריט לדוגמה:
- קלוריות: {cals} קק"ל
- חלבון: {prot} גרם | שומן: {fat} גרם | פחמימות: {carbs} גרם
- מספר ארוחות: {meals_count}
- דגשים מיוחדים / רגישויות: {condition if condition else 'ללא מגבלות'}
"""
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_menu_prompt,
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
        with st.spinner("מחשב ומחלק כמויות לפי מאגרי מזון אמינים ועקרונות מדעיים..."):
            menu_output = generate_menu_framework(
                round(target_calories), protein_g, fat_g, carbs_g, num_meals, special_condition, age
            )
            st.markdown(menu_output)

# ==========================================
# לשונית 2: מחולל תוכניות אימון חכם
# ==========================================
with tab_workout:
    st.subheader("מחולל תוכנית אימון מבוססת ראיות והתאמה אישית")
    st.caption("לוגיקת נפחים דינמית, נקודות חוזקה/חולשה, רמת מתאמן, וזמני מנוחה משתנים")

    w_col1, w_col2, w_col3 = st.columns(3)
    with w_col1:
        trainee_level = st.selectbox(
            "רמת המתאמן:",
            ["מתחיל (פחות משנה של אימון עקבי)", "בינוני (1-3 שנות אימון רציף)", "מתקדם (מעל 3 שנות אימון שיטתי)"]
        )
    with w_col2:
        weekly_days = st.selectbox(
            "מספר ימי אימון בשבוע:",
            ["2 ימים (Full Body)", "3 ימים (Full Body / Upper-Lower)", "4 ימים (Upper / Lower)", "5 ימים (Push / Pull / Legs / Upper / Lower)", "6 ימים (Push / Pull / Legs x2)"],
            index=2
        )
    with w_col3:
        session_time = st.text_input("זמן זמין לכל אימון (דקות):", value="60")

    w_col4, w_col5 = st.columns(2)
    with w_col4:
        weak_points = st.text_input("נקודות חולשה / שרירים שרוצים לתעדף:", placeholder="למשל: דלתואיד צידי, ישבן, חזה עליון")
    with w_col5:
        strong_points = st.text_input("נקודות חוזקה / שרירים מפותחים (נפח תחזוקה):", placeholder="למשל: רגליים דומיננטיות, יד קדמית")

    w_col6, w_col7 = st.columns(2)
    with w_col6:
        injuries = st.text_input("פציעות, כאבים או מגבלות תנועה:", placeholder="למשל: רגישות בכתף בלחיצות מעל הראש, כאב ברך בסקוואט עמוק")
    with w_col7:
        preferences = st.text_input("העדפות תרגילים ופונקציונליות יומיומית:", placeholder="למשל: העדפה למשקולות חופשיות / תנועות משיכה לסחיבת קניות")

    def generate_workout_program(level, days, time_limit, weak, strong, inj, pref, user_age):
        system_workout_prompt = f"""
אתה מאמן כושר ופיזיולוג מאמץ מבוסס ראיות (Evidence-Based Coach), הפועל ברוח התכנים המדעיים וההדרכות של:
- אשד לין (אתר ותכני אינסטגרם מקצועיים)
- קהילת EVB תזונה וכושר
- גיא שלמון (פורום ועמוד פייסבוק)
- טל בן משה
- מייק בייקוב (אתר קילוגרם וקבוצת הפייסבוק)
לצד הספרות והמטא-אנליזות של Brad Schoenfeld, Eric Helms ו-Mike Israetel.

הנחיות לבניית התוכנית:
1. התאמה לרמת המתאמן ({level}):
   - מתחיל: פשטות, תרגילים רב-מפרקיים מרכזיים, נפח של 8-12 סטים שבועיים לשריר, RIR 2-3 לבקרת טכניקה.
   - בינוני: 12-16 סטים שבועיים, פיצול אופטימלי, עבודה ב-RIR 1-2.
   - מתקדם: 16-20+ סטים לשרירי מטרה, RIR 0-2, מחזורי עומס.
2. גיל המתאמן ({user_age}):
   - אם המתאמן מתחת לגיל 18: דגש על שליטה תנועתית, הימנעות מכשל שרירי מוחלט, ובניית בסיס אתלטי בטוח.
3. חלוקת נפח וחוזקות/חולשות:
   - חולשות ({weak}): עדיפות בתחילת האימון ונפח מוגבר (תוספת 2-4 סטים שבועיים).
   - חוזקות ({strong}): נפח תחזוקה מתון למניעת עייפות מיותרת.
4. מגבלות ופציעות ({inj}):
   - שלול תרגילים מעוררי כאב והצע חלופות ביומכניות בטוחות.
5. זמני מנוחה דינמיים ובקרת עומסים:
   - תרגילים מורכבים כבדים (סקוואט, דדליפט, לחיצות): 2.5-3.5 דקות מנוחה.
   - תרגילי בידוד ומכונות: 1.5-2 דקות.
   - התחשבות במספר החזרות בסט הקודם ובקרבה לכשל: אם הסט הקודם הגיע ל-RIR נמוך מ-1, יש להאריך את המנוחה בהתאם.
   - התאמה למגבלת הזמן ({time_limit} דקות): אם הזמן קצר, שקול Superset של קבוצות שריר אנטגוניסטיות.
6. מבנה הפלט:
   - פירוט מלא של ימי האימון (תרגיל, סטים, טווח חזרות, יעד RIR, וזמן מנוחה מומלץ).
   - הסבר קצר על ההיגיון בחלוקת הנפח.
   - תזכורת להתקדמות הדרגתית בעומסים (Progressive Overload) ושבוע דילואד (Deload) לפי הצורך.
"""
        user_prompt = f"""
בנה תוכנית אימונים מותאמת אישית:
- רמה: {level}
- ימי אימון: {days}
- זמן זמין לאימון: {time_limit} דקות
- שרירים לתעדוף (חולשה): {weak if weak else 'חלוקה מאוזנת'}
- שרירים דומיננטיים (חוזקה): {strong if strong else 'חלוקה מאוזנת'}
- פציעות/מגבלות: {inj if inj else 'ללא כאבים או פציעות'}
- העדפות תרגילים/פונקציונליות: {pref if pref else 'תרגילים קלאסיים'}
"""
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_workout_prompt,
                    safety_settings=[
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    ]
                )
            )
            return response.text if response.text else "לא נוצרה תוכנית."
        except Exception as e:
            return f"אירעה שגיאה בבניית תוכנית האימונים ({e}). אנא נסה שוב."

    if st.button("בנה תוכנית אימונים מותאמת אישית", use_container_width=True):
        with st.spinner("מנתח נפחים שבועיים, מגבלות תנועה ופיזיולוגיית מאמץ..."):
            workout_output = generate_workout_program(
                trainee_level, weekly_days, session_time, weak_points, strong_points, injuries, preferences, age
            )
            st.markdown(workout_output)

# ==========================================
# לשונית 3: יומן מעקב ושקילות
# ==========================================
with tab_tracker:
    st.subheader("יומן מעקב שקילות ואימונים")
    st.caption("הקלדה ישירה ללא חיצים ומעקב אחר מגמת ההתקדמות")
    
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
            log_workout = st.text_input("אימון שבוצע / דגשים:", placeholder="למשל: עליון A, חזה RIR 1, סקוואט הרגיש קל")
            
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
# לשונית 4: צ'אט מחקרים ומומחים
# ==========================================
with tab_chat:
    st.subheader("שאלות ותשובות מבוססות מחקרים ומומחי הקהילה")
    st.caption("מנוע מבוסס ראיות בהשראת אשד לין (אתר ואינסטגרם), EVB, גיא שלמון, טל בן משה, מייק בייקוב (קילוגרם), ISSN ו-PubMed")
    
    SYSTEM_INSTRUCTION = """
אתה מומחה בכיר בתחומי תזונת הספורט, פיזיולוגיית המאמץ והאימונים.
בסיס הידע שלך מושתת על מדרג הראיות המדעיות (Evidence Hierarchy), תוך עדיפות למטא-אנליזות, סקירות שיטתיות וניסויים קליניים (RCTs), לצד הגישה המדעית המונגשת בקהילות המובילות בישראל:
- אשד לין (האתר ותכני האינסטגרם המקצועיים)
- קבוצת EVB תזונה וכושר בפייסבוק
- הפורום והתכנים של גיא שלמון
- התכנים המקצועיים של טל בן משה
- אתר קילוגרם (Kilogrm) והקבוצה/עמוד של מייק בייקוב

עקרונות מענה:
1. שילוב בין תזונה לאימונים: הסבר מנגנונים (מתח מכני, סטים אפקטיביים, RIR/RPE, מאזן אנרגטי, חלבון יומי, מנוחה והתאוששות).
2. ניתוח מבוסס מחקר: ציין שמות חוקרים וניירות עמדה רלוונטיים (Morton, Schoenfeld, Aragon, Helms, ISSN, ACSM).
3. החרגה רפואית: המידע הינו לימודי בלבד ואינו תחליף לייעוץ פרטני אצל דיאטן קליני מורשה או רופא.
"""

    def generate_ai_reply(prompt_text: str):
        try:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
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
            return response.text if response.text else "לא התקבלה תשובה מהמודל."
        except Exception as e:
            return f"אירעה שגיאה בעיבוד הנתונים ({e}). אנא נסה שוב מאוחר יותר."

    if "chat_history_v3" not in st.session_state:
        st.session_state.chat_history_v3 = []

    for msg in st.session_state.chat_history_v3:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    chat_query = st.chat_input("שאל/י על אימונים, תזונת ספורט, קריאטין, עומסים ומחקרים...")
    if chat_query:
        st.session_state.chat_history_v3.append({"role": "user", "content": chat_query})
        with st.chat_message("user"):
            st.markdown(chat_query)
            
        with st.chat_message("assistant"):
            with st.spinner("סורק ספרות מחקרית ומנתח נתונים..."):
                reply_out = generate_ai_reply(chat_query)
                st.markdown(reply_out)
                        
        st.session_state.chat_history_v3.append({"role": "assistant", "content": reply_out})
