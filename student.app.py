import os
import time
import sqlite3
import hashlib
from datetime import date

import streamlit as st
import pandas as pd

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ======================================================
# DATABASE SETUP
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "student_ai_assistant.db")

_conn = None


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def db_init():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        create_tables(_conn)
    return _conn


def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            gpa_target REAL DEFAULT 4.0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            subject TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            zoom_link TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            read INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            duration_minutes INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            description TEXT NOT NULL,
            target_date TEXT,
            completed INTEGER DEFAULT 0
        )
    """)

    conn.commit()


# ======================================================
# DATABASE FUNCTIONS
# ======================================================

def db_register_user(fullname, email, password, gpa_target=4.0):
    conn = db_init()
    hashed_password = _hash_password(password)
    try:
        conn.execute(
            "INSERT INTO users (fullname, email, password, gpa_target) VALUES (?, ?, ?, ?)",
            (fullname, email, hashed_password, gpa_target)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {e}")
        return False


def db_login_user(email, password):
    conn = db_init()
    hashed_password = _hash_password(password)
    cur = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hashed_password)
    )
    return cur.fetchone()


def db_get_user_gpa_target(user_email):
    conn = db_init()
    cur = conn.execute("SELECT gpa_target FROM users WHERE email=?", (user_email,))
    row = cur.fetchone()
    return row["gpa_target"] if row else 4.0


def db_update_gpa_target(user_email, new_gpa_target):
    conn = db_init()
    conn.execute("UPDATE users SET gpa_target=? WHERE email=?", (new_gpa_target, user_email))
    conn.commit()


def db_add_assignment(user_email, title, subject, due_date, priority):
    conn = db_init()
    conn.execute(
        "INSERT INTO assignments (user_email, title, subject, due_date, priority) VALUES (?, ?, ?, ?, ?)",
        (user_email, title, subject, due_date, priority)
    )
    conn.commit()


def db_get_assignments(user_email):
    conn = db_init()
    cur = conn.execute(
        "SELECT * FROM assignments WHERE user_email=? ORDER BY due_date ASC",
        (user_email,)
    )
    return cur.fetchall()


def db_update_assignment(assignment_id, title, subject, due_date, priority, status):
    conn = db_init()
    conn.execute(
        "UPDATE assignments SET title=?, subject=?, due_date=?, priority=?, status=? WHERE id=?",
        (title, subject, due_date, priority, status, assignment_id)
    )
    conn.commit()


def db_delete_assignment(assignment_id):
    conn = db_init()
    conn.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))
    conn.commit()


def db_add_timetable_entry(user_email, day_of_week, subject, start_time, end_time, zoom_link):
    conn = db_init()
    conn.execute(
        "INSERT INTO timetable (user_email, day_of_week, subject, start_time, end_time, zoom_link) VALUES (?, ?, ?, ?, ?, ?)",
        (user_email, day_of_week, subject, start_time, end_time, zoom_link)
    )
    conn.commit()


def db_get_timetable(user_email):
    conn = db_init()
    cur = conn.execute(
        "SELECT * FROM timetable WHERE user_email=? ORDER BY id DESC",
        (user_email,)
    )
    return cur.fetchall()


def db_delete_timetable_entry(entry_id):
    conn = db_init()
    conn.execute("DELETE FROM timetable WHERE id=?", (entry_id,))
    conn.commit()


def db_add_flashcard(user_email, subject, question, answer):
    conn = db_init()
    conn.execute(
        "INSERT INTO flashcards (user_email, subject, question, answer) VALUES (?, ?, ?, ?)",
        (user_email, subject, question, answer)
    )
    conn.commit()


def db_get_flashcards(user_email):
    conn = db_init()
    cur = conn.execute(
        "SELECT * FROM flashcards WHERE user_email=? ORDER BY id DESC",
        (user_email,)
    )
    return cur.fetchall()


def db_add_notification(user_email, message):
    conn = db_init()
    conn.execute(
        "INSERT INTO notifications (user_email, message) VALUES (?, ?)",
        (user_email, message)
    )
    conn.commit()


def db_get_notifications(user_email):
    conn = db_init()
    cur = conn.execute(
        "SELECT * FROM notifications WHERE user_email=? ORDER BY timestamp DESC",
        (user_email,)
    )
    return cur.fetchall()


def db_mark_notification_read(notification_id):
    conn = db_init()
    conn.execute("UPDATE notifications SET read=1 WHERE id=?", (notification_id,))
    conn.commit()


def db_get_or_update_streak(user_email):
    # Simple placeholder logic
    return 5, ["Consistency Badge"]


def db_add_quiz_record(user_email, subject, score, total_questions):
    conn = db_init()
    conn.execute(
        "INSERT INTO quiz_records (user_email, subject, score, total_questions) VALUES (?, ?, ?, ?)",
        (user_email, subject, score, total_questions)
    )
    conn.commit()


def db_get_quiz_records(user_email):
    conn = db_init()
    cur = conn.execute(
        "SELECT * FROM quiz_records WHERE user_email=? ORDER BY timestamp DESC",
        (user_email,)
    )
    return cur.fetchall()


def db_add_study_goal(user_email, description, target_date):
    conn = db_init()
    conn.execute(
        "INSERT INTO study_goals (user_email, description, target_date) VALUES (?, ?, ?)",
        (user_email, description, target_date)
    )
    conn.commit()


def db_get_study_goals(user_email):
    conn = db_init()
    cur = conn.execute(
        "SELECT * FROM study_goals WHERE user_email=? ORDER BY target_date ASC",
        (user_email,)
    )
    return cur.fetchall()


def db_update_study_goal(goal_id, description, target_date, completed):
    conn = db_init()
    conn.execute(
        "UPDATE study_goals SET description=?, target_date=?, completed=? WHERE id=?",
        (description, target_date, completed, goal_id)
    )
    conn.commit()


def db_delete_study_goal(goal_id):
    conn = db_init()
    conn.execute("DELETE FROM study_goals WHERE id=?", (goal_id,))
    conn.commit()


# ======================================================
# AI FUNCTIONS
# ======================================================

KNOWLEDGE_BASE = {
    "math": {
        "summary": "Mathematics is the study of numbers, quantity, structure, and change.",
        "concepts": ["Algebra", "Calculus", "Geometry", "Statistics"]
    },
    "biology": {
        "summary": "Biology is the study of living organisms.",
        "concepts": ["Cells", "Genetics", "Evolution", "Ecology"]
    },
    "computer science": {
        "summary": "Computer science studies computation and information processing.",
        "concepts": ["Algorithms", "Data Structures", "Programming", "Databases"]
    }
}


def ai_chat_response(prompt):
    text = prompt.lower()
    for subject, data in KNOWLEDGE_BASE.items():
        if subject in text:
            return f"{data['summary']}\n\nKey concepts: {', '.join(data['concepts'])}"
    return "I can help with summaries, flashcards, quizzes, assignments, and study planning."


def ai_generate_flashcards(text, subject=None):
    base_subject = subject if subject else "General"
    return [
        {
            "question": f"What is the main idea of {base_subject}?",
            "answer": "It is the core concept explained in the notes."
        },
        {
            "question": f"Define an important term from {base_subject}.",
            "answer": "It is a key term that appears in the study material."
        }
    ]


def ai_summarise_notes(text):
    return f"Summary: {text[:150]}..." if text else "No notes provided."


def ai_draw_concept_board(concept):
    return f"Concept board for '{concept}': main idea, related ideas, examples, and applications."


def ai_grammar_plagiarism_check(text):
    return {
        "score": 88,
        "plagiarism_percent": 12,
        "feedback": "Good overall writing. Improve sentence clarity and grammar in a few places.",
        "grammar_errors": ["Check subject-verb agreement.", "Improve punctuation in long sentences."],
        "plagiarism_sources": ["Possible similarity detected with public source."]
    }


def ai_generate_quiz_questions(subject, difficulty="Medium", num_questions=5):
    questions = []
    for i in range(num_questions):
        questions.append({
            "question": f"{subject.title()} question {i + 1} ({difficulty})",
            "options": ["A", "B", "C", "D"],
            "answer": "A"
        })
    return questions


def ai_predict_gpa(current_gpa, target_gpa, study_hours_per_week):
    if current_gpa >= target_gpa:
        return "You are already at or above your target GPA."
    if study_hours_per_week < 10:
        return "Increase study hours to improve your chances of reaching your target GPA."
    return "You have a good chance of reaching your target GPA with consistent effort."


# ======================================================
# STREAMLIT SETUP
# ======================================================

st.set_page_config(page_title="Student AI Assistant", page_icon="🎓", layout="wide")

st.markdown("""
<style>
.main-title {
    font-size: 3rem;
    font-weight: 800;
    text-align: center;
    color: #4a90e2;
}
.sub-title {
    text-align: center;
    color: #666;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

db_init()


# ======================================================
# SESSION STATE DEFAULTS
# ======================================================

defaults = {
    "logged_in": False,
    "user_email": "",
    "user_fullname": "",
    "chat_history": [],
    "quiz_questions": [],
    "quiz_score": 0,
    "quiz_total_questions": 0,
    "quiz_current_question": 0,
    "quiz_timer_start": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ======================================================
# AUTH SCREEN
# ======================================================

if not st.session_state.logged_in:
    st.markdown("<div class='main-title'>🎓 Student AI Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Your all-in-one study companion</div>", unsafe_allow_html=True)

    auth_mode = st.sidebar.selectbox("Access", ["Login", "Register"])

    if auth_mode == "Login":
        st.subheader("Login")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = db_login_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = user["email"]
                st.session_state.user_fullname = user["fullname"]
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    else:
        st.subheader("Register")

        fullname = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        gpa_target = st.number_input("Target GPA", min_value=0.0, max_value=5.0, value=4.0, step=0.1)

        if st.button("Register"):
            if not fullname or not email or not password:
                st.warning("Please fill all fields.")
            else:
                ok = db_register_user(fullname, email, password, gpa_target)
                if ok:
                    st.success("Registration successful. Please log in.")
                else:
                    st.error("Email already exists or database error.")

    st.stop()


# ======================================================
# MAIN APP
# ======================================================

st.sidebar.markdown(f"### 🎓 {st.session_state.user_fullname}")
st.sidebar.caption(st.session_state.user_email)

page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "AI Assistant", "Assignments", "Timetable", "Quiz Arena", "Analytics", "Settings"]
)

if st.sidebar.button("Logout"):
    for key, value in defaults.items():
        st.session_state[key] = value
    st.rerun()

user_email = st.session_state.user_email
assignments = db_get_assignments(user_email)
timetable = db_get_timetable(user_email)
streak, badges = db_get_or_update_streak(user_email)
notifications = db_get_notifications(user_email)
quiz_records = db_get_quiz_records(user_email)
study_goals = db_get_study_goals(user_email)


# ======================================================
# DASHBOARD
# ======================================================

if page == "Dashboard":
    st.header(f"Welcome, {st.session_state.user_fullname}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Streak", f"{streak} days")
    c2.metric("Assignments", len(assignments))
    c3.metric("Unread Notifications", len([n for n in notifications if n["read"] == 0]))

    st.subheader("Badges")
    if badges:
        st.write(", ".join(badges))
    else:
        st.write("No badges yet.")

    st.subheader("Study Goals")
    if study_goals:
        for goal in study_goals:
            st.write(f"- {goal['description']} | Due: {goal['target_date']} | Completed: {bool(goal['completed'])}")
    else:
        st.info("No study goals yet.")

    st.subheader("Today's Timetable")
    today = date.today().strftime("%A")
    todays_classes = [row for row in timetable if row["day_of_week"] == today]

    if todays_classes:
        st.dataframe(pd.DataFrame(todays_classes), use_container_width=True)
    else:
        st.info("No classes today.")


# ======================================================
# AI ASSISTANT
# ======================================================

elif page == "AI Assistant":
    st.header("AI Assistant")

    query = st.text_input("Ask a question")
    if st.button("Send") and query:
        response = ai_chat_response(query)
        st.session_state.chat_history.append(("You", query))
        st.session_state.chat_history.append(("Assistant", response))

    for sender, message in st.session_state.chat_history:
        st.write(f"**{sender}:** {message}")

    st.divider()
    st.subheader("Flashcard Generator")

    notes = st.text_area("Paste notes here")
    subject = st.text_input("Subject (optional)")

    if st.button("Generate Flashcards") and notes:
        cards = ai_generate_flashcards(notes, subject)
        for card in cards:
            st.write(f"**Q:** {card['question']}")
            st.write(f"**A:** {card['answer']}")


# ======================================================
# ASSIGNMENTS
# ======================================================

elif page == "Assignments":
    st.header("Assignments")

    with st.form("assignment_form"):
        title = st.text_input("Title")
        subject = st.text_input("Subject")
        due_date = st.date_input("Due Date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        submitted = st.form_submit_button("Add Assignment")

        if submitted:
            if title and subject:
                db_add_assignment(user_email, title, subject, due_date.isoformat(), priority)
                st.success("Assignment added.")
                st.rerun()
            else:
                st.warning("Please enter title and subject.")

    if assignments:
        df = pd.DataFrame(assignments, columns=assignments[0].keys())
        st.dataframe(df, use_container_width=True)

        st.subheader("Manage Assignments")
        for row in assignments:
            with st.expander(f"{row['title']} - {row['subject']}"):
                new_title = st.text_input("Title", value=row["title"], key=f"title_{row['id']}")
                new_subject = st.text_input("Subject", value=row["subject"], key=f"subject_{row['id']}")
                new_due_date = st.text_input("Due Date", value=row["due_date"], key=f"due_{row['id']}")
                new_priority = st.selectbox(
                    "Priority",
                    ["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(row["priority"]) if row["priority"] in ["Low", "Medium", "High"] else 1,
                    key=f"priority_{row['id']}"
                )
                new_status = st.selectbox(
                    "Status",
                    ["Pending", "Completed"],
                    index=0 if row["status"] == "Pending" else 1,
                    key=f"status_{row['id']}"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update", key=f"update_{row['id']}"):
                        db_update_assignment(
                            row["id"],
                            new_title,
                            new_subject,
                            new_due_date,
                            new_priority,
                            new_status
                        )
                        st.success("Assignment updated.")
                        st.rerun()

                with col2:
                    if st.button("Delete", key=f"delete_{row['id']}"):
                        db_delete_assignment(row["id"])
                        st.success("Assignment deleted.")
                        st.rerun()
    else:
        st.info("No assignments yet.")


# ======================================================
# TIMETABLE
# ======================================================

elif page == "Timetable":
    st.header("Timetable")

    with st.form("timetable_form"):
        day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        subject = st.text_input("Subject")
        start_time = st.text_input("Start Time (e.g. 09:00)")
        end_time = st.text_input("End Time (e.g. 10:00)")
        zoom_link = st.text_input("Zoom Link (optional)")
        submitted = st.form_submit_button("Add Entry")

        if submitted:
            if subject and start_time and end_time:
                db_add_timetable_entry(user_email, day, subject, start_time, end_time, zoom_link)
                st.success("Timetable entry added.")
                st.rerun()
            else:
                st.warning("Please fill all required fields.")

    if timetable:
        df = pd.DataFrame(timetable, columns=timetable[0].keys())
        st.dataframe(df, use_container_width=True)

        st.subheader("Manage Timetable")
        for row in timetable:
            with st.expander(f"{row['day_of_week']} - {row['subject']}"):
                new_day = st.selectbox(
                    "Day",
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(row["day_of_week"]),
                    key=f"day_{row['id']}"
                )
                new_subject = st.text_input("Subject", value=row["subject"], key=f"tsub_{row['id']}")
                new_start = st.text_input("Start Time", value=row["start_time"], key=f"start_{row['id']}")
                new_end = st.text_input("End Time", value=row["end_time"], key=f"end_{row['id']}")
                new_zoom = st.text_input("Zoom Link", value=row["zoom_link"] or "", key=f"zoom_{row['id']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Delete", key=f"del_t_{row['id']}"):
                        db_delete_timetable_entry(row["id"])
                        st.success("Timetable entry deleted.")
                        st.rerun()
                with col2:
                    if st.button("Save", key=f"save_t_{row['id']}"):
                        conn = db_init()
                        conn.execute(
                            "UPDATE timetable SET day_of_week=?, subject=?, start_time=?, end_time=?, zoom_link=? WHERE id=?",
                            (new_day, new_subject, new_start, new_end, new_zoom, row["id"])
                        )
                        conn.commit()
                        st.success("Timetable updated.")
                        st.rerun()
    else:
        st.info("No timetable entries yet.")


# ======================================================
# QUIZ ARENA
# ======================================================

elif page == "Quiz Arena":
    st.header("Quiz Arena")

    subject = st.selectbox("Subject", list(KNOWLEDGE_BASE.keys()))
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    num_questions = st.slider("Number of Questions", 1, 10, 5)

    if st.button("Start Quiz"):
        st.session_state.quiz_questions = ai_generate_quiz_questions(subject, difficulty, num_questions)
        st.session_state.quiz_score = 0
        st.session_state.quiz_total_questions = len(st.session_state.quiz_questions)
        st.session_state.quiz_current_question = 0
        st.session_state.quiz_timer_start = time.time()

    if st.session_state.quiz_questions:
        q = st.session_state.quiz_questions[st.session_state.quiz_current_question]

        st.write(f"**Question {st.session_state.quiz_current_question + 1}:** {q['question']}")
        answer = st.radio("Choose an answer", q["options"], key=f"ans_{st.session_state.quiz_current_question}")

        if st.button("Submit Answer"):
            if answer == q["answer"]:
                st.session_state.quiz_score += 1

            st.session_state.quiz_current_question += 1

            if st.session_state.quiz_current_question >= st.session_state.quiz_total_questions:
                st.success(f"Quiz finished. Score: {st.session_state.quiz_score}/{st.session_state.quiz_total_questions}")
                db_add_quiz_record(user_email, subject, st.session_state.quiz_score, st.session_state.quiz_total_questions)
                st.session_state.quiz_questions = []
            st.rerun()


# ======================================================
# ANALYTICS
# ======================================================

elif page == "Analytics":
    st.header("Analytics")

    if quiz_records:
        df = pd.DataFrame(quiz_records, columns=quiz_records[0].keys())
        df["Percentage"] = (df["score"] / df["total_questions"]) * 100
        st.dataframe(df, use_container_width=True)

        if PLOTLY_AVAILABLE:
            fig = px.line(df, x="timestamp", y="Percentage", color="subject", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No quiz data yet.")

    st.divider()
    st.subheader("GPA Prediction")

    current_gpa = st.number_input("Current GPA", min_value=0.0, max_value=5.0, value=3.0, step=0.01)
    study_hours = st.slider("Weekly Study Hours", 0, 50, 10)

    if st.button("Predict GPA"):
        prediction = ai_predict_gpa(current_gpa, db_get_user_gpa_target(user_email), study_hours)
        st.info(prediction)


# ======================================================
# SETTINGS
# ======================================================

elif page == "Settings":
    st.header("Settings")

    current_target = db_get_user_gpa_target(user_email)
    new_target = st.number_input("Target GPA", min_value=0.0, max_value=5.0, value=float(current_target), step=0.1)

    if st.button("Update GPA Target"):
        db_update_gpa_target(user_email, new_target)
        st.success("GPA target updated.")
        st.rerun()

    st.divider()
    st.subheader("Add Study Goal")

    goal_desc = st.text_input("Goal Description")
    goal_date = st.date_input("Target Date")

    if st.button("Add Goal"):
        if goal_desc:
            db_add_study_goal(user_email, goal_desc, goal_date.isoformat())
            st.success("Study goal added.")
            st.rerun()
        else:
            st.warning("Please enter a goal description.")

    st.divider()
    st.subheader("Study Goals")

    if study_goals:
        for goal in study_goals:
            with st.expander(goal["description"]):
                desc = st.text_input("Description", value=goal["description"], key=f"goal_desc_{goal['id']}")
                tdate = st.text_input("Target Date", value=goal["target_date"] or "", key=f"goal_date_{goal['id']}")
                completed = st.checkbox("Completed", value=bool(goal["completed"]), key=f"goal_comp_{goal['id']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save", key=f"save_goal_{goal['id']}"):
                        db_update_study_goal(goal["id"], desc, tdate, int(completed))
                        st.success("Goal updated.")
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"del_goal_{goal['id']}"):
                        db_delete_study_goal(goal["id"])
                        st.success("Goal deleted.")
                        st.rerun()
    else:
        st.info("No study goals yet.")


# ======================================================
# NOTIFICATION SIDEBAR INFO
# ======================================================

with st.sidebar.expander("Notifications"):
    if notifications:
        for notif in notifications[:10]:
            st.write(f"- {notif['message']}")
    else:
        st.write("No notifications.")

with st.sidebar.expander("Quick Tools"):
    if st.button("Add Demo Notification"):
        db_add_notification(user_email, "This is a demo notification.")
        st.success("Notification added.")
        st.rerun()
# =====================================================
# FOOTER
# =====================================================

st.markdown("---")
st.caption("© 2026 EduMate AI")

# ======================================================
# RUN:
# streamlit run app.py
# ======================================================
