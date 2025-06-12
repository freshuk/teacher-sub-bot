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

# ───────── טעינת נתונים ─────────
@st.cache_data
def load_table():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour'] = df['hour'].astype(int)
    df['subject'] = df['subject'].str.strip()
    return df
df = load_table()

# ───────── פונקציות עזר ─────────
def teacher_matrix(data, name):
    sub = data[data.teacher == name]
    mat = sub.pivot_table(index='hour', columns='day',
                          values='subject', aggfunc='first')
    return mat.reindex(index=range(1,7), columns=DAYS)

def color_cells(val):
    for k,c in COLOR_MAP.items():
        if pd.notna(val) and val.startswith(k):
            return f'background-color:{c};'
    return ''

def find_substitutes(absent_teacher, day):
    ts = df[(df.teacher == absent_teacher) & (df.day == day)]
    if not ts.empty and (ts['subject'] == DAY_OFF).all():
        return "DAY_OFF"
    res={}
    absent_map={r.hour:r.subject for _,r in ts.iterrows()}
    for h in range(1,7):
        subj = absent_map.get(h,"—")
        if subj in ('פרטני',DAY_OFF):
            res[h]=(subj,None)
            continue
        subs=[]
        for t in TEACHERS:
            if t==absent_teacher: continue
            rec=df[(df.teacher==t)&(df.day==day)&(df.hour==h)]
            if rec.empty: continue
            status=rec.iloc[0]['subject']
            if status in PRIORITY_MAP:
                subs.append((PRIORITY_MAP[status],t,status))
        subs.sort(key=lambda x:(x[0],TEACHERS.index(x[1])))
        res[h]=(subj,subs)
    return res

# ───────── בחירת תצורה ─────────
MODE = st.radio("בחר/י תצורה:", ["ממשק טפסים", "עוזר אישי (צ'אט)"])

# =================================================
# 1) ממשק טפסים  (לא השתנה)
# =================================================
if MODE=="ממשק טפסים":
    tab_subs, tab_cal = st.tabs(["🧑‍🏫 חלופות", "📅 לוח שבועי"])
    # ...  (כל קוד הטפסים נשאר כמו אצלך) ...

# =================================================
# 2) עוזר אישי (צ'אט)
# =================================================
else:
    st.title("🤖 עוזר אישי למציאת מחליפות")

    if 'hist' not in st.session_state:
        st.session_state.hist=[("bot","שלום גלית! אני העוזר האישי שלך למציאת מחליפות 😊\nאיזו מורה נעדרת היום?")]
        st.session_state.stage="teacher"

    def bot(msg):  st.session_state.hist.append(("bot",msg))
    def user(msg): st.session_state.hist.append(("user",msg))

    placeholder = st.container()
    def render():
        placeholder.empty()
        for role,msg in st.session_state.hist:
            with placeholder.chat_message("assistant" if role=="bot" else "user"):
                st.markdown(msg)
    render()

    # ----- שלב בחירת מורה -----
    if st.session_state.stage=="teacher":
        teacher = st.selectbox("בחרי מורה חסרה:",[""]+TEACHERS,key="chat_teacher")
        if teacher:
            user(teacher)
            st.session_state.teacher=teacher
            bot(f"מצוין, בחרנו במורה **{teacher}**.\nעכשיו בחרי באיזה יום היא נעדרת:")
            st.session_state.stage="day"
            if hasattr(st,"experimental_rerun"):
                st.experimental_rerun()

    # ----- שלב בחירת יום -----
    if st.session_state.stage=="day":
        day = st.selectbox("בחרי יום:",[""]+DAYS,key="chat_day")
        if day:
            user(day)
            res=find_substitutes(st.session_state.teacher,day)

            if res=="DAY_OFF":
                ans=f"✋ {st.session_state.teacher} בחופש ביום **{day}** – אין צורך במחליפה."
            else:
                ans=f"להלן החלופות למורה **{st.session_state.teacher}** ביום **{day}**:\n"
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
            bot("אם תרצי לבדוק שוב, בחרי מורה אחרת מהתיבה למעלה 😊")

            # reset stage
            st.session_state.stage="teacher"
            for k in ('chat_teacher','chat_day'):
                st.session_state.pop(k, None)
            render()
            # 🔄 רענון כדי שה־UI יחזור לשדה 'מורה'
            if hasattr(st,"experimental_rerun"):
                st.experimental_rerun()
