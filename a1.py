import streamlit as st
import pandas as pd
import time

# ───────── הגדרות עמוד + CSS ─────────
st.set_page_config(page_title="צמרובוט – עוזר חלופות", layout="centered")
st.markdown("""
<style>
h1{font-size:1.7rem;font-weight:800;}
button,select,input{font-size:1rem;}
.chat-bubble{background:#f1f3f6;border-radius:12px;padding:0.6rem 0.9rem;margin:0.2rem 0;}
.user-bubble{background:#d1e7ff;}
section[data-testid="stSidebar"]{display:none;}
</style>
""",unsafe_allow_html=True)

# ───────── נתונים וקבועים ─────────
DATA_FILE="schedule.csv"
TEACHERS  = ['דנה','לילך','רעות','ליאת','לימור']
DAYS      = ['ראשון','שני','שלישי','רביעי','חמישי','שישי']
DAY_OFF   = 'יום חופשי'
PRIORITY  = {'שהייה':1,'פרטני':2}

@st.cache_data
def load_df():
    df=pd.read_csv(DATA_FILE,dtype=str)
    df['hour']=df['hour'].astype(int)
    df['subject']=df['subject'].str.strip()
    return df
df=load_df()

def find_subs(tchr,day,start_hr):
    rows=df[(df.teacher==tchr)&(df.day==day)]
    if not rows.empty and (rows.subject==DAY_OFF).all():
        return "DAY_OFF"
    absent={r.hour:r.subject for _,r in rows.iterrows()}
    out={}
    for h in range(start_hr,7):
        subj=absent.get(h,'—')
        if subj in ('פרטני',DAY_OFF):
            out[h]=(subj,None); continue
        opts=[]
        for t in TEACHERS:
            if t==tchr: continue
            r=df[(df.teacher==t)&(df.day==day)&(df.hour==h)]
            if r.empty: continue
            stat=r.iloc[0].subject
            if stat in PRIORITY:
                opts.append((PRIORITY[stat],t,stat))
        opts.sort(key=lambda x:(x[0],TEACHERS.index(x[1])))
        out[h]=(subj,opts)
    return out

# ────────────────────────────────────────────────
#   (מצב טפסים הישן – אם תרצי להחזיר, הסירי את ה‑comment)
# ------------------------------------------------
# def forms_mode():
#     ...
# ------------------------------------------------

# ───────── צמרובוט – עוזר אישי (צ'אט) ─────────
st.title("🤖 צמרובוט – העוזר האישי שלי")

GREET = "שלום גלית! אני צמרובוט, העוזר האישי שלך 😊\nבמה אני יכול לעזור לך היום?"
if 'chat' not in st.session_state:
    st.session_state.chat=[("bot",GREET)]
    st.session_state.stage="teacher"

def bot(txt):
    st.session_state.chat.append(("bot",txt))
def user(txt):
    st.session_state.chat.append(("user",txt))

# --- הצגת צ'אט ---
msg_area=st.container()
def redraw():
    msg_area.empty()
    for role,txt in st.session_state.chat:
        with msg_area.chat_message("assistant" if role=="bot" else "user"):
            st.markdown(txt,unsafe_allow_html=True)
redraw()

# --- callbacks ---
def choose_teacher():
    t=st.session_state.sel_teacher
    if t:
        user(t)
        st.session_state.teacher=t
        st.session_state.stage="day"
        bot("בחרת **{}**.\nלאיזה יום מדובר?".format(t))
        redraw()

def choose_day():
    d=st.session_state.sel_day
    if d:
        user(d)
        st.session_state.day=d
        st.session_state.stage="scope"
        bot("האם המורה נעדרת כל היום או החל משעה מסוימת?")
        redraw()

def choose_scope():
    scope=st.session_state.abs_scope
    st.session_state.scope=scope
    if scope=="יום שלם":
        start_hr=1
        process(start_hr)
    # אם בחרו 'מ‑שעה' – תוצג מיד Select נוסף לבחירת שעה

def choose_start_hour():
    hr=st.session_state.sel_hour
    if hr:
        process(int(hr))

def process(start_hr:int):
    with st.spinner("צמרובוט חושב…"):
        time.sleep(2)           # סימולציית דיבור
        res=find_subs(st.session_state.teacher,st.session_state.day,start_hr)
    if res=="DAY_OFF":
        bot(f"✋ {st.session_state.teacher} בחופש ביום **{st.session_state.day}** – "
            "אין צורך בחלופה.")
    else:
        ans=f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{st.session_state.day}**:\n"
        for h in range(start_hr,7):
            subj,subs=res[h]
            ans+=f"\n**🕐 שעה {h}** – {subj}\n"
            if subs is None:
                ans+="▪️ אין צורך בחלופה\n"
            elif subs:
                line=" / ".join(f"{t} ({s})" for _,t,s in subs)
                ans+=f"▪️ חלופה: {line}\n"
            else:
                ans+="▪️ אין חלופה זמינה\n"
        bot(ans)
    bot("מקווה שעזרתי לך! צריכה פתרונות נוספים? שיהיה לך המשך יום נפלא 🌸")
    # reset
    st.session_state.stage="teacher"
    st.session_state.sel_teacher=""
    st.session_state.sel_day=""
    st.session_state.abs_scope=""
    st.session_state.sel_hour=""
    redraw()

# --- UI דינמי ---
if st.session_state.stage=="teacher":
    st.selectbox("בחרי מורה חסרה:",[""]+TEACHERS,
                 key="sel_teacher", on_change=choose_teacher)

elif st.session_state.stage=="day":
    st.selectbox("בחרי יום:",[""]+DAYS,
                 key="sel_day", on_change=choose_day)

elif st.session_state.stage=="scope":
    st.radio("היעדרות:",["יום שלם","מ‑שעה"],
             key="abs_scope", on_change=choose_scope)
    if st.session_state.get("abs_scope")=="מ‑שעה":
        st.selectbox("בחרי שעת התחלה (1‑6):",
                     [""]+[str(i) for i in range(1,7)],
                     key="sel_hour", on_change=choose_start_hour)
