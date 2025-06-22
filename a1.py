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
st.markdown("""
<style>
/* ... (כל ה-CSS נשאר זהה) ... */
.main-header { display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 1rem; }
.main-header img { width: 80px !important; margin-bottom: 0.5rem; }
.main-header h3 { font-size: 1.8rem; font-weight: 800; text-align: center; width: 100%; }
.chat-msg { background:#f5f8ff; border-radius:14px; padding:0.7rem 1rem; margin:0.3rem 0; color: #31333F; direction: rtl; text-align: right; }
.chat-user {background:#d2e1ff;}
.stSelectbox div[data-baseweb="select"] > div {background-color: #d2e1ff;}
div[data-testid="stRadio"] > div { flex-direction: row-reverse; justify-content: flex-start; }
div[data-testid="stRadio"] label { margin-left: 0.5rem !important; margin-right: 0 !important; }
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
    # ... (הפונקציה נשארת זהה)
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
        st.session_state.chat=[("bot","שלום גלית! אני צמרובוט 😊 במה אני יכול לעזור לך היום?")]
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

    def find_subs(t,day,start, end):
        # ... (הפונקציה נשארת זהה)
        rows=df[(df.teacher==t)&(df.day==day)]
        if not rows.empty and (rows.subject==DAY_OFF).all(): return "DAY_OFF"
        absent_teacher_schedule = {r.hour:r.subject for _,r in rows.iterrows()}
        out={}
        for h in range(start, end + 1):
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
            txt=f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{st.session_state.day}**:<br>"
            for h in range(st.session_state.start, st.session_state.end + 1):
                subj,subs=res.get(h, ('—', []))
                txt+=f"<br>**🕐 שעה {h}** – {subj}<br>"
                if subs is None: txt+="▪️ אין צורך בחלופה<br>"
                elif subs: txt+= "▪️ חלופה: " + " / ".join(f"{t} ({s})" for _, t, s in subs) + "<br>"
                else: txt+="▪️ אין חלופה זמינה<br>"
            add("bot", txt)
        add("bot","שמחתי לעזור! תמיד כאן לשירותך, צמרובוט 🌸")
        st.session_state.stage="done"

    def start_new_search():
        st.session_state.stage="teacher"
        add("bot", "בטח, נתחיל מחדש. איזו מורה נעדרת הפעם?")

    def display_teacher_selection():
        if not TEACHERS: return
        st.selectbox("בחרי מורה חסרה:",[""]+TEACHERS,key="sel_teacher",on_change=choose_teacher, label_visibility="collapsed")
    def display_day_selection():
        st.selectbox("בחרי יום:",[""]+DAYS,key="sel_day",on_change=choose_day, label_visibility="collapsed")
    def display_scope_selection():
        st.radio("",("יום שלם","בטווח שעות"),key="sel_scope",on_change=choose_scope, horizontal=True, index=None)
    def display_hour_selection():
        add("bot", "בחרי שעת התחלה (1-9):")
        st.selectbox("שעת התחלה:",[""]+[str(i) for i in range(1,10)], key="sel_hr",on_change=choose_hour, label_visibility="collapsed")
    def display_end_hour_selection():
        add("bot", "עד איזו שעה?")
        start_hour = st.session_state.get('start', 1)
        options = [str(i) for i in range(start_hour, 10)]
        st.selectbox("שעת סיום:", [""] + options, key="sel_end_hr", on_change=choose_end_hour, label_visibility="collapsed")
    def display_done_state():
        st.button("🔎 חיפוש חדש", on_click=start_new_search)
    
    stage = st.session_state.get('stage', 'teacher')
    if stage =="teacher": display_teacher_selection()
    elif stage =="day": display_day_selection()
    elif stage =="scope": display_scope_selection()
    elif stage == "hour": display_hour_selection()
    elif stage == "end_hour": display_end_hour_selection()
    elif stage == "done": display_done_state()
    
    render_chat(chat_container)
    st.divider()
    if st.button("🗑️ נקה מסך"):
        keys_to_keep = ['active_tab_radio']
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        st.rerun()
    
    ### שינוי: קריאה לגלילה אוטומטית בסוף הטאב ###
    # This is the "Anchor Hack" for reliable auto-scrolling
    st.markdown('<div id="end-of-chat-anchor" style="height: 0px;"></div>', unsafe_allow_html=True)
    components.html(
        """
        <script>
            // We target the anchor element within the parent document
            const anchor = window.parent.document.getElementById("end-of-chat-anchor");
            if (anchor) {
                // The timeout is crucial to wait for the DOM to be updated.
                setTimeout(() => {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }, 250);
            }
        </script>
        """,
        height=0,
    )

# ──────────────────────────────────────────────────────────
# ─────────── לוגיקה עבור הטאב השני ──────────────
# ──────────────────────────────────────────────────────────
elif active_tab == tab_names[1]:
    st.subheader("מערכת שעות שבועית")

    if not TEACHERS:
        st.warning("לא נטענו מורים. בדוק את החיבור לגוגל שיטס ואת מבנה הקובץ.")
    else:
        selected_teacher = st.selectbox(
            "בחרי מורה לצפייה במערכת:",
            options=[""] + TEACHERS,
            key="schedule_teacher_select",
            label_visibility="collapsed"
        )

        if selected_teacher:
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
                        return 'background-color: #e6ffed'
                    elif val == '':
                        return 'background-color: #f0f2f6'
                    return ''

                st.dataframe(
                    schedule_pivot.style.apply(lambda x: x.map(color_schedule)),
                    use_container_width=True
                )