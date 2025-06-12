import streamlit as st
import pandas as pd
import time
from pathlib import Path

# ───────── הגדרות עמוד + CSS ─────────
st.set_page_config(page_title="צמרובוט – העוזר האישי שלי", layout="centered")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Heebo', sans-serif !important;
}

h1{font-size:1.8rem;font-weight:800;margin-bottom:0.4rem;display:inline;}

.chat-msg{
    background: linear-gradient(135deg, #f8faff 0%, #ecf2ff 100%);
    border:1px solid #e1e8f7;
    border-radius:18px;
    padding:1rem 1.2rem;
    margin:0.8rem 0;
    box-shadow: 0 2px 12px rgba(102, 126, 234, 0.1);
    animation: fadeIn 0.5s ease-out;
}

.chat-user{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    text-align: right;
    font-weight: 500;
}

.thinking-indicator {
    background: rgba(102, 126, 234, 0.08);
    border: 1px solid rgba(102, 126, 234, 0.2);
    border-radius: 12px;
    padding: 1rem;
    margin: 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #667eea;
    font-weight: 500;
}

.typing-dots {
    display: flex;
    gap: 4px;
}

.typing-dots span {
    width: 6px;
    height: 6px;
    background: #667eea;
    border-radius: 50%;
    animation: typing 1.4s infinite;
}

.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-10px); opacity: 1; }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

button,select,input,label{font-size:1rem;}
section[data-testid="stSidebar"]{display:none;}

.stSelectbox > div > div {
    border: 2px solid #e1e8f7;
    border-radius: 12px;
    transition: border-color 0.3s ease;
}

.stSelectbox > div > div:hover {
    border-color: #667eea;
}

.stButton > button {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white !important;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.2);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(255, 107, 107, 0.3);
}
</style>
""", unsafe_allow_html=True)

# ───────── אייקון בוט ─────────
ICON = Path("bot_calendar.png")          # ודא שהקובץ הזה קיים בריפו
if ICON.exists():
    ic, ttl = st.columns([1,9])
    with ic:  st.image(str(ICON), width=64)
    with ttl: st.markdown("### צמרובוט – העוזר האישי שלי")
else:
    st.title("🤖 צמרובוט – העוזר האישי שלי")

# ───────── נתונים וקבועים ─────────
DATA_FILE="schedule.csv"
TEACHERS=['דנה','לילך','רעות','ליאת','לימור']
DAYS=['ראשון','שני','שלישי','רביעי','חמישי','שישי']
DAY_OFF='יום חופשי'
PRIORITY={'שהייה':1,'פרטני':2}

@st.cache_data
def load_df():
    df=pd.read_csv(DATA_FILE,dtype=str)
    df['hour']=df['hour'].astype(int)
    df['subject']=df['subject'].str.strip()
    return df
df=load_df()

def get_subs(teacher, day, start_hr):
    rows=df[(df.teacher==teacher)&(df.day==day)]
    if not rows.empty and (rows.subject==DAY_OFF).all():
        return "DAY_OFF"
    absent={r.hour:r.subject for _,r in rows.iterrows()}
    res={}
    for h in range(start_hr,7):
        subj=absent.get(h,'—')
        if subj in ('פרטני',DAY_OFF):
            res[h]=(subj,None); continue
        opts=[]
        for t in TEACHERS:
            if t==teacher: continue
            r=df[(df.teacher==t)&(df.day==day)&(df.hour==h)]
            if r.empty: continue
            stat=r.iloc[0].subject
            if stat in PRIORITY:
                opts.append((PRIORITY[stat],t,stat))
        opts.sort(key=lambda x:(x[0],TEACHERS.index(x[1])))
        res[h]=(subj,opts)
    return res

# ───────── צ'אט ─────────
GREET="שלום גלית! אני צמרובוט, העוזר האישי שלך 😊\nבמה אני יכול לעזור לך היום?"
if 'chat' not in st.session_state:
    st.session_state.chat=[("bot",GREET)]
    st.session_state.stage="teacher"
    st.session_state.teacher=st.session_state.day=""
    st.session_state.start=1
    st.session_state.sel_teacher=st.session_state.sel_day=st.session_state.sel_scope=st.session_state.sel_hr=""

def bot(m):  st.session_state.chat.append(("bot",m))
def usr(m):  st.session_state.chat.append(("user",m))

def show_thinking():
    thinking_placeholder = st.empty()
    thinking_placeholder.markdown("""
    <div class="thinking-indicator">
        🤖 צמרובוט חושב
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(1.5)
    thinking_placeholder.empty()

def redraw():
    box.empty()
    for role,msg in st.session_state.chat:
        cls="chat-msg chat-user" if role=="user" else "chat-msg"
        with box:
            st.markdown(f"<div class='{cls}'>{msg}</div>",unsafe_allow_html=True)

box = st.container()
redraw()

# ---------- callbacks ----------
def cb_teacher():
    t=st.session_state.sel_teacher
    if t:
        usr(t); st.session_state.teacher=t; st.session_state.stage="day"
        show_thinking()
        bot(f"מעולה, בחרנו במורה **{t}**.\nלאיזה יום היא נעדרת?")
        redraw()

def cb_day():
    d=st.session_state.sel_day
    if d:
        usr(d); st.session_state.day=d; st.session_state.stage="scope"
        show_thinking()
        bot("היא נעדרת **יום שלם** או **מ-שעה**?")
        redraw()

def cb_scope():
    s=st.session_state.sel_scope
    if s=="יום שלם":
        usr("יום שלם")
        st.session_state.start=1; run()
    elif s=="מ-שעה":
        usr("מ-שעה")
        show_thinking()
        bot("בחרי שעת התחלה (1-6):"); redraw()

def cb_hr():
    hr=st.session_state.sel_hr
    if hr:
        usr(f"מהשעה {hr}"); st.session_state.start=int(hr); run()

def run():
    show_thinking()
    res=get_subs(st.session_state.teacher, st.session_state.day, st.session_state.start)
    if res=="DAY_OFF":
        bot(f"✋ {st.session_state.teacher} בחופש ביום **{st.session_state.day}** – אין צורך בחלופה.")
    else:
        ans=f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{st.session_state.day}**:\n"
        for h in range(st.session_state.start,7):
            subj,subs=res[h]
            ans+=f"\n**🕐 שעה {h}** – {subj}\n"
            if subs is None:
                ans+="▪️ אין צורך בחלופה\n"
            elif subs:
                ans+="▪️ חלופה: "+" / ".join(f"{t} ({s})" for _,t,s in subs)+"\n"
            else:
                ans+="▪️ אין חלופה זמינה\n"
        bot(ans)
    bot("שמחתי לעזור! תמיד כאן לשירותך, צמרובוט 🌸")
    reset(); redraw()

def reset():
    st.session_state.stage="teacher"
    st.session_state.sel_teacher=st.session_state.sel_day=st.session_state.sel_scope=st.session_state.sel_hr=""

# ---------- UI ----------
if st.session_state.stage=="teacher":
    st.selectbox("👩‍🏫 בחרי מורה חסרה:",[""]+TEACHERS,
                 key="sel_teacher",on_change=cb_teacher)
elif st.session_state.stage=="day":
    st.selectbox("📅 בחרי יום:",[""]+DAYS,
                 key="sel_day",on_change=cb_day)
elif st.session_state.stage=="scope":
    st.radio("⏰ היעדרות:",("", "יום שלם","מ-שעה"),
             key="sel_scope",on_change=cb_scope)
    if st.session_state.sel_scope=="מ-שעה":
        st.selectbox("🕐 שעת התחלה (1-6):",[""]+[str(i) for i in range(1,7)],
                     key="sel_hr",on_change=cb_hr)

# ---------- כפתור ניקוי ----------
st.divider()
if st.button("🗑️ נקה מסך"):
    st.session_state.clear()  # איפוס מלא
    st.rerun()                # רענון חוקי – לא בתוך callback