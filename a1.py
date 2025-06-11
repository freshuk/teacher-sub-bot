import streamlit as st
import pandas as pd
import numpy as np   # כבר הוספנו ל-requirements.txt

# ────────────────── הגדרות עמוד + CSS מובייל ──────────────────
st.set_page_config(page_title="בוט חלופות", layout="centered")

st.markdown("""
<style>
h1 {font-size:1.4rem;}
button, select, input {font-size:1rem;}
section[data-testid="stSidebar"] {display:none;}
</style>
""", unsafe_allow_html=True)

# ────────────────── קבועים ──────────────────
DATA_FILE    = "schedule.csv"
TEACHERS     = ['דנה', 'לילך', 'רעות', 'ליאת', 'לימור']
PRIORITY_MAP = {'שהייה': 1, 'פרטני': 2}
DAYS         = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']
COLOR_MAP    = {          # רקעים לטבלה
    'שהייה':     '#c8e6c9',   # ירוק-בהיר
    'פרטני':     '#bbdefb',   # כחול-בהיר
    'יום חופשי': '#e0e0e0'    # אפור
}

# ────────────────── טעינת נתונים ──────────────────
@st.cache_data
def load_table():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour'] = df['hour'].astype(int)
    return df

df = load_table()

# ────────────────── פונקציות עזר ──────────────────
def teacher_matrix(data: pd.DataFrame, name: str) -> pd.DataFrame:
    sub = data[data.teacher == name]
    mat = sub.pivot_table(index='hour', columns='day',
                          values='subject', aggfunc='first')
    return mat.reindex(index=range(1, 7), columns=DAYS)

def color_cells(val: str) -> str:
    for key, color in COLOR_MAP.items():
        if pd.notna(val) and val.startswith(key):
            return f'background-color:{color};'
    return ''

# ────────────────── טאבים ──────────────────
tab_subs, tab_calendar = st.tabs(["🧑‍🏫 חלופות", "📅 לוח שבועי"])

# ===== טאב 1 – חלופות =====
with tab_subs:
    st.title("🧑‍🏫 בוט חלופות מורים")

    absent_teacher = st.selectbox("בחר/י מורה חסרה",
                                  sorted(df['teacher'].unique()))
    day = st.selectbox("בחר/י יום בשבוע", DAYS)

    if st.button("מצא חלופות", use_container_width=True):
        teacher_sched = df[(df.teacher == absent_teacher) & (df.day == day)]

        # --- בדיקה: האם זה יום חופשי מלא? ---
        if not teacher_sched.empty and (teacher_sched['subject'] == 'יום חופשי').all():
            st.info(f"✋‎ {absent_teacher} ביום חופשי, אין צורך בחלופה.")
        else:
            # תצוגת כותרת
            st.subheader(f"📌 המורה החסרה: {absent_teacher} | יום {day}")

            # מילון {שעה → מקצוע}
            absent_map = {row.hour: row.subject
                          for _, row in teacher_sched.iterrows()}

            # חיפוש חלופות לשעות 1-6
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

# ===== טאב 2 – לוח שבועי =====
with tab_calendar:
    st.title("📅 לוח שעות – כל המורות")
    st.markdown(
        "<span style='font-size:0.9rem;'>🟩 שהייה &nbsp;&nbsp; 🟦 פרטני &nbsp;&nbsp; ⬜ מקצוע &nbsp;&nbsp; ⬜ יום חופשי</span>",
        unsafe_allow_html=True
    )
    for t in TEACHERS:
        with st.expander(f"📋 {t}", expanded=False):
            mat = teacher_matrix(df, t)
            styled = mat.style.applymap(color_cells)
            st.dataframe(styled, use_container_width=True, height=240)
