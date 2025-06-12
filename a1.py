import streamlit as st
import pandas as pd

# ───────── הגדרות עמוד ─────────
st.set_page_config(page_title="בוט חלופות", layout="centered")
st.markdown("""
<style>
h1{font-size:1.5rem;}
button,select,input{font-size:1rem;}
section[data-testid="stSidebar"]{display:none;}
</style>
""", unsafe_allow_html=True)

# ───────── קבועים ─────────
DATA_FILE = "schedule.csv"
TEACHERS  = ['דנה','לילך','רעות','ליאת','לימור']
DAYS      = ['ראשון','שני','שלישי','רביעי','חמישי','שישי']
DAY_OFF   = 'יום חופשי'
PRIORITY  = {'שהייה':1,'פרטני':2}
COLOR_MAP = {'שהייה':'#c8e6c9','פרטני':'#bbdefb',DAY_OFF:'#e0e0e0'}

# ───────── טעינת נתונים ─────────
@st.cache_data
def load_df():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour']    = df['hour'].astype(int)
    df['subject'] = df['subject'].str.strip()
    return df
df = load_df()

# ───────── פונקציות עזר ─────────
def find_subs(teacher, day):
    rows = df[(df.teacher == teacher) & (df.day == day)]
    if not rows.empty and (rows.subject == DAY_OFF).all():
        return "DAY_OFF"
    absent = {r.hour: r.subject for _, r in rows.iterrows()}
    res = {}
    for h in range(1, 7):
        subj = absent.get(h, "—")
        if subj in ('פרטני', DAY_OFF):
            res[h] = (subj, None)
            continue
        opts = []
        for t in TEACHERS:
            if t == teacher:
                continue
            r = df[(df.teacher == t) & (df.day == day) & (df.hour == h)]
            if r.empty:
                continue
            stat = r.iloc[0].subject
            if stat in PRIORITY:
                opts.append((PRIORITY[stat], t, stat))
        opts.sort(key=lambda x: (x[0], TEACHERS.index(x[1])))
        res[h] = (subj, opts)
    return res

def teacher_matrix(name: str):
    sub = df[df.teacher == name]
    wide = sub.pivot_table(index='hour', columns='day', values='subject', aggfunc='first')
    return wide.reindex(index=range(1,7), columns=DAYS)

def color_cells(val):
    for k, c in COLOR_MAP.items():
        if pd.notna(val) and val.startswith(k):
            return f'background-color:{c}'
    return ''

# ───────── מצב ראשי ─────────
MODE = st.radio("בחר/י תצורה:", ["ממשק טפסים", "עוזר אישי (צ'אט)"])

# =================================================
# 1) ממשק טפסים + לוח שבועי
# =================================================
if MODE == "ממשק טפסים":
    tabs = st.tabs(["🧑‍🏫 חלופות", "📅 לוח שבועי"])

    # --- טאב חלופות ---
    with tabs[0]:
        st.title("🧑‍🏫 בוט חלופות מורים")
        t_sel = st.selectbox("מורה חסרה", TEACHERS, key="form_teacher")
        d_sel = st.selectbox("יום בשבוע", DAYS, key="form_day")
        if st.button("מצא חלופות", use_container_width=True):
            res = find_subs(t_sel, d_sel)
            if res == "DAY_OFF":
                st.info(f"✋ {t_sel} בחופש ביום {d_sel} – אין צורך בחלופה.")
            else:
                st.subheader(f"📌 {t_sel} | יום {d_sel}")
                for h in range(1, 7):
                    subj, subs = res[h]
                    st.markdown(f"**🕐 שעה {h}: {subj}**")
                    if subs is None:
                        st.info("אין צורך בחלופה")
                    elif subs:
                        st.success(" / ".join(f"{t} ({s})" for _, t, s in subs))
                    else:
                        st.warning("אין חלופה זמינה")

    # --- טאב לוח שבועי ---
    with tabs[1]:
        st.title("📅 לוח שעות – כל המורות")
        st.markdown("<span style='font-size:0.9rem;'>🟩 שהייה&nbsp;&nbsp;🟦 פרטני&nbsp;&nbsp;⬜ מקצוע&nbsp;&nbsp;⬜ יום חופשי</span>",
                    unsafe_allow_html=True)
        for t in TEACHERS:
            with st.expander(f"📋 {t}", expanded=False):
                styled = teacher_matrix(t).style.map(color_cells)
                st.dataframe(styled, use_container_width=True, height=240)

# =================================================
# 2) עוזר אישי (צ'אט)  – ללא rerun
# =================================================
else:
    st.title("🤖 עוזר אישי למציאת מחליפות")

    GREET = "שלום גלית! אני העוזר האישי שלך למציאת מחליפות 😊\nאיזו מורה נעדרת היום?"

    if 'hist' not in st.session_state:
        st.session_state.hist   = []
        st.session_state.stage  = "teacher"
        st.session_state.teacher = ""
        st.session_state.day     = ""
    # הוספת ברכה פעם אחת בלבד
    if not st.session_state.hist or st.session_state.hist[0][1] != GREET:
        st.session_state.hist.insert(0, ("bot", GREET))

    def bot(txt):  st.session_state.hist.append(("bot", txt))
    def user(txt): st.session_state.hist.append(("user", txt))

    chat = st.container()
    def redraw():
        chat.empty()
        for role, msg in st.session_state.hist:
            with chat.chat_message("assistant" if role == "bot" else "user"):
                st.markdown(msg)
    redraw()

    # --- callback למורה ---
    def choose_teacher():
        t = st.session_state.sel_teacher
        if t:
            user(t)
            st.session_state.teacher = t
            st.session_state.stage   = "day"
            bot(f"מצוין, בחרנו במורה **{t}**.\nעכשיו בחרי יום היעדרות:")
            redraw()

    # --- callback ליום ---
    def choose_day():
        d = st.session_state.sel_day
        if d:
            user(d)
            res = find_subs(st.session_state.teacher, d)
            if res == "DAY_OFF":
                ans = f"✋ {st.session_state.teacher} בחופש ביום **{d}** – אין צורך במחליפה."
            else:
                ans = f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{d}**:\n"
                for h in range(1, 7):
                    subj, subs = res[h]
                    ans += f"\n**🕐 שעה {h}** – {subj}\n"
                    if subs is None:
                        ans += "▪️ אין צורך בחלופה\n"
                    elif subs:
                        ans += "▪️ חלופה: " + " / ".join(f"{t} ({s})" for _, t, s in subs) + "\n"
                    else:
                        ans += "▪️ אין חלופה זמינה\n"
            bot(ans)
            bot("אם תרצי שוב – בחרי מורה חדשה 😊")
            # reset
            st.session_state.stage   = "teacher"
            st.session_state.teacher = ""
            st.session_state.day     = ""
            st.session_state.sel_teacher = ""
            st.session_state.sel_day     = ""
            redraw()

    # --- UI דינמי ---
    if st.session_state.stage == "teacher":
        st.selectbox("בחרי מורה חסרה:",
                     [""] + TEACHERS,
                     key="sel_teacher",
                     on_change=choose_teacher)
    elif st.session_state.stage == "day":
        st.selectbox("בחרי יום:",
                     [""] + DAYS,
                     key="sel_day",
                     on_change=choose_day)

    redraw()
