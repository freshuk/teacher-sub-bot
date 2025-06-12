import streamlit as st
import pandas as pd
import numpy as np

# ───────── הגדרות עמוד + CSS ─────────
st.set_page_config(page_title="בוט חלופות", layout="centered")
st.markdown("""
<style>
h1 {font-size:1.5rem;}
button, select, input {font-size:1rem;}
section[data-testid="stSidebar"] {display:none;}
</style>
""", unsafe_allow_html=True)

# ───────── קבועים ─────────
DATA_FILE    = "schedule.csv"
TEACHERS     = ['דנה', 'לילך', 'רעות', 'ליאת', 'לימור']
PRIORITY_MAP = {'שהייה': 1, 'פרטני': 2}
DAYS         = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']
DAY_OFF      = 'יום חופשי'
COLOR_MAP    = {'שהייה':'#c8e6c9', 'פרטני':'#bbdefb', DAY_OFF:'#e0e0e0'}

@st.cache_data
def load_table():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour']    = df['hour'].astype(int)
    df['subject'] = df['subject'].str.strip()
    return df
df = load_table()

def find_substitutes(absent_teacher, day):
    ts = df[(df.teacher == absent_teacher) & (df.day == day)]
    if not ts.empty and (ts['subject'] == DAY_OFF).all():
        return "DAY_OFF"
    res={}
    absent_map={r.hour:r.subject for _,r in ts.iterrows()}
    for h in range(1,7):
        subj = absent_map.get(h,"—")
        if subj in ('פרטני',DAY_OFF):
            res[h]=(subj,None); continue
        subs=[]
        for t in TEACHERS:
            if t==absent_teacher: continue
            rec=df[(df.teacher==t)&(df.day==day)&(df.hour==h)]
            if rec.empty: continue
            status=rec.iloc[0]['subject']
            if status in PRIORITY_MAP:
                subs.append((PRIORITY_MAP[status],t,status))
        subs.sort(key=lambda x:(x[0], TEACHERS.index(x[1])))
        res[h]=(subj,subs)
    return res

# ───────── בחירת תצורה ─────────
MODE = st.radio("בחר/י תצורה:", ["ממשק טפסים", "עוזר אישי (צ'אט)"])

# (קוד “ממשק טפסים” נשאר כבעבר – לא שונה, אז קיצרתי כאן)

# =================================================
# 2) עוזר אישי (צ'אט)
# =================================================
if MODE == "עוזר אישי (צ'אט)":
    st.title("🤖 עוזר אישי למציאת מחליפות")

    if 'hist' not in st.session_state:
        st.session_state.hist=[
            ("bot","שלום גלית! אני העוזר האישי שלך למציאת מחליפות 😊\nאיזו מורה נעדרת היום?")
        ]
        st.session_state.stage="teacher"

    def bot(msg):  st.session_state.hist.append(("bot",msg))
    def user(msg): st.session_state.hist.append(("user",msg))

    chat = st.container()
    def render():
        chat.empty()
        for role,msg in st.session_state.hist:
            with chat.chat_message("assistant" if role=="bot" else "user"):
                st.markdown(msg)
    render()

    # ── בחירת מורה ──
    if st.session_state.stage=="teacher":
        teach = st.selectbox("בחרי מורה חסרה:", [""]+TEACHERS, key="sel_t")
        if teach:
            user(teach)
            st.session_state.teacher = teach
            bot(f"מצוין, בחרנו במורה **{teach}**.\nעכשיו בחרי באיזה יום היא נעדרת:")
            st.session_state.stage = "day"
            st.experimental_rerun()

    # ── בחירת יום וחישוב ──
    if st.session_state.stage=="day":
        day = st.selectbox("בחרי יום:", [""]+DAYS, key="sel_d")
        if day:
            user(day)
            res = find_substitutes(st.session_state.teacher, day)
            if res == "DAY_OFF":
                ans = f"✋ {st.session_state.teacher} בחופש ביום **{day}** – אין צורך במחליפה."
            else:
                ans = f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{day}**:\n"
                for h in range(1,7):
                    subj, subs = res[h]
                    ans += f"\n**🕐 שעה {h}** – {subj}\n"
                    if subs is None:
                        ans += "▪️ אין צורך בחלופה\n"
                    elif subs:
                        line = " / ".join(f"{t} ({s})" for _,t,s in subs)
                        ans += f"▪️ חלופה: {line}\n"
                    else:
                        ans += "▪️ אין חלופה זמינה\n"
            bot(ans)
            bot("אם תרצי לבדוק שוב, בחרי מורה אחרת מהתיבה למעלה 😊")

            # reset
            st.session_state.stage = "teacher"
            for k in ('sel_t','sel_d'):
                st.session_state.pop(k, None)
            render()
            # 🔄 רענון ועצירה: ה-UI יתאפס לשדה 'מורה'
            st.experimental_rerun()     # 🔄
            st.stop()                   # 🔄
