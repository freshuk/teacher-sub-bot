import streamlit as st
import pandas as pd
import time

# ─────────────────── הגדרות עמוד + CSS ───────────────────
st.set_page_config(page_title="צמרובוט – העוזר האישי שלי", layout="centered")
st.markdown("""
<style>
h1{font-size:1.7rem;font-weight:800;margin-bottom:0.3rem;}
.chat-msg{background:#f1f3f6;border-radius:14px;padding:0.65rem 0.9rem;margin:0.25rem 0;}
.chat-user{background:#d1e7ff;}
button,select,input,textarea{font-size:1rem;}
section[data-testid="stSidebar"]{display:none;}
</style>
""", unsafe_allow_html=True)

# ─────────────────── נתונים וקבועים ──────────────────────
DATA_FILE = "schedule.csv"
TEACHERS  = ['דנה', 'לילך', 'רעות', 'ליאת', 'לימור']
DAYS      = ['ראשון','שני','שלישי','רביעי','חמישי','שישי']
DAY_OFF   = 'יום חופשי'
PRIORITY  = {'שהייה':1,'פרטני':2}

@st.cache_data
def load_table():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour'] = df['hour'].astype(int)
    df['subject'] = df['subject'].str.strip()
    return df
df = load_table()

# ─────────────────── חישוב חלופות ───────────────────────
def find_substitutes(absent_teacher: str, day: str, start_hour: int):
    rows = df[(df.teacher == absent_teacher) & (df.day == day)]
    if not rows.empty and (rows.subject == DAY_OFF).all():
        return "DAY_OFF"
    absent = {r.hour: r.subject for _, r in rows.iterrows()}
    res = {}
    for h in range(start_hour, 7):
        subj = absent.get(h, "—")
        if subj in ('פרטני', DAY_OFF):
            res[h] = (subj, None)
            continue
        opts = []
        for t in TEACHERS:
            if t == absent_teacher:
                continue
            r = df[(df.teacher == t) & (df.day == day) & (df.hour == h)]
            if r.empty:
                continue
            status = r.iloc[0].subject
            if status in PRIORITY:
                opts.append((PRIORITY[status], t, status))
        opts.sort(key=lambda x: (x[0], TEACHERS.index(x[1])))
        res[h] = (subj, opts)
    return res

# ─────────────────── צמרובוט – עוזר אישי ─────────────────
st.title("🤖 צמרובוט – העוזר האישי שלי")

GREETING = "שלום גלית! אני צמרובוט, העוזר האישי שלך 😊\nבמה אני יכול לעזור לך היום?"

# --------------- Session init ---------------
if 'chat' not in st.session_state:
    st.session_state.chat   = []
    st.session_state.stage  = "teacher"
    st.session_state.teacher= ""
    st.session_state.day    = ""
    st.session_state.scope  = "יום שלם"
    st.session_state.start  = 1
    st.session_state.greeted = False

# ברכה יחידה
if not st.session_state.greeted:
    st.session_state.chat.append(("bot", GREETING))
    st.session_state.greeted = True

# ---------- פונקציות עזר לצ’אט ----------
def bot(msg):
    st.session_state.chat.append(("bot", msg))
def user(msg):
    st.session_state.chat.append(("user", msg))

# ---------- ציור צ’אט ----------
chat_area = st.container()
def redraw():
    chat_area.empty()
    for role, txt in st.session_state.chat:
        css = "chat-msg chat-user" if role=="user" else "chat-msg"
        with chat_area:
            st.markdown(f"<div class='{css}'>{txt}</div>", unsafe_allow_html=True)
redraw()

# ---------- Callbacks ----------
def on_choose_teacher():
    t = st.session_state.sel_teacher
    if t:
        user(t)
        st.session_state.teacher = t
        st.session_state.stage   = "day"
        bot("מעולה, בחרנו במורה **{}**.\nלאיזה יום היא נעדרת?".format(t))
        redraw()

def on_choose_day():
    d = st.session_state.sel_day
    if d:
        user(d)
        st.session_state.day  = d
        st.session_state.stage= "scope"
        bot("האם היא נעדרת **יום שלם** או החל **משעה מסוימת**?")
        redraw()

def on_choose_scope():
    scope = st.session_state.sel_scope
    st.session_state.scope = scope
    if scope == "יום שלם":
        st.session_state.start = 1
        process()
    else:
        redraw()   # מצייר Select שעה

def on_choose_hour():
    hr = st.session_state.sel_hr
    if hr:
        st.session_state.start = int(hr)
        user(f"מהשעה {hr}")
        process()

def process():
    with st.spinner("צמרובוט חושב…"):
        time.sleep(1.8)
        res = find_substitutes(st.session_state.teacher,
                               st.session_state.day,
                               st.session_state.start)
    if res == "DAY_OFF":
        bot(f"✋ {st.session_state.teacher} בחופש ביום **{st.session_state.day}** – אין צורך בחלופה.")
    else:
        ans = f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{st.session_state.day}**:\n"
        for h in range(st.session_state.start, 7):
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
    bot("מקווה שעזרתי לך! את צריכה פתרונות נוספים?\nשיהיה לך המשך יום נפלא 🌸")

    # reset לשאילתה הבאה
    st.session_state.stage   = "teacher"
    st.session_state.sel_teacher = ""
    st.session_state.sel_day     = ""
    st.session_state.sel_scope   = "יום שלם"
    st.session_state.sel_hr      = ""
    redraw()

# ---------- UI דינמי ----------
if st.session_state.stage == "teacher":
    st.selectbox("בחרי מורה חסרה:",
                 [""] + TEACHERS,
                 key="sel_teacher",
                 on_change=on_choose_teacher)

elif st.session_state.stage == "day":
    st.selectbox("בחרי יום:",
                 [""] + DAYS,
                 key="sel_day",
                 on_change=on_choose_day)

elif st.session_state.stage == "scope":
    st.radio("היעדרות:", ["יום שלם", "מ-שעה"],
             key="sel_scope",
             on_change=on_choose_scope)
    if st.session_state.sel_scope == "מ-שעה":
        st.selectbox("בחרי שעת התחלה (1-6):",
                     [""] + [str(i) for i in range(1, 7)],
                     key="sel_hr",
                     on_change=on_choose_hour)

# =========================================================
#  ☑ מצב הטפסים הישן נשמר למטה כ-Comment – להחזרה מהירה
# =========================================================
"""
### מצב טפסים היסטורי
# def forms_mode():
#     ...
"""
