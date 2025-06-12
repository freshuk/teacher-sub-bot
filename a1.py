import streamlit as st
import pandas as pd

# ───────── הגדרות עמוד ─────────
st.set_page_config(page_title="בוט חלופות", layout="centered")
st.markdown("""
<style>
h1 {font-size:1.5rem;}
button,select,input{font-size:1rem;}
section[data-testid="stSidebar"]{display:none;}
</style>
""", unsafe_allow_html=True)

# ───────── נתונים וקבועים ─────────
DATA_FILE = "schedule.csv"
TEACHERS  = ['דנה','לילך','רעות','ליאת','לימור']
DAYS      = ['ראשון','שני','שלישי','רביעי','חמישי','שישי']
DAY_OFF   = 'יום חופשי'
PRIORITY  = {'שהייה':1,'פרטני':2}

@st.cache_data
def load_df():
    df = pd.read_csv(DATA_FILE,dtype=str)
    df['hour']    = df['hour'].astype(int)
    df['subject'] = df['subject'].str.strip()
    return df
df = load_df()

def find_subs(teacher, day):
    rows = df[(df.teacher == teacher) & (df.day == day)]
    if not rows.empty and (rows.subject == DAY_OFF).all():
        return "DAY_OFF"
    absent = {r.hour: r.subject for _, r in rows.iterrows()}
    out = {}
    for h in range(1, 7):
        subj = absent.get(h, "—")
        if subj in ('פרטני', DAY_OFF):
            out[h] = (subj, None)
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
        out[h] = (subj, opts)
    return out

# ───────── תצורה ראשית ─────────
MODE = st.radio("בחר/י תצורה:", ["ממשק טפסים", "עוזר אישי (צ'אט)"])

# =================================================
# 1) ממשק טפסים (כפי שהיה, ללא שינוי)
# =================================================
if MODE == "ממשק טפסים":
    st.title("🧑‍🏫 בוט חלופות מורים")
    t_sel = st.selectbox("מורה חסרה", TEACHERS)
    d_sel = st.selectbox("יום בשבוע", DAYS)
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

# =================================================
# 2) עוזר אישי (צ'אט) – עם callbacks
# =================================================
else:
    st.title("🤖 עוזר אישי למציאת מחליפות")

    # --- אתחול state ---
    if 'hist' not in st.session_state:
        st.session_state.hist   = [("bot", "שלום גלית! אני העוזר האישי שלך למציאת מחליפות 😊\nאיזו מורה נעדרת היום?")]
        st.session_state.stage  = "teacher"
        st.session_state.teacher = ""
        st.session_state.day     = ""

    # --- פונקציות עזר לצ'אט ---
    def bot(txt):  st.session_state.hist.append(("bot", txt))
    def user(txt): st.session_state.hist.append(("user", txt))

    chat = st.container()
    def redraw():
        chat.empty()
        for role, msg in st.session_state.hist:
            with chat.chat_message("assistant" if role == "bot" else "user"):
                st.markdown(msg)
    redraw()

    # --- callback לבחירת מורה ---
    def on_teacher_change():
        teacher = st.session_state.sel_teacher
        if teacher:
            user(teacher)
            st.session_state.teacher = teacher
            st.session_state.stage   = "day"
            bot(f"מצוין, בחרנו במורה **{teacher}**.\nעכשיו בחרי יום היעדרות:")
    # --- callback לבחירת יום ---
    def on_day_change():
        day = st.session_state.sel_day
        if day:
            user(day)
            res = find_subs(st.session_state.teacher, day)
            if res == "DAY_OFF":
                ans = f"✋ {st.session_state.teacher} בחופש ביום **{day}** – אין צורך במחליפה."
            else:
                ans = f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{day}**:\n"
                for h in range(1, 7):
                    subj, subs = res[h]
                    ans += f"\n**🕐 שעה {h}** – {subj}\n"
                    if subs is None:
                        ans += "▪️ אין צורך בחלופה\n"
                    elif subs:
                        line = " / ".join(f"{t} ({s})" for _, t, s in subs)
                        ans += f"▪️ חלופה: {line}\n"
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

    # --- UI דינמי ---
    if st.session_state.stage == "teacher":
        st.selectbox("בחרי מורה חסרה:",
                     [""] + TEACHERS,
                     key="sel_teacher",
                     on_change=on_teacher_change)
    elif st.session_state.stage == "day":
        st.selectbox("בחרי יום:",
                     [""] + DAYS,
                     key="sel_day",
                     on_change=on_day_change)

    redraw()
