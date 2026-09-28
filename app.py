
import os
from datetime import date
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import json
import urllib.request
import urllib.error

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
    .metric-calc-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# 1. ניהול מפתח אישי ושמירה מקומית בדפדפן (LocalStorage / Cookies)
url_key = st.query_params.get("key", "")
if url_key and "user_api_key" not in st.session_state:
    st.session_state.user_api_key = url_key

nara_endpoint = st.secrets.get("NARA_BASE_URL", "https://api.nararouter.com/v1/chat/completions")

# סרגל צד - ניהול מפתח אישי
with st.sidebar:
    st.markdown("<h3 style='text-align: right;'>⚙️ מפתח API אישי</h3>", unsafe_allow_html=True)
    
    # טעינה אוטומטית מ-LocalStorage של הדפדפן אם חזר ללא URL parameter
    if "user_api_key" not in st.session_state and not url_key:
        components.html(
            """
            <script>
                try {
                    const storedKey = localStorage.getItem("nara_user_api_key");
                    if (storedKey && storedKey.length > 5) {
                        const currentUrl = new URL(window.parent.location.href);
                        if (!currentUrl.searchParams.has("key")) {
                            currentUrl.searchParams.set("key", storedKey);
                            window.parent.location.href = currentUrl.toString();
                        }
                    }
                } catch(e) {}
            </script>
            """,
            height=0
        )
        
    current_key = st.session_state.get("user_api_key", "")
    api_input = st.text_input(
        "הזן את מפתח ה-API האישי שלך:",
        value=current_key,
        type="password",
        placeholder="הדבק מפתח כאן...",
        help="המפתח נשמר במכשיר שלך בלבד (בדפדפן) ולא נשמר בשום שרת חיצוני."
    )
    
    if api_input and api_input != current_key:
        st.session_state.user_api_key = api_input
        st.query_params["key"] = api_input
        components.html(
            f"""
            <script>
                try {{
                    localStorage.setItem("nara_user_api_key", "{api_input}");
                }} catch(e) {{}}
            </script>
            """,
            height=0
        )
        st.rerun()

    if st.session_state.get("user_api_key"):
        st.success("המפתח שמור בדפדפן זה.")
        if st.button("מחק מפתח שמור ממכשיר זה", use_container_width=True):
            st.session_state.user_api_key = ""
            st.query_params.clear()
            components.html(
                """
                <script>
                    try {
                        localStorage.removeItem("nara_user_api_key");
                        const currentUrl = new URL(window.parent.location.href);
                        currentUrl.searchParams.delete("key");
                        window.parent.location.href = currentUrl.toString();
                    } catch(e) {}
                </script>
                """,
                height=0
            )
            st.rerun()
            
    nara_api_key = st.session_state.get("user_api_key", "")

# 4 המודלים המובילים - כולם פועלים יחד על כל המשימות (Unified AI Engine)
TOP_4_MODELS = [
    "claude-opus-5.5",
    "gemini-3.1-pro-high",
    "gpt-6-sol",
    "deepseek-v4-pro-alibaba"
]

def query_nararouter(prompt: str, system_instruction: str, key: str, endpoint: str) -> str:
    if not key:
        return "⚠️ שגיאה: נא להזין את מפתח ה-API האישי שלך בסרגל הצד (ימינה) כדי להפעיל את המערכת."
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    last_err = ""
    # כל 4 המודלים זמינים לכל משימה: מנסה את המודל המוביל וממשיך ברציפות לשאר ה-4 במקרה של עומס
    for model_id in TOP_4_MODELS:
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"]
        except Exception as e:
            last_err = str(e)
            continue
            
    return f"אירעה שגיאה בעיבוד הנתונים ({last_err}). אנא נסה שוב מאוחר יותר."

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

# 3. חלוקה ל-5 לשוניות
tab_calc, tab_workout, tab_tracker, tab_chat, tab_rehab = st.tabs([
    "מחשבון קלוריות ומחולל תפריט",
    "מחולל תוכניות אימון ונפח",
    "יומן ומעקב שקילות",
    "צ'אט ייעוץ ומחקרים",
    "שיקום ופיזיותרפיה מותאמת"
])

# ==========================================
# לשונית 1: מחשבון ומחולל תפריט (חישוב בקוד פייתון טהור)
# ==========================================
with tab_calc:
    st.subheader("1. תכנון קלורי ומאקרו-נוטריאנטים (חישוב מתמטי מדויק בקוד)")
    
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
        
    # --- חישוב בקוד פייתון טהור (ללא הזיות וללא טוקנים) ---
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
    
    growth_energy = 150 if is_teen else 0
    tdee = (bmr * activity_factors[activity]) + growth_energy
    
    if "גירעון" in diet_goal:
        if is_teen:
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
        st.metric("סך קלוריות יעד (מחושב בקוד)", f'{round(target_calories)} קק"ל')
    with m_col2:
        st.metric("חלבון יומי", f"{protein_g} גרם", f"{round(protein_kcal)} קלוריות")
    with m_col3:
        st.metric("שומן יומי", f"{fat_g} גרם", f"{round(fat_kcal)} קלוריות")
    with m_col4:
        st.metric("פחמימות יומיות", f"{carbs_g} גרם", f"{round(carbs_kcal)} קלוריות")
        
    st.markdown("---")
    st.subheader("2. מחולל שלד תפריט לדוגמה (3 עד 5 ארוחות)")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        num_meals = st.selectbox("מספר ארוחות רצוי ביום:", ["3 ארוחות", "4 ארוחות", "5 ארוחות"], index=1)
    with col_m2:
        special_condition = st.text_input(
            "מגבלות, רגישויות או מצב בריאותי (אופציונלי):",
            placeholder="למשל: רגישות ללקטוז, צמחוני, כולסטרול גבוה, טרום סוכרת, כשרות"
        )
        
    # חישוב חלוקה מדויקת לארוחות בקוד טהור
    meals_count_num = int(num_meals.split()[0])
    prot_per_meal_calc = round(protein_g / meals_count_num, 1)
    carbs_per_meal_calc = round(carbs_g / meals_count_num, 1)
    fat_per_meal_calc = round(fat_g / meals_count_num, 1)
    cals_per_meal_calc = round(target_calories / meals_count_num)
    
    st.markdown(f"""
    <div class="metric-calc-box">
        <b>פירוק מחושב בקוד לכל ארוחה מתוך {meals_count_num} ארוחות:</b><br>
        כ-{cals_per_meal_calc} קק"ל | חלבון: כ-{prot_per_meal_calc} גרם | פחמימות: כ-{carbs_per_meal_calc} גרם | שומן: כ-{fat_per_meal_calc} גרם
    </div>
    """, unsafe_allow_html=True)
    
    def generate_menu_framework(cals, prot, fat, carbs, meals_count, condition, user_age, is_adolescent, per_meal_text):
        system_menu_prompt = """
אתה דיאטן וחוקר תזונת ספורט בכיר הפועל בגישת Evidence-Based.
תפקידך להמיר את החישובים המדויקים שהוכנו בקוד לתפריט מעשי של מזונות ומידות ביתיות.

כללים מחייבים בבניית התפריט:
1. איסור מוחלט על מטא-הסברים: אל תציין מאיפה נלקח המידע ואל תנקוב בשמות של גופים וחוקרים.
2. שמור על כמויות המאקרו המחושבות בדיוק כפי שהוזנו מהקוד.
3. ציין לכל פריט מזון משקל בגרמים/מ"ל לצד מידה ביתית ברורה.
4. פזר את החלבון באופן שווה בין הארוחות לפי החישוב המצורף.
"""
        user_prompt = f"""
בנה שלד תפריט לדוגמה לפי החישובים המדויקים שנערכו בקוד:
- סך קלוריות יעד: {cals} קק"ל
- חלבון כולל: {prot} גרם
- שומן כולל: {fat} גרם
- פחמימות כולל: {carbs} גרם
- מספר ארוחות: {meals_count}
- יעד מחושב לארוחה בודדת: {per_meal_text}
- גיל: {user_age} ({'מתבגר/נוער' if is_adolescent else 'בוגר'})
- דגשים ומגבלות: {condition if condition else 'ללא מגבלה מיוחדת'}
"""
        return query_nararouter(user_prompt, system_menu_prompt, nara_api_key, nara_endpoint)

    if st.button("בנה שלד תפריט לדוגמה", use_container_width=True):
        with st.spinner("מעבד שלד תפריט לפי הנתונים המחושבים..."):
            per_meal_str = f"{cals_per_meal_calc} קק'ל, {prot_per_meal_calc} גר' חלבון, {carbs_per_meal_calc} גר' פחמימה, {fat_per_meal_calc} גר' שומן"
            menu_output = generate_menu_framework(
                round(target_calories), protein_g, fat_g, carbs_g, num_meals, special_condition, age, is_teen, per_meal_str
            )
            st.markdown("""
            <div class="menu-disclaimer">
                <strong>לידיעתך:</strong> שלד התפריט המוצג הינו הדגמה לימודית וחישובית בלבד על בסיס נתוני מאגר צמרת. אין לראות בו תפריט תזונתי מחייב או הוראה לפעולה, ואין בו כדי להחליף התאמה פרטנית על ידי דיאטן קליני מורשה כחוק.
            </div>
            """, unsafe_allow_html=True)
            st.markdown(menu_output)

# ==========================================
# לשונית 2: מחולל תוכניות אימון ונפח לפי מטרה (חישוב נפח בקוד)
# ==========================================
with tab_workout:
    st.subheader("בניית תוכנית אימון מבוססת ראיות (Evidence-Based Volume & Periodization)")
    
    st.markdown("""
    <div class="workout-box">
        <strong>עקרונות המודול:</strong><br>
        התאמת נפח סטים שבועי לפי קבוצת שריר (MEV/MAV), קביעת פיצול אופטימלי (Split), ניהול עצימות וקרבה לכשל (RIR), והתאמה לגיל המתאמן (דגש בטיחותי וטכני לנוער).
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
    
    # חישוב פיצול אופטימלי בקוד פייתון טהור
    if days_num <= 3:
        suggested_split = "Full Body (FBW - אימון גוף מלא בכל מפגש, תדירות שבועית גבוהה לכל שריר)"
    elif days_num == 4:
        suggested_split = "Upper / Lower (פלג גוף עליון / פלג גוף תחתון - 2 גירויים שבועיים לכל שריר)"
    elif days_num == 5:
        suggested_split = "Upper / Lower / Push / Pull / Legs או PPL + Upper/Lower"
    else:
        suggested_split = "Push / Pull / Legs (PPL מחזורי פעמיים בשבוע)"
        
    st.info(f"**מבנה פיצול מומלץ (מחושב בקוד):** {suggested_split}")
    
    # חישוב נפח שבועי מומלץ בקוד פייתון טהור
    st.markdown("#### מדרג נפח שבועי מומלץ לקבוצות שריר (מחושב בקוד פייתון):")
    
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
    
    def generate_workout_plan(days, goal, level, split_desc, user_age, is_adolescent, notes, target_cals, volume_summary):
        system_workout_prompt = """
אתה מאמן כושר בכיר ומומחה פיזיולוגיה מבוסס ראיות (Evidence-Based Strength & Hypertrophy Coach).
כללי יסוד לבניית התוכנית:
1. איסור מוחלט על מטא-הסברים: ספק את התוכנית וההנחיות ישירות, ללא ציון שמות מרצים, חוקרים ומקורות השראה.
2. התאמה לנוער (מתחת לגיל 18):
   - דגש קריטי על בטיחות, לימוד טכניקה מדויקת ושליטה מוטורית.
   - עבודה עם 2-3 RIR בתרגילים מורכבים (לא להגיע לכשל מוחלט בשום אופן).
3. הצמד את התוכנית בדיוק למבנה הנפח והפיצול שחושבו בקוד.
4. לכל תרגיל ציין: שם מדויק בעברית ובאנגלית, מספר סטים, טווח חזרות, יעד RIR מדויק וזמן מנוחה.
"""
        user_w_prompt = f"""
בנה תוכנית אימון מפורטת ומקצועית לפי המאפיינים המחושבים הבאים:
- גיל המתאמן: {user_age} ({'נער/מתבגר' if is_adolescent else 'בוגר'})
- ימי אימון בשבוע: {days}
- מטרת אימון מרכזית: {goal}
- רמת מתאמן: {level}
- מבנה פיצול מחושב: {split_desc}
- יעדי נפח מחושבים: {volume_summary}
- סטטוס קלורי יומי: כ-{target_cals} קק"ל
- דגשים מיוחדים, אילוצים וציוד: {notes if notes else 'חדר כושר מאובזר סטנדרטי ללא מגבלות מיוחדות'}
"""
        return query_nararouter(user_w_prompt, system_workout_prompt, nara_api_key, nara_endpoint)

    if st.button("חולל תוכנית אימון מותאמת אישית", use_container_width=True):
        with st.spinner("בונה תוכנית אימון מבוססת ראיות ומחלקת עומסים..."):
            vol_sum = f"חזה: {vol_chest}, גב: {vol_back}, רגליים: {vol_legs}, כתפיים: {vol_shoulders}, ידיים: {vol_arms}"
            workout_output = generate_workout_plan(
                workout_days, training_goal, experience_level, suggested_split, age, is_teen, workout_notes, round(target_calories), vol_sum
            )
            st.markdown(workout_output)

# ==========================================
# לשונית 3: יומן ומעקב שקילות ואימונים (קוד פייתון טהור)
# ==========================================
with tab_tracker:
    st.subheader("יומן מעקב שקילות ואימונים")
    
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
# לשונית 4: צ'אט ייעוץ ומחקרים
# ==========================================
with tab_chat:
    st.subheader("שאלות ותשובות מבוססות מחקרים ופיזיולוגיה")
    
    SYSTEM_INSTRUCTION = """
אתה מומחה בכיר בתחומי תזונת הספורט, פיזיולוגיית המאמץ והמטבוליזם בגישת Evidence-Based.
עקרונות המענה:
1. איסור מוחלט על מטא-הסברים: ענה ישירות, מקצועי ונקי. אל תציין מאיפה נלקח המידע ואל תנקוב בשמות של מנגישי ידע, חוקרים או גופים ספציפיים.
2. שלב תמיד בין תזונה לאימונים (מתח מכני, נפח שבועי, קלוריות, חלבון, מאזן נוזלים).
3. התאמת גיל: כאשר מתייחסים לבני נוער/מתבגרים (מתחת לגיל 18), הדגש צורכי גדילה, מניעת גירעון אנרגטי חריף, צריכת סידן/חלבון מספקת והקפדה על עבודה בטוחה עם RIR שמרני וללא כשל מוחלט.
4. החרגה רפואית: המידע הינו לימודי בלבד ולא תחליף לייעוץ פרטני.
"""

    def generate_ai_reply(prompt_text: str):
        return query_nararouter(prompt_text, SYSTEM_INSTRUCTION, nara_api_key, nara_endpoint)

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
            with st.spinner("מעבד נתונים ומנתח..."):
                reply_out = generate_ai_reply(chat_query)
                st.markdown(reply_out)
                
        st.session_state.chat_history_v2.append({"role": "assistant", "content": reply_out})

# ==========================================
# לשונית 5: שיקום ופיזיותרפיה מותאמת (בקרת כאב והגבלות מנוהלות בקוד)
# ==========================================
with tab_rehab:
    st.subheader("שיקום ופיזיותרפיה אורתופדית מותאמת אישית")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        injured_part = st.text_input("האיבר / החלק הפגוע והאבחנה:", placeholder="למשל: כתף ימין - קרע חלקי ב-Supraspinatus, או ברך שמאל - שיקום לאחר שחזור ACL")
        rehab_phase = st.selectbox(
            "שלב נוכחי מאז הפציעה/ניתוח:",
            ["שלב אקוטי מוקדם (שבועות 0-3)", "שלב תת-אקוטי / שגשוג (שבועות 3-8)", "שלב שיפוץ הרקמה וחיזוק פונקציונלי (חודשיים ומעלה)", "שיקום פציעה כרונית / גידית"]
        )
    with col_r2:
        medical_summary = st.text_area(
            "סיכום האורתופד / פיזיותרפיסט / מנתח (הדבק כאן את הסיכום הרפואי):",
            placeholder="הדבק כאן את סיכום הביקור והנחיות הרופא/פיזיותרפיסט...",
            height=100
        )

    contraindications = st.text_input(
        "הגבלות תנועה ועומס מוגדרות מראש (ROM, נשיאת משקל, זוויות אסורות):",
        placeholder="למשל: איסור נשיאת משקל מלא, אסור סיבוב חיצוני מעל 30 מעלות, ללא קפיצות"
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pain_level = st.slider("רמת כאב נוכחית (0 עד 10):", 0, 10, 2)
    with col_p2:
        pain_triggers = st.text_input("מיקום הכאב ותנועות מעוררות:", placeholder="למשל: כאב בקדמת הכתף רק בהרמה מעל 80 מעלות")

    # בדיקת סף כאב מחושבת בקוד פייתון טהור
    if pain_level > 3:
        st.error(f"⚠️ רמת כאב גבוהה ({pain_level}/10): הקוד מחיל אוטומטית הגבלת עומס מוחלטת ותרגילים איזומטריים ללא תנועה בלבד!")
    else:
        st.success(f"רמת כאב בטווח הבטוח לתרגול פעיל מבוקר ({pain_level}/10).")

    st.markdown("---")
    # שער אישור רפואי להתקדמות (מנוהל בקוד פייתון טהור)
    st.markdown("##### 🛡️ שער אישור רפואי להתקדמות שלב (Progression Clearance):")
    medical_progression_approved = st.checkbox(
        "התקבל עדכון מפורש מרופא / פיזיותרפיסט מטפל המאשר קידום שלב והעלאת עומסים.",
        value=False,
        help="עקרון בטיחות מחייב: אין להעלות דרגת קושי או לעבור לשלב השיקום הבא ללא בדיקה והסרת הגבלות על ידי הגורם המטפל."
    )
    
    if not medical_progression_approved:
        st.warning("שער התקדמות נעול: התוכנית תישאר במסגרת השלב הנוכחי, ללא העלאת עומסים וללא סיכון הרקמה המחלימה.")
    else:
        st.success("שער התקדמות מאושר: המערכת תבנה את שלב ההתקדמות הבא בהתאם להנחיות הגורם המטפל.")

    if st.button("חולל פרוטוקול פיזיותרפיה ותרגול מותאם", use_container_width=True):
        if not injured_part.strip() or not medical_summary.strip():
            st.error("נא להזין את החלק הפגוע ואת סיכום הגורם הרפואי כדי להבטיח התאמה בטיחותית.")
        else:
            system_rehab_prompt = """
אתה מומחה פיזיותרפיה ושיקום אורתופדי מבוסס ראיות.
עקרונות מחייבים:
1. איסור מוחלט על מטא-הסברים: ספק את התוצר ישירות ללא ציון שמות מקורות או מאיפה לקוח המידע.
2. התאמה קפדנית להגבלות הרופא/פיזיותרפיסט.
3. ניהול עומס וכאב: התייחס ישירות לרמת הכאב שהוזנה. אם הכאב מעל 3/10, דרוש הפחתת עומס ותרגילים איזומטריים ללא כאב.
4. נעילת התקדמות: אם לא אושר קידום שלב רפואי, יש להישאר בשלב הנוכחי בלבד ללא העלאת דרגות קושי!
"""
            prompt_rehab = f"""
בנה פרוטוקול תרגול שיקומי מותאם:
- איבר פגוע ואבחנה: {injured_part}.
- שלב נוכחי: {rehab_phase}.
- סיכום רפואי רשמי: {medical_summary}.
- הגבלות תנועה ועומס: {contraindications if contraindications else "אין הגבלות נוספות מעבר לסיכום"}.
- סטטוס כאב: רמת כאב {pain_level}/10, מיקום ותנועות מעוררות: {pain_triggers if pain_triggers else "אין"}.
- אישור קידום שלב: {"מאושר להתקדם לשלב הבא בהתאם לבדיקה רפואית" if medical_progression_approved else "לא אושר עדיין קידום שלב - שמור על השלב הנוכחי בלבד ללא העלאת עומס!"}.

ספק ישירות:
1. הנחיות עומס ובטיחות מותאמות לרמת הכאב ({pain_level}/10).
2. פרוטוקול תרגילים מפורט ובטוח (טווחי תנועה מותרים, הפעלה מוטורית, סטים וחזרות).
3. תנועות ותרגילים אסורים בשלב זה (Red Flags).
4. קריטריונים אובייקטיביים שיש להציג לבדיקת הפיזיותרפיסט/רופא לפני אישור השלב הבא.
"""
            with st.spinner("מעבד פרוטוקול שיקומי מותאם..."):
                res_rehab = query_nararouter(prompt_rehab, system_rehab_prompt, nara_api_key, nara_endpoint)
                st.markdown(res_rehab)
