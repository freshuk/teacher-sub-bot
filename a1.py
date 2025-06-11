import streamlit as st
import pandas as pd
import numpy as np

# ─────────────── הגדרות עמוד + CSS ───────────────
st.set_page_config(page_title="בוט חלופות", layout="centered")
st.markdown("""
<style>
h1 {font-size:1.5rem;}
button, select, input {font-size:1rem;}
section[data-testid="stSidebar"] {display:none;}
</style>
""", unsafe_allow_html=True)

# ─────────────── קבועים ───────────────
DATA_FILE    = "schedule.csv"
TEACHERS     = ['דנה', 'לילך', 'רעות', 'ליאת', 'לימור']
PRIORITY_MAP = {'שהייה': 1, 'פרטני': 2}
DAYS         = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']
DAY_OFF      = 'יום חופשי'
COLOR_MAP    = {'שהייה': '#c8e6c9', 'פרטני': '#bbdefb', DAY_OFF: '#e0e0e0'}

# ─────────────── טעינת נתונים ───────────────
@st.cache_data
def load_table() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour']    = df['hour'].astype(int)
    df['subject'] = df['subject'].str.strip()
    return df
df = load_table()

# ─────────────── פונקציות עזר ───────────────
def teacher_matrix(data: pd.DataFrame, name: str) -> pd.DataFrame:
    sub = data[data.teacher == name]
    mat = sub.pivot_table(index='hour', columns='day',
                          values='subject', aggfunc='first')
    return mat.reindex(index=range(1, 7), columns=DAYS)

def color_cells(val: str) -> str:
    for key, color in COLOR_MAP.items():
        if pd.notna(val) and val.startswith(key):
            return f'background-color:{color};'
    return ''

def find_substitutes(absent_teacher: str, day: str):
    ts = df[(df.teacher == absent_teacher) & (df.day == day)]
    if not ts.empty and (ts['subject'] == DAY_OFF).all():
        return "DAY_OFF"
    absent_map = {r.hour: r.subject for _, r in ts.iterrows()}
    results = {}
    for h in range(1, 7):
        subject = absent_map.get(h, "—")
        if subject in ('פרטני', DAY_OFF):
            results[h] = (subject, None)
            continue
        subs = []
        for t in TEACHERS:
            if t == absent_teacher:
                continue
            rec = df[(df.teacher == t) & (df.day == day) & (df.hour == h)]
            if rec.empty:
                continue
            status = rec.iloc[0]['subject']
            if status in PRIORITY_MAP:
                subs.append((PRIORITY_MAP[status], t, status))
        subs.sort(key=lambda x: (x[0], TEACHERS.index(x[1])))
        results[h] = (subject, subs)
    return results

# ─────────────── בחירת מצב ───────────────
MODE = st.radio("בחר/י תצורה:", ["ממשק טפסים", "עוזר אישי (צ'אט)"])

# =================================================
# 1) ממשק טפסים
# =================================================
if MODE == "ממשק טפסים":
    tab_subs, tab_calendar = st.tabs(["🧑‍🏫 חלופות", "📅 לוח שבועי"])

    with tab_subs:
        st.title("🧑‍🏫 בוט חלופות מורים")
        absent_teacher = st.selectbox("בחר/י מורה חסרה", TEACHERS)
        day            = st.selectbox("בחר/י יום בשבוע", DAYS)

        if st.button("מצא חלופות", use_container_width=True):
            res = find_substitutes(absent_teacher, day)
            if res == "DAY_OFF":
                st.info(f"✋ {absent_teacher} בחופש ביום {day} – אין צורך בחלופה.")
            else:
                st.subheader(f"📌 המורה החסרה: {absent_teacher} | יום {day}")
                for h in range(1, 7):
                    subj, subs = res[h]
                    st.markdown(f"**🕐 שעה {h}: {subj}**")
                    if subs is None:
                        st.info("אין צורך בחלופה")
                    elif subs:
                        line = " / ".join(f"{t} ({s})" for _, t, s in subs)
                        st.success(f"חלופה: {line}")
                    else:
                        st.warning("אין חלופה זמינה")

    with tab_calendar:
        st.title("📅 לוח שעות – כל המורות")
        st.markdown("<span style='font-size:0.9rem;'>🟩 שהייה&nbsp;&nbsp;🟦 פרטני&nbsp;&nbsp;⬜ מקצוע&nbsp;&nbsp;⬜ יום חופשי</span>",
                    unsafe_allow_html=True)
        for t in TEACHERS:
            with st.expander(f"📋 {t}", expanded=False):
                styled = teacher_matrix(df, t).style.applymap(color_cells)
                st.dataframe(styled, use_container_width=True, height=240)

# =================================================
# 2) עוזר אישי (צ'אט)  – רענון מיידי
# =================================================
else:
    st.title("🤖 עוזר אישי למציאת מחליפות")

    # אתחול session_state
    if 'history' not in st.session_state:
        st.session_state.history = [("bot", "שלום גלית! אני העוזר האישי שלך למציאת מחליפות 😊\n"
                                           "איזו מורה נעדרת היום?")]
        st.session_state.stage = "teacher"   # teacher → day → done

    # קונסולת צ'אט
    chat_box = st.container()

    def render_chat():
        """מצייר מחדש את כל ההודעות בתוך ה-container."""
        chat_box.empty()
        for role, txt in st.session_state.history:
            with chat_box.chat_message("assistant" if role == "bot" else "user"):
                st.markdown(txt)

    render_chat()

    # ── בחירת מורה ──
    if st.session_state.stage == "teacher":
        teacher = st.selectbox("בחרי מורה חסרה:", [""] + TEACHERS, key="sel_teacher")
        if teacher:
            st.session_state.history.append(("user", teacher))
            st.session_state.teacher = teacher
            st.session_state.history.append(
                ("bot", f"מצוין, בחרנו במורה **{teacher}**.\n"
                        "עכשיו בחרי באיזה יום היא נעדרת:"))
            st.session_state.stage = "day"
            render_chat()

    # ── בחירת יום וחישוב ──
    elif st.session_state.stage == "day":
        day = st.selectbox("בחרי יום:", [""] + DAYS, key="sel_day")
        if day:
            st.session_state.history.append(("user", day))
            res = find_substitutes(st.session_state.teacher, day)

            # בניית תשובה
            if res == "DAY_OFF":
                answer = (f"✋ {st.session_state.teacher} בחופש ביום **{day}** – "
                          "אין צורך במחליפה.")
            else:
                answer = (f"להלן החלופות למורה **{st.session_state.teacher}** "
                          f"ביום **{day}**:\n")
                for h in range(1, 7):
                    subj, subs = res[h]
                    answer += f"\n**🕐 שעה {h}** – {subj}\n"
                    if subs is None:
                        answer += "▪️ אין צורך בחלופה\n"
                    elif subs:
                        line = " / ".join(f\"{t} ({s})\" for _, t, s in subs)
                        answer += f"▪️ חלופה: {line}\n"
                    else:
                        answer += "▪️ אין חלופה זמינה\n"

            st.session_state.history.append(("bot", answer))
            st.session_state.history.append(("bot", "אם תרצי לבדוק שוב, בחרי מורה אחרת מהתיבה למעלה 😉"))

            # איפוס בחירות
            st.session_state.stage = "teacher"
            st.session_state.pop('sel_teacher', None)
            st.session_state.pop('sel_day', None)
            render_chat()
