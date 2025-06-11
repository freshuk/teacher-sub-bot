import streamlit as st
import pandas as pd

# ---------- הגדרות עמוד + CSS מובייל ----------
st.set_page_config(page_title="בוט חלופות", layout="centered")

MOBILE_CSS = """
<style>
h1 {font-size:1.4rem;}
button, select, input {font-size:1rem;}
section[data-testid="stSidebar"] {display:none;}   /* הסתרת סייד־בר אם יש */
</style>
"""
st.markdown(MOBILE_CSS, unsafe_allow_html=True)


# ---------- קבועים ----------
DATA_FILE    = "schedule.csv"
TEACHERS     = ['דנה', 'לילך', 'רעות', 'ליאת', 'לימור']
PRIORITY_MAP = {'שהייה': 1, 'פרטני': 2}
DAYS         = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']


# ---------- טעינת נתונים ----------
@st.cache_data
def load_table():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour'] = df['hour'].astype(int)
    return df

df = load_table()


# ---------- בניית Pivot ללוח שבועי ----------
def make_pivot(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data['key'] = data['day'] + '-' + data['hour'].astype(str)
    pivot = data.pivot_table(index='teacher',
                             columns='key',
                             values='subject',
                             aggfunc='first')
    # סדר עמודות – ראשון-1, ראשון-2, … שישי-6
    ordered_cols = [f"{d}-{h}" for d in DAYS for h in range(1, 7)]
    pivot = pivot.reindex(columns=ordered_cols)
    return pivot

pivot_df = make_pivot(df)


# ---------- טאבים ----------
tab_subs, tab_calendar = st.tabs(["🧑‍🏫 חלופות", "📅 לוח שבועי"])

# ====== טאב 1 – חלופות ======
with tab_subs:
    st.title("🧑‍🏫 בוט חלופות מורים")

    absent_teacher = st.selectbox("בחר/י מורה חסרה",
                                  sorted(df['teacher'].unique()))
    day = st.selectbox("בחר/י יום בשבוע", DAYS)

    if st.button("מצא חלופות", use_container_width=True):
        # שלב 1 – תכנית המורה החסרה
        st.subheader(f"📌 המורה החסרה: {absent_teacher} | יום {day}")
        teacher_sched = df[(df.teacher == absent_teacher) & (df.day == day)]
        absent_map = {row.hour: row.subject
                      for _, row in teacher_sched.iterrows()}

        # שלב 2 – חיפוש חלופות
        for h in range(1, 7):
            subject = absent_map.get(h, "—")
            st.markdown(f"**🕐 שעה {h}: {subject}**")

            if subject == "פרטני":
                st.info("אין צורך בחלופה")
                continue

            substitutes = []
            for t in TEACHERS:
                if t == absent_teacher:
                    continue
                rec = df[(df.teacher == t) & (df.day == day) & (df.hour == h)]
                if rec.empty:
                    continue
                status = rec.iloc[0]['subject']
                if status in PRIORITY_MAP:
                    substitutes.append((PRIORITY_MAP[status], t, status))

            substitutes.sort(key=lambda x: (x[0], TEACHERS.index(x[1])))

            if substitutes:
                line = " / ".join([f"{t} ({s})" for _, t, s in substitutes])
                st.success(f"חלופה: {line}")
            else:
                st.warning("אין חלופה זמינה")


# ====== טאב 2 – לוח שבועי ======
with tab_calendar:
    st.title("📅 לוח שעות – כל המורות")
    st.dataframe(pivot_df, use_container_width=True)
