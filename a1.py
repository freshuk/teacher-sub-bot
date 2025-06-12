import streamlit as st
import pandas as pd
import time
from pathlib import Path
import streamlit.components.v1 as components

# ───────── הגדרות בסיס + CSS ─────────
st.set_page_config(page_title="צמרובוט – העוזר האישי שלי", layout="centered")
st.markdown("""
<style>
h1{font-size:1.8rem;font-weight:800;margin-bottom:0.4rem;display:inline;}
.chat-msg{background:#f5f8ff;border-radius:14px;padding:0.7rem 1rem;margin:0.3rem 0;}
.chat-user{background:#d2e1ff;}
button,select,input,label{font-size:1rem;}
section[data-testid="stSidebar"]{display:none;}
</style>
""", unsafe_allow_html=True)

# ───────── אייקון קבוע ─────────
if Path("bot_calendar.png").exists():
    c1, c2 = st.columns([1, 9])
    with c1: 
        st.image("bot_calendar.png", width=60)
    with c2: 
        st.markdown("### צמרובוט – העוזר האישי שלי")
else:
    st.title("🤖 צמרובוט – העוזר האישי שלי")

# ───────── נתונים וקבועים ─────────
DATA = "schedule.csv"
TEACHERS = ['דנה', 'לילך', 'רעות', 'ליאת', 'לימור']
DAYS = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']
DAY_OFF = 'יום חופשי'
PRIORITY = {'שהייה': 1, 'פרטני': 2}

@st.cache_data
def load_data():
    d = pd.read_csv(DATA, dtype=str)
    d['hour'] = d['hour'].astype(int)
    return d

df = load_data()

# ───────── init state ─────────
if "chat" not in st.session_state:
    st.session_state.chat = [("bot", "שלום גלית! אני צמרובוט 😊 במה אני יכול לעזור לך היום?")]
    st.session_state.stage = "teacher"
    st.session_state.done_teacher = ""
    st.session_state.done_day = ""

# ───────── chat helpers ─────────
def add(role, msg):
    if not st.session_state.chat or st.session_state.chat[-1] != (role, msg):
        st.session_state.chat.append((role, msg))

def render_chat():
    for r, m in st.session_state.chat:
        cls = "chat-msg chat-user" if r == "user" else "chat-msg"
        st.markdown(f"<div class='{cls}'>{m}</div>", unsafe_allow_html=True)

# ───────── substitute fn ─────────
def find_subs(t, day, start):
    rows = df[(df.teacher == t) & (df.day == day)]
    if not rows.empty and (rows.subject == DAY_OFF).all(): 
        return "DAY_OFF"
    
    absmap = {r.hour: r.subject for _, r in rows.iterrows()}
    out = {}
    
    for h in range(start, 7):
        subj = absmap.get(h, '—')
        if subj in ('פרטני', DAY_OFF): 
            out[h] = (subj, None)
            continue
            
        opts = []
        for cand in TEACHERS:
            if cand == t: 
                continue
            rec = df[(df.teacher == cand) & (df.day == day) & (df.hour == h)]
            if rec.empty: 
                continue
            stat = rec.iloc[0].subject
            if stat in PRIORITY: 
                opts.append((PRIORITY[stat], cand, stat))
                
        opts.sort(key=lambda x: (x[0], TEACHERS.index(x[1])))
        out[h] = (subj, opts)
    
    return out

# ───────── callbacks ─────────
def choose_teacher():
    t = st.session_state.sel_teacher
    if t and t != st.session_state.done_teacher:
        add("user", t)
        st.session_state.teacher = t
        st.session_state.stage = "day"
        add("bot", f"מעולה, בחרנו במורה **{t}**.\nלאיזה יום היא נעדרת?")
        st.session_state.done_teacher = t
        st.session_state.sel_teacher = ""

def choose_day():
    d = st.session_state.sel_day
    if d and d != st.session_state.done_day:
        add("user", d)
        st.session_state.day = d
        st.session_state.stage = "scope"
        add("bot", "היא נעדרת **יום שלם** או **מ-שעה**?")
        st.session_state.done_day = d
        st.session_state.sel_day = ""

def choose_scope():
    sc = st.session_state.sel_scope
    if sc == "יום שלם":
        add("user", "יום שלם")
        st.session_state.start = 1
        st.session_state.sel_scope = ""
        calculate()
    elif sc == "מ-שעה":
        add("user", "מ-שעה")
        st.session_state.stage = "hour"
        add("bot", "בחרי שעת התחלה (1-6):")
        st.session_state.sel_scope = ""

def choose_hour():
    hr = st.session_state.sel_hr
    if hr:
        add("user", f"מהשעה {hr}")
        st.session_state.start = int(hr)
        st.session_state.sel_hr = ""
        calculate()

def calculate():
    with st.spinner("צמרובוט חושב…"): 
        time.sleep(1.1)
    
    res = find_subs(st.session_state.teacher, st.session_state.day, st.session_state.start)
    
    if res == "DAY_OFF":
        add("bot", f"✋ {st.session_state.teacher} בחופש ביום **{st.session_state.day}** – אין צורך בחלופה.")
    else:
        txt = f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{st.session_state.day}**:\n"
        for h in range(st.session_state.start, 7):
            subj, subs = res[h]
            txt += f"\n**🕐 שעה {h}** – {subj}\n"
            if subs is None: 
                txt += "▪️ אין צורך בחלופה\n"
            elif subs: 
                txt += "▪️ חלופה: " + " / ".join(f"{t} ({s})" for _, t, s in subs) + "\n"
            else: 
                txt += "▪️ אין חלופה זמינה\n"
        add("bot", txt)
    
    add("bot", "שמחתי לעזור! תמיד כאן לשירותך, צמרובוט 🌸")
    st.session_state.stage = "teacher"
    st.session_state.done_teacher = ""
    st.session_state.done_day = ""

# ───────── יצירת containers ─────────
# יצירת container ראשי
main_container = st.container()

with main_container:
    # Container לצ'אט
    chat_container = st.empty()
    
    # Container ל-widgets
    widget_container = st.empty()
    
    # רינדור הצ'אט
    with chat_container.container():
        render_chat()
    
    # רינדור ה-widgets הדינמיים
    with widget_container.container():
        if st.session_state.stage == "teacher":
            st.selectbox("בחרי מורה חסרה:", [""] + TEACHERS, 
                        key="sel_teacher", on_change=choose_teacher)
                        
        elif st.session_state.stage == "day":
            st.selectbox("בחרי יום:", [""] + DAYS, 
                        key="sel_day", on_change=choose_day)
                        
        elif st.session_state.stage == "scope":
            st.radio("היעדרות:", ("", "יום שלם", "מ-שעה"), 
                    key="sel_scope", on_change=choose_scope)
                    
        elif st.session_state.stage == "hour":
            st.selectbox("שעת התחלה (1-6):", [""] + [str(i) for i in range(1, 7)],
                        key="sel_hr", on_change=choose_hour)

# ───────── ניקוי מסך ─────────
st.divider()
if st.button("🗑️ נקה מסך"):
    st.session_state.clear()
    st.rerun()

# ───────── גלילה אוטומטית גלובלית ─────────
components.html("<script>window.scrollTo(0, document.body.scrollHeight);</script>", height=0)