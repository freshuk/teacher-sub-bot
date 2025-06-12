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

# ───────── נתונים וקבועים ─────────
DATA_FILE="schedule.csv"
TEACHERS  = ['דנה','לילך','רעות','ליאת','לימור']
DAYS      = ['ראשון','שני','שלישי','רביעי','חמישי','שישי']
DAY_OFF   = 'יום חופשי'
PRIORITY  = {'שהייה':1,'פרטני':2}
COLOR     = {'שהייה':'#c8e6c9','פרטני':'#bbdefb',DAY_OFF:'#e0e0e0'}

@st.cache_data
def load_df():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour']=df['hour'].astype(int)
    df['subject']=df['subject'].str.strip()
    return df
df = load_df()

# ───────── פונקציות עזר ─────────
def find_subs(tchr,day):
    rows=df[(df.teacher==tchr)&(df.day==day)]
    if not rows.empty and (rows.subject==DAY_OFF).all():
        return "DAY_OFF"
    absent={r.hour:r.subject for _,r in rows.iterrows()}
    out={}
    for h in range(1,7):
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

def matrix(name):
    wide=df[df.teacher==name].pivot_table(index='hour',columns='day',
                                          values='subject',aggfunc='first')
    return wide.reindex(index=range(1,7),columns=DAYS)

def shade(v):
    for k,c in COLOR.items():
        if pd.notna(v) and v.startswith(k): return f'background-color:{c}'
    return ''

# ───────── בחירת תצורה ─────────
MODE=st.radio("בחר/י תצורה:",["ממשק טפסים","עוזר אישי (צ'אט)"])

# =================================================
# 1) ממשק טפסים + לוח שבועי
# =================================================
if MODE=="ממשק טפסים":
    tab_sub,tab_cal=st.tabs(["🧑‍🏫 חלופות","📅 לוח שבועי"])

    with tab_sub:
        st.title("🧑‍🏫 בוט חלופות מורים")
        t_sel=st.selectbox("מורה חסרה",TEACHERS)
        d_sel=st.selectbox("יום בשבוע",DAYS)
        if st.button("מצא חלופות",use_container_width=True):
            res=find_subs(t_sel,d_sel)
            if res=="DAY_OFF":
                st.info(f"✋ {t_sel} בחופש ביום {d_sel} – אין צורך בחלופה.")
            else:
                st.subheader(f"📌 {t_sel} | יום {d_sel}")
                for h in range(1,7):
                    subj,subs=res[h]
                    st.markdown(f"**🕐 שעה {h}: {subj}**")
                    if subs is None:
                        st.info("אין צורך בחלופה")
                    elif subs:
                        st.success(" / ".join(f"{t} ({s})" for _,t,s in subs))
                    else:
                        st.warning("אין חלופה זמינה")

    with tab_cal:
        st.title("📅 לוח שעות – כל המורות")
        st.markdown("<span style='font-size:0.9rem;'>🟩 שהייה&nbsp;&nbsp;🟦 פרטני&nbsp;&nbsp;⬜ מקצוע&nbsp;&nbsp;⬜ יום חופשי</span>",
                    unsafe_allow_html=True)
        for t in TEACHERS:
            with st.expander(f"📋 {t}",expanded=False):
                st.dataframe(matrix(t).style.map(shade),
                             use_container_width=True,height=240)

# =================================================
# 2) עוזר אישי (צ'אט)
# =================================================
else:
    st.title("🤖 עוזר אישי למציאת מחליפות")

    # --- state init ---
    if 'hist' not in st.session_state:
        st.session_state.hist=[]
        st.session_state.stage="teacher"
        st.session_state.teacher=""

    GREET="שלום גלית! אני העוזר האישי שלך למציאת מחליפות 😊\nאיזו מורה נעדרת היום?"

    # ✨ דה‑דופליקציה של ברכה
    greet_idxs=[i for i,(r,m) in enumerate(st.session_state.hist)
                if r=="bot" and m.startswith("שלום גלית")]
    if len(greet_idxs)==0:
        st.session_state.hist.insert(0,("bot",GREET))
    elif len(greet_idxs)>1:             # השאר אחד, מחק עודפים
        for idx in greet_idxs[1:][::-1]:
            st.session_state.hist.pop(idx)

    def bot(t):  st.session_state.hist.append(("bot",t))
    def usr(t):  st.session_state.hist.append(("user",t))

    chat=st.container()
    def redraw():
        chat.empty()
        for role,msg in st.session_state.hist:
            with chat.chat_message("assistant" if role=="bot" else "user"):
                st.markdown(msg)
    redraw()

    def pick_teacher():
        t=st.session_state.box_teacher
        if t:
            usr(t)
            st.session_state.teacher=t
            st.session_state.stage="day"
            bot(f"מצוין, בחרנו במורה **{t}**.\nעכשיו בחרי יום היעדרות:")
            redraw()

    def pick_day():
        d=st.session_state.box_day
        if d:
            usr(d)
            res=find_subs(st.session_state.teacher,d)
            if res=="DAY_OFF":
                ans=f"✋ {st.session_state.teacher} בחופש ביום **{d}** – אין צורך במחליפה."
            else:
                ans=f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{d}**:\n"
                for h in range(1,7):
                    subj,subs=res[h]
                    ans+=f"\n**🕐 שעה {h}** – {subj}\n"
                    if subs is None:
                        ans+="▪️ אין צורך בחלופה\n"
                    elif subs:
                        ans+="▪️ חלופה: "+" / ".join(f"{t} ({s})" for _,t,s in subs)+"\n"
                    else:
                        ans+="▪️ אין חלופה זמינה\n"
            bot(ans)
            bot("אם תרצי שוב – בחרי מורה חדשה 😊")
            # reset
            st.session_state.stage="teacher"
            st.session_state.box_teacher=""
            st.session_state.box_day=""
            redraw()

    if st.session_state.stage=="teacher":
        st.selectbox("בחרי מורה חסרה:",[""]+TEACHERS,
                     key="box_teacher",on_change=pick_teacher)
    elif st.session_state.stage=="day":
        st.selectbox("בחרי יום:",[""]+DAYS,
                     key="box_day",on_change=pick_day)

    redraw()
