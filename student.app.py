import streamlit as st
import datetime
import pandas as pd # Assuming pandas might be used for data handling/display
# import database as db # Uncomment this once database.py is defined
# import ai_engine as ai # Uncomment this once ai_engine.py is defined

# --- Placeholder for database functions ---
# In a real app, these would interact with a database (e.g., SQLite, PostgreSQL)
class MockDatabase:
    def __init__(self):
        self.assignments = [
            (1, "Essay on AI", "Computer Science", "2026-06-01", "High", "Hard", "Pending", datetime.datetime.now()),
            (2, "Chemistry Lab Report", "Chemistry", "2026-05-28", "Medium", "Medium", "In Progress", datetime.datetime.now()),
            (3, "Math Homework 1", "Mathematics", "2026-05-25", "Low", "Easy", "Completed", datetime.datetime.now()),
        ]
        self.next_id = 4

    def init_db(self):
        st.success("Mock Database Initialized (no real database used).")

    def add_assignment(self, title, subject, due_date, priority, difficulty, status):
        self.assignments.append((self.next_id, title, subject, due_date, priority, difficulty, status, datetime.datetime.now()))
        self.next_id += 1
        st.success(f"Assignment '{title}' added!")

    def get_assignments(self):
        return self.assignments

    def update_assignment(self, assignment_id, title, subject, due_date, priority, difficulty, status):
        for i, assign in enumerate(self.assignments):
            if assign[0] == assignment_id:
                self.assignments[i] = (assignment_id, title, subject, due_date, priority, difficulty, status, assign[7])
                st.success(f"Assignment '{title}' updated!")
                return
        st.error("Assignment not found.")

    def delete_assignment(self, assignment_id):
        self.assignments = [assign for assign in self.assignments if assign[0] != assignment_id]
        st.success("Assignment deleted!")

# Initialize mock database
db = MockDatabase() # In a real app, this would be `db.init_db()` and calls to the actual database functions

# --- Placeholder for AI Engine (from ai_engine.py) ---
class MockAIEngine:
    KNOWLEDGE_BASE = {
        "CHEMISTRY": {
            "summary": "Chemistry is the scientific study of the properties and behavior of matter. It is a natural science that covers the elements that make up matter to the compounds composed of atoms, molecules and ions: their composition, structure, properties, behavior and the changes they undergo during a reaction with other substances.",
            "whiteboard": "### Chemistry — Periodic Table\n\n```\n  H                                                  He\n  Li Be                               B C N O F Ne\n  Na Mg                             Al Si P S Cl Ar\n```\n- Group 1: Alkali Metals\n- Group 17: Halogens\n- Group 18: Noble Gases\n",
            "tips": [
                "Visualise molecular shapes in 3D.",
                "Practice balancing equations regularly.",
                "Understand reaction mechanisms step-by-step.",
            ],
            "flashcards": [
                ("What is Avogadro's number?", "6.022 × 10²³ particles per mole."),
                ("What pH is neutral?", "7.0 (pure water)."),
                ("Describe an exothermic reaction.", "A reaction that releases heat to its surroundings."),
            ],
        },
        "COMPUTER SCIENCE": {
            "summary": "Computer Science is the study of computation and information. Computer science deals with theory of computation, algorithms, computational problems and the design of computer systems hardware and software.",
            "whiteboard": (
                "### CS — Binary Search Tree\n\n"\
                "```\n"\
                "            [8]   ← Root\n"\
                "           /   \\\n"\
                "         [3]   [10]\n"\
                "        /   \\     \\\n"\
                "      [1]   [6]   [14]\n"\
                "```\n"\
                "- Left child < parent < right child.\n"\
                "- Lookup: O(log n) in a balanced tree."
            ),
            "tips": [
                "Trace code manually using a dry-run table.",
                "Practice coding problems regularly (e.g., LeetCode).",
                "Understand data structures and algorithms deeply.",
            ],
            "flashcards": [
                ("What is a binary search tree?", "A tree-based data structure where each node has at most two children, typically referred to as left and right."),
                ("What is Big O notation?", "A mathematical notation that describes the limiting behavior of a function when the argument tends towards a particular value or infinity."),
                ("What is a 'stack'?", "A linear data structure which follows a particular order in which the operations are performed. The order is LIFO (Last In First Out)."),
            ],
        },
         "MATHEMATICS": {
            "summary": "Mathematics is the study of quantity, structure, space, and change. It deals with logical reasoning and quantitative calculation, and its development has involved an increasing degree of idealization and abstraction of its subject matter.",
            "whiteboard": "### Maths — Quadratic Formula\n\n$$ x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a} $$\n\n- Used to find the roots of a quadratic equation: $$ ax^2 + bx + c = 0 $$\n",
            "tips": [
                "Practice problem-solving daily.",
                "Understand the 'why' behind formulas, not just the 'how'.",
                "Work through example problems step-by-step.",
            ],
            "flashcards": [
                ("What is Pi (π) approximately?", "3.14159"),
                ("What is the Pythagorean theorem?", "$$ a^2 + b^2 = c^2 $$ for a right-angled triangle."),
                ("What is a derivative in calculus?", "It measures the sensitivity of change of a function's output with respect to a change in its input."),
            ],
        }
    }

    def get_subject_info(self, subject):
        return self.KNOWLEDGE_BASE.get(subject.upper(), None)

    def generate_flashcards(self, subject):
        info = self.get_subject_info(subject)
        return info["flashcards"] if info else []

    def get_subject_summary(self, subject):
        info = self.get_subject_info(subject)
        return info["summary"] if info else "No summary available."

    def get_subject_whiteboard(self, subject):
        info = self.get_subject_info(subject)
        return info["whiteboard"] if info else "No whiteboard content available."

    def get_subject_tips(self, subject):
        info = self.get_subject_info(subject)
        return info["tips"] if info else []

ai = MockAIEngine()

# --- Page Config ---
st.set_page_config(
    page_title="EduMate AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling (from app.py snippets) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');

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
        color: #818cf8;
        margin-bottom: 5px;
    }
    .metric-card p {
        color: #94a3b8;
        font-size: 16px;
    }
    .stProgress > div > div > div > div {
        background-color: #818cf8;
    }
    .stButton > button {
        background-color: #6366f1;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #4f46e5;
        transform: translateY(-2px);
    }
    .stTextInput > div > div > input, .stDateInput > label + div > div > input, .stSelectbox > div > div > div > div > div > div > input {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        color: white;
    }
    .stTextInput > label, .stDateInput > label, .stSelectbox > label {
        color: #94a3b8;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size:1.1rem;
        color: #e2e8f0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab-list"] button {
        background-color: rgba(255,255,255,0.08);
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: rgba(255,255,255,0.15);
    }
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        border-color: #6366f1 !important;
    }
    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 14px;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid rgba(255,255,255,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "draft_assignment" not in st.session_state:
    st.session_state.draft_assignment = {
        "title": "", "subject": "", "due_date": datetime.date.today(),
        "priority": "Medium", "difficulty": "Medium", "status": "Pending"
    }

# --- Authentication Logic (Simplified) ---
def authenticate(username, password):
    # In a real app, this would check against a secure user database
    if username == "student" and password == "password":
        st.session_state.authenticated = True
        st.session_state.username = username
        return True
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.draft_assignment = {
        "title": "", "subject": "", "due_date": datetime.date.today(),
        "priority": "Medium", "difficulty": "Medium", "status": "Pending"
    }
    st.rerun()

if not st.session_state.authenticated:
    st.markdown("<h1 class='main-title'>EduMate AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Your intelligent academic companion</p>", unsafe_allow_html=True)

    col_login, col_features = st.columns([1, 1])

    with col_login:
        st.markdown("<div class='glass-card'><h3>Login</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if authenticate(username, password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
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
    st.stop() # Stop further execution if not authenticated

# --- Main App (Authenticated Users) ---
st.sidebar.markdown(f"## Welcome, {st.session_state.username.capitalize()}!")
if st.sidebar.button("Logout"):
    logout()

st.markdown("<h1 class='main-title'>Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Overview of your academic progress</p>", unsafe_allow_html=True)

# Fetch assignments (from mock DB)
assignments = db.get_assignments()

# Convert assignments to a more usable format for display and calculations
assignments_df = pd.DataFrame(assignments, columns=[
    "id", "Title", "Subject", "Due Date", "Priority", "Difficulty", "Status", "Created At"
])
# Convert 'Due Date' column to datetime objects for sorting and comparison
assignments_df['Due Date'] = pd.to_datetime(assignments_df['Due Date'])

# --- Metrics ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_assignments = len(assignments)
    st.markdown(f"<div class='metric-card'><h1>{total_assignments}</h1><p>Total Assignments</p></div>", unsafe_allow_html=True)
with col2:
    completed_assignments = assignments_df[assignments_df['Status'] == 'Completed'].shape[0]
    st.markdown(f"<div class='metric-card'><h1>{completed_assignments}</h1><p>Completed</p></div>", unsafe_allow_html=True)
with col3:
    pending_assignments = assignments_df[assignments_df['Status'] == 'Pending'].shape[0]
    st.markdown(f"<div class='metric-card'><h1>{pending_assignments}</h1><p>Pending</p></div>", unsafe_allow_html=True)
with col4:
    upcoming_due = assignments_df[
        (assignments_df['Status'] != 'Completed') &
        (assignments_df['Status'] != 'Submitted') &
        (assignments_df['Due Date'] > datetime.datetime.now())
    ].sort_values(by='Due Date').head(1)
    if not upcoming_due.empty:
        days_left = (upcoming_due['Due Date'].iloc[0].date() - datetime.date.today()).days
        st.markdown(f"<div class='metric-card'><h1>{days_left}</h1><p>Days to Due ({upcoming_due['Subject'].iloc[0]})</p></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='metric-card'><h1>N/A</h1><p>Upcoming Due</p></div>", unsafe_allow_html=True)

# --- Main Content Area: Tabs for Dashboard, AI Assistant, Assignments ---
tab_dashboard, tab_ai_assistant, tab_assignments = st.tabs(["📊 Dashboard", "🧠 AI Assistant", "📝 Assignments"])

with tab_dashboard:
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        st.markdown("<div class='glass-card'><h3>Subject Completion</h3>", unsafe_allow_html=True)
        subject_progress: dict = {}
        for _, a in assignments_df.iterrows(): # Iterate over DataFrame rows
            sub, status = a["Subject"], a["Status"]
            subject_progress.setdefault(sub, {"total": 0, "done": 0})
            subject_progress[sub]["total"] += 1
            if status in ("Completed", "Graded"): # Assuming 'Graded' is also a completion status
                subject_progress[sub]["done"] += 1
        if subject_progress:
            for sub, p in subject_progress.items():
                pct = int(p["done"] / p["total"] * 100)
                st.write(f"**{sub}** ({pct}%)")
                st.progress(pct / 100.0)
        else:
            st.info("Add assignments to track progress.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='glass-card'><h3>Upcoming Deadlines</h3>", unsafe_allow_html=True)
        # Filter for pending/in-progress assignments with future due dates
        upcoming_df = assignments_df[
            (assignments_df['Status'].isin(['Pending', 'In Progress'])) &
            (assignments_df['Due Date'] >= pd.Timestamp(datetime.date.today()))
        ].sort_values(by='Due Date')

        if not upcoming_df.empty:
            for _, row in upcoming_df.head(5).iterrows(): # Show top 5 upcoming
                days_left = (row['Due Date'].date() - datetime.date.today()).days
                st.write(f"**{row['Title']}** ({row['Subject']})")
                st.caption(f"Due: {row['Due Date'].strftime('%Y-%m-%d')} ({days_left} days left)")
        else:
            st.info("No upcoming deadlines.")
        st.markdown("</div>", unsafe_allow_html=True)


with tab_ai_assistant:
    st.markdown("<h2 style='text-align: center; color: #818cf8;'>AI Study Assistant</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Get summaries, flashcards, and study tips for your subjects.</p>", unsafe_allow_html=True)

    subjects = list(ai.KNOWLEDGE_BASE.keys()) # Get subjects from the mock AI engine
    selected_subject = st.selectbox("Select a Subject", subjects)

    if selected_subject:
        subject_info = ai.get_subject_info(selected_subject)
        if subject_info:
            tab_summary, tab_flashcards, tab_whiteboard, tab_tips = st.tabs(["Summary", "Flashcards", "Concept Board", "Study Tips"])

            with tab_summary:
                st.markdown(f"<div class='glass-card'><h3>Summary for {selected_subject.capitalize()}</h3><p>{subject_info['summary']}</p></div>", unsafe_allow_html=True)

            with tab_flashcards:
                st.markdown(f"<div class='glass-card'><h3>Flashcards for {selected_subject.capitalize()}</h3>", unsafe_allow_html=True)
                flashcards = subject_info["flashcards"]
                if flashcards:
                    for i, (question, answer) in enumerate(flashcards):
                        with st.expander(f"Flashcard {i+1}: {question}"):
                            st.write(answer)
                else:
                    st.info("No flashcards available for this subject.")
                st.markdown("</div>", unsafe_allow_html=True)

            with tab_whiteboard:
                st.markdown(f"<div class='glass-card'><h3>Concept Board for {selected_subject.capitalize()}</h3>", unsafe_allow_html=True)
                st.markdown(subject_info["whiteboard"])
                st.markdown("</div>", unsafe_allow_html=True)

            with tab_tips:
                st.markdown(f"<div class='glass-card'><h3>Study Tips for {selected_subject.capitalize()}</h3>", unsafe_allow_html=True)
                tips = subject_info["tips"]
                if tips:
                    for tip in tips:
                        st.markdown(f"- {tip}")
                else:
                    st.info("No study tips available for this subject.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("Subject information not found in AI engine.")


with tab_assignments:
    st.markdown("<h2 style='text-align: center; color: #818cf8;'>Assignment Management</h2>", unsafe_allow_html=True)

    col_form, col_list = st.columns([1, 1.2])

    with col_form:
        st.markdown("<div class='glass-card'><h3>Add Assignment</h3>", unsafe_allow_html=True)
        with st.form("add_assignment_form", clear_on_submit=True):
            draft = st.session_state.draft_assignment
            title      = st.text_input("Title", value=draft["title"])
            subject    = st.text_input("Subject", value=draft["subject"])
            # Ensure due_date is a datetime.date object
            due_date   = st.date_input("Due Date", value=draft["due_date"] if isinstance(draft["due_date"], datetime.date) else datetime.date.today())
            priority   = st.selectbox("Priority", ["Low", "Medium", "High"],   index=["Low","Medium","High"].index(draft["priority"]))
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy","Medium","Hard"].index(draft["difficulty"]))
            status     = st.selectbox("Status", ["Pending", "In Progress", "Completed", "Submitted"])

            add_submitted = st.form_submit_button("Add Assignment")
            if add_submitted:
                db.add_assignment(title, subject, due_date.strftime("%Y-%m-%d"), priority, difficulty, status)
                # Reset draft after submission
                st.session_state.draft_assignment = {
                    "title": "", "subject": "", "due_date": datetime.date.today(),
                    "priority": "Medium", "difficulty": "Medium", "status": "Pending"
                }
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_list:
        st.markdown("<div class='glass-card'><h3>All Assignments</h3>", unsafe_allow_html=True)
        if not assignments_df.empty:
            # Display assignments as a table or sortable list
            st.dataframe(
                assignments_df[['Title', 'Subject', 'Due Date', 'Priority', 'Status']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Due Date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD")
                }
            )

            st.markdown("<h4>Update/Delete Assignment</h4>", unsafe_allow_html=True)
            col_select_id, col_actions = st.columns([0.7, 1.3])
            with col_select_id:
                assignment_ids = assignments_df['id'].tolist()
                selected_assignment_id = st.selectbox("Select Assignment ID", assignment_ids, key="edit_assign_id")

            if selected_assignment_id:
                selected_assignment = assignments_df[assignments_df['id'] == selected_assignment_id].iloc[0]
                with st.form(f"edit_assignment_form_{selected_assignment_id}"):
                    edit_title      = st.text_input("Title", value=selected_assignment["Title"])
                    edit_subject    = st.text_input("Subject", value=selected_assignment["Subject"])
                    edit_due_date   = st.date_input("Due Date", value=selected_assignment["Due Date"].date()) # .date() to get date object
                    edit_priority   = st.selectbox("Priority", ["Low", "Medium", "High"],   index=["Low","Medium","High"].index(selected_assignment["Priority"]))
                    edit_difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy","Medium","Hard"].index(selected_assignment["Difficulty"]))
                    edit_status     = st.selectbox("Status", ["Pending", "In Progress", "Completed", "Submitted"], index=["Pending", "In Progress", "Completed", "Submitted"].index(selected_assignment["Status"]))

                    col_update, col_delete = st.columns(2)
                    with col_update:
                        update_submitted = st.form_submit_button("Update Assignment")
                    with col_delete:
                        delete_submitted = st.form_submit_button("Delete Assignment")

                    if update_submitted:
                        db.update_assignment(selected_assignment_id, edit_title, edit_subject, edit_due_date.strftime("%Y-%m-%d"), edit_priority, edit_difficulty, edit_status)
                        st.rerun()
                    if delete_submitted:
                        db.delete_assignment(selected_assignment_id)
                        st.rerun()
        else:
            st.info("No assignments added yet.")
        st.markdown("</div>", unsafe_allow_html=True)


st.markdown("<div class='footer'>© 2026 EduMate AI</div>", unsafe_allow_html=True)

# ======================================================
# RUN:
# streamlit run app.py
# ======================================================
