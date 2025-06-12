import streamlit as st
import pandas as pd
import time
from pathlib import Path

# ───────── הגדרות עמוד ─────────
st.set_page_config(
    page_title="צמרובוט – העוזר האישי שלי",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ───────── CSS מקצועי ─────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Heebo', sans-serif !important;
    direction: rtl;
    text-align: right;
}

.main .block-container {
    padding-top: 2rem;
    max-width: 42rem;
}

section[data-testid="stSidebar"] { display: none; }
.stDeployButton { display: none; }
footer { display: none; }
header { display: none; }
</style>
""", unsafe_allow_html=True)

# CSS נוסף - חלק 2
st.markdown("""
<style>
.app-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
    color: white;
    text-align: center;
}

.app-title {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
}

.app-subtitle {
    font-size: 1rem;
    opacity: 0.9;
    margin-top: 0.5rem;
}

.chat-container {
    background: #ffffff;
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    border: 1px solid rgba(102, 126, 234, 0.1);
    min-height: 300px;
    max-height: 500px;
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

# CSS חלק 3 - הודעות צ'אט
st.markdown("""
<style>
.chat-msg {
    margin: 1rem 0;
    animation: fadeInUp 0.5s ease-out;
    clear: both;
}

.chat-bot {
    background: linear-gradient(135deg, #f8faff 0%, #ecf2ff 100%);
    border: 1px solid #e1e8f7;
    border-radius: 18px 18px 18px 4px;
    padding: 1rem 1.2rem;
    margin-left: 2rem;
    position: relative;
    box-shadow: 0 2px 12px rgba(102, 126, 234, 0.1);
}

.chat-bot::before {
    content: "🤖";
    position: absolute;
    right: -0.5rem;
    top: -0.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.chat-user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 1rem 1.2rem;
    margin-right: 2rem;
    box-shadow: 0 2px 12px rgba(102, 126, 234, 0.2);
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

# CSS חלק 4 - אנימציות ואלמנטים
st.markdown("""
<style>
.thinking-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #667eea;
    font-weight: 500;
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(102, 126, 234, 0.05);
    border-radius: 12px;
    border-right: 4px solid #667eea;
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

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.loading-spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(102, 126, 234, 0.3);
    border-radius: 50%;
    border-top-color: #667eea;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)

# CSS חלק 5 - פאנל בקרה וכפתורים
st.markdown("""
<style>
.control-panel {
    background: linear-gradient(135deg, #f8faff 0%, #ffffff 100%);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    border: 1px solid rgba(102, 126, 234, 0.1);
    margin-bottom: 1rem;
}

.control-title {
    color: #667eea;
    font-weight: 600;
    font-size: 1.1rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.stSelectbox > div > div {
    background: white;
    border: 2px solid #e1e8f7;
    border-radius: 12px;
    transition: all 0.3s ease;
}

.stButton > button {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.8rem 1.5rem;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.2);
    width: 100%;
}

@media (max-width: 768px) {
    .main .block-container { padding: 1rem; }
    .app-header { padding: 1rem; margin-bottom: 1rem; }
    .app-title { font-size: 1.5rem; }
    .chat-container { padding: 1rem; max-height: 400px; }
    .chat-bot { margin-left: 1rem; }
    .chat-user { margin-right: 1rem; }
    .control-panel { padding: 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ───────── נתונים וקבועים ─────────
DATA_FILE = "schedule.csv"
TEACHERS = ['דנה', 'לילך', 'רעות', 'ליאת', 'לימור']
DAYS = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']
DAY_OFF = 'יום חופשי'
PRIORITY = {'שהייה': 1, 'פרטני': 2}

@st.cache_data
def load_df():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df['hour'] = df['hour'].astype(int)
    df['subject'] = df['subject'].str.strip()
    return df

df = load_df()

def get_subs(teacher, day, start_hr):
    rows = df[(df.teacher == teacher) & (df.day == day)]
    if not rows.empty and (rows.subject == DAY_OFF).all():
        return "DAY_OFF"
    absent = {r.hour: r.subject for _, r in rows.iterrows()}
    res = {}
    for h in range(start_hr, 7):
        subj = absent.get(h, '—')
        if subj in ('פרטני', DAY_OFF):
            res[h] = (subj, None)
            continue
        opts = []
        for t in TEACHERS:
            if t == teacher:
                continue
            r = df[(df.teacher == t) & (df.day == day) & (df.hour == h)]
            if r.empty:
                continue
            stat = r.iloc[0].subject
            if stat in PRIORITY:
                opts.append((PRIORITY[stat], t, stat))
        opts.sort(key=lambda x: (x[0], TEACHERS.index(x[1])))
        res[h] = (subj, opts)
    return res

# ───────── Header ─────────
st.markdown("""
<div class="app-header">
    <div class="app-title">🤖 צמרובוט</div>
    <div class="app-subtitle">העוזר האישי שלך למציאת מורה מחליפה</div>
</div>
""", unsafe_allow_html=True)

# ───────── אתחול צ'אט ─────────
GREET = "שלום גלית! 👋 אני צמרובוט, העוזר האישי שלך.<br><br>אני כאן לעזור לך למצוא מורה מחליפה במהירות ובקלות. בואי נתחיל!"

if 'chat' not in st.session_state:
    st.session_state.chat = [("bot", GREET)]
    st.session_state.stage = "teacher"
    st.session_state.teacher = st.session_state.day = ""
    st.session_state.start = 1
    st.session_state.sel_teacher = st.session_state.sel_day = st.session_state.sel_scope = st.session_state.sel_hr = ""

def bot(m):
    st.session_state.chat.append(("bot", m))

def usr(m):
    st.session_state.chat.append(("user", m))

def show_thinking():
    """הצגת אנימציית חשיבה"""
    thinking_placeholder = st.empty()
    thinking_placeholder.markdown("""
    <div class="thinking-indicator">
        <div class="loading-spinner"></div>
        <span>צמרובוט חושב</span>
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
    """עדכון תצוגת הצ'אט"""
    chat_container.empty()
    with chat_container.container():
        for role, msg in st.session_state.chat:
            if role == "user":
                st.markdown(f"""
                <div class="chat-msg">
                    <div class="chat-user">{msg}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-msg">
                    <div class="chat-bot">{msg}</div>
                </div>
                """, unsafe_allow_html=True)

# ───────── תצוגת צ'אט ─────────
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
chat_container = st.container()
redraw()
st.markdown('</div>', unsafe_allow_html=True)

# ───────── Callbacks ─────────
def cb_teacher():
    t = st.session_state.sel_teacher
    if t:
        usr(f"מורה: {t}")
        st.session_state.teacher = t
        st.session_state.stage = "day"
        show_thinking()
        bot(f"מעולה! בחרנו במורה <strong>{t}</strong> ✨<br><br>לאיזה יום היא נעדרת?")
        redraw()

def cb_day():
    d = st.session_state.sel_day
    if d:
        usr(f"יום: {d}")
        st.session_state.day = d
        st.session_state.stage = "scope"
        show_thinking()
        bot("האם היא נעדרת <strong>יום שלם</strong> או רק <strong>מ-שעה מסוימת</strong>? 🕐")
        redraw()

def cb_scope():
    s = st.session_state.sel_scope
    if s == "יום שלם":
        usr("יום שלם")
        st.session_state.start = 1
        run()
    elif s == "מ-שעה":
        usr("מ-שעה")
        show_thinking()
        bot("באיזו שעה מתחילה ההיעדרות? (שעות 1-6) 📚")
        redraw()

def cb_hr():
    hr = st.session_state.sel_hr
    if hr:
        usr(f"משעה {hr}")
        st.session_state.start = int(hr)
        run()

def run():
    """ביצוע החיפוש והצגת התוצאות"""
    show_thinking()
    res = get_subs(st.session_state.teacher, st.session_state.day, st.session_state.start)
    
    if res == "DAY_OFF":
        bot(f"""
        ✋ מצוין! 
        <strong>{st.session_state.teacher}</strong> נמצאת בחופש ביום <strong>{st.session_state.day}</strong><br>
        <strong>אין צורך בחלופה</strong> 🎉
        """)
    else:
        ans = f"""
        📋 הנה החלופות למורה <strong>{st.session_state.teacher}</strong> ביום <strong>{st.session_state.day}</strong>:<br><br>
        """
        
        for h in range(st.session_state.start, 7):
            subj, subs = res[h]
            ans += f"<strong>🕐 שעה {h}</strong> – {subj}<br>"
            
            if subs is None:
                ans += "▪️ אין צורך בחלופה<br>"
            elif subs:
                ans += "▪️ <strong>חלופה זמינה:</strong> " + " / ".join(f"{t} ({s})" for _, t, s in subs) + "<br>"
            else:
                ans += "▪️ <em>אין חלופה זמינה</em><br>"
            ans += "<br>"
        
        bot(ans)
    
    # סיום מחזור
    time.sleep(1)
    bot("שמחתי לעזור! 😊<br>אם יש לך עוד שאלות, אני כאן בשבילך 🌸")
    reset()
    redraw()

def reset():
    """איפוס למחזור חדש"""
    st.session_state.stage = "teacher"
    st.session_state.sel_teacher = st.session_state.sel_day = st.session_state.sel_scope = st.session_state.sel_hr = ""

# ───────── פאנל בקרה ─────────
st.markdown('<div class="control-panel">', unsafe_allow_html=True)

if st.session_state.stage == "teacher":
    st.markdown('<div class="control-title">👩‍🏫 בחירת מורה</div>', unsafe_allow_html=True)
    st.selectbox(
        "איזו מורה נעדרת?",
        [""] + TEACHERS,
        key="sel_teacher",
        on_change=cb_teacher,
        help="בחרי את המורה שאת מחפשת עבורה חלופה"
    )

elif st.session_state.stage == "day":
    st.markdown('<div class="control-title">📅 בחירת יום</div>', unsafe_allow_html=True)
    st.selectbox(
        "באיזה יום היא נעדרת?",
        [""] + DAYS,
        key="sel_day",
        on_change=cb_day,
        help="בחרי את יום ההיעדרות"
    )

elif st.session_state.stage == "scope":
    st.markdown('<div class="control-title">⏰ סוג היעדרות</div>', unsafe_allow_html=True)
    st.radio(
        "היקף ההיעדרות:",
        ("", "יום שלם", "מ-שעה"),
        key="sel_scope",
        on_change=cb_scope,
        horizontal=True,
        help="האם ההיעדרות היא ליום שלם או מתחילה משעה מסוימת?"
    )
    
    if st.session_state.sel_scope == "מ-שעה":
        st.selectbox(
            "מאיזו שעה?",
            [""] + [str(i) for i in range(1, 7)],
            key="sel_hr",
            on_change=cb_hr,
            help="בחרי את השעה שבה מתחילה ההיעדרות"
        )

st.markdown('</div>', unsafe_allow_html=True)

# ───────── כפתור ניקוי ─────────
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🗑️ התחל מחדש", help="נקה את המסך והתחל שיחה חדשה"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()