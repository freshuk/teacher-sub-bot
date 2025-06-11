import streamlit as st
import pandas as pd

# ---------- קבועים ----------
DATA_FILE   = "schedule.csv"
TEACHERS    = ['דנה', 'לילך', 'רעות', 'ליאת', 'לימור']
PRIORITY_MAP = {'שהייה': 1, 'פרטני': 2}

# ---------- טעינת נתונים ----------
@st.cache_data
def load_table():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour'] = df['hour'].astype(int)
    return df

df = load_table()

# ---------- כותרת ו-GUI ----------
st.title("🧑‍🏫 בוט חלופות מורים")
absent_teacher = st.selectbox("בחר/י מורה חסרה", sorted(df['teacher'].unique()))
day            = st.selectbox("בחר/י יום בשבוע", ['ראשון','שני','שלישי','רביעי','חמישי','שישי'])

if st.button("מצא חלופות"):
    # שלב 1 – תכנית המורה החסרה
    st.subheader(f"📌 המורה החסרה: {absent_teacher} | יום {day}")
    teacher_sched = df[(df.teacher == absent_teacher) & (df.day == day)]
    # יצירת מילון {שעה → מקצוע}
    absent_map = {row.hour: row.subject for _, row in teacher_sched.iterrows()}

    # שלב 2 – חיפוש חלופות
    for h in range(1, 7):
        subject = absent_map.get(h, "—")
        st.write(f"### 🕐 שעה {h}: {subject}")
        # אין צורך בחלופה אם זה פרטני
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

        # מיון לפי עדיפות
        substitutes.sort(key=lambda x: (x[0], TEACHERS.index(x[1])))

        if substitutes:
            line = " / ".join([f"{t} ({s})" for _, t, s in substitutes])
            st.success(f"חלופה: {line}")
        else:
            st.warning("אין חלופה זמינה")
