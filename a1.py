import streamlit as st
import pandas as pd

# ── הגדרות עמוד + CSS ─────────────────────────────
st.set_page_config(page_title="בוט חלופות", layout="centered")
st.markdown("""
<style>
h1 {font-size:1.5rem;}
button,select,input{font-size:1rem;}
section[data-testid="stSidebar"]{display:none;}
</style>""",unsafe_allow_html=True)

# ── קבועים ─────────────────────────────────────────
DATA_FILE   = "schedule.csv"
TEACHERS    = ['דנה','לילך','רעות','ליאת','לימור']
PRIORITY    = {'שהייה':1,'פרטני':2}
DAYS        = ['ראשון','שני','שלישי','רביעי','חמישי','שישי']
DAY_OFF     = 'יום חופשי'
COLORS      = {'שהייה':'#c8e6c9','פרטני':'#bbdefb',DAY_OFF:'#e0e0e0'}

# ── נתונים ─────────────────────────────────────────
@st.cache_data
def load_df():
    df = pd.read_csv(DATA_FILE,dtype=str)
    df['hour']    = df['hour'].astype(int)
    df['subject'] = df['subject'].str.strip()
    return df
df = load_df()

# ── עזרי לוח/חילופים ──────────────────────────────
def teacher_matrix(name):
    sub = df[df.teacher==name]
    wide = sub.pivot_table(index='hour',columns='day',
                           values='subject',aggfunc='first')
    return wide.reindex(index=range(1,7),columns=DAYS)

def color(val):
    for k,c in COLORS.items():
        if pd.notna(val) and val.startswith(k): return f'background-color:{c}'
    return ''

def find_subs(absent,day):
    rows = df[(df.teacher==absent)&(df.day==day)]
    if not rows.empty and (rows.subject==DAY_OFF).all():
        return "DAY_OFF"
    m = {r.hour:r.subject for _,r in rows.iterrows()}
    out={}
    for h in range(1,7):
        subj=m.get(h,'—')
        if subj in ('פרטני',DAY_OFF):
            out[h]=(subj,None); continue
        opts=[]
        for t in TEACHERS:
            if t==absent: continue
            r=df[(df.teacher==t)&(df.day==day)&(df.hour==h)]
            if r.empty: continue
            stat=r.iloc[0].subject
            if stat in PRIORITY:
                opts.append((PRIORITY[stat],t,stat))
        opts.sort(key=lambda x:(x[0],TEACHERS.index(x[1])))
        out[h]=(subj,opts)
    return out

# ── תצורה ראשית ───────────────────────────────────
MODE = st.radio("בחר/י תצורה:",["ממשק טפסים","עוזר אישי (צ'אט)"])

# =================================================
# 1) ממשק טפסים
# =================================================
if MODE=="ממשק טפסים":
    tabs = st.tabs(["🧑‍🏫 חלופות","📅 לוח שבועי"])
    with tabs[0]:
        st.title("🧑‍🏫 בוט חלופות מורים")
        t_sel=st.selectbox("מורה חסרה",TEACHERS,key='form_t')
        d_sel=st.selectbox("יום בשבוע",DAYS,key='form_d')
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
                        line=" / ".join(f"{t} ({s})" for _,t,s in subs)
                        st.success(f"חלופה: {line}")
                    else:
                        st.warning("אין חלופה זמינה")
    with tabs[1]:
        st.title("📅 לוח שעות – כל המורות")
        for t in TEACHERS:
            with st.expander(f"📋 {t}",expanded=False):
                st.dataframe(
                    teacher_matrix(t).style.applymap(color),
                    use_container_width=True,
                    height=240,
                )

# =================================================
# 2) עוזר אישי (צ'אט)
# =================================================
else:
    st.title("🤖 עוזר אישי למציאת מחליפות")

    if 'hist' not in st.session_state:
        st.session_state.hist=[("bot","שלום גלית! אני העוזר האישי שלך למציאת מחליפות 😊\nאיזו מורה נעדרת היום?")]
        st.session_state.stage="teacher"

    def bot(txt):  st.session_state.hist.append(("bot",txt))
    def usr(txt):  st.session_state.hist.append(("user",txt))

    box=st.container()
    def redraw():
        box.empty()
        for role,txt in st.session_state.hist:
            with box.chat_message("assistant" if role=="bot" else "user"):
                st.markdown(txt)
    redraw()

    # ── שלב בחירת מורה ──
    if st.session_state.stage=="teacher":
        t=st.selectbox("בחרי מורה חסרה:",[""]+TEACHERS,key='chat_t')
        if t:
            usr(t)
            st.session_state.teacher=t
            bot(f"מצוין, בחרנו במורה **{t}**.\nעכשיו בחרי יום היעדרות:")
            st.session_state.stage="day"
            try:                     # ⚡
                st.experimental_rerun()
            except AttributeError:
                st.stop()

    # ── שלב בחירת יום ──
    if st.session_state.stage=="day":
        d=st.selectbox("בחרי יום:",[""]+DAYS,key='chat_d')
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
                        line=" / ".join(f"{t} ({s})" for _,t,s in subs)
                        ans+=f"▪️ חלופה: {line}\n"
                    else:
                        ans+="▪️ אין חלופה זמינה\n"
            bot(ans)
            bot("אם תרצי לבדוק שוב – בחרי מורה חדשה 😊")

            # איפוס
            st.session_state.stage="teacher"
            for k in ('chat_t','chat_d'):
                st.session_state.pop(k,None)
            redraw()
            try:                     # ⚡
                st.experimental_rerun()
            except AttributeError:
                st.stop()
