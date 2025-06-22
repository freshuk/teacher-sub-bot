import streamlit as st
import pandas as pd
import time
from pathlib import Path
import streamlit.components.v1 as components
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re # נוסיף את ספריית הביטויים הרגולריים לניקוי טקסט

# ───────── הגדרות בסיס + CSS ─────────
st.set_page_config(page_title="צמרובוט – העוזר האישי שלי", layout="centered")
st.markdown("""
<style>
h1{font-size:1.8rem;font-weight:800;margin-bottom:0.4rem;display:inline;}
.chat-msg{background:#f5f8ff;border-radius:14px;padding:0.7rem 1rem;margin:0.3rem 0;}
.chat-user{background:#d2e1ff;}
button,select,input,label{font-size:1rem;}
section[data-testid="stSidebar"]{display:none;}
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #d2e1ff; /* צבע רקע כמו של כפתור משתמש */
}
</style>
""", unsafe_allow_html=True)

# ───────── אייקון קבוע ─────────
# (הקוד נשאר זהה)
if Path("bot_calendar.png").exists():
    c1,c2=st.columns([1,9])
    with c1: st.image("bot_calendar.png",width=60)
    with c2: st.markdown("### צמרובוט – העוזר האישי שלי")
else:
    st.title("🤖 צמרובוט – העוזר האישי שלי")

# ───────── נתונים וקבועים ─────────
DAYS=['יום א','יום ב','יום ג','יום ד','יום ה','יום ו']
DAY_OFF='יום חופשי'
# נרחיב את רשימת המקצועות שלא דורשים החלפה
NO_SUB_NEEDED = ['פרטני', DAY_OFF, 'שהייה', 'הדרכה', 'תגבור', 'שילוב']
PRIORITY={'שהייה':1,'פרטני':2}

### שינוי מרכזי: פונקציה מתוקנת לקריאה ועיבוד הנתונים מגוגל שיטס ###
@st.cache_data(ttl=600) # שמירה בזיכרון המטמון ל-10 דקות
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
    header_map = {} # מילון שימפה שם יום לאינדקס עמודה

    for row in data:
        if not any(cell.strip() for cell in row): continue # דילוג על שורות ריקות לחלוטין

        # זיהוי שורת כותרת של מורה חדש
        if "מערכת שעות למורה" in row[0]:
            current_teacher = row[0].replace("מערכת שעות למורה", "").strip()
            header_map = {} # איפוס מפת הכותרות עבור המורה החדש
            continue

        # זיהוי שורת הכותרת של הימים (מתחילה ב"שעה")
        if row and row[0].strip() == 'שעה' and current_teacher:
            # יצירת מפה של שם היום לאינדקס העמודה שלו
            header_map = {day_name.strip(): i for i, day_name in enumerate(row) if day_name.strip() in DAYS}
            continue

        # זיהוי שורת נתונים (תא ראשון הוא מספר)
        if row and row[0].isdigit() and current_teacher and header_map:
            hour = int(row[0])
            # לולאה על הימים שמצאנו בכותרת
            for day_name, col_index in header_map.items():
                if col_index < len(row) and row[col_index].strip():
                    # ניקוי שם המקצוע: הסרת ירידות שורה והסרת שם הכיתה
                    raw_subject = row[col_index].strip()
                    # שימוש בביטוי רגולרי להסרת שם הכיתה (למשל, " א1")
                    clean_subject = re.sub(r'\s+[א-ו]\d?$', '', raw_subject.replace('\n', ' ')).strip()
                    
                    # טיפול בערכים עם נקודה, כמו 'שהייה.מליאה'
                    if '.' in clean_subject:
                        clean_subject = clean_subject.split('.')[0]

                    record = {
                        'teacher': current_teacher,
                        'day': day_name,
                        'hour': hour,
                        'subject': clean_subject
                    }
                    all_records.append(record)

    df = pd.DataFrame(all_records)
    if df.empty:
        st.warning("לא נמצאו נתונים בפורמט הצפוי בגוגל שיטס. בדוק את מבנה הקובץ.")
    return df

# --- שאר הקוד נשאר זהה ---

# טעינת הנתונים
df = load_data_from_gsheet()
if not df.empty:
    TEACHERS = sorted(df['teacher'].unique())
else:
    TEACHERS = []

# ───────── init state ─────────
if "chat" not in st.session_state:
    st.session_state.chat=[("bot","שלום גלית! אני צמרובוט 😊 במה אני יכול לעזור לך היום?")]
    st.session_state.stage="teacher"

# ───────── chat helpers ─────────
def add(role,msg):
    if not st.session_state.chat or st.session_state.chat[-1]!=(role,msg):
        st.session_state.chat.append((role,msg))

def render_chat(container):
    with container:
        for r,m in st.session_state.chat:
            cls="chat-msg chat-user" if r=="user" else "chat-msg"
            st.markdown(f"<div class='{cls}'>{m}</div>",unsafe_allow_html=True)

chat_container = st.container()

# ───────── substitute fn ─────────
def find_subs(t,day,start, end):
    rows=df[(df.teacher==t)&(df.day==day)]
    if not rows.empty and (rows.subject==DAY_OFF).all(): return "DAY_OFF"
    absmap={r.hour:r.subject for _,r in rows.iterrows()}
    out={}
    for h in range(start, end + 1):
        subj=absmap.get(h,'—')
        # שימוש ברשימה המורחבת של מקצועות ללא צורך בהחלפה
        if any(keyword in subj for keyword in NO_SUB_NEEDED):
            out[h]=(subj,None)
            continue
        
        opts=[]
        for cand in TEACHERS:
            if cand==t: continue
            rec=df[(df.teacher==cand)&(df.day==day)&(df.hour==h)]
            if rec.empty: continue
            stat=rec.iloc[0].subject
            if any(keyword in stat for keyword in NO_SUB_NEEDED):
                priority = PRIORITY.get(stat.split('.')[0], 99)
                opts.append((priority, cand, stat))
        opts.sort(key=lambda x:(x[0],TEACHERS.index(x[1])))
        out[h]=(subj,opts)
    return out

# ───────── callbacks ─────────
def choose_teacher():
    t=st.session_state.sel_teacher
    if t:
        add("user",t)
        st.session_state.teacher=t
        st.session_state.stage="day"
        add("bot",f"מעולה, בחרנו במורה **{t}**.\nלאיזה יום היא נעדרת?")
        st.session_state.sel_teacher=""

def choose_day():
    d=st.session_state.sel_day
    if d:
        add("user",d)
        st.session_state.day=d
        st.session_state.stage="scope"
        add("bot","היא נעדרת **יום שלם** או **בטווח שעות**?")
        st.session_state.sel_day=""

def choose_scope():
    sc=st.session_state.sel_scope
    if not sc: return
    add("user", sc)
    if sc=="יום שלם":
        st.session_state.start=1
        st.session_state.end=9
        calculate()
    elif sc=="בטווח שעות":
        st.session_state.stage="hour"

def choose_hour():
    hr=st.session_state.sel_hr
    if hr:
        add("user",f"משעה {hr}")
        st.session_state.start=int(hr)
        st.session_state.stage="end_hour"
        st.session_state.sel_hr=""

def choose_end_hour():
    end_hr = st.session_state.sel_end_hr
    if end_hr:
        add("user", f"עד שעה {end_hr}")
        st.session_state.end = int(end_hr)
        st.session_state.sel_end_hr = ""
        calculate()

def calculate():
    with st.spinner("צמרובוט חושב…"): time.sleep(1.1)
    res=find_subs(st.session_state.teacher,st.session_state.day,st.session_state.start, st.session_state.end)
    if res=="DAY_OFF":
        add("bot",f"✋ **{st.session_state.teacher}** בחופש ביום **{st.session_state.day}** – אין צורך בחלופה.")
    else:
        txt=f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{st.session_state.day}**:\n"
        for h in range(st.session_state.start, st.session_state.end + 1):
            subj,subs=res.get(h, ('—', []))
            txt+=f"\n**🕐 שעה {h}** – {subj}\n"
            if subs is None: txt+="▪️ אין צורך בחלופה\n"
            elif subs: txt+= "▪️ חלופה: " + " / ".join(f"{t} ({s})" for _, t, s in subs) + "\n"
            else: txt+="▪️ אין חלופה זמינה\n"
        add("bot",txt)
    add("bot","שמחתי לעזור! תמיד כאן לשירותך, צמרובוט 🌸")
    st.session_state.stage="done"

def start_new_search():
    st.session_state.stage="teacher"
    add("bot", "בטח, נתחיל מחדש. איזו מורה נעדרת הפעם?")

# ───────── פונקציות להצגת הווידג'טים ─────────
def display_teacher_selection():
    if not TEACHERS:
        st.warning("לא נטענו מורים. בדוק את החיבור לגוגל שיטס ואת מבנה הקובץ.")
        return
    st.selectbox("בחרי מורה חסרה:",[""]+TEACHERS,key="sel_teacher",on_change=choose_teacher,
                 label_visibility="collapsed")

def display_day_selection():
    st.selectbox("בחרי יום:",[""]+DAYS,key="sel_day",on_change=choose_day,
                 label_visibility="collapsed")

def display_scope_selection():
    st.radio("",("יום שלם","בטווח שעות"),key="sel_scope",on_change=choose_scope, horizontal=True, index=None)

def display_hour_selection():
    add("bot", "בחרי שעת התחלה (1-9):")
    st.selectbox("שעת התחלה:",[""]+[str(i) for i in range(1,10)], key="sel_hr",on_change=choose_hour,
                 label_visibility="collapsed")

def display_end_hour_selection():
    add("bot", "עד איזו שעה?")
    start_hour = st.session_state.get('start', 1)
    options = [str(i) for i in range(start_hour, 10)]
    st.selectbox("שעת סיום:", [""] + options, key="sel_end_hr", on_change=choose_end_hour,
                 label_visibility="collapsed")

def display_done_state():
    st.button("🔎 חיפוש חדש", on_click=start_new_search)


# ───────── לוגיקה ראשית להצגת הווידג'טים ─────────
stage = st.session_state.get('stage', 'teacher')

if stage =="teacher":
    display_teacher_selection()
elif stage =="day":
    display_day_selection()
elif stage =="scope":
    display_scope_selection()
elif stage == "hour":
    display_hour_selection()
elif stage == "end_hour":
    display_end_hour_selection()
elif stage == "done":
    display_done_state()

# === הצגת הצ'אט בתוך המיכל הריק, אחרי כל הלוגיקה ===
render_chat(chat_container)

# ───────── ניקוי מסך ─────────
st.divider()
if st.button("🗑️ נקה מסך"):
    keys_to_keep = []
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]
    st.rerun()

# ───────── גלילה אוטומטית גלובלית ─────────
components.html("<script>window.scrollTo(0, document.body.scrollHeight);</script>",height=0)