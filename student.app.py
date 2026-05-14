import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="EduMate AI",
    page_icon="🎓",
    layout="wide"
)

# =========================
# DATABASE SETUP
# =========================
@st.cache_resource
def get_connection():
    """Return a cached, thread-safe DB connection."""
    conn = sqlite3.connect("student_ai_assistant.db", check_same_thread=False)
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        title TEXT,
        subject TEXT,
        due_date TEXT,
        priority TEXT,
        status TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        subject TEXT,
        day TEXT,
        start_time TEXT,
        end_time TEXT
    )
    ''')

    # FIX: Added study_streak table to persist streak (was random before)
    c.execute('''
    CREATE TABLE IF NOT EXISTS study_streak (
        user_email TEXT PRIMARY KEY,
        streak INTEGER DEFAULT 0,
        last_login TEXT
    )
    ''')

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
    except Exception:
        return False


def login_user(email, password):
    c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hash_password(password))
    )
    return c.fetchone()


def add_assignment(user_email, title, subject, due_date, priority, status):
    c.execute(
        "INSERT INTO assignments (user_email, title, subject, due_date, priority, status) VALUES (?, ?, ?, ?, ?, ?)",
        (user_email, title, subject, due_date, priority, status)
    )
    conn.commit()


def get_assignments(user_email):
    c.execute(
        "SELECT id, title, subject, due_date, priority, status FROM assignments WHERE user_email=? ORDER BY due_date ASC",
        (user_email,)
    )
    return c.fetchall()


def delete_assignment(assignment_id):
    c.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))
    conn.commit()


def add_timetable(user_email, subject, day, start_time, end_time):
    c.execute(
        "INSERT INTO timetable (user_email, subject, day, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
        (user_email, subject, day, start_time, end_time)
    )
    conn.commit()


def get_timetable(user_email):
    # FIX: Days are now ordered logically Mon–Sat
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    c.execute(
        "SELECT id, subject, day, start_time, end_time FROM timetable WHERE user_email=?",
        (user_email,)
    )
    rows = c.fetchall()
    return sorted(rows, key=lambda r: day_order.index(r[2]) if r[2] in day_order else 99)


def delete_timetable(entry_id):
    c.execute("DELETE FROM timetable WHERE id=?", (entry_id,))
    conn.commit()


# FIX: Persist and update streak based on login date
def get_or_update_streak(user_email):
    today = str(date.today())
    c.execute("SELECT streak, last_login FROM study_streak WHERE user_email=?", (user_email,))
    row = c.fetchone()

    if row is None:
        c.execute("INSERT INTO study_streak (user_email, streak, last_login) VALUES (?, 1, ?)", (user_email, today))
        conn.commit()
        return 1

    streak, last_login = row
    if last_login == today:
        return streak

    # Check if yesterday → increment streak, else reset
    from datetime import timedelta
    yesterday = str(date.today() - timedelta(days=1))
    new_streak = streak + 1 if last_login == yesterday else 1
    c.execute("UPDATE study_streak SET streak=?, last_login=? WHERE user_email=?", (new_streak, today, user_email))
    conn.commit()
    return new_streak


# FIX: Real keyword-based AI response (much more comprehensive)
def ai_response(prompt):
    prompt_lower = prompt.lower()

    responses = {
        "math": (
            "**Mathematics Tips:**\n"
            "- Break problems into smaller steps and identify the right formula first.\n"
            "- Write out all known and unknown variables clearly.\n"
            "- Check units and dimensions when solving applied problems.\n"
            "- Practice past exam questions to build pattern recognition.\n"
            "- For algebra: isolate the variable step by step."
        ),
        "physics": (
            "**Physics Study Guide:**\n"
            "- Always identify known and unknown variables before selecting a formula.\n"
            "- Draw free-body diagrams for mechanics problems.\n"
            "- Remember: F = ma, v = u + at, s = ut + ½at².\n"
            "- For circuits, apply Ohm's Law (V = IR) and Kirchhoff's Laws.\n"
            "- Practice unit conversions regularly."
        ),
        "biology": (
            "**Biology Study Tips:**\n"
            "- Focus on understanding processes, not just memorising terms.\n"
            "- Draw and label diagrams (cell structure, organ systems).\n"
            "- Use mnemonics for classification: Kingdom, Phylum, Class, Order, Family, Genus, Species.\n"
            "- Link structure to function for every organ or organelle.\n"
            "- Revise past papers to understand examiner expectations."
        ),
        "chemistry": (
            "**Chemistry Tips:**\n"
            "- Practice balancing chemical equations daily.\n"
            "- Memorise the periodic table groups and their properties.\n"
            "- For moles: n = m/M and n = cV.\n"
            "- Understand reaction types: synthesis, decomposition, displacement, redox.\n"
            "- Write out electron configurations for atomic structure questions."
        ),
        "history": (
            "**History Study Strategy:**\n"
            "- Build timelines to visualise cause and effect.\n"
            "- Use the PEEL structure for essay answers (Point, Evidence, Explain, Link).\n"
            "- Focus on key turning points and their long/short-term causes.\n"
            "- Compare different historical perspectives and sources.\n"
            "- Practice writing timed essay responses."
        ),
        "computer": (
            "**Computer Science Tips:**\n"
            "- Code every day — even 20 minutes builds strong habits.\n"
            "- Understand algorithms (sorting, searching) and their time complexity.\n"
            "- Practice tracing through code manually to find logic errors.\n"
            "- Study data structures: arrays, linked lists, stacks, queues, trees.\n"
            "- Work on small projects to apply concepts practically."
        ),
        "english": (
            "**English Tips:**\n"
            "- Read widely to improve vocabulary and comprehension.\n"
            "- For essay writing: plan before you write (intro, body, conclusion).\n"
            "- Analyse language techniques: metaphor, simile, alliteration, tone.\n"
            "- Practice summarising passages in your own words.\n"
            "- Proofread your work for grammar, punctuation, and clarity."
        ),
        "geography": (
            "**Geography Study Tips:**\n"
            "- Learn key case studies for physical and human geography.\n"
            "- Draw and annotate maps and diagrams.\n"
            "- Link theory to real-world examples (e.g. climate change impacts).\n"
            "- Use acronyms to remember processes (e.g. DRIER for desertification causes).\n"
            "- Practice 6-mark and 8-mark extended answer structures."
        ),
        "study": (
            "**General Study Strategies:**\n"
            "- Use the Pomodoro Technique: 25 minutes focused study, 5-minute break.\n"
            "- Active recall is more effective than re-reading — test yourself.\n"
            "- Spaced repetition: revisit material after 1 day, 3 days, 1 week.\n"
            "- Summarise notes in your own words after each session.\n"
            "- Sleep is critical — your brain consolidates memory during sleep."
        ),
        "exam": (
            "**Exam Preparation Tips:**\n"
            "- Start revising at least 4 weeks before exams.\n"
            "- Create a revision timetable and stick to it.\n"
            "- Practise past papers under timed conditions.\n"
            "- Focus on weak areas first, then reinforce strong ones.\n"
            "- The night before: light review only, sleep early, eat well."
        ),
    }

    for keyword, answer in responses.items():
        if keyword in prompt_lower:
            return answer

    # FIX: Meaningful fallback instead of useless random string
    return (
        "**Study Tips:**\n"
        "- Be specific with your question for more tailored advice!\n"
        "- Try asking about a subject (Math, Biology, Physics, Chemistry, History, etc.)\n"
        "- Or ask about study techniques, exam preparation, or note-taking strategies.\n\n"
        "*Example: 'How do I study for a biology exam?' or 'Give me tips for solving math problems.'*"
    )


# FIX: Quiz data expanded; state managed properly via session_state
QUIZ_BANK = {
    "biology": [
        ("What is the powerhouse of the cell?", "Mitochondria"),
        ("What molecule carries genetic information?", "DNA"),
        ("What process do plants use to make food?", "Photosynthesis"),
        ("What is the basic unit of life?", "Cell"),
        ("What organ pumps blood through the body?", "Heart"),
    ],
    "math": [
        ("What is 12 × 8?", "96"),
        ("What is the square root of 81?", "9"),
        ("What is 15% of 200?", "30"),
        ("What is the value of π (pi) to 2 decimal places?", "3.14"),
        ("What is 7²?", "49"),
    ],
    "physics": [
        ("What is the SI unit of force?", "Newton"),
        ("What formula represents Newton's second law?", "F=ma"),
        ("What is the speed of light (m/s)?", "300000000"),
        ("What is the SI unit of energy?", "Joule"),
        ("What force keeps planets in orbit?", "Gravity"),
    ],
    "chemistry": [
        ("What is the chemical symbol for water?", "H2O"),
        ("What is the atomic number of carbon?", "6"),
        ("What is the chemical symbol for gold?", "Au"),
        ("What gas do plants absorb for photosynthesis?", "CO2"),
        ("What is the pH of a neutral solution?", "7"),
    ],
    "history": [
        ("In what year did World War II end?", "1945"),
        ("Who was the first President of the United States?", "George Washington"),
        ("In what year did the Berlin Wall fall?", "1989"),
        ("Which empire was ruled by Julius Caesar?", "Roman"),
        ("In what year did World War I begin?", "1914"),
    ],
}

def generate_quiz(topic):
    return QUIZ_BANK.get(topic.lower(), [])


# =========================
# SESSION STATE INIT
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# FIX: Quiz state managed in session to prevent reset on re-render
if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = ""

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# =========================
# AUTHENTICATION
# =========================
if not st.session_state.logged_in:

    st.title("🎓 EduMate AI")
    st.subheader("Smart Student AI Assistant")

    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

    if menu == "Register":
        st.header("Create Account")

        fullname = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")  # FIX: Added confirmation

        if st.button("Register"):
            # FIX: Proper validation
            if not fullname or not email or not password:
                st.warning("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif "@" not in email:
                st.error("Please enter a valid email address.")
            else:
                success = create_user(fullname, email, password)
                if success:
                    st.success("✅ Account created successfully! Please login.")
                else:
                    st.error("This email is already registered.")

    elif menu == "Login":
        st.header("Login")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if not email or not password:
                st.warning("Please enter your email and password.")
            else:
                result = login_user(email, password)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

# =========================
# MAIN APPLICATION
# =========================
else:
    st.sidebar.title("🎓 EduMate AI")

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

    st.sidebar.success(f"Logged in as:\n{st.session_state.user_email}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.quiz_topic = ""
        st.session_state.quiz_questions = []
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.rerun()

    # =========================
    # DASHBOARD
    # =========================
    if page == "Dashboard":
        st.title("📚 Student Dashboard")

        assignments = get_assignments(st.session_state.user_email)
        timetable = get_timetable(st.session_state.user_email)

        # FIX: Streak is now persisted, not random
        streak = get_or_update_streak(st.session_state.user_email)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Assignments", len(assignments))

        with col2:
            st.metric("Classes Scheduled", len(timetable))

        with col3:
            st.metric("🔥 Study Streak", f"{streak} Day{'s' if streak != 1 else ''}")

        # FIX: Show overdue indicator
        st.subheader("Upcoming Assignments")

        if assignments:
            today_str = str(date.today())
            rows = []
            for a in assignments:
                # a = (id, title, subject, due_date, priority, status)
                overdue = (
                    a[3] < today_str and a[5] != "Completed"
                )
                rows.append({
                    "Title": a[1],
                    "Subject": a[2],
                    "Due Date": a[3],
                    "Priority": a[4],
                    "Status": a[5],
                    "⚠️ Overdue": "Yes" if overdue else "No"
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No assignments added yet. Go to Assignments to add one.")

        st.subheader("💬 Today's Motivation")
        motivations = [
            "Success starts with discipline.",
            "Consistency beats intensity.",
            "Small progress each day matters.",
            "Study now, shine later.",
            "Your future is built today.",
            "Every expert was once a beginner.",
            "Hard work pays off — keep going!",
            "Focus on progress, not perfection.",
        ]
        # FIX: Use date-based seed so motivation is stable per day, not random on every render
        daily_seed = int(date.today().strftime("%Y%m%d"))
        motivation = motivations[daily_seed % len(motivations)]
        st.success(motivation)

    # =========================
    # AI ASSISTANT
    # =========================
    elif page == "AI Assistant":
        st.title("🤖 AI Study Assistant")
        st.write("Ask any academic question and get helpful study advice.")

        prompt = st.text_area("Enter your question", placeholder="e.g. How do I study for a chemistry exam?")

        if st.button("Get AI Help"):
            if not prompt.strip():
                st.warning("Please enter a question first.")
            else:
                response = ai_response(prompt)
                st.subheader("📘 AI Response")
                st.markdown(response)

        st.markdown("---")
        st.caption("💡 Try asking about: Math, Physics, Biology, Chemistry, History, Computer Science, English, Geography, study techniques, or exam tips.")

    # =========================
    # ASSIGNMENTS
    # =========================
    elif page == "Assignments":
        st.title("📝 Assignment Tracker")

        with st.form("assignment_form"):
            title = st.text_input("Assignment Title")
            subject = st.text_input("Subject")
            due_date = st.date_input("Due Date", min_value=date.today())
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])

            submitted = st.form_submit_button("Add Assignment")

            if submitted:
                # FIX: Validate inputs before inserting
                if not title.strip() or not subject.strip():
                    st.error("Title and Subject cannot be empty.")
                else:
                    add_assignment(
                        st.session_state.user_email,
                        title.strip(),
                        subject.strip(),
                        str(due_date),
                        priority,
                        status
                    )
                    st.success(f"✅ Assignment '{title}' added successfully!")

        st.subheader("Your Assignments")

        assignments = get_assignments(st.session_state.user_email)

        if assignments:
            for a in assignments:
                # a = (id, title, subject, due_date, priority, status)
                col1, col2 = st.columns([5, 1])
                with col1:
                    overdue = (str(a[3]) < str(date.today()) and a[5] != "Completed")
                    label = f"**{a[1]}** | {a[2]} | Due: {a[3]} | {a[4]} Priority | {a[5]}"
                    if overdue:
                        label += " ⚠️ *Overdue*"
                    st.markdown(label)
                with col2:
                    # FIX: Delete button per assignment
                    if st.button("🗑️ Delete", key=f"del_assign_{a[0]}"):
                        delete_assignment(a[0])
                        st.rerun()
        else:
            st.info("No assignments found. Add one above!")

    # =========================
    # TIMETABLE
    # =========================
    elif page == "Timetable":
        st.title("📅 Timetable Manager")

        with st.form("timetable_form"):
            subject = st.text_input("Subject Name")
            day = st.selectbox(
                "Day",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            )
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")

            submitted = st.form_submit_button("Add Class")

            if submitted:
                # FIX: Validate subject input and time logic
                if not subject.strip():
                    st.error("Subject name cannot be empty.")
                elif start_time >= end_time:
                    st.error("End time must be after start time.")
                else:
                    add_timetable(
                        st.session_state.user_email,
                        subject.strip(),
                        day,
                        str(start_time),
                        str(end_time)
                    )
                    st.success(f"✅ Class '{subject}' on {day} added!")

        st.subheader("Weekly Timetable")

        timetable = get_timetable(st.session_state.user_email)

        if timetable:
            for entry in timetable:
                # entry = (id, subject, day, start_time, end_time)
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{entry[2]}** | {entry[1]} | {entry[3]} – {entry[4]}")
                with col2:
                    # FIX: Delete button per timetable entry
                    if st.button("🗑️ Delete", key=f"del_tt_{entry[0]}"):
                        delete_timetable(entry[0])
                        st.rerun()
        else:
            st.info("No timetable entries found. Add a class above!")

    # =========================
    # QUIZ GENERATOR  (FIX: Fully rewritten — no more broken state)
    # =========================
    elif page == "Quiz Generator":
        st.title("🧠 AI Quiz Generator")

        available_topics = list(QUIZ_BANK.keys())
        topic_input = st.selectbox(
            "Choose a Topic",
            [""] + [t.capitalize() for t in available_topics]
        )

        if st.button("Generate Quiz"):
            if not topic_input:
                st.warning("Please select a topic.")
            else:
                # FIX: Store quiz in session_state so it survives re-renders
                questions = generate_quiz(topic_input)
                st.session_state.quiz_topic = topic_input
                st.session_state.quiz_questions = questions
                st.session_state.quiz_answers = {i: "" for i in range(len(questions))}
                st.session_state.quiz_submitted = False

        if st.session_state.quiz_questions:
            st.subheader(f"📝 Quiz: {st.session_state.quiz_topic}")

            with st.form("quiz_form"):
                for i, (question, _) in enumerate(st.session_state.quiz_questions):
                    st.write(f"**Q{i+1}. {question}**")
                    st.session_state.quiz_answers[i] = st.text_input(
                        f"Your answer for Q{i+1}",
                        key=f"q_{i}"
                    )

                submit_quiz = st.form_submit_button("Submit Quiz")

                if submit_quiz:
                    st.session_state.quiz_submitted = True

            # FIX: Score only shown after explicit submission
            if st.session_state.quiz_submitted:
                score = 0
                st.subheader("📊 Results")
                for i, (question, correct_answer) in enumerate(st.session_state.quiz_questions):
                    user_ans = st.session_state.quiz_answers.get(i, "").strip().lower()
                    correct = correct_answer.strip().lower()
                    is_correct = user_ans == correct
                    if is_correct:
                        score += 1
                    icon = "✅" if is_correct else "❌"
                    st.write(f"{icon} **Q{i+1}:** {question}")
                    if not is_correct:
                        st.write(f"   Your answer: *{st.session_state.quiz_answers.get(i, '') or 'No answer'}* | Correct: **{correct_answer}**")

                total = len(st.session_state.quiz_questions)
                percentage = round((score / total) * 100)
                st.markdown(f"### 🏆 Score: {score}/{total} ({percentage}%)")

                if percentage == 100:
                    st.balloons()
                    st.success("Perfect score! Outstanding work! 🎉")
                elif percentage >= 60:
                    st.success(f"Good job! You scored {percentage}%. Keep practising!")
                else:
                    st.warning(f"You scored {percentage}%. Review this topic and try again.")

                if st.button("🔄 Retake Quiz"):
                    st.session_state.quiz_answers = {i: "" for i in range(len(st.session_state.quiz_questions))}
                    st.session_state.quiz_submitted = False
                    st.rerun()

    # =========================
    # ANALYTICS
    # =========================
    elif page == "Analytics":
        st.title("📈 Student Analytics")

        assignments = get_assignments(st.session_state.user_email)

        if assignments:
            # a = (id, title, subject, due_date, priority, status)
            df = pd.DataFrame(assignments, columns=["ID", "Title", "Subject", "Due Date", "Priority", "Status"])

            completed = len(df[df["Status"] == "Completed"])
            in_progress = len(df[df["Status"] == "In Progress"])
            pending = len(df[df["Status"] == "Pending"])
            today_str = str(date.today())
            overdue = len(df[(df["Due Date"] < today_str) & (df["Status"] != "Completed")])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("✅ Completed", completed)
            with col2:
                st.metric("🔄 In Progress", in_progress)
            with col3:
                st.metric("⏳ Pending", pending)
            with col4:
                st.metric("⚠️ Overdue", overdue)

            st.subheader("Assignments by Priority")
            # FIX: Guard against empty value_counts to avoid crashes
            priority_counts = df["Priority"].value_counts()
            if not priority_counts.empty:
                st.bar_chart(priority_counts)

            st.subheader("Assignments by Status")
            status_counts = df["Status"].value_counts()
            if not status_counts.empty:
                st.bar_chart(status_counts)

            st.subheader("Assignments by Subject")
            subject_counts = df["Subject"].value_counts()
            if not subject_counts.empty:
                st.bar_chart(subject_counts)

        else:
            st.info("No analytics available yet. Add assignments to see your progress!")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("EduMate AI © 2026 | Smart Student Assistant")

# =========================
# RUN COMMAND
# =========================
# streamlit run app.py
