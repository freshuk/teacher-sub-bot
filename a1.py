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
/* ... (CSS is now much simpler as we removed the problematic fixes) ... */
.main-header { display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 1rem; }
.main-header img { width: 80px !important; margin-bottom: 0.5rem; }
.main-header h3 { font-size: 1.8rem; font-weight: 800; text-align: center; width: 100%; }
.chat-msg { background:#f5f8ff; border-radius:14px; padding:0.7rem 1rem; margin:0.3rem 0; color: #31333F; direction: rtl; text-align: right; }
.chat-user {background:#d2e1ff;}
div[data-testid="stRadio"] > div { flex-direction: row-reverse; justify-content: flex-start; }
div[data-testid="stRadio"] label { margin-left: 0.5rem !important; margin-right: 0 !important; }
.hour-grid-container { display: flex; flex-direction: row; gap: 10px; }
.hour-grid-col { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.hour-checkbox-item { border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; display: flex; flex-direction: row-reverse; align-items: center; justify-content: space-between; cursor: pointer; }
.hour-checkbox-item:hover { background-color: #f5f8ff; }
.hour-checkbox-item span { font-weight: bold; font-size: 1.1rem; }
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
        st.session_state.chat=[("bot","שלום גלית! אני צמרובוט 😊 אשמח לעזור לך! בבקשה הקלידי את שם המורה הנעדר\\ת ונמשיך משם.")]
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
        add("bot", f"מעולה, בחרנו במורה **{teacher_name}**.\nלאיזה יום היא נעדרת?")
        st.session_state.teacher_search = ""

    def choose_day():
        d=st.session_state.sel_day
        if d:
            add("user",d)
            st.session_state.day=d
            st.session_state.stage="scope"
            add("bot","היא נעדרת **יום שלם** או **בשעות ספציפיות**?")
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

    def calculate():
        with st.spinner("צמרובוט חושב…"): time.sleep(1.1)
        res=find_subs(st.session_state.teacher, st.session_state.day, st.session_state.selected_hours)
        if res=="DAY_OFF":
            add("bot",f"✋ **{st.session_state.teacher}** בחופש ביום **{st.session_state.day}** – אין צורך בחלופה.")
        else:
            txt=f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{st.session_state.day}**:<br>"
            for h in sorted(res.keys()):
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
        add("bot", "בטח, נתחיל מחדש. הקלידי את שם המורה הנעדר\\ת.")

    ### שינוי: החלפת ה-selectbox ברכיב חיפוש עם כפתורים ###
    def display_teacher_selection():
        if not TEACHERS: return
        
        search_term = st.text_input(
            "הקלידי שם מורה כדי לחפש:",
            key="teacher_search",
            placeholder="לדוגמה: אביטל"
        )

        search_term = search_term.strip().lower()
        if search_term:
            filtered_teachers = [t for t in TEACHERS if search_term in t.lower()][:5]
            
            if not filtered_teachers:
                st.info("לא נמצאו מורים תואמים לחיפוש.")
            else:
                for teacher in filtered_teachers:
                    st.button(teacher, key=f"btn_{teacher}", on_click=select_teacher, args=(teacher,), use_container_width=True)

    def display_day_selection():
        st.selectbox("בחרי יום:",[""]+DAYS,key="sel_day",on_change=choose_day, label_visibility="collapsed")
    
    def display_scope_selection():
        st.radio("",("יום שלם","בשעות ספציפיות"),key="sel_scope",on_change=choose_scope, horizontal=True, index=None)
    
    def display_hour_selection():
        add("bot", "סמני את השעות שבהן המורה נעדרת ולחצי על 'מצא מחליפים'.")
        
        with st.form(key="hours_form"):
            st.markdown('<div class="hour-grid-container">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="hour-grid-col">', unsafe_allow_html=True)
                for h in range(1, 6):
                    st.markdown(f'<div class="hour-checkbox-item"><span>שעה {h}</span>', unsafe_allow_html=True)
                    st.checkbox("", key=f"hour_{h}", label_visibility="collapsed")
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="hour-grid-col">', unsafe_allow_html=True)
                for h in range(6, 10):
                    st.markdown(f'<div class="hour-checkbox-item"><span>שעה {h}</span>', unsafe_allow_html=True)
                    st.checkbox("", key=f"hour_{h}", label_visibility="collapsed")
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("מצא מחליפים", use_container_width=True)
            if submitted:
                selected_hours = [h for h in range(1, 10) if st.session_state.get(f"hour_{h}", False)]
                if not selected_hours:
                    st.warning("יש לבחור לפחות שעה אחת.")
                else:
                    st.session_state.selected_hours = selected_hours
                    hours_str = ", ".join(map(str, selected_hours))
                    add("user", f"שעות נבחרות: {hours_str}")
                    calculate()

    def display_done_state():
        st.button("🔎 חיפוש חדש", on_click=start_new_search)
    
    stage = st.session_state.get('stage', 'teacher')
    if stage =="teacher": display_teacher_selection()
    elif stage =="day": display_day_selection()
    elif stage =="scope": display_scope_selection()
    elif stage == "select_hours": display_hour_selection()
    elif stage == "done": display_done_state()
    
    render_chat(chat_container)
    st.divider()
    if st.button("🗑️ נקה מסך"):
        keys_to_keep = ['active_tab_radio']
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        st.rerun()
    
    st.markdown('<div id="end-of-chat-anchor" style="height: 0px;"></div>', unsafe_allow_html=True)
    components.html(
        """
        <script>
            const anchor = window.parent.document.getElementById("end-of-chat-anchor");
            if (anchor) {
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
        search_term_sched = st.text_input(
            "הקלידי שם מורה לצפייה במערכת:",
            key="schedule_teacher_search",
            placeholder="לדוגמה: אביטל"
        ).strip().lower()

        if 'selected_schedule_teacher' not in st.session_state:
            st.session_state.selected_schedule_teacher = None

        if search_term_sched:
            filtered_teachers_sched = [t for t in TEACHERS if search_term_sched in t.lower()][:5]
            
            if not filtered_teachers_sched:
                st.info("לא נמצאו מורים תואמים לחיפוש.")
            else:
                for teacher in filtered_teachers_sched:
                    if st.button(teacher, key=f"sched_btn_{teacher}", use_container_width=True):
                        st.session_state.selected_schedule_teacher = teacher
        
        if st.session_state.selected_schedule_teacher:
            selected_teacher = st.session_state.selected_schedule_teacher
            st.write(f"**מציג מערכת עבור: {selected_teacher}**")
            
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