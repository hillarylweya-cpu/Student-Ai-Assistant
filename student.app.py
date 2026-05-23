import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time

import database as db
import ai_engine as ai

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ── Page Config ───────────────────────────────────────

st.set_page_config(
    page_title="EduMate AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    color: #f8fafc;
}
.stApp {
    background: linear-gradient(135deg, #090d16 0%, #0f172a 40%, #1e1b4b 100%);
    background-attachment: fixed;
}
.main-title {
    text-align: center;
    background: linear-gradient(90deg, #818cf8, #6366f1, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 58px;
    font-weight: 800;
    letter-spacing: -2px;
    margin-bottom: 0;
}
.sub-title {
    text-align: center;
    color: #94a3b8;
    font-size: 20px;
    margin-bottom: 28px;
}
.glass-card {
    background: rgba(255,255,255,0.04);
    border-radius: 20px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 18px;
}
.metric-card {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 18px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 14px;
}
.metric-card h1 {
    font-size: 40px;
    margin: 4px 0;
    font-weight: 800;
    background: linear-gradient(90deg, #60a5fa, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.badge-pill {
    background: linear-gradient(135deg, #4338ca, #1e1b4b);
    border: 1px solid #6366f1;
    color: #e0e7ff;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    display: inline-block;
    margin: 3px;
}
.stButton > button {
    width: 100%;
    border: none;
    border-radius: 12px;
    padding: 10px 18px;
    font-size: 15px;
    font-weight: 700;
    background: linear-gradient(90deg, #4f46e5, #3b82f6);
    color: white !important;
    transition: all 0.25s ease;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #3b82f6, #2563eb);
    transform: translateY(-2px);
}
.chat-user {
    background: rgba(59,130,246,0.14);
    border-left: 4px solid #3b82f6;
    padding: 12px 18px;
    border-radius: 0 16px 16px 0;
    margin: 8px 0;
}
.chat-ai {
    background: rgba(129,140,248,0.11);
    border-left: 4px solid #818cf8;
    padding: 12px 18px;
    border-radius: 16px 0 16px 16px;
    margin: 8px 0;
}
.active-class {
    background: rgba(239,68,68,0.12);
    border: 2px solid #ef4444;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 14px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
    70%  { box-shadow: 0 0 0 10px rgba(239,68,68,0); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}
.footer {
    text-align: center;
    color: #475569;
    margin-top: 48px;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────

defaults = {
    "logged_in": False,
    "user_email": "",
    "user_fullname": "",
    "chat_history": [],
    "quiz_questions": [],
    "quiz_score": 0,
    "quiz_timer_start": 0,
    "battle_mode": False,
    "draft_assignment": {"title": "", "subject": "", "priority": "Medium", "difficulty": "Medium"},
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ═══════════════════════════════════════════════════════
# AUTH SCREENS
# ═══════════════════════════════════════════════════════

if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🎓 EduMate AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Premium AI Education Platform</div>', unsafe_allow_html=True)

    auth_tab = st.sidebar.selectbox("Access", ["Login", "Register"])

    if auth_tab == "Register":
        st.markdown("<div class='glass-card'><h2>Create Account</h2>", unsafe_allow_html=True)
        fullname = st.text_input("Full Name")
        email    = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        confirm  = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if not fullname or not email or not password:
                st.warning("All fields are required.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif db.create_user(fullname, email, password):
                st.success("Account created! Please log in.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("That email is already registered.")
        st.markdown("</div>", unsafe_allow_html=True)

    else:  # Login
        col_form, col_features = st.columns([1.2, 1])

        with col_form:
            st.markdown("<div class='glass-card'><h2 style='text-align:center;'>Sign In</h2>", unsafe_allow_html=True)
            email    = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.button("Sign In"):
                user = db.login_user(email, password)
                if user:
                    st.session_state.logged_in     = True
                    st.session_state.user_email    = user[2]
                    st.session_state.user_fullname = user[1]
                    st.success(f"Welcome back, {user[1]}!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_features:
            st.markdown("""
            <div class='glass-card'>
                <h3 style='color:#818cf8;'>What's included</h3>
                <p>AI Assistant — ask questions, generate flashcards, summarise notes, draw concept boards.</p>
                <p>Assignment Tracker — plagiarism checker, grammar scan, deadline management.</p>
                <p>Timetable Planner — live class highlighter and Zoom link launcher.</p>
                <p>Adaptive Quiz Arena — multiple levels, timer, multiplayer simulation.</p>
                <p>Analytics Dashboard — focus logs, quiz trends, GPA predictor.</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='footer'>© 2026 EduMate AI</div>", unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════
# MAIN APP — authenticated students only
# ═══════════════════════════════════════════════════════

# Sidebar
st.sidebar.markdown("<h2 style='text-align:center;'>🎓 EduMate AI</h2>", unsafe_allow_html=True)
st.sidebar.success(f"{st.session_state.user_fullname}\n{st.session_state.user_email}")

page = st.sidebar.radio("Navigate", [
    "Dashboard",
    "AI Assistant",
    "Assignments",
    "Timetable",
    "Quiz Arena",
    "Analytics",
])

if st.sidebar.button("Logout"):
    for key in defaults:
        st.session_state[key] = defaults[key]
    st.rerun()

# Fetch data once
assignments    = db.get_assignments(st.session_state.user_email)
timetable      = db.get_timetable(st.session_state.user_email)
streak, badges = db.get_or_update_streak(st.session_state.user_email)
notifications  = db.get_notifications(st.session_state.user_email)
quiz_records   = db.get_quiz_records(st.session_state.user_email)
focus_sessions = db.get_focus_sessions(st.session_state.user_email)
gpa_target     = db.get_user_gpa_target(st.session_state.user_email)

# ── 1. Dashboard ──────────────────────────────────────

if page == "Dashboard":
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    now_str  = datetime.now().strftime("%I:%M %p")

    quotes = [
        "Believe you can and you're halfway there.",
        "Education is the most powerful weapon you can use to change the world.",
        "The secret of getting ahead is getting started.",
        "Every expert was once a beginner.",
    ]
    quote = quotes[hash(st.session_state.user_fullname) % len(quotes)]

    st.markdown(f"""
    <div class='glass-card' style='border-left:6px solid #6366f1;'>
        <h1 style='margin:0;'>{greeting}, {st.session_state.user_fullname} 👋</h1>
        <p style='color:#a5b4fc; margin-top:6px;'>"{quote}"</p>
        <p style='color:#64748b; margin:0;'>⏰ {now_str}</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    pending = len([a for a in assignments if a[5] not in ("Completed", "Graded")])
    for col, label, value, sub in [
        (c1, "Pending Tasks",  pending,         "Action required"),
        (c2, "Classes Set",    len(timetable),  "In your timetable"),
        (c3, "Streak",         f"{streak} days","Keep it going!"),
        (c4, "Target GPA",     f"{gpa_target:.2f}", "Track in Analytics"),
    ]:
        col.markdown(f"""
        <div class='metric-card'>
            <p style='color:#94a3b8; font-size:14px; margin:0;'>{label}</p>
            <h1>{value}</h1>
            <span style='color:#64748b; font-size:12px;'>{sub}</span>
        </div>
        """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        st.markdown("<div class='glass-card'><h3>Subject Completion</h3>", unsafe_allow_html=True)
        subject_progress: dict = {}
        for a in assignments:
            sub, status = a[2], a[5]
            subject_progress.setdefault(sub, {"total": 0, "done": 0})
            subject_progress[sub]["total"] += 1
            if status in ("Completed", "Graded"):
                subject_progress[sub]["done"] += 1
        if subject_progress:
            for sub, p in subject_progress.items():
                pct = int(p["done"] / p["total"] * 100)
                st.write(f"**{sub}** ({pct}%)")
                st.progress(pct / 100.0)
        else:
            st.info("Add assignments to track progress.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'><h3>Timetable Summary</h3>", unsafe_allow_html=True)
        if timetable:
            for t in timetable:
                st.markdown(f"📅 **{t[2]}** — {t[1]} ({t[3]}–{t[4]}) | {t[5]}")
        else:
            st.info("No classes added yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='glass-card'><h3>Badges</h3>", unsafe_allow_html=True)
        badge_html = "".join(f"<span class='badge-pill'>{b}</span>" for b in badges)
        st.markdown(badge_html or "<p style='color:#64748b;'>No badges yet. Keep studying!</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'><h3>Upcoming Deadlines</h3>", unsafe_allow_html=True)
        active = [a for a in assignments if a[5] not in ("Completed", "Graded")]
        if active:
            for a in active:
                try:
                    due = datetime.strptime(a[3], "%Y-%m-%d").date()
                    delta = (due - date.today()).days
                    if delta < 0:
                        status_html = f"<span style='color:#f87171;'>Overdue by {abs(delta)} days</span>"
                    elif delta == 0:
                        status_html = "<span style='color:#f87171;'>Due today!</span>"
                    elif delta == 1:
                        status_html = "<span style='color:#fbbf24;'>Due tomorrow</span>"
                    else:
                        status_html = f"<span style='color:#34d399;'>Due in {delta} days</span>"
                    st.markdown(f"✍️ **{a[1]}** ({a[2]}) — {status_html}", unsafe_allow_html=True)
                except ValueError:
                    st.markdown(f"✍️ **{a[1]}** ({a[2]}) — {a[3]}")
        else:
            st.success("No pending assignments!")
        st.markdown("</div>", unsafe_allow_html=True)

    # Notifications
    unread = len([n for n in notifications if n[3] == 0])
    st.markdown(f"<div class='glass-card'><h3>Notifications ({unread} unread)</h3>", unsafe_allow_html=True)
    if notifications:
        for n in notifications[:5]:
            dot = "🔵" if n[3] == 0 else "⚪"
            st.markdown(f"{dot} <small style='color:#64748b;'>{n[2]}</small> {n[1]}", unsafe_allow_html=True)
        if st.button("Mark all as read"):
            db.mark_notifications_read(st.session_state.user_email)
            st.rerun()
    else:
        st.write("No notifications.")
    st.markdown("</div>", unsafe_allow_html=True)

# ── 2. AI Assistant ───────────────────────────────────

elif page == "AI Assistant":
    st.markdown("<div class='glass-card'><h1 style='margin:0;'>AI Assistant</h1><p style='color:#a5b4fc;'>Chat, flashcards, whiteboard, notes translator</p></div>", unsafe_allow_html=True)

    col_ctrl, col_chat = st.columns([1, 2])

    with col_ctrl:
        st.markdown("<div class='glass-card'><h3>Settings</h3>", unsafe_allow_html=True)
        persona_mode   = st.selectbox("Tutor personality", ["Friendly Tutor", "Strict Teacher", "Motivational Coach"])
        active_subject = st.selectbox("Subject focus", ["Mathematics", "Biology", "Physics", "Chemistry", "Computer Science"])
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'><h3>Note Summariser</h3>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload notes (TXT, PDF, DOCX)", type=["txt", "pdf", "docx"])
        if uploaded and st.button("Summarise"):
            summary = (
                f"**Summary of `{uploaded.name}`**\n\n"
                "1. Core concepts rely on fundamental principles and rules.\n"
                "2. Memorise formulas early; build mind-maps to connect terms.\n"
                "3. Review step-by-step before exams."
            )
            st.session_state.chat_history.append({"role": "user",      "content": f"Summarise: {uploaded.name}"})
            st.session_state.chat_history.append({"role": "assistant", "content": summary})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'><h3>Translate Notes</h3>", unsafe_allow_html=True)
        lang   = st.selectbox("Target language", ["Spanish", "French", "German", "Swahili", "Japanese", "Chinese"])
        t_text = st.text_area("Text to translate", key="trans_input")
        if st.button("Translate"):
            if t_text.strip():
                st.code(ai.translate_notes(t_text, lang))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'><h3>Flashcard Generator</h3>", unsafe_allow_html=True)
        fc_prompt = st.text_input("Topic prompt", placeholder="e.g. photosynthesis")
        if st.button("Generate Flashcards"):
            if fc_prompt.strip():
                cards = ai.generate_flashcards(fc_prompt, active_subject)
                for card in cards:
                    db.add_flashcard(st.session_state.user_email, card["subject"], card["front"], card["back"])
                st.success(f"Generated {len(cards)} flashcards for {active_subject}.")
                db.add_notification(st.session_state.user_email, f"Flashcards created for {active_subject}.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chat:
        st.markdown("<div class='glass-card'><h3>Chat</h3>", unsafe_allow_html=True)
        chat_area = st.container(height=420)
        with chat_area:
            if not st.session_state.chat_history:
                st.markdown(f"<div class='chat-ai'>Hi {st.session_state.user_fullname}! I'm your <b>{persona_mode}</b>. Ask me anything.</div>", unsafe_allow_html=True)
            for msg in st.session_state.chat_history:
                css = "chat-user" if msg["role"] == "user" else "chat-ai"
                label = "You" if msg["role"] == "user" else "AI"
                st.markdown(f"<div class='{css}'><b>{label}:</b> {msg['content']}</div>", unsafe_allow_html=True)

        chat_input = st.text_input("Ask a question…", key="chat_input")
        col_send, col_clear = st.columns([3, 1])
        with col_send:
            if st.button("Send"):
                if chat_input.strip():
                    st.session_state.chat_history.append({"role": "user", "content": chat_input})
                    reply = ai.ai_chat_response(chat_input, active_subject, persona_mode)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
        with col_clear:
            if st.button("Clear"):
                st.session_state.chat_history = []
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'><h3>Concept Whiteboard</h3>", unsafe_allow_html=True)
        wb_subject = st.selectbox("Subject to visualise", ["Mathematics", "Biology", "Physics", "Chemistry", "Computer Science"], key="wb_sel")
        if st.button("Render Whiteboard"):
            st.markdown(ai.generate_whiteboard_diagram(wb_subject))
        st.markdown("</div>", unsafe_allow_html=True)

# ── 3. Assignments ────────────────────────────────────

elif page == "Assignments":
    st.markdown("<div class='glass-card'><h1 style='margin:0;'>Assignments</h1><p style='color:#a5b4fc;'>Track, manage, and scan your work</p></div>", unsafe_allow_html=True)

    col_form, col_list = st.columns([1, 1.2])

    with col_form:
        st.markdown("<div class='glass-card'><h3>Add Assignment</h3>", unsafe_allow_html=True)
        draft = st.session_state.draft_assignment
        title      = st.text_input("Title", value=draft["title"])
        subject    = st.text_input("Subject", value=draft["subject"])
        due_date   = st.date_input("Due Date")
        priority   = st.selectbox("Priority", ["Low", "Medium", "High"],   index=["Low","Medium","High"].index(draft["priority"]))
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy","Medium","Hard"].index(draft["difficulty"]))
        status     = st.selectbox("Status", ["Pending", "In Progress", "Completed", "Submitted"])

        if st.button("Save Assignment"):
            if title.strip() and subject.strip():
                db.add_assignment(
                    st.session_state.user_email, title, subject,
                    str(due_date), priority, status, difficulty
                )
                st.success("Assignment saved!")
                st.session_state.draft_assignment = {"title":"","subject":"","priority":"Medium","difficulty":"Medium"}
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("Title and subject are required.")

        # Auto-save draft
        st.session_state.draft_assignment = {"title": title, "subject": subject, "priority": priority, "difficulty": difficulty}
        st.markdown("</div>", unsafe_allow_html=True)

    with col_list:
        st.markdown("<div class='glass-card'><h3>Task List</h3>", unsafe_allow_html=True)
        subjects = ["All"] + list({a[2] for a in assignments})
        f_sub  = st.selectbox("Filter by subject",  subjects)
        f_pri  = st.selectbox("Filter by priority", ["All","High","Medium","Low"])

        filtered = [
            a for a in assignments
            if (f_sub == "All" or a[2] == f_sub)
            and (f_pri == "All" or a[4] == f_pri)
        ]

        if filtered:
            for a in filtered:
                with st.expander(f"{a[1]} — {a[2]} ({a[5]})"):
                    st.write(f"Due: {a[3]} | Priority: **{a[4]}** | Difficulty: {a[6]}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Delete", key=f"del_{a[0]}"):
                            db.delete_assignment(a[0])
                            st.rerun()
                    with c2:
                        if a[5] != "Completed" and st.button("Mark done", key=f"done_{a[0]}"):
                            db.update_assignment_status(a[0], "Completed")
                            db.add_notification(st.session_state.user_email, f"Completed: {a[1]}!")
                            st.rerun()
        else:
            st.info("No matching assignments.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='glass-card'><h3>Grammar & Plagiarism Scanner</h3>", unsafe_allow_html=True)
    check_text = st.text_area("Paste essay or draft here…", height=140)
    if st.button("Run Scan"):
        if check_text.strip():
            result = ai.ai_grammar_plagiarism_check(check_text)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Quality Score", f"{result['score']}/100")
                st.metric("Plagiarism Index", f"{result['plagiarism_percent']}%")
            with c2:
                st.info(result["feedback"])
                for err in result["grammar_errors"]:
                    st.warning(err)
                for src in result["plagiarism_sources"]:
                    st.error(src)
        else:
            st.warning("Please paste some text first.")
    st.markdown("</div>", unsafe_allow_html=True)

# ── 4. Timetable ──────────────────────────────────────

elif page == "Timetable":
    st.markdown("<div class='glass-card'><h1 style='margin:0;'>Timetable</h1><p style='color:#a5b4fc;'>Schedule, track attendance, and launch classes</p></div>", unsafe_allow_html=True)

    weekdays     = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    current_day  = weekdays[datetime.now().weekday()]
    current_time = datetime.now().strftime("%H:%M")
    st.info(f"Today is **{current_day}** — {current_time}")

    active_found = False
    for t in timetable:
        t_id, t_sub, t_day, t_start, t_end, t_teacher, t_contact, t_zoom, t_att = t
        if t_day == current_day and t_start <= current_time <= t_end:
            active_found = True
            zoom_url = t_zoom if t_zoom else "https://zoom.us"
            st.markdown(f"""
            <div class='active-class'>
                <h3 style='color:#ef4444; margin:0;'>LIVE: {t_sub.upper()}</h3>
                <p>{t_start}–{t_end} | {t_teacher} ({t_contact})</p>
                <a href='{zoom_url}' target='_blank'>
                  <button style='background:#ef4444;border:none;padding:8px 16px;color:white;border-radius:8px;font-weight:bold;cursor:pointer;'>
                    Launch Zoom
                  </button>
                </a>
            </div>
            """, unsafe_allow_html=True)

    if not active_found:
        st.success("No class is active right now.")

    col_grid, col_add = st.columns([1.5, 1])

    with col_grid:
        st.markdown("<div class='glass-card'><h3>Weekly Schedule</h3>", unsafe_allow_html=True)
        schedule: dict = {d: [] for d in ["Monday","Tuesday","Wednesday","Thursday","Friday"]}
        for t in timetable:
            if t[2] in schedule:
                schedule[t[2]].append(t)

        for day, classes in schedule.items():
            st.markdown(f"**{day}**")
            if classes:
                for cl in classes:
                    att_label = "Attended" if cl[8] == 1 else "Mark attended"
                    st.markdown(f"- **{cl[1]}** ({cl[3]}–{cl[4]}) | {cl[5]}")
                    ca, cb, cc = st.columns(3)
                    with ca:
                        if cl[7]:
                            st.markdown(f"[Join Zoom]({cl[7]})")
                    with cb:
                        if st.button("Remove", key=f"rm_{cl[0]}"):
                            db.delete_timetable(cl[0])
                            st.rerun()
                    with cc:
                        if st.button(att_label, key=f"att_{cl[0]}"):
                            db.toggle_timetable_attendance(cl[0], 0 if cl[8] == 1 else 1)
                            st.rerun()
            else:
                st.caption("No classes.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_add:
        st.markdown("<div class='glass-card'><h3>Add Class</h3>", unsafe_allow_html=True)
        with st.form("add_class"):
            sub      = st.text_input("Subject")
            day      = st.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday"])
            t_start  = st.time_input("Start", value=datetime.strptime("09:00","%H:%M").time())
            t_end    = st.time_input("End",   value=datetime.strptime("10:00","%H:%M").time())
            teacher  = st.text_input("Instructor", "Dr. Jane Smith")
            contact  = st.text_input("Contact", "instructor@edu.ac")
            zoom_lnk = st.text_input("Zoom URL", "https://zoom.us/j/1234567890")

            if st.form_submit_button("Add to Schedule"):
                if sub.strip():
                    db.add_timetable(
                        st.session_state.user_email, sub, day,
                        t_start.strftime("%H:%M"), t_end.strftime("%H:%M"),
                        teacher, contact, zoom_lnk
                    )
                    db.add_notification(st.session_state.user_email, f"Class added: {sub} on {day}.")
                    st.success("Class scheduled!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("Subject name is required.")
        st.markdown("</div>", unsafe_allow_html=True)

# ── 5. Quiz Arena ─────────────────────────────────────

elif page == "Quiz Arena":
    st.markdown("<div class='glass-card'><h1 style='margin:0;'>Quiz Arena</h1><p style='color:#a5b4fc;'>Adaptive quizzes with timers and leaderboards</p></div>", unsafe_allow_html=True)

    col_setup, col_board = st.columns([1, 1])

    with col_setup:
        st.markdown("<div class='glass-card'><h3>Build Your Quiz</h3>", unsafe_allow_html=True)
        q_subject = st.selectbox("Subject", ["Mathematics","Biology","Physics","Chemistry","Computer Science"])
        q_level   = st.selectbox("Level", ["Primary School","High School","University"])
        battle    = st.checkbox("Simulate Multiplayer Battle vs AI")

        if st.button("Start Quiz"):
            st.session_state.quiz_questions   = ai.generate_adaptive_quiz(q_subject, q_level)
            st.session_state.quiz_score       = 0
            st.session_state.quiz_timer_start = time.time()
            st.session_state.battle_mode      = battle
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_board:
        st.markdown("<div class='glass-card'><h3>Leaderboard</h3>", unsafe_allow_html=True)
        lb = pd.DataFrame([
            {"Rank":1, "Student": st.session_state.user_fullname + " (You)", "Score":"95%","Streak":"7 days"},
            {"Rank":2, "Student":"AI Bot Tutor",     "Score":"90%","Streak":"14 days"},
            {"Rank":3, "Student":"Classmate Alpha",  "Score":"82%","Streak":"3 days"},
            {"Rank":4, "Student":"Classmate Beta",   "Score":"60%","Streak":"0 days"},
        ])
        st.table(lb)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.quiz_questions:
        elapsed   = int(time.time() - st.session_state.quiz_timer_start)
        time_left = max(0, 60 - elapsed)

        st.markdown(f"<div class='glass-card'><h3>{q_subject} — {q_level}</h3>", unsafe_allow_html=True)
        if time_left == 0:
            st.error("Time's up! Submit your answers.")
        else:
            st.warning(f"Time remaining: {time_left}s")
        if st.session_state.battle_mode:
            st.info("Battle mode: race the AI!")

        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(st.session_state.quiz_questions):
                st.write(f"**Q{i+1}: {q['question']}**")
                user_answers[i] = st.radio("Answer:", q["options"], key=f"q_{i}")

            if st.form_submit_button("Submit Answers"):
                correct = 0
                total   = len(st.session_state.quiz_questions)
                review  = ""
                for i, q in enumerate(st.session_state.quiz_questions):
                    if user_answers[i] == q["answer"]:
                        correct += 1
                        review += f"<p style='color:#34d399;'>Q{i+1}: Correct — {user_answers[i]}</p>"
                    else:
                        review += f"<p style='color:#f87171;'>Q{i+1}: Incorrect — you chose {user_answers[i]}, answer is <b>{q['answer']}</b></p>"

                pct = int(correct / total * 100)
                db.add_quiz_record(st.session_state.user_email, q_subject, correct, total, pct, q_level)
                st.metric("Score", f"{correct}/{total} ({pct}%)")
                if pct >= 80:
                    st.success("Excellent work!")
                    st.balloons()
                else:
                    st.warning("Keep practising — review the answers below.")
                st.markdown(review, unsafe_allow_html=True)
                st.session_state.quiz_questions = []

        st.markdown("</div>", unsafe_allow_html=True)

# ── 6. Analytics ──────────────────────────────────────

elif page == "Analytics":
    st.markdown("<div class='glass-card'><h1 style='margin:0;'>Analytics</h1><p style='color:#a5b4fc;'>Focus tracking, quiz trends, and GPA prediction</p></div>", unsafe_allow_html=True)

    col_log, col_gpa = st.columns([1.2, 1])

    with col_log:
        st.markdown("<div class='glass-card'><h3>Log Study Session</h3>", unsafe_allow_html=True)
        with st.form("focus_form"):
            mins        = st.number_input("Duration (minutes)", min_value=5, max_value=480, value=60)
            sess_date   = st.date_input("Date", value=date.today())
            if st.form_submit_button("Record Session"):
                db.add_focus_session(st.session_state.user_email, sess_date, mins)
                db.add_notification(st.session_state.user_email, f"Logged {mins} minute study session.")
                st.success("Session recorded!")
                time.sleep(0.5)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_gpa:
        st.markdown("<div class='glass-card'><h3>Target GPA</h3>", unsafe_allow_html=True)
        new_gpa = st.slider("Set target GPA", 1.0, 4.0, gpa_target, 0.1)
        if st.button("Save Target"):
            db.update_user_gpa_target(st.session_state.user_email, new_gpa)
            st.success(f"Target GPA set to {new_gpa:.1f}!")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if PLOTLY_AVAILABLE:
        c1, c2 = st.columns(2)
        with c1:
            if quiz_records:
                df_q = pd.DataFrame(quiz_records, columns=["ID","Subject","Score","Total","Percentage","Date","Difficulty"])
                df_q["Date"] = pd.to_datetime(df_q["Date"])
                fig = px.line(df_q.sort_values("Date"), x="Date", y="Percentage", color="Subject",
                              markers=True, title="Quiz Scores Over Time", template="plotly_dark")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Take quizzes to see score trends.")

        with c2:
            if focus_sessions:
                df_f = pd.DataFrame(focus_sessions, columns=["ID","Date","Minutes"])
                df_f["Date"] = pd.to_datetime(df_f["Date"])
                fig = px.bar(df_f.sort_values("Date"), x="Date", y="Minutes",
                             title="Study Minutes Per Session", template="plotly_dark",
                             color_discrete_sequence=["#818cf8"])
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Log sessions to see productivity charts.")
    else:
        if quiz_records:
            df_q = pd.DataFrame(quiz_records, columns=["ID","Subject","Score","Total","Percentage","Date","Difficulty"])
            st.bar_chart(df_q.set_index("Date")["Percentage"])
        if focus_sessions:
            df_f = pd.DataFrame(focus_sessions, columns=["ID","Date","Minutes"])
            st.bar_chart(df_f.set_index("Date")["Minutes"])

    # GPA Prediction
    st.markdown("<div class='glass-card'><h3>GPA Prediction</h3>", unsafe_allow_html=True)
    if quiz_records:
        avg = sum(q[4] for q in quiz_records) / len(quiz_records)
        predicted = min(4.0, avg / 100.0 * 4.0 + 0.2)
        st.write(f"Quiz average: **{avg:.1f}%** → Predicted GPA: **{predicted:.2f}** / Target: **{gpa_target:.2f}**")
        if predicted >= gpa_target:
            st.success("On track to meet or exceed your target!")
        else:
            st.warning("Slightly below target — check recommendations below.")
    else:
        st.info("Complete quizzes to enable GPA prediction.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Recommendations
    st.markdown("<div class='glass-card'><h3>Study Recommendations</h3>", unsafe_allow_html=True)
    recs = ai.generate_study_recommendations(quiz_records, assignments)
    for r in recs:
        color = {"High": "#f87171", "Medium": "#fbbf24", "Low": "#34d399"}.get(r["priority"], "#64748b")
        st.markdown(f"""
        <div style='padding:10px;border-radius:10px;background:rgba(255,255,255,0.03);
                    border-left:4px solid {color};margin-bottom:8px;'>
            <strong>[{r['priority']}] {r['subject']}</strong>: {r['reason']}
            <em style='color:#64748b;'> → {r['action']}</em>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Report download
    st.markdown("<div class='glass-card'><h3>Download Report Card</h3>", unsafe_allow_html=True)
    rows = "".join(
        f"<tr><td>{q[1]}</td><td>{q[2]}/{q[3]}</td><td>{q[4]}%</td><td>{q[5]}</td></tr>"
        for q in quiz_records
    )
    report_html = f"""
    <html><head><style>
      body{{font-family:sans-serif;padding:20px}}
      table{{width:100%;border-collapse:collapse}}
      th,td{{border:1px solid #ccc;padding:8px;text-align:left}}
    </style></head><body>
      <h1>EduMate AI — Academic Report</h1>
      <p><strong>Student:</strong> {st.session_state.user_fullname}</p>
      <p><strong>Email:</strong> {st.session_state.user_email}</p>
      <p><strong>Generated:</strong> {date.today()}</p>
      <hr/>
      <h2>Quiz Records</h2>
      <table><tr><th>Subject</th><th>Score</th><th>Percentage</th><th>Date</th></tr>
      {rows}</table>
    </body></html>
    """
    st.download_button(
        "Download HTML Report",
        data=report_html,
        file_name=f"edumate_report_{st.session_state.user_fullname.replace(' ','_')}.html",
        mime="text/html",
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────
st.markdown("<div class='footer'>© 2026 EduMate AI</div>", unsafe_allow_html=True)
