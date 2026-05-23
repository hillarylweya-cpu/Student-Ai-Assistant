import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time
import sqlite3
import hashlib
import json
import os
from difflib import get_close_matches
import random

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ═══════════════════════════════════════════════════════
# DATABASE MODULE (originally database.py)
# ═══════════════════════════════════════════════════════

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edumate_ai.db")

_conn = None

def db_get_connection():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        db__init_tables(_conn)
    return _conn

def db__init_tables(conn):
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        gpa_target REAL DEFAULT 4.0
    );
    CREATE TABLE IF NOT EXISTS assignments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        title TEXT NOT NULL,
        subject TEXT,
        due_date DATE,
        priority TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY (user_email) REFERENCES users(email)
    );
    CREATE TABLE IF NOT EXISTS timetable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        day_of_week TEXT NOT NULL,
        subject TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        zoom_link TEXT,
        FOREIGN KEY (user_email) REFERENCES users(email)
    );
    CREATE TABLE IF NOT EXISTS flashcards(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        FOREIGN KEY (user_email) REFERENCES users(email)
    );
    CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        read INTEGER DEFAULT 0,
        FOREIGN KEY (user_email) REFERENCES users(email)
    );
    CREATE TABLE IF NOT EXISTS focus_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        duration_minutes INTEGER,
        FOREIGN KEY (user_email) REFERENCES users(email)
    );
    CREATE TABLE IF NOT EXISTS quiz_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_email) REFERENCES users(email)
    );
    CREATE TABLE IF NOT EXISTS study_goals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        description TEXT NOT NULL,
        target_date DATE,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY (user_email) REFERENCES users(email)
    );
    """)
    conn.commit()

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def db_register_user(fullname, email, password, gpa_target=4.0):
    conn = db_get_connection()
    hashed_password = _hash_password(password)
    try:
        conn.execute(
            "INSERT INTO users (fullname, email, password, gpa_target) VALUES (?, ?, ?, ?)",
            (fullname, email, hashed_password, gpa_target)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Email already exists

def db_login_user(email, password):
    conn = db_get_connection()
    hashed_password = _hash_password(password)
    cursor = conn.execute(
        "SELECT id, fullname, email, gpa_target FROM users WHERE email=? AND password=?",
        (email, hashed_password)
    )
    user = cursor.fetchone()
    return user

def db_get_user_gpa_target(user_email):
    conn = db_get_connection()
    cursor = conn.execute("SELECT gpa_target FROM users WHERE email=?", (user_email,))
    result = cursor.fetchone()
    return result[0] if result else 4.0

def db_update_gpa_target(user_email, new_gpa_target):
    conn = db_get_connection()
    conn.execute("UPDATE users SET gpa_target=? WHERE email=?", (new_gpa_target, user_email))
    conn.commit()

# --- Assignments ---
def db_add_assignment(user_email, title, subject, due_date, priority):
    conn = db_get_connection()
    conn.execute(
        "INSERT INTO assignments(user_email, title, subject, due_date, priority) VALUES(?, ?, ?, ?, ?)",
        (user_email, title, subject, due_date, priority)
    )
    conn.commit()

def db_get_assignments(user_email):
    conn = db_get_connection()
    cursor = conn.execute("SELECT id, title, subject, due_date, priority, status FROM assignments WHERE user_email=?", (user_email,))
    return cursor.fetchall()

def db_update_assignment(assignment_id, title, subject, due_date, priority, status):
    conn = db_get_connection()
    conn.execute(
        "UPDATE assignments SET title=?, subject=?, due_date=?, priority=?, status=? WHERE id=?",
        (title, subject, due_date, priority, status, assignment_id)
    )
    conn.commit()

def db_delete_assignment(assignment_id):
    conn = db_get_connection()
    conn.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))
    conn.commit()

# --- Timetable ---
def db_add_timetable_entry(user_email, day_of_week, subject, start_time, end_time, zoom_link):
    conn = db_get_connection()
    conn.execute(
        "INSERT INTO timetable(user_email, day_of_week, subject, start_time, end_time, zoom_link) VALUES(?, ?, ?, ?, ?, ?)",
        (user_email, day_of_week, subject, start_time, end_time, zoom_link)
    )
    conn.commit()

def db_get_timetable(user_email):
    conn = db_get_connection()
    cursor = conn.execute(
        "SELECT id, day_of_week, subject, start_time, end_time, zoom_link FROM timetable WHERE user_email=?",
        (user_email,)
    )
    return cursor.fetchall()

def db_update_timetable_entry(entry_id, day_of_week, subject, start_time, end_time, zoom_link):
    conn = db_get_connection()
    conn.execute(
        "UPDATE timetable SET day_of_week=?, subject=?, start_time=?, end_time=?, zoom_link=? WHERE id=?",
        (day_of_week, subject, start_time, end_time, zoom_link, entry_id)
    )
    conn.commit()

def db_delete_timetable_entry(entry_id):
    conn = db_get_connection()
    conn.execute("DELETE FROM timetable WHERE id=?", (entry_id,))
    conn.commit()

# --- Flashcards ---
def db_add_flashcard(user_email, subject, question, answer):
    conn = db_get_connection()
    conn.execute(
        "INSERT INTO flashcards(user_email, subject, question, answer) VALUES(?, ?, ?, ?)",
        (user_email, subject, question, answer)
    )
    conn.commit()

def db_get_flashcards(user_email, subject=None):
    conn = db_get_connection()
    if subject:
        cursor = conn.execute("SELECT id, subject, question, answer FROM flashcards WHERE user_email=? AND subject=?", (user_email, subject))
    else:
        cursor = conn.execute("SELECT id, subject, question, answer FROM flashcards WHERE user_email=?", (user_email,))
    return cursor.fetchall()

def db_update_flashcard(flashcard_id, subject, question, answer):
    conn = db_get_connection()
    conn.execute(
        "UPDATE flashcards SET subject=?, question=?, answer=? WHERE id=?",
        (subject, question, answer, flashcard_id)
    )
    conn.commit()

def db_delete_flashcard(flashcard_id):
    conn = db_get_connection()
    conn.execute("DELETE FROM flashcards WHERE id=?", (flashcard_id,))
    conn.commit()

# --- Notifications ---
def db_add_notification(user_email, message):
    conn = db_get_connection()
    conn.execute(
        "INSERT INTO notifications(user_email, message) VALUES(?, ?)",
        (user_email, message)
    )
    conn.commit()

def db_get_notifications(user_email):
    conn = db_get_connection()
    return conn.execute(
        "SELECT id, message, timestamp, read FROM notifications WHERE user_email=? ORDER BY timestamp DESC",
        (user_email,)
    ).fetchall()

def db_mark_notifications_read(user_email):
    conn = db_get_connection()
    conn.execute("UPDATE notifications SET read=1 WHERE user_email=?", (user_email,))
    conn.commit()

# --- Focus Sessions ---
def db_add_focus_session(user_email, start_time, end_time, duration_minutes):
    conn = db_get_connection()
    conn.execute(
        "INSERT INTO focus_sessions(user_email, start_time, end_time, duration_minutes) VALUES(?, ?, ?, ?)",
        (user_email, start_time, end_time, duration_minutes)
    )
    conn.commit()

def db_get_focus_sessions(user_email):
    conn = db_get_connection()
    cursor = conn.execute(
        "SELECT id, start_time, end_time, duration_minutes FROM focus_sessions WHERE user_email=? ORDER BY start_time DESC",
        (user_email,)
    )
    return cursor.fetchall()

# --- Quiz Records ---
def db_add_quiz_record(user_email, subject, score, total_questions):
    conn = db_get_connection()
    conn.execute(
        "INSERT INTO quiz_records(user_email, subject, score, total_questions) VALUES(?, ?, ?, ?)",
        (user_email, subject, score, total_questions)
    )
    conn.commit()

def db_get_quiz_records(user_email):
    conn = db_get_connection()
    cursor = conn.execute(
        "SELECT id, subject, score, total_questions, timestamp FROM quiz_records WHERE user_email=? ORDER BY timestamp DESC",
        (user_email,)
    )
    return cursor.fetchall()

def db_get_all_quizzes_by_subject(subject):
    # This is a placeholder. In a real app, you might have a global quiz bank.
    # For now, it returns dummy data.
    return [
        {"question": f"What is {subject} concept 1?", "options": ["A", "B", "C", "D"], "answer": "A"},
        {"question": f"What is {subject} concept 2?", "options": ["W", "X", "Y", "Z"], "answer": "W"}
    ]

# --- Study Goals ---
def db_add_study_goal(user_email, description, target_date):
    conn = db_get_connection()
    conn.execute(
        "INSERT INTO study_goals(user_email, description, target_date) VALUES(?, ?, ?)",
        (user_email, description, target_date)
    )
    conn.commit()

def db_get_study_goals(user_email):
    conn = db_get_connection()
    cursor = conn.execute(
        "SELECT id, description, target_date, completed FROM study_goals WHERE user_email=? ORDER BY target_date ASC",
        (user_email,)
    )
    return cursor.fetchall()

def db_update_study_goal(goal_id, description, target_date, completed):
    conn = db_get_connection()
    conn.execute(
        "UPDATE study_goals SET description=?, target_date=?, completed=? WHERE id=?",
        (description, target_date, completed, goal_id)
    )
    conn.commit()

def db_delete_study_goal(goal_id):
    conn = db_get_connection()
    conn.execute("DELETE FROM study_goals WHERE id=?", (goal_id,))
    conn.commit()

# --- Streak/Badges (Placeholder) ---
def db_get_or_update_streak(user_email):
    # In a real app, this would involve more complex logic to track login/activity streaks.
    # For simplicity, returning a fixed streak and empty badges.
    return 5, [] # streak, badges


# ═══════════════════════════════════════════════════════
# AI ENGINE MODULE (originally ai_engine.py)
# ═══════════════════════════════════════════════════════

# Simplified knowledge base for demonstration
KNOWLEDGE_BASE = {
    "math": {
        "summary": "Mathematics is the study of quantity, structure, space, and change.",
        "concepts": ["Algebra", "Calculus", "Geometry", "Statistics"],
        "diagrams": ["Equation graphs", "Geometric shapes"],
        "flashcards": [
            {"q": "What is the Pythagorean theorem?", "a": "a² + b² = c²"},
            {"q": "Derivative of x^n?", "a": "n*x^(n-1)"}
        ]
    },
    "biology": {
        "summary": "Biology is the natural science that studies life and living organisms.",
        "concepts": ["Cell biology", "Genetics", "Ecology", "Evolution"],
        "diagrams": ["Cell structure", "DNA double helix"],
        "flashcards": [
            {"q": "What is ATP?", "a": "Adenosine Triphosphate, energy currency of the cell"},
            {"q": "Stages of Mitosis?", "a": "Prophase, Metaphase, Anaphase, Telophase"}
        ]
    },
    "computer science": {
        "summary": "Computer science is the study of computation, automation, and information.",
        "concepts": ["Algorithms", "Data Structures", "Programming Languages", "Operating Systems"],
        "diagrams": ["Flowcharts", "UML diagrams"],
        "flashcards": [
            {"q": "What is a 'for loop'?", "a": "A control flow statement for iteration"},
            {"q": "What does SQL stand for?", "a": "Structured Query Language"}
        ]
    },
    # Add other subjects as needed
}

def ai_get_subject_info(subject, info_type):
    subject_lower = subject.lower()
    for key, data in KNOWLEDGE_BASE.items():
        if get_close_matches(subject_lower, [key], n=1, cutoff=0.7):
            return data.get(info_type)
    return None

def ai_chat_response(prompt):
    prompt_lower = prompt.lower()
    response = "I'm sorry, I don't have information on that specific query yet. Please try another educational topic."

    # General subject queries
    for subject, data in KNOWLEDGE_BASE.items():
        if subject in prompt_lower:
            if "summary" in prompt_lower or "about" in prompt_lower:
                response = f"Here's a summary of {subject}: {data['summary']}"
            elif "concepts" in prompt_lower:
                response = f"Key concepts in {subject}: {', '.join(data['concepts'])}"
            elif "diagrams" in prompt_lower or "draw" in prompt_lower:
                response = f"Common diagrams in {subject} include: {', '.join(data['diagrams'])}. (Image generation not supported directly in chat, but I can describe them!)"
            elif "flashcards" in prompt_lower or "quiz me" in prompt_lower:
                if data['flashcards']:
                    flashcard = random.choice(data['flashcards'])
                    response = f"Here's a flashcard for {subject}:\n**Question:** {flashcard['q']}\n**Answer:** {flashcard['a']}"
                else:
                    response = f"I don't have flashcards for {subject} yet."
            elif "history" in prompt_lower:
                response = f"I cannot provide historical context."
            elif "problem" in prompt_lower:
                response = f"What kind of {subject} problem do you have? I can help with basic concepts."
            return response

    # Specific query types
    if any(kw in prompt_lower for kw in ("python", "code", "programming")):
        response = (
            "Here is a Python template to get you started:\n"
            "```python\n"
            "def solve_problem(data):\n"
            "    # Step 1: Understand the input\n"
            "    # Step 2: Apply logic or formula\n"
            "    # Step 3: Return or print the result\n"
            "    return data\n\n"
            "print(solve_problem('EduMate AI'))\n"
            "```"
        )
    elif any(kw in prompt_lower for kw in ("essay", "write", "draft", "outline")):
        response = (
            "**Essay outline**\n\n"
            "1. **Introduction** — background context and a clear thesis statement.\n"
            "2. **Body 1** — primary argument with supporting evidence.\n"
            "3. **Body 2** — secondary argument and analysis.\n"
            "4. **Counter-argument** — acknowledge opposing views and refute logically.\n"
            "5. **Conclusion** — restate thesis, summarise, and leave a lasting impression."
        )
    return response

def ai_generate_flashcards(text, subject=None):
    # Placeholder for generating flashcards from text
    return [
        {"question": "Generated Q1", "answer": "Generated A1"},
        {"question": "Generated Q2", "answer": "Generated A2"}
    ]

def ai_summarise_notes(text):
    # Placeholder for summarising notes
    return f"Summary of your notes: {text[:50]}..."

def ai_draw_concept_board(concept):
    # Placeholder for generating a concept board (e.g., a textual description or a link to an image service)
    return f"A concept board for '{concept}' would visually link related ideas like (Idea A) -> (Idea B) -> (Idea C)."

def ai_grammar_plagiarism_check(text):
    # Placeholder for grammar and plagiarism check
    return {
        "score": random.randint(60, 99),
        "plagiarism_percent": random.randint(5, 25),
        "feedback": "Overall good, but check for sentence structure variation.",
        "grammar_errors": ["Fragment: 'Running quickly.' (Consider: 'He was running quickly.')"],
        "plagiarism_sources": ["Source 1: wikipedia.org (12%)", "Source 2: example.com (3%)"]
    }

def ai_generate_quiz_questions(subject, difficulty="Medium", num_questions=5):
    # Placeholder for generating quiz questions
    questions = []
    sample_options = ["Option A", "Option B", "Option C", "Option D"]
    for i in range(num_questions):
        questions.append({
            "question": f"Generated {subject} question {i+1} (Difficulty: {difficulty})",
            "options": random.sample(sample_options, 4),
            "answer": random.choice(sample_options)
        })
    return questions

def ai_grade_assignment(submission_text, assignment_details):
    # Placeholder for grading an assignment
    return {
        "grade": "B+",
        "feedback": "Good effort, but needs more detailed analysis in section 3. Formatting is excellent.",
        "plagiarism_score": 15
    }

def ai_predict_gpa(current_gpa, target_gpa, study_hours_per_week):
    # Placeholder for GPA prediction
    # This would involve a more complex model based on historical data and study patterns
    if study_hours_per_week < 10 and target_gpa > current_gpa:
        return f"To reach a GPA of {target_gpa} from {current_gpa} with {study_hours_per_week} hours/week, it might be challenging. Consider increasing your study time or focusing on specific weaknesses."
    elif study_hours_per_week >= 10 and target_gpa > current_gpa:
        return f"With {study_hours_per_week} hours/week, reaching a GPA of {target_gpa} from {current_gpa} is achievable with consistent effort and effective study strategies."
    else:
        return "Keep up the good work!"

# ═══════════════════════════════════════════════════════
# STREAMLIT APP LOGIC (originally app.py)
# ═══════════════════════════════════════════════════════

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

html, body, [class*="css"]  {
    font-family: 'Outfit', sans-serif;
    color: #333333;
}
h1, h2, h3, h4, h5, h6 {
    color: #2c3e50;
    font-weight: 600;
}
.main-title {
    font-size: 3.5em;
    font-weight: 800;
    color: #4a90e2;
    text-align: center;
    margin-top: 50px;
    margin-bottom: 10px;
}
.sub-title {
    font-size: 1.5em;
    font-weight: 300;
    color: #666666;
    text-align: center;
    margin-bottom: 50px;
}
.stButton>button {
    background-color: #4a90e2;
    color: white;
    border-radius: 5px;
    border: none;
    padding: 10px 20px;
    font-size: 1em;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    background-color: #357ABD;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.stTextInput>div>div>input {
    border-radius: 5px;
    border: 1px solid #ddd;
    padding: 10px;
}
.glass-card {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding: 20px;
    margin-bottom: 20px;
}
.sidebar .sidebar-content {
    background: linear-gradient(to bottom, #4a90e2, #6a82fb);
    color: white;
}
.sidebar .sidebar-content h2 {
    color: white !important;
}
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #f1f1f1;
    color: #888;
    text-align: center;
    padding: 10px;
    font-size: 0.8em;
}
/* Style for success/info/warning/error messages */
.stAlert {
    border-radius: 5px;
}
.stAlert.info, .stAlert.success, .stAlert.warning, .stAlert.error {
    background-color: rgba(255, 255, 255, 0.85); /* Slightly transparent white for glass effect */
    border-left: 5px solid; /* Color will be added by Streamlit */
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
/* Adjust specific Streamlit elements */
.stRadio > label {
    font-weight: 600;
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
    "quiz_total_questions": 0,
    "quiz_current_question": 0,
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

    col_form, col_features = st.columns([1.2, 1])

    with col_form:
        if auth_tab == "Login":
            st.markdown("<div class='glass-card'><h2 style='text-align:center;'>Sign In</h2>", unsafe_allow_html=True)
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.button("Sign In"):
                user = db_login_user(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_email = user[2]
                    st.session_state.user_fullname = user[1]
                    st.success(f"Welcome back, {user[1]}!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
            st.markdown("</div>", unsafe_allow_html=True)

        elif auth_tab == "Register":
            st.markdown("<div class='glass-card'><h2 style='text-align:center;'>Register</h2>", unsafe_allow_html=True)
            fullname = st.text_input("Full Name")
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            gpa_target = st.number_input("Target GPA (e.g., 4.0)", min_value=0.0, max_value=5.0, value=4.0, step=0.1)

            if st.button("Register"):
                if fullname and email and password:
                    if db_register_user(fullname, email, password, gpa_target):
                        st.success("Registration successful! Please log in.")
                        # Optionally auto-login or switch to login tab
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.user_fullname = fullname
                        st.rerun()
                    else:
                        st.error("Email already registered or an error occurred.")
                else:
                    st.warning("Please fill in all fields.")
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
    "Settings" # Added a settings page for GPA target
])

if st.sidebar.button("Logout"):
    for key in defaults:
        st.session_state[key] = defaults[key]
    st.rerun()

# Fetch data once (or cache with st.cache_data)
user_email = st.session_state.user_email
assignments = db_get_assignments(user_email)
timetable = db_get_timetable(user_email)
streak, badges = db_get_or_update_streak(user_email)
notifications = db_get_notifications(user_email)
quiz_records = db_get_quiz_records(user_email)
focus_sessions = db_get_focus_sessions(user_email)
gpa_target = db_get_user_gpa_target(user_email)
study_goals = db_get_study_goals(user_email)

# ── 1. Dashboard ──────────────────────────────────────
if page == "Dashboard":
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    now_str = datetime.now().strftime("%I:%M %p")

    st.markdown(f"## {greeting}, {st.session_state.user_fullname}!")
    st.write(f"It's {now_str}.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='glass-card'><h3>🔥 Streak</h3><p style='font-size:2em;'>{streak} Days</p></div>", unsafe_allow_html=True)
    with col2:
        upcoming_assignments = [a for a in assignments if a[5] == 'Pending' and datetime.strptime(a[3], '%Y-%m-%d').date() >= date.today()]
        st.markdown(f"<div class='glass-card'><h3>📚 Upcoming Assignments</h3><p style='font-size:2em;'>{len(upcoming_assignments)}</p></div>", unsafe_allow_html=True)
    with col3:
        unread_notifications = [n for n in notifications if n[3] == 0]
        st.markdown(f"<div class='glass-card'><h3>🔔 Notifications</h3><p style='font-size:2em;'>{len(unread_notifications)} new</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Your Study Goals")
    if study_goals:
        for goal_id, desc, target_date_str, completed in study_goals:
            col_goal, col_status, col_actions = st.columns([0.6, 0.2, 0.2])
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            with col_goal:
                st.markdown(f"- {desc} (Due: {target_date.strftime('%b %d, %Y')})")
            with col_status:
                is_completed = col_status.checkbox("Completed", value=bool(completed), key=f"goal_{goal_id}")
                if is_completed != bool(completed):
                    db_update_study_goal(goal_id, desc, target_date_str, int(is_completed))
                    st.rerun()
            with col_actions:
                if col_actions.button("Delete", key=f"delete_goal_{goal_id}"):
                    db_delete_study_goal(goal_id)
                    st.rerun()
    else:
        st.info("No study goals set yet. Add some in the 'Settings' page!")

    st.subheader("Today's Timetable")
    today = date.today().strftime("%A") # e.g., 'Friday'
    today_timetable = [entry for entry in timetable if entry[1] == today]
    if today_timetable:
        df_timetable = pd.DataFrame(today_timetable, columns=["ID", "Day", "Subject", "Start", "End", "Zoom Link"])
        st.table(df_timetable[["Subject", "Start", "End", "Zoom Link"]])
    else:
        st.info("No classes scheduled for today.")


# ── 2. AI Assistant ───────────────────────────────────
elif page == "AI Assistant":
    st.header("AI Assistant")

    st.markdown("Ask me anything about your studies, generate content, or get help!")

    tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Flashcard Generator", "Note Summariser", "Concept Board"])

    with tab1:
        st.subheader("AI Chat")
        user_query = st.text_input("Ask EduMate AI:")
        if st.button("Send"):
            if user_query:
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                ai_response = ai_chat_response(user_query)
                st.session_state.chat_history.append({"role": "ai", "content": ai_response})
            else:
                st.warning("Please enter a query.")

        for chat_message in st.session_state.chat_history:
            if chat_message["role"] == "user":
                st.markdown(f"**You:** {chat_message['content']}")
            else:
                st.markdown(f"**EduMate AI:** {chat_message['content']}")

    with tab2:
        st.subheader("Flashcard Generator")
        flashcard_text = st.text_area("Paste text to generate flashcards from:", height=150)
        flashcard_subject = st.text_input("Subject for flashcards (optional):")
        if st.button("Generate Flashcards"):
            if flashcard_text:
                generated_flashcards = ai_generate_flashcards(flashcard_text, flashcard_subject)
                st.success(f"Generated {len(generated_flashcards)} flashcards!")
                for i, fc in enumerate(generated_flashcards):
                    st.markdown(f"**Flashcard {i+1}**")
                    st.write(f"**Q:** {fc['question']}")
                    st.write(f"**A:** {fc['answer']}")
                    if flashcard_subject:
                        if st.button(f"Add to {flashcard_subject} collection", key=f"add_fc_{i}"):
                            db_add_flashcard(user_email, flashcard_subject, fc['question'], fc['answer'])
                            st.success("Flashcard added!")
            else:
                st.warning("Please paste some text first.")

    with tab3:
        st.subheader("Note Summariser")
        notes_to_summarise = st.text_area("Paste your notes here:", height=200)
        if st.button("Summarise Notes"):
            if notes_to_summarise:
                summary = ai_summarise_notes(notes_to_summarise)
                st.info(summary)
            else:
                st.warning("Please paste some notes to summarise.")

    with tab4:
        st.subheader("Concept Board Generator")
        concept_to_draw = st.text_input("Enter a concept to visualise:")
        if st.button("Draw Concept Board"):
            if concept_to_draw:
                concept_board_description = ai_draw_concept_board(concept_to_draw)
                st.info(concept_board_description)
            else:
                st.warning("Please enter a concept.")

# ── 3. Assignments ────────────────────────────────────
elif page == "Assignments":
    st.header("Assignments & Study Goals")

    tab1, tab2, tab3 = st.tabs(["My Assignments", "Grammar & Plagiarism Check", "Study Goals"])

    with tab1:
        st.subheader("My Assignments")
        if st.button("Add New Assignment"):
            st.session_state.draft_assignment = {"title": "", "subject": "", "priority": "Medium", "difficulty": "Medium"}
            st.session_state.show_assignment_form = True

        if "show_assignment_form" in st.session_state and st.session_state.show_assignment_form:
            with st.form("new_assignment_form"):
                st.write("Add/Edit Assignment")
                title = st.text_input("Title", value=st.session_state.draft_assignment["title"])
                subject = st.text_input("Subject", value=st.session_state.draft_assignment["subject"])
                due_date = st.date_input("Due Date", value=datetime.today().date() + timedelta(days=7))
                priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(st.session_state.draft_assignment["priority"]))
                status = st.selectbox("Status", ["Pending", "In Progress", "Completed", "Overdue"], index=0) # Default status for new

                submitted = st.form_submit_button("Save Assignment")
                if submitted:
                    if title and subject:
                        db_add_assignment(user_email, title, subject, due_date.strftime('%Y-%m-%d'), priority)
                        st.success("Assignment added!")
                        st.session_state.show_assignment_form = False
                        st.rerun()
                    else:
                        st.error("Title and Subject are required.")
                if st.form_submit_button("Cancel"):
                    st.session_state.show_assignment_form = False
                    st.rerun()

        if assignments:
            df_assignments = pd.DataFrame(assignments, columns=["ID", "Title", "Subject", "Due Date", "Priority", "Status"])
            df_assignments['Due Date'] = pd.to_datetime(df_assignments['Due Date']).dt.date

            st.dataframe(df_assignments.drop('ID', axis=1), use_container_width=True)

            st.subheader("Manage Existing Assignments")
            assignment_to_manage = st.selectbox("Select an assignment to update/delete:", [""] + [f"{a[1]} ({a[3]})" for a in assignments])
            if assignment_to_manage:
                selected_id = [a[0] for a in assignments if f"{a[1]} ({a[3]})" == assignment_to_manage][0]
                selected_assignment = next(a for a in assignments if a[0] == selected_id)

                with st.form(f"edit_assignment_form_{selected_id}"):
                    st.write(f"Editing: {selected_assignment[1]}")
                    edit_title = st.text_input("Title", value=selected_assignment[1])
                    edit_subject = st.text_input("Subject", value=selected_assignment[2])
                    edit_due_date = st.date_input("Due Date", value=datetime.strptime(selected_assignment[3], '%Y-%m-%d').date())
                    edit_priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(selected_assignment[4]))
                    edit_status = st.selectbox("Status", ["Pending", "In Progress", "Completed", "Overdue"], index=["Pending", "In Progress", "Completed", "Overdue"].index(selected_assignment[5]))

                    col_update, col_delete = st.columns(2)
                    with col_update:
                        if st.form_submit_button("Update Assignment"):
                            db_update_assignment(selected_id, edit_title, edit_subject, edit_due_date.strftime('%Y-%m-%d'), edit_priority, edit_status)
                            st.success("Assignment updated!")
                            st.rerun()
                    with col_delete:
                        if st.form_submit_button("Delete Assignment"):
                            db_delete_assignment(selected_id)
                            st.success("Assignment deleted!")
                            st.rerun()
        else:
            st.info("No assignments added yet. Use the 'Add New Assignment' button to get started!")

    with tab2:
        st.markdown("<div class='glass-card'><h3>Grammar & Plagiarism Scanner</h3>", unsafe_allow_html=True)
        check_text = st.text_area("Paste essay or draft here…", height=140)
        if st.button("Run Scan"):
            if check_text.strip():
                result = ai_grammar_plagiarism_check(check_text)
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

    with tab3:
        st.subheader("My Study Goals")
        new_goal_desc = st.text_input("New Study Goal Description")
        new_goal_date = st.date_input("Target Date", value=datetime.today().date() + timedelta(days=30))
        if st.button("Add Study Goal"):
            if new_goal_desc:
                db_add_study_goal(user_email, new_goal_desc, new_goal_date.strftime('%Y-%m-%d'))
                st.success("Study goal added!")
                st.rerun()
            else:
                st.warning("Please enter a description for your goal.")

        if study_goals:
            st.markdown("---")
            st.write("### Current Goals")
            for goal_id, desc, target_date_str, completed in study_goals:
                col_goal, col_status, col_actions = st.columns([0.6, 0.2, 0.2])
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
                with col_goal:
                    st.markdown(f"- {desc} (Due: {target_date.strftime('%b %d, %Y')})")
                with col_status:
                    is_completed = col_status.checkbox("Completed", value=bool(completed), key=f"goal_edit_{goal_id}")
                    if is_completed != bool(completed):
                        db_update_study_goal(goal_id, desc, target_date_str, int(is_completed))
                        st.rerun()
                with col_actions:
                    if col_actions.button("Delete", key=f"delete_goal_edit_{goal_id}"):
                        db_delete_study_goal(goal_id)
                        st.rerun()
        else:
            st.info("You haven't set any study goals yet.")


# ── 4. Timetable ──────────────────────────────────────
elif page == "Timetable":
    st.header("My Timetable")

    st.subheader("Add New Timetable Entry")
    with st.form("new_timetable_entry"):
        day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        subject = st.text_input("Subject/Course Name")
        start_time_str = st.time_input("Start Time", value=datetime.now().time())
        end_time_str = st.time_input("End Time", value=(datetime.now() + timedelta(hours=1)).time())
        zoom_link = st.text_input("Zoom/Meeting Link (optional)")

        submitted = st.form_submit_button("Add Entry")
        if submitted:
            if subject:
                db_add_timetable_entry(user_email, day, subject, start_time_str.strftime('%H:%M'), end_time_str.strftime('%H:%M'), zoom_link)
                st.success("Timetable entry added!")
                st.rerun()
            else:
                st.error("Subject is required.")

    st.markdown("---")
    st.subheader("Current Timetable")

    if timetable:
        df_timetable = pd.DataFrame(timetable, columns=["ID", "Day", "Subject", "Start Time", "End Time", "Zoom Link"])
        
        # Order days correctly
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df_timetable["Day"] = pd.Categorical(df_timetable["Day"], categories=day_order, ordered=True)
        df_timetable = df_timetable.sort_values(by=["Day", "Start Time"])

        st.dataframe(df_timetable.drop("ID", axis=1), use_container_width=True)

        st.subheader("Manage Timetable Entries")
        entry_to_manage = st.selectbox("Select an entry to update/delete:", [""] + [f"{e[2]} on {e[1]} at {e[3]}" for e in timetable])
        if entry_to_manage:
            selected_id = [e[0] for e in timetable if f"{e[2]} on {e[1]} at {e[3]}" == entry_to_manage][0]
            selected_entry = next(e for e in timetable if e[0] == selected_id)

            with st.form(f"edit_timetable_form_{selected_id}"):
                st.write(f"Editing: {selected_entry[2]} on {selected_entry[1]}")
                edit_day = st.selectbox("Day of Week", day_order, index=day_order.index(selected_entry[1]))
                edit_subject = st.text_input("Subject/Course Name", value=selected_entry[2])
                edit_start_time = st.time_input("Start Time", value=datetime.strptime(selected_entry[3], '%H:%M').time())
                edit_end_time = st.time_input("End Time", value=datetime.strptime(selected_entry[4], '%H:%M').time())
                edit_zoom_link = st.text_input("Zoom/Meeting Link (optional)", value=selected_entry[5] if selected_entry[5] else "")

                col_update, col_delete = st.columns(2)
                with col_update:
                    if st.form_submit_button("Update Entry"):
                        db_update_timetable_entry(selected_id, edit_day, edit_subject, edit_start_time.strftime('%H:%M'), edit_end_time.strftime('%H:%M'), edit_zoom_link)
                        st.success("Timetable entry updated!")
                        st.rerun()
                with col_delete:
                    if st.form_submit_button("Delete Entry"):
                        db_delete_timetable_entry(selected_id)
                        st.success("Timetable entry deleted!")
                        st.rerun()
    else:
        st.info("Your timetable is empty. Add entries above!")

# ── 5. Quiz Arena ─────────────────────────────────────
elif page == "Quiz Arena":
    st.header("Quiz Arena")

    tab1, tab2 = st.tabs(["Take a Quiz", "My Flashcards"])

    with tab1:
        st.subheader("Take a Quiz")
        subject_options = list(KNOWLEDGE_BASE.keys()) # Or fetch from database of available quizzes
        quiz_subject = st.selectbox("Select Subject", subject_options)
        quiz_difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        num_questions = st.slider("Number of Questions", 1, 10, 5)

        if st.button("Start Quiz"):
            st.session_state.quiz_questions = ai_generate_quiz_questions(quiz_subject, quiz_difficulty, num_questions)
            st.session_state.quiz_score = 0
            st.session_state.quiz_total_questions = len(st.session_state.quiz_questions)
            st.session_state.quiz_current_question = 0
            st.session_state.quiz_timer_start = time.time()
            st.success(f"Quiz started for {quiz_subject}!")

        if st.session_state.quiz_questions:
            st.markdown("---")
            st.subheader(f"Question {st.session_state.quiz_current_question + 1}/{st.session_state.quiz_total_questions}")
            current_q = st.session_state.quiz_questions[st.session_state.quiz_current_question]

            st.markdown(f"**{current_q['question']}**")
            user_answer = st.radio("Choose your answer:", current_q['options'], key=f"q_{st.session_state.quiz_current_question}")

            if st.button("Submit Answer", key=f"submit_{st.session_state.quiz_current_question}"):
                if user_answer == current_q['answer']:
                    st.success("Correct!")
                    st.session_state.quiz_score += 1
                else:
                    st.error(f"Incorrect. The correct answer was: {current_q['answer']}")
                
                time.sleep(1) # Give user time to see feedback
                st.session_state.quiz_current_question += 1

                if st.session_state.quiz_current_question >= st.session_state.quiz_total_questions:
                    st.markdown("---")
                    st.subheader("Quiz Finished!")
                    final_score = st.session_state.quiz_score
                    total_q = st.session_state.quiz_total_questions
                    quiz_duration = int(time.time() - st.session_state.quiz_timer_start)
                    st.markdown(f"You scored **{final_score}** out of **{total_q}** in **{quiz_duration} seconds**.")
                    db_add_quiz_record(user_email, quiz_subject, final_score, total_q)
                    st.balloons()
                    st.session_state.quiz_questions = [] # Clear quiz
                st.rerun()

    with tab2:
        st.subheader("My Flashcards")
        my_flashcards = db_get_flashcards(user_email)
        
        if my_flashcards:
            df_flashcards = pd.DataFrame(my_flashcards, columns=["ID", "Subject", "Question", "Answer"])
            st.dataframe(df_flashcards.drop("ID", axis=1), use_container_width=True)

            st.subheader("Practice Flashcards")
            flashcard_subjects = sorted(list(df_flashcards['Subject'].unique()))
            selected_fc_subject = st.selectbox("Select subject for practice:", ["All Subjects"] + flashcard_subjects)

            filtered_flashcards = my_flashcards
            if selected_fc_subject != "All Subjects":
                filtered_flashcards = [fc for fc in my_flashcards if fc[1] == selected_fc_subject]
            
            if filtered_flashcards:
                if "current_flashcard_idx" not in st.session_state:
                    st.session_state.current_flashcard_idx = 0
                if "show_flashcard_answer" not in st.session_state:
                    st.session_state.show_flashcard_answer = False

                current_fc = filtered_flashcards[st.session_state.current_flashcard_idx]

                st.markdown(f"<div class='glass-card'><h4>Question:</h4><p>{current_fc[2]}</p></div>", unsafe_allow_html=True)
                
                if st.session_state.show_flashcard_answer:
                    st.markdown(f"<div class='glass-card'><h4>Answer:</h4><p>{current_fc[3]}</p></div>", unsafe_allow_html=True)
                
                col_fc1, col_fc2, col_fc3 = st.columns(3)
                with col_fc1:
                    if st.button("Show/Hide Answer"):
                        st.session_state.show_flashcard_answer = not st.session_state.show_flashcard_answer
                        st.rerun()
                with col_fc2:
                    if st.button("Next Flashcard"):
                        st.session_state.current_flashcard_idx = (st.session_state.current_flashcard_idx + 1) % len(filtered_flashcards)
                        st.session_state.show_flashcard_answer = False
                        st.rerun()
                with col_fc3:
                    if st.button("Previous Flashcard"):
                        st.session_state.current_flashcard_idx = (st.session_state.current_flashcard_idx - 1 + len(filtered_flashcards)) % len(filtered_flashcards)
                        st.session_state.show_flashcard_answer = False
                        st.rerun()
            else:
                st.info("No flashcards found for selected subject.")

        else:
            st.info("You haven't added any flashcards yet. Use the 'Flashcard Generator' in AI Assistant to create some!")


# ── 6. Analytics ──────────────────────────────────────
elif page == "Analytics":
    st.header("Analytics Dashboard")

    st.subheader("Quiz Performance Trends")
    if quiz_records:
        df_quizzes = pd.DataFrame(quiz_records, columns=["ID", "Subject", "Score", "Total Questions", "Timestamp"])
        df_quizzes["Percentage"] = (df_quizzes["Score"] / df_quizzes["Total Questions"]) * 100
        df_quizzes["Timestamp"] = pd.to_datetime(df_quizzes["Timestamp"])
        
        # Group by subject and show average performance
        avg_scores = df_quizzes.groupby('Subject')['Percentage'].mean().reset_index()
        st.write("Average Score by Subject:")
        st.dataframe(avg_scores)

        if PLOTLY_AVAILABLE:
            fig_quiz = px.line(df_quizzes.sort_values('Timestamp'), x="Timestamp", y="Percentage", color="Subject",
                            title="Quiz Score Over Time", markers=True)
            st.plotly_chart(fig_quiz, use_container_width=True)
        else:
            st.warning("Plotly is not available for advanced charting. Please install it (`pip install plotly`).")
    else:
        st.info("No quiz records yet. Take some quizzes in the 'Quiz Arena'!")

    st.subheader("Focus Session Logs")
    if focus_sessions:
        df_focus = pd.DataFrame(focus_sessions, columns=["ID", "Start Time", "End Time", "Duration (minutes)"])
        df_focus["Start Time"] = pd.to_datetime(df_focus["Start Time"])
        df_focus["Date"] = df_focus["Start Time"].dt.date

        daily_focus = df_focus.groupby("Date")["Duration (minutes)"].sum().reset_index()
        st.write("Total Focus Time per Day:")
        st.dataframe(daily_focus)

        if PLOTLY_AVAILABLE:
            fig_focus = px.bar(daily_focus, x="Date", y="Duration (minutes)", title="Daily Focus Time")
            st.plotly_chart(fig_focus, use_container_width=True)
        else:
            st.warning("Plotly is not available for advanced charting. Please install it (`pip install plotly`).")
    else:
        st.info("No focus sessions recorded yet. Start a focus timer when you study!")

    st.subheader("GPA Predictor (Beta)")
    current_gpa = st.number_input("Your current GPA", min_value=0.0, max_value=5.0, value=gpa_target, step=0.01)
    study_hours = st.slider("Weekly Study Hours", 0, 50, 15)

    if st.button("Predict GPA"):
        prediction = ai_predict_gpa(current_gpa, gpa_target, study_hours)
        st.info(prediction)

# ── 7. Settings ──────────────────────────────────────
elif page == "Settings":
    st.header("User Settings")

    st.subheader("GPA Target")
    current_gpa_target = db_get_user_gpa_target(user_email)
    new_gpa_target = st.number_input(
        "Set your target GPA:",
        min_value=0.0,
        max_value=5.0,
        value=float(current_gpa_target),
        step=0.01
    )
    if st.button("Update GPA Target"):
        db_update_gpa_target(user_email, new_gpa_target)
        st.success(f"Your GPA target has been updated to {new_gpa_target:.2f}")
        st.rerun()

    st.subheader("Notifications")
    st.write("Manage your notifications settings here.")
    # Add future notification settings (e.g., enable/disable, types of notifications)

    st.markdown("---")
    st.subheader("About EduMate AI")
    st.info("EduMate AI is your personal AI-powered education platform, designed to help you excel in your studies.")


# ── Footer ────────────────────────────────────────────
st.markdown("<div class='footer'>© 2026 EduMate AI</div>", unsafe_allow_html=True)

# ======================================================
# RUN:
# streamlit run app.py
# ======================================================
