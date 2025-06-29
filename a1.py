import streamlit as st
import pandas as pd
import time
from pathlib import Path
import streamlit.components.v1 as components
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import base64

# ───────── הגדרות בסיס + CSS ─────────
st.set_page_config(page_title="צמרובוט – העוזר האישי שלי", layout="centered")

# CSS מפוצל למקטעים
st.markdown("""
<style>
/* עיצוב כללי משופר */
.stApp {
    background-color: #f8f9fa;
}
.main-header { 
    display: flex; 
    flex-direction: column; 
    align-items: center; 
    text-align: center; 
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
}
.main-header img { 
    width: 90px !important; 
    margin-bottom: 0.8rem;
    filter: drop-shadow(0 5px 15px rgba(0,0,0,0.2));
}
.main-header h3 { 
    font-size: 2rem; 
    font-weight: 800; 
    text-align: center; 
    width: 100%;
    color: white;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}
/* הסתרת אלמנטים ריקים - משופר */
.element-container:has(> div:empty) {
    display: none !important;
}
.element-container:has(> .stMarkdown:empty) {
    display: none !important;
}
div[data-testid="column"]:empty {
    display: none !important;
}
/* תיקון ליישור אלמנטים */
div[data-testid="column"] > div {
    width: 100%;
}
/* תיקון גלילה ב-selectbox במובייל */
.stSelectbox select {
    -webkit-overflow-scrolling: touch !important;
    overflow-y: auto !important;
}
/* במובייל - הגדלת גובה הרשימה */
@media (max-width: 768px) {
    .stSelectbox select {
        max-height: 300px !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* עיצוב הצ'אט */
.chat-msg { 
    background: white;
    border-radius: 18px;
    padding: 1rem 1.4rem;
    margin: 0.5rem 0;
    color: #2d3436;
    direction: rtl;
    text-align: right;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    animation: fadeIn 0.3s ease-in;
    line-height: 1.6;
}
.chat-user {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    margin-left: 2rem;
}
.chat-msg:not(.chat-user) {
    margin-right: 2rem;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* עיצוב הטאבים */
div[data-testid="stRadio"] > div { 
    flex-direction: row-reverse; 
    justify-content: center;
    gap: 1rem;
}
div[data-testid="stRadio"] label { 
    margin: 0 !important;
    padding: 0.8rem 2rem !important;
    background: white;
    border-radius: 25px;
    border: 2px solid #e0e0e0;
    transition: all 0.3s ease;
    font-weight: 600;
}
div[data-testid="stRadio"] label:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
}
div[data-testid="stRadio"] label[data-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-color: #667eea;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* עיצוב משופר לבחירת השעות */
.hours-selection-container {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    margin: 1rem 0;
}
/* עיצוב ה-checkbox */
div[data-testid="stCheckbox"] {
    margin: 0.5rem 0;
}
div[data-testid="stCheckbox"] label {
    font-weight: 600;
    font-size: 1.1rem;
}
/* רשת שעות - התאמה למובייל */
@media (max-width: 768px) {
    /* הסתרת העמודה השלישית במובייל */
    .hours-selection-grid > div[data-testid="column"]:nth-child(3) {
        display: none !important;
    }
    /* הגדלת העמודות הנותרות */
    .hours-selection-grid > div[data-testid="column"] {
        flex: 1 1 50% !important;
        max-width: 50% !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* עיצוב כפתורים */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.75rem 2rem;
    border-radius: 25px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}
/* עיצוב תיבות בחירה וטקסט */
.stSelectbox > div > div {
    background: white;
    border-radius: 12px;
    border: 2px solid #e8eaed;
    padding: 0.5rem;
}
.stTextInput > div > div {
    background: white;
    border-radius: 12px;
    border: 2px solid #e8eaed;
}
.stTextInput > div > div:focus-within {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
/* עיצוב רשימת מורים */
.teacher-list-container {
    background: white;
    border-radius: 15px;
    padding: 1rem;
    box-shadow: 0 3px 15px rgba(0,0,0,0.08);
}
.teacher-list-container .stButton > button {
    background: white;
    color: #2d3436;
    border: 2px solid #e8eaed;
    margin: 0.3rem 0;
    box-shadow: none;
}
.teacher-list-container .stButton > button:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-color: #667eea;
}
/* תיקון לגלילה במובייל */
div[data-testid="stVerticalBlock"] > div:has(> div > .teacher-list-container) {
    overflow-y: auto !important;
    -webkit-overflow-scrolling: touch !important;
    max-height: 300px !important;
}
/* עיצוב לנייד */
@media (max-width: 768px) {
    .chat-msg:not(.chat-user) {
        margin-right: 1rem;
    }
    .chat-user {
        margin-left: 1rem;
    }
    .main-header h3 {
        font-size: 1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ───────── אייקון וכותרת ─────────
def get_image_as_base64(path):
    if not Path(path).exists(): return None
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

img_base64 = get_image_as_base64("bot_calendar.png")
if img_base64:
    st.markdown(f"""
    <div class="main-header">
        <img src="data:image/png;base64,{img_base64}" alt="Bot Icon">
        <h3>צמרובוט – העוזר האישי שלי</h3>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown('<div class="main-header"><h3>🤖 צמרובוט – העוזר האישי שלי</h3></div>', unsafe_allow_html=True)

# ───────── נתונים וקבועים ─────────
DAYS=['יום א','יום ב','יום ג','יום ד','יום ה','יום ו']
DAY_OFF='יום חופשי'
AVAILABLE_KEYWORDS = ["שהייה", "פרטני", "תגבור", "הדרכה", "מצטיינים", "שילוב"]
PRIORITY = {key: i for i, key in enumerate(AVAILABLE_KEYWORDS)}

@st.cache_data(ttl=600, show_spinner="טוען מערכת שעות עדכנית...")
def load_data_from_gsheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("מורים")
        worksheet = spreadsheet.worksheet("גיליון1")
        data = worksheet.get_all_values()
    except Exception as e:
        st.error(f"שגיאה בהתחברות לגוגל שיטס: {e}. ודא שהשמות נכונים ושיתפת את הקובץ.")
        return pd.DataFrame()

    all_records = []
    current_teacher = None
    header_map = {}

    for row in data:
        if not any(cell.strip() for cell in row): continue
        if "מערכת שעות למורה" in row[0]:
            current_teacher = row[0].replace("מערכת שעות למורה", "").strip()
            header_map = {}
            continue
        if row and row[0].strip() == 'שעה' and current_teacher:
            header_map = {day_name.strip(): i for i, day_name in enumerate(row) if day_name.strip() in DAYS}
            continue
        if row and row[0].isdigit() and current_teacher and header_map:
            hour = int(row[0])
            for day_name, col_index in header_map.items():
                if col_index < len(row) and row[col_index].strip():
                    raw_subject = row[col_index].strip()
                    clean_subject = re.sub(r'\s+[א-ו]\d?$', '', raw_subject.replace('\n', ' ')).strip()
                    record = {'teacher': current_teacher, 'day': day_name, 'hour': hour, 'subject': clean_subject}
                    all_records.append(record)
    df = pd.DataFrame(all_records)
    if df.empty: st.warning("לא נמצאו נתונים בפורמט הצפוי בגוגל שיטס.")
    return df

df = load_data_from_gsheet()
if not df.empty:
    TEACHERS = sorted(df['teacher'].unique())
else:
    TEACHERS = []

# ───────── ניווט טאבים ─────────
tab_names = ["🤖 מצא מחליף", "📅 צפה במערכת"]
active_tab = st.radio(
    "ניווט", tab_names,
    horizontal=True,
    label_visibility="collapsed",
    key="active_tab_radio"
)

# ──────────────────────────────────────────────────────────
# ─────────── לוגיקה עבור הטאב הראשון ──────────────
# ──────────────────────────────────────────────────────────
if active_tab == tab_names[0]:
    if "chat" not in st.session_state:
        st.session_state.chat=[("bot","שלום גלית! 👋 אני צמרובוט, העוזר האישי שלך למציאת מחליפים. בואי נתחיל - איזו מורה נעדרת?")]
        st.session_state.stage="teacher"
    
    def add(role,msg):
        if not st.session_state.chat or st.session_state.chat[-1]!=(role,msg):
            st.session_state.chat.append((role,msg))

    def render_chat(container):
        with container:
            for r,m in st.session_state.chat:
                cls="chat-msg chat-user" if r=="user" else "chat-msg"
                st.markdown(f"<div class='{cls}'>{m}</div>",unsafe_allow_html=True)
    
    chat_container = st.container()

    def find_subs(t, day, hours_list):
        rows=df[(df.teacher==t)&(df.day==day)]
        if not rows.empty and (rows.subject==DAY_OFF).all(): return "DAY_OFF"
        absent_teacher_schedule = {r.hour:r.subject for _,r in rows.iterrows()}
        out={}
        for h in hours_list:
            subj = absent_teacher_schedule.get(h)
            if subj is None:
                out[h] = ("לא בבית הספר", None)
                continue
            if any(keyword in subj for keyword in AVAILABLE_KEYWORDS):
                out[h] = (subj, None)
                continue
            opts=[]
            for cand in TEACHERS:
                if cand == t: continue
                rec = df[(df.teacher==cand)&(df.day==day)&(df.hour==h)]
                if rec.empty: continue
                stat = rec.iloc[0].subject
                for keyword in AVAILABLE_KEYWORDS:
                    if keyword in stat:
                        priority = PRIORITY.get(keyword, 99)
                        opts.append((priority, cand, stat))
                        break
            opts.sort(key=lambda x:(x[0],TEACHERS.index(x[1])))
            out[h]=(subj,opts)
        return out

    def select_teacher(teacher_name):
        add("user", teacher_name)
        st.session_state.teacher = teacher_name
        st.session_state.stage = "day"
        add("bot", f"מעולה! בחרת ב**{teacher_name}**. 📅 לאיזה יום היא נעדרת?")
        # תיקון - מחיקת המפתח אם קיים
        if 'teacher_search_chat' in st.session_state:
            del st.session_state.teacher_search_chat

    def choose_day():
        d=st.session_state.sel_day
        if d:
            add("user",d)
            st.session_state.day=d
            st.session_state.stage="scope"
            add("bot","🕐 האם היא נעדרת **יום שלם** או רק **בשעות ספציפיות**?")
            st.session_state.sel_day=""

    def choose_scope():
        sc=st.session_state.sel_scope
        if not sc: return
        add("user", sc)
        if sc=="יום שלם":
            st.session_state.selected_hours = list(range(1, 10))
            calculate()
        elif sc=="בשעות ספציפיות":
            st.session_state.stage="select_hours"
            # איפוס בחירת השעות
            for h in range(1, 10):
                st.session_state[f"hour_check_{h}"] = False

    def calculate():
        with st.spinner("🔍 צמרובוט מחפש את המחליפים הטובים ביותר..."): time.sleep(1.1)
        res=find_subs(st.session_state.teacher, st.session_state.day, st.session_state.selected_hours)
        if res=="DAY_OFF":
            add("bot",f"✋ **{st.session_state.teacher}** בחופש ביום **{st.session_state.day}** – אין צורך בחלופה.")
        else:
            txt=f"✅ מצאתי! להלן החלופות למורה **{st.session_state.teacher}** ביום **{st.session_state.day}**:<br><br>"
            for h in sorted(res.keys()):
                subj,subs=res.get(h, ('—', []))
                txt+=f"**🕐 שעה {h}** – {subj}<br>"
                if subs is None: txt+="▪️ אין צורך בחלופה<br>"
                elif subs: txt+= "▪️ מחליפים זמינים: " + " / ".join(f"**{t}** ({s})" for _, t, s in subs) + "<br>"
                else: txt+="▪️ ⚠️ אין מחליף זמין<br>"
                txt+="<br>"
            add("bot", txt)
        add("bot","💜 שמחתי לעזור! תמיד כאן לשירותך. צמרובוט 🌸")
        st.session_state.stage="done"

    def start_new_search():
        st.session_state.stage="teacher"
        add("bot", "בואי נתחיל חיפוש חדש! 🔄 איזו מורה נעדרת הפעם?")
        # איפוס בחירת השעות
        for h in range(1, 10):
            if f"hour_check_{h}" in st.session_state:
                st.session_state[f"hour_check_{h}"] = False

    def display_teacher_selection():
        if not TEACHERS: return
        
        st.markdown("#### 📋 בחרי מורה מהרשימה")
        
        # תיבת בחירה עם חיפוש משולב
        selected_teacher = st.selectbox(
            "הקלידי או בחרי שם מורה:",
            [""] + TEACHERS,
            key="teacher_dropdown",
            help="ניתן להקליד לחיפוש מהיר או לבחור מהרשימה"
        )
        
        if selected_teacher and selected_teacher != "":
            select_teacher(selected_teacher)
            st.rerun()

    def display_day_selection():
        st.selectbox("בחרי יום:",[""]+DAYS,key="sel_day",on_change=choose_day)
    
    def display_scope_selection():
        st.radio("",("יום שלם","בשעות ספציפיות"),key="sel_scope",on_change=choose_scope, horizontal=True, index=None)
    
    def display_hour_selection():
        # רק אם השלב הנוכחי הוא בחירת שעות
        if st.session_state.stage != "select_hours":
            return
            
        add("bot", "⏰ סמני את השעות שבהן המורה נעדרת:")
        
        # Initialize hour states if not exists
        for h in range(1, 10):
            if f"hour_check_{h}" not in st.session_state:
                st.session_state[f"hour_check_{h}"] = False
        
        with st.container():
            st.markdown("##### בחירת שעות להיעדרות")
            
            # יצירת רשת עם 2 עמודות (יופיע טוב גם במובייל וגם בדסקטופ)
            col1, col2 = st.columns(2)
            
            # חלוקת השעות בין 2 העמודות
            hours_col1 = [1, 2, 3, 4, 5]
            hours_col2 = [6, 7, 8, 9]
            
            with col1:
                for h in hours_col1:
                    st.checkbox(f"שעה {h}", key=f"hour_check_{h}")
            
            with col2:
                for h in hours_col2:
                    st.checkbox(f"שעה {h}", key=f"hour_check_{h}")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ מצא מחליפים", use_container_width=True, type="primary"):
                    selected_hours = [h for h in range(1, 10) if st.session_state.get(f"hour_check_{h}", False)]
                    if not selected_hours:
                        st.warning("⚠️ יש לבחור לפחות שעה אחת.")
                    else:
                        st.session_state.selected_hours = selected_hours
                        hours_str = ", ".join(map(str, selected_hours))
                        add("user", f"שעות נבחרות: {hours_str}")
                        calculate()
            
            with col_btn2:
                if st.button("🔄 בחר הכל", use_container_width=True):
                    for h in range(1, 10):
                        st.session_state[f"hour_check_{h}"] = True
                    st.rerun()

    def display_done_state():
        st.button("🔎 חיפוש חדש", on_click=start_new_search, type="primary")
    
    # הצגת האלמנטים לפי השלב הנוכחי
    stage = st.session_state.get('stage', 'teacher')
    
    # מיכל נפרד לאלמנטי הקלט שיימחק אחרי בחירה
    input_container = st.container()
    
    with input_container:
        if stage =="teacher": 
            display_teacher_selection()
        elif stage =="day": 
            display_day_selection()
        elif stage =="scope": 
            display_scope_selection()
        elif stage == "select_hours": 
            display_hour_selection()
        elif stage == "done": 
            display_done_state()
    
    # הצגת הצ'אט
    render_chat(chat_container)
    
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ נקה", use_container_width=True):
            keys_to_keep = ['active_tab_radio']
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            st.rerun()
    
    # JavaScript לגלילה אוטומטית
    components.html(
        """
        <script>
            setTimeout(() => {
                const messages = window.parent.document.querySelectorAll('.chat-msg');
                if (messages.length > 0) {
                    messages[messages.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            }, 100);
        </script>
        """,
        height=0,
    )

# ──────────────────────────────────────────────────────────
# ─────────── לוגיקה עבור הטאב השני ──────────────
# ──────────────────────────────────────────────────────────
elif active_tab == tab_names[1]:
    st.subheader("📅 מערכת שעות שבועית")

    if not TEACHERS:
        st.warning("לא נטענו מורים. בדוק את החיבור לגוגל שיטס ואת מבנה הקובץ.")
    else:
        st.markdown("#### 🔍 חיפוש מורה")
        
        # תיבת בחירה עם חיפוש משולב
        selected_teacher = st.selectbox(
            "הקלידי או בחרי שם מורה לצפייה במערכת:",
            [""] + TEACHERS,
            key="schedule_dropdown",
            help="ניתן להקליד לחיפוש מהיר או לבחור מהרשימה"
        )
        
        if selected_teacher and selected_teacher != "":
            st.markdown(f"### מערכת שעות של: **{selected_teacher}**")
            
            teacher_df = df[df['teacher'] == selected_teacher]

            if teacher_df.empty:
                st.write("לא נמצאה מערכת שעות עבור מורה זו.")
            else:
                schedule_pivot = teacher_df.pivot_table(
                    index='hour', columns='day', values='subject', aggfunc='first'
                )
                all_hours = pd.Index(range(1, 10), name='hour')
                schedule_pivot = schedule_pivot.reindex(all_hours).fillna('')
                ordered_days = [day for day in DAYS if day in schedule_pivot.columns]
                schedule_pivot = schedule_pivot[ordered_days]
                schedule_pivot.index.name = "שעה"

                def color_schedule(val):
                    if any(keyword in str(val) for keyword in AVAILABLE_KEYWORDS):
                        return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                    elif val == '':
                        return 'background-color: #f8f9fa; color: #6c757d;'
                    return 'background-color: #fff3cd; color: #856404;'

                st.dataframe(
                    schedule_pivot.style.apply(lambda x: x.map(color_schedule)),
                    use_container_width=True,
                    height=400
                )