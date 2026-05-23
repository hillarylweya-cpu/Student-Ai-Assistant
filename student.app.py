import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date, timedelta
import pandas as pd

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="EduMate AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# MODERN UI STYLING
# =========================
st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b, #2563eb);
    background-attachment: fixed;
}

.main-title {
    text-align: center;
    color: white;
    font-size: 55px;
    font-weight: bold;
    margin-bottom: 10px;
}

.sub-title {
    text-align: center;
    color: #dbeafe;
    font-size: 20px;
    margin-bottom: 35px;
}

.glass-box {
    background: rgba(255,255,255,0.10);
    backdrop-filter: blur(14px);
    border-radius: 24px;
    padding: 30px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.15);
    color: white;
}

.metric-card {
    background: rgba(255,255,255,0.12);
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    color: white;
    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
}

.feature-card {
    background: rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 18px;
    margin-bottom: 18px;
    color: white;
    transition: 0.3s;
}

.feature-card:hover {
    transform: scale(1.02);
    background: rgba(255,255,255,0.14);
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    border: none;
    background: linear-gradient(90deg, #3b82f6, #2563eb);
    color: white;
    font-size: 17px;
    font-weight: bold;
    padding: 12px;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
}

.footer {
    text-align: center;
    color: #cbd5e1;
    margin-top: 40px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# DATABASE
# =========================
@st.cache_resource
def get_connection():
    conn = sqlite3.connect(
        "student_ai_assistant.db",
        check_same_thread=False
    )

    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        title TEXT,
        subject TEXT,
        due_date TEXT,
        priority TEXT,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        subject TEXT,
        day TEXT,
        start_time TEXT,
        end_time TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS study_streak (
        user_email TEXT PRIMARY KEY,
        streak INTEGER DEFAULT 0,
        last_login TEXT
    )
    """)

    conn.commit()
    return conn


conn = get_connection()
c = conn.cursor()

# =========================
# HELPERS
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(fullname, email, password):
    try:
        c.execute(
            "INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)",
            (fullname, email, hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False


def login_user(email, password):
    c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hash_password(password))
    )
    return c.fetchone()


def add_assignment(user_email, title, subject, due_date, priority, status):
    c.execute("""
    INSERT INTO assignments
    (user_email, title, subject, due_date, priority, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_email, title, subject, due_date, priority, status))
    conn.commit()


def get_assignments(user_email):
    c.execute("""
    SELECT id, title, subject, due_date, priority, status
    FROM assignments
    WHERE user_email=?
    ORDER BY due_date ASC
    """, (user_email,))
    return c.fetchall()


def delete_assignment(aid):
    c.execute("DELETE FROM assignments WHERE id=?", (aid,))
    conn.commit()


def add_timetable(user_email, subject, day, start_time, end_time):
    c.execute("""
    INSERT INTO timetable
    (user_email, subject, day, start_time, end_time)
    VALUES (?, ?, ?, ?, ?)
    """, (user_email, subject, day, start_time, end_time))
    conn.commit()


def get_timetable(user_email):
    c.execute("""
    SELECT id, subject, day, start_time, end_time
    FROM timetable
    WHERE user_email=?
    """, (user_email,))
    return c.fetchall()


def delete_timetable(tid):
    c.execute("DELETE FROM timetable WHERE id=?", (tid,))
    conn.commit()


def get_or_update_streak(user_email):
    today = str(date.today())

    c.execute("""
    SELECT streak, last_login
    FROM study_streak
    WHERE user_email=?
    """, (user_email,))

    row = c.fetchone()

    if row is None:
        c.execute("""
        INSERT INTO study_streak
        (user_email, streak, last_login)
        VALUES (?, 1, ?)
        """, (user_email, today))
        conn.commit()
        return 1

    streak, last_login = row

    if last_login == today:
        return streak

    yesterday = str(date.today() - timedelta(days=1))

    new_streak = streak + 1 if last_login == yesterday else 1

    c.execute("""
    UPDATE study_streak
    SET streak=?, last_login=?
    WHERE user_email=?
    """, (new_streak, today, user_email))

    conn.commit()
    return new_streak


def ai_response(prompt):
    prompt = prompt.lower()

    if "math" in prompt:
        return """
### 📘 Mathematics Tips
- Break problems into steps
- Practice formulas daily
- Solve past papers
- Focus on weak topics
"""

    if "biology" in prompt:
        return """
### 🧬 Biology Tips
- Draw diagrams
- Revise processes
- Use flashcards
- Practice labeling
"""

    if "physics" in prompt:
        return """
### ⚡ Physics Tips
- Understand formulas
- Practice calculations
- Draw force diagrams
- Learn SI units
"""

    return """
### 🤖 AI Study Help
Ask about:
- Math
- Biology
- Physics
- Chemistry
- Exams
- Study techniques
"""

# =========================
# QUIZ BANK
# =========================
QUIZ_BANK = {
  QUIZ_BANK = {

    "Mathematics": [
        {
            "question": "What is 15 × 12?",
            "options": ["120", "180", "150", "170"],
            "answer": "180"
        },
        {
            "question": "What is the square root of 144?",
            "options": ["10", "11", "12", "14"],
            "answer": "12"
        }
    ],

    "Biology": [
        {
            "question": "What is the powerhouse of the cell?",
            "options": ["Nucleus", "Mitochondria", "Ribosome", "Cytoplasm"],
            "answer": "Mitochondria"
        },
        {
            "question": "What carries genetic information?",
            "options": ["RNA", "DNA", "Protein", "Enzyme"],
            "answer": "DNA"
        }
    ],

    "Physics": [
        {
            "question": "What is the SI unit of force?",
            "options": ["Pascal", "Newton", "Joule", "Volt"],
            "answer": "Newton"
        }
    ],

    "Chemistry": [
        {
            "question": "What is the chemical formula for water?",
            "options": ["H2O", "CO2", "NaCl", "O2"],
            "answer": "H2O"
        }
    ],

    "English": [
        {
            "question": "Which is a noun?",
            "options": ["Run", "Beautiful", "School", "Quickly"],
            "answer": "School"
        }
    ],

    "History": [
        {
            "question": "When did World War II end?",
            "options": ["1940", "1945", "1950", "1939"],
            "answer": "1945"
        }
    ],

    "Geography": [
        {
            "question": "Which is the largest ocean?",
            "options": ["Indian", "Pacific", "Atlantic", "Arctic"],
            "answer": "Pacific"
        }
    ],

    "Computer Science": [
        {
            "question": "What does CPU stand for?",
}

def generate_quiz(topic):
    return QUIZ_BANK.get(topic.lower(), [])

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# =========================
# AUTHENTICATION
# =========================
if not st.session_state.logged_in:

    st.markdown(
        '<div class="main-title">🎓 EduMate AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Modern AI-Powered Student Learning Platform</div>',
        unsafe_allow_html=True
    )

    menu = st.sidebar.selectbox(
        "Menu",
        ["Login", "Register"]
    )

    # =========================
    # REGISTER
    # =========================
    if menu == "Register":

        st.markdown("""
        <div class='glass-box'>
        <h2>Create Student Account</h2>
        """, unsafe_allow_html=True)

        fullname = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.button("Create Account"):

            if not fullname or not email or not password:
                st.warning("Fill all fields")

            elif password != confirm:
                st.error("Passwords do not match")

            else:
                success = create_user(
                    fullname,
                    email,
                    password
                )

                if success:
                    st.success("Account created successfully")

                else:
                    st.error("Email already exists")

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # LOGIN
    # =========================
    elif menu == "Login":

        left, right = st.columns([1.2, 1])

        with left:

            st.markdown("""
            <div class='glass-box'>
            <h2 style='text-align:center;'>🔐 Student Login</h2>
            <p style='text-align:center;color:#dbeafe;'>
            Access your smart learning dashboard
            </p>
            """, unsafe_allow_html=True)

            email = st.text_input("📧 Email")
            password = st.text_input(
                "🔑 Password",
                type="password"
            )

            remember = st.checkbox("Remember Me")

            if st.button("🚀 Login"):

                result = login_user(email, password)

                if result:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email

                    st.success("Login successful 🎉")
                    st.balloons()

                    st.rerun()

                else:
                    st.error("Invalid email or password")

            st.markdown("</div>", unsafe_allow_html=True)

        with right:

            st.markdown("""
            <div class='feature-card'>
            <h3>🤖 AI Learning Assistant</h3>
            <p>Get intelligent study recommendations.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='feature-card'>
            <h3>📚 Assignment Tracking</h3>
            <p>Manage assignments and deadlines.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='feature-card'>
            <h3>📈 Student Analytics</h3>
            <p>Track your academic progress.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='feature-card'>
            <h3>🌙 Modern Dashboard</h3>
            <p>Responsive desktop and mobile UI.</p>
            </div>
            """, unsafe_allow_html=True)

# =========================
# MAIN APP
# =========================
else:

    st.sidebar.title("🎓 EduMate AI")
    st.sidebar.info("📚 Smart Student Platform")

    st.sidebar.success(
        f"👨‍🎓 Logged in:\n{st.session_state.user_email}"
    )

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "AI Assistant",
            "Assignments",
            "Timetable",
            "Quiz Generator",
            "Analytics"
        ]
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

    # =========================
    # DASHBOARD
    # =========================
    if page == "Dashboard":

        st.title("📚 Student Dashboard")

        st.markdown("""
        <div class='glass-box'>
        <h3>👋 Welcome to EduMate AI</h3>
        <p>Your intelligent learning companion.</p>
        </div>
        """, unsafe_allow_html=True)

        assignments = get_assignments(
            st.session_state.user_email
        )

        timetable = get_timetable(
            st.session_state.user_email
        )

        streak = get_or_update_streak(
            st.session_state.user_email
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class='metric-card'>
            <h1>{len(assignments)}</h1>
            <p>📝 Assignments</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class='metric-card'>
            <h1>{len(timetable)}</h1>
            <p>📅 Classes</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class='metric-card'>
            <h1>{streak}</h1>
            <p>🔥 Study Streak</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("## 📌 Upcoming Assignments")

        if assignments:

            rows = []

            for a in assignments:

                rows.append({
                    "Title": a[1],
                    "Subject": a[2],
                    "Due Date": a[3],
                    "Priority": a[4],
                    "Status": a[5]
                })

            df = pd.DataFrame(rows)

            st.dataframe(
                df,
                use_container_width=True
            )

        else:
            st.info("No assignments available")

    # =========================
    # AI ASSISTANT
    # =========================
    elif page == "AI Assistant":

        st.title("🤖 AI Assistant")
        st.markdown("""
### 🌍 Supported Worldwide Subjects

- Mathematics
- Biology
- Physics
- Chemistry
- English
- Geography
- History
- Computer Science
- ICT
- Programming
- Economics
- Business Studies
- Accounting
- Agriculture
- Medicine
- Engineering
- Law
- Philosophy
- Sociology
- Psychology
- Political Science
- Environmental Science
- Statistics
- Architecture
- Nursing
- Artificial Intelligence
- Cybersecurity
- Data Science
- Networking
- Graphic Design
- Music
- Art & Design
- Literature
- French
- German
- Arabic
- Chinese
- Kiswahili
- Religious Education
- Entrepreneurship
- Technical Subjects
- Aviation
- Maritime Studies
- Hospitality
- Tourism
- Journalism
- Media Studies
""")

        prompt = st.text_area(
            "Ask your question"
        )

        if st.button("Get AI Help"):

            if prompt:
                response = from difflib import get_close_matches
    "medicine": "Study anatomy, physiology, diseases, and clinical practice.",
    "engineering": "Understand mechanics, structures, electricity, and innovation.",
    "accounting": "Practice bookkeeping, ledgers, balancing, and financial reports.",
    "psychology": "Study human behavior, emotions, and mental processes.",
    "statistics": "Learn probability, data analysis, graphs, and interpretation.",
    "cybersecurity": "Understand ethical hacking, networks, security systems, and encryption.",
    "data science": "Learn machine learning, data analysis, and visualization.",
    "networking": "Study routers, protocols, IP addressing, and communication systems."
}


def ai_response(prompt):

    prompt = prompt.lower()

    matched = get_close_matches(prompt, GLOBAL_SUBJECTS.keys(), n=1, cutoff=0.3)

    if matched:
        subject = matched[0]

        return f"""
# 📘 {subject.title()} Study Guide

{GLOBAL_SUBJECTS[subject]}

### ✅ Smart Learning Tips
- Revise daily
- Practice quizzes
- Use flashcards
- Watch educational videos
- Solve past papers
- Use active recall techniques
- Join group discussions

### 🌍 Global Curriculum Support
This subject support works for:
- Cambridge
- IB
- KCSE
- GCSE
- American Curriculum
- University Systems
- Tertiary Institutions
"""

    return """
# 🤖 EduMate AI Global Assistant

Ask about any worldwide subject including:

- Science
- Technology
- Engineering
- Medicine
- Law
- Business
- Languages
- Humanities
- Arts
- AI & Computing
- Technical Education
- University Courses

Example:
- Help me study mathematics
- Explain biology
- Give accounting tips
- Teach networking
- Explain artificial intelligence
"""

                st.markdown(response)

    # =========================
    # ASSIGNMENTS
    # =========================
    elif page == "Assignments":

        st.title("📝 Assignment Tracker")

        with st.form("assignment_form"):

            title = st.text_input(
                "Assignment Title"
            )

            subject = st.text_input(
                "Subject"
            )

            due_date = st.date_input(
                "Due Date"
            )

            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High"]
            )

            status = st.selectbox(
                "Status",
                ["Pending", "In Progress", "Completed"]
            )

            submitted = st.form_submit_button(
                "Add Assignment"
            )

            if submitted:

                add_assignment(
                    st.session_state.user_email,
                    title,
                    subject,
                    str(due_date),
                    priority,
                    status
                )

                st.success("Assignment Added")

        st.subheader("Your Assignments")

        assignments = get_assignments(
            st.session_state.user_email
        )

        for a in assignments:

            col1, col2 = st.columns([5, 1])

            with col1:
                st.markdown(
                    f"""
                    **{a[1]}**
                    | {a[2]}
                    | Due: {a[3]}
                    | {a[4]}
                    | {a[5]}
                    """
                )

            with col2:

                if st.button(
                    "Delete",
                    key=a[0]
                ):

                    delete_assignment(a[0])
                    st.rerun()

    # =========================
    # TIMETABLE
    # =========================
    elif page == "Timetable":

        st.title("📅 Timetable")

        with st.form("tt_form"):

            subject = st.text_input(
                "Subject"
            )

            day = st.selectbox(
                "Day",
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday"
                ]
            )

            start = st.time_input(
                "Start Time"
            )

            end = st.time_input(
                "End Time"
            )

            submitted = st.form_submit_button(
                "Add Class"
            )

            if submitted:

                add_timetable(
                    st.session_state.user_email,
                    subject,
                    day,
                    str(start),
                    str(end)
                )

                st.success("Class Added")

        timetable = get_timetable(
            st.session_state.user_email
        )

        for t in timetable:

            col1, col2 = st.columns([5, 1])

            with col1:
                st.markdown(
                    f"""
                    **{t[2]}**
                    | {t[1]}
                    | {t[3]} - {t[4]}
                    """
                )

            with col2:

                if st.button(
                    "Delete",
                    key=f"t{t[0]}"
                ):

                    delete_timetable(t[0])
                    st.rerun()

    # =========================
    # QUIZ
    # =========================
    elif page == "Quiz Generator":
        "🎓 Select Education Level",
        [
            "Primary School",
            "Junior School",
            "High School",
            "College",
            "University",
            "Tertiary Institution"
        ]
    )

    topic = st.selectbox(
        "📘 Select Subject",
        list(QUIZ_BANK.keys())
    )

    if st.button("Generate Quiz"):

        st.subheader(f"📚 {topic} Quiz")
        st.caption(f"Education Level: {education_level}")

        questions = QUIZ_BANK[topic]

        score = 0

        with st.form("quiz_form"):

            answers = {}

            for i, q in enumerate(questions):

                answers[i] = st.radio(
                    q["question"],
                    q["options"],
                    key=f"quiz_{i}"
                )

            submitted = st.form_submit_button("Submit Quiz")

            if submitted:

                for i, q in enumerate(questions):
                    if answers[i] == q["answer"]:
                        score += 1

                total = len(questions)
                percentage = int((score / total) * 100)

                st.success(f"🏆 Score: {score}/{total} ({percentage}%)")

                if percentage >= 80:
                    st.balloons()
                    st.success("Excellent Performance 🎉")
                elif percentage >= 50:
                    st.info("Good effort. Keep studying!")
                else:
                    st.warning("Needs improvement. Practice more.")

    # =========================
    # ANALYTICS
    # =========================
    elif page == "Analytics":

        st.title("📈 Analytics")

        assignments = get_assignments(
            st.session_state.user_email
        )

        if assignments:

            df = pd.DataFrame(
                assignments,
                columns=[
                    "ID",
                    "Title",
                    "Subject",
                    "Due Date",
                    "Priority",
                    "Status"
                ]
            )

            st.subheader("Assignments by Status")

            st.bar_chart(
                df["Status"].value_counts()
            )

            st.subheader("Assignments by Subject")

            st.bar_chart(
                df["Subject"].value_counts()
            )

        else:
            st.info("No analytics yet")

# =========================
# FOOTER
# =========================
st.markdown("""
<div class='footer'>
© 2026 EduMate AI Platform | Built with Streamlit 🚀
</div>
""", unsafe_allow_html=True)

# =========================
# RUN:
# streamlit run app.py
# =========================
