import streamlit as st, pandas as pd, time

# ───── הגדרות עמוד + CSS ─────
st.set_page_config(page_title="צמרובוט – העוזר האישי שלי", layout="centered")
st.markdown("""
<style>
h1{font-size:1.8rem;font-weight:800;margin-bottom:0.4rem;}
.chat-msg{background:#f1f4f8;border-radius:14px;padding:0.7rem 1rem;margin:0.25rem 0;}
.chat-user{background:#d9e8ff;}
button,select,input,label{font-size:1rem;}
section[data-testid="stSidebar"]{display:none;}
</style>
""",unsafe_allow_html=True)

# ───── נתונים וקבועים ─────
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
            stat=r.iloc[0]['subject']
            if stat in PRIORITY:
                opts.append((PRIORITY[stat],t,stat))
        opts.sort(key=lambda x:(x[0],TEACHERS.index(x[1])))
        res[h]=(subj,opts)
    return res

# ───── צמרובוט ─────
st.title("🤖 צמרובוט – העוזר האישי שלי")
GREET="שלום גלית! אני צמרובוט, העוזר האישי שלך 😊\nבמה אני יכול לעזור לך היום?"

if 'chat' not in st.session_state:
    st.session_state.chat=[("bot",GREET)]
    st.session_state.stage="teacher"
    st.session_state.teacher=""
    st.session_state.day=""
    st.session_state.start=1
    # מפתחות וידג׳ט בכדי למנוע Missing key
    st.session_state.sel_teacher=""
    st.session_state.sel_day=""
    st.session_state.sel_scope=""
    st.session_state.sel_hr=""

def bot(m):  st.session_state.chat.append(("bot",m))
def usr(m):  st.session_state.chat.append(("user",m))

def redraw():
    container.empty()
    for role,msg in st.session_state.chat:
        cls="chat-msg chat-user" if role=="user" else "chat-msg"
        with container: st.markdown(f"<div class='{cls}'>{msg}</div>",unsafe_allow_html=True)

def reset():
    st.session_state.stage="teacher"
    # במקום pop – מאפסים לערך ריק
    st.session_state.sel_teacher=""
    st.session_state.sel_day=""
    st.session_state.sel_scope=""
    st.session_state.sel_hr=""
    st.session_state.teacher=""
    st.session_state.day=""
    st.session_state.start=1

container=st.container(); redraw()

# ----- callbacks -----
def cb_teacher():
    t=st.session_state.sel_teacher
    if t:
        usr(t); st.session_state.teacher=t
        st.session_state.stage="day"
        bot(f"מעולה, בחרנו במורה **{t}**.\nלאיזה יום היא נעדרת?")
        redraw()

def cb_day():
    d=st.session_state.sel_day
    if d:
        usr(d); st.session_state.day=d
        st.session_state.stage="scope"
        bot("היא נעדרת יום שלם או החל משעה מסוימת?")
        redraw()

def cb_scope():
    scope=st.session_state.sel_scope
    if scope not in ("יום שלם","מ-שעה"): return
    if scope=="יום שלם":
        st.session_state.start=1; run()
    else:
        bot("בחרי שעת התחלה (1-6):"); redraw()

def cb_hr():
    hr=st.session_state.sel_hr
    if hr:
        usr(f"מהשעה {hr}")
        st.session_state.start=int(hr)
        run()

def run():
    with st.spinner("צמרובוט חושב…"): time.sleep(1.4)
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

# ----- UI -----
if st.session_state.stage=="teacher":
    st.selectbox("בחרי מורה חסרה:",[""]+TEACHERS,
                 key="sel_teacher",on_change=cb_teacher)
elif st.session_state.stage=="day":
    st.selectbox("בחרי יום:",[""]+DAYS,
                 key="sel_day",on_change=cb_day)
elif st.session_state.stage=="scope":
    st.radio("היעדרות:",("", "יום שלם","מ-שעה"),
             key="sel_scope",on_change=cb_scope)
    if st.session_state.sel_scope=="מ-שעה":
        st.selectbox("שעת התחלה (1-6):",[""]+[str(i) for i in range(1,7)],
                     key="sel_hr",on_change=cb_hr)

# ----- כפתור ניקוי -----
st.divider()
if st.button("🗑️ נקה מסך"):
    st.session_state.chat=[("bot",GREET)]
    reset(); redraw()
