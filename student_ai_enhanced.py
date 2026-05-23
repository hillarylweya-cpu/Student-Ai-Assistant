import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date, timedelta
import pandas as pd
import random
from enum import Enum

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="EduMate AI - Enhanced",
    page_icon="🎓",
    layout="wide"
)

# =========================
# ENUMS & CONSTANTS
# =========================
class ExplanationLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class QuestionType(Enum):
    MCQ = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"

# =========================
# DATABASE SETUP
# =========================
@st.cache_resource
def get_connection():
    """Return a cached, thread-safe DB connection."""
    conn = sqlite3.connect("student_ai_assistant_enhanced.db", check_same_thread=False)
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

    c.execute('''
    CREATE TABLE IF NOT EXISTS study_streak (
        user_email TEXT PRIMARY KEY,
        streak INTEGER DEFAULT 0,
        last_login TEXT
    )
    ''')

    # NEW: Gamification system
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_stats (
        user_email TEXT PRIMARY KEY,
        xp_points INTEGER DEFAULT 0,
        badges TEXT DEFAULT "",
        level INTEGER DEFAULT 1,
        total_quizzes_taken INTEGER DEFAULT 0,
        total_quizzes_passed INTEGER DEFAULT 0,
        last_challenge_date TEXT
    )
    ''')

    # NEW: AI conversation history
    c.execute('''
    CREATE TABLE IF NOT EXISTS conversation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        topic TEXT,
        question TEXT,
        response TEXT,
        explanation_level TEXT,
        timestamp TEXT
    )
    ''')

    # NEW: Student notes for AI processing
    c.execute('''
    CREATE TABLE IF NOT EXISTS student_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        subject TEXT,
        content TEXT,
        created_date TEXT
    )
    ''')

    # NEW: Revision plans
    c.execute('''
    CREATE TABLE IF NOT EXISTS revision_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        exam_name TEXT,
        exam_date TEXT,
        subjects TEXT,
        revision_schedule TEXT,
        created_date TEXT
    )
    ''')

    # NEW: Daily challenges
    c.execute('''
    CREATE TABLE IF NOT EXISTS daily_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        challenge_date TEXT,
        subject TEXT,
        challenge_type TEXT,
        challenge_content TEXT,
        completed BOOLEAN DEFAULT 0,
        xp_earned INTEGER DEFAULT 0
    )
    ''')

    # NEW: Wellness tracking
    c.execute('''
    CREATE TABLE IF NOT EXISTS wellness_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        date TEXT,
        stress_level INTEGER,
        engagement_level INTEGER,
        study_hours REAL,
        mood TEXT
    )
    ''')

    conn.commit()
    return conn


conn = get_connection()
c = conn.cursor()

# =========================
# HELPER FUNCTIONS - AUTHENTICATION
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(fullname, email, password):
    try:
        c.execute(
            "INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)",
            (fullname, email, hash_password(password))
        )
        # Initialize user stats
        c.execute(
            "INSERT INTO user_stats (user_email) VALUES (?)",
            (email,)
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


# =========================
# HELPER FUNCTIONS - ASSIGNMENTS & TIMETABLE
# =========================
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


# =========================
# HELPER FUNCTIONS - STREAK & STATS
# =========================
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

    from datetime import timedelta
    yesterday = str(date.today() - timedelta(days=1))
    new_streak = streak + 1 if last_login == yesterday else 1
    c.execute("UPDATE study_streak SET streak=?, last_login=? WHERE user_email=?", (new_streak, today, user_email))
    conn.commit()
    return new_streak


# =========================
# GAMIFICATION FUNCTIONS
# =========================
def get_user_stats(user_email):
    c.execute(
        "SELECT xp_points, badges, level, total_quizzes_taken, total_quizzes_passed FROM user_stats WHERE user_email=?",
        (user_email,)
    )
    return c.fetchone()


def add_xp_points(user_email, xp):
    """Add XP to user and check for level up"""
    stats = get_user_stats(user_email)
    if stats:
        current_xp, badges, level, quizzes_taken, quizzes_passed = stats
        new_xp = current_xp + xp
        new_level = (new_xp // 100) + 1
        
        c.execute(
            "UPDATE user_stats SET xp_points=?, level=? WHERE user_email=?",
            (new_xp, new_level, user_email)
        )
        conn.commit()
        return new_xp, new_level


def award_badge(user_email, badge_name):
    """Award a badge to user"""
    stats = get_user_stats(user_email)
    if stats:
        xp, badges, level, quizzes_taken, quizzes_passed = stats
        badge_list = badges.split(",") if badges else []
        
        if badge_name not in badge_list:
            badge_list.append(badge_name)
            new_badges = ",".join(badge_list)
            c.execute(
                "UPDATE user_stats SET badges=? WHERE user_email=?",
                (new_badges, user_email)
            )
            conn.commit()
            return True
    return False


def update_quiz_stats(user_email, passed):
    """Update quiz statistics"""
    stats = get_user_stats(user_email)
    if stats:
        xp, badges, level, quizzes_taken, quizzes_passed = stats
        new_quizzes_taken = quizzes_taken + 1
        new_quizzes_passed = quizzes_passed + (1 if passed else 0)
        
        c.execute(
            "UPDATE user_stats SET total_quizzes_taken=?, total_quizzes_passed=? WHERE user_email=?",
            (new_quizzes_taken, new_quizzes_passed, user_email)
        )
        conn.commit()


# =========================
# AI CONVERSATION & STUDY BUDDY
# =========================
STUDY_RESPONSES = {
    "math": {
        "beginner": (
            "🔰 **Beginner Level - Math Basics**\n\n"
            "Let's break this down into simple steps:\n"
            "1. **Identify what you know** - Write down all given numbers\n"
            "2. **Identify what you need to find** - What is the question asking?\n"
            "3. **Choose a formula** - Select the right tool for the job\n"
            "4. **Substitute values** - Plug in your numbers carefully\n"
            "5. **Solve step-by-step** - Take it one operation at a time\n\n"
            "**Example:** If you have 5 apples and gain 3 more, you now have 5 + 3 = 8 apples.\n\n"
            "What specific math problem would you like help with? I can explain it step-by-step!"
        ),
        "intermediate": (
            "📚 **Intermediate Level - Math Problem Solving**\n\n"
            "Here's my approach to solving math problems:\n"
            "1. **Read carefully** - Underline key numbers and what's being asked\n"
            "2. **Draw a diagram** - Visualize the problem (especially for geometry)\n"
            "3. **List formulas** - Write down relevant equations\n"
            "4. **Show all steps** - Never skip steps; your work is as important as the answer\n"
            "5. **Check your work** - Substitute your answer back into the problem\n\n"
            "**Key tips:**\n"
            "- For algebra: Keep equations balanced by doing the same operation on both sides\n"
            "- For geometry: Remember angle/length relationships\n"
            "- For calculus: Know when to differentiate vs. integrate\n\n"
            "Share your problem and I'll guide you through it!"
        ),
        "advanced": (
            "🎓 **Advanced Level - Mathematical Thinking**\n\n"
            "At this level, we focus on:\n"
            "1. **Conceptual understanding** - Why does this formula work?\n"
            "2. **Proof techniques** - Mathematical induction, contradiction, direct proof\n"
            "3. **Multiple approaches** - Can you solve this problem different ways?\n"
            "4. **Optimization** - Finding maxima/minima using calculus\n"
            "5. **Real-world applications** - Where is this math used?\n\n"
            "**Advanced techniques:**\n"
            "- Transform problems into simpler forms\n"
            "- Look for patterns and symmetries\n"
            "- Use mathematical logic and set theory\n"
            "- Consider edge cases and boundary conditions\n\n"
            "Let's explore a challenging problem together!"
        ),
    },
    "physics": {
        "beginner": (
            "🔰 **Beginner Level - Physics Fundamentals**\n\n"
            "Physics is the study of how things move and interact:\n"
            "1. **Define variables** - What are we measuring? (distance, time, speed, force?)\n"
            "2. **Draw a diagram** - Show forces with arrows (free-body diagram)\n"
            "3. **Apply Newton's Laws** - Objects at rest stay at rest, F = ma\n"
            "4. **Use formulas** - velocity, acceleration, force, energy\n"
            "5. **Check units** - Always include units in your answer\n\n"
            "**Basic concepts:**\n"
            "- Speed = distance ÷ time\n"
            "- Acceleration = change in velocity ÷ time\n"
            "- Force = mass × acceleration\n\n"
            "What physics topic interests you?"
        ),
        "intermediate": (
            "📚 **Intermediate Level - Physics Problem Solving**\n\n"
            "Now we're applying physics to real problems:\n"
            "1. **Analyze motion** - Is it constant velocity, accelerated, projectile?\n"
            "2. **Energy conservation** - Total energy is conserved in closed systems\n"
            "3. **Circular motion** - Understand centripetal force and acceleration\n"
            "4. **Waves & sound** - Frequency, wavelength, speed relationships\n"
            "5. **Electricity basics** - V = IR, P = VI\n\n"
            "**Problem-solving approach:**\n"
            "- Identify forces acting on the object\n"
            "- Use vector components (horizontal/vertical)\n"
            "- Apply conservation laws (energy, momentum)\n"
            "- Solve the resulting equations\n\n"
            "Ready for a physics challenge?"
        ),
        "advanced": (
            "🎓 **Advanced Level - Advanced Physics**\n\n"
            "We're diving deep into physical principles:\n"
            "1. **Thermodynamics** - Entropy, heat transfer, work\n"
            "2. **Quantum mechanics** - Wave functions, uncertainty principle\n"
            "3. **Relativity** - Time dilation, mass-energy equivalence\n"
            "4. **Field theory** - Gravitational and electromagnetic fields\n"
            "5. **Complex systems** - Coupled oscillators, chaos theory\n\n"
            "**Advanced techniques:**\n"
            "- Lagrangian and Hamiltonian mechanics\n"
            "- Differential equations and boundary conditions\n"
            "- Symmetry analysis and conservation laws\n"
            "- Numerical simulations\n\n"
            "Let's tackle advanced physics!"
        ),
    },
    "biology": {
        "beginner": (
            "🔰 **Beginner Level - Biology Basics**\n\n"
            "Biology is the study of living things:\n"
            "1. **Cells** - The basic unit of life (animal, plant, prokaryotic)\n"
            "2. **DNA** - The instruction manual for life\n"
            "3. **Photosynthesis** - How plants make food from sunlight\n"
            "4. **Respiration** - How cells get energy\n"
            "5. **Ecosystems** - How organisms interact with their environment\n\n"
            "**Key terms:**\n"
            "- Mitochondria: Powerhouse of the cell\n"
            "- Chloroplast: Where photosynthesis happens (plants)\n"
            "- Enzyme: Protein that speeds up reactions\n\n"
            "What biology topic would you like to explore?"
        ),
        "intermediate": (
            "📚 **Intermediate Level - Biology Systems**\n\n"
            "Understanding how biological systems work:\n"
            "1. **Genetics** - Inheritance, dominant/recessive traits, Punnett squares\n"
            "2. **Evolution** - Natural selection, adaptation, speciation\n"
            "3. **Human body systems** - Circulatory, nervous, digestive, immune\n"
            "4. **Ecology** - Food chains, population dynamics, succession\n"
            "5. **Photosynthesis & respiration** - Detailed processes\n\n"
            "**Study approach:**\n"
            "- Draw and label diagrams of processes\n"
            "- Connect structure to function\n"
            "- Learn key pathways and reactions\n"
            "- Practice explaining mechanisms\n\n"
            "Ready to dive into biological systems?"
        ),
        "advanced": (
            "🎓 **Advanced Level - Advanced Biology**\n\n"
            "Exploring sophisticated biological concepts:\n"
            "1. **Molecular biology** - Gene expression, protein synthesis, regulation\n"
            "2. **Biochemistry** - Metabolic pathways, enzyme kinetics\n"
            "3. **Developmental biology** - Embryogenesis, differentiation\n"
            "4. **Systems biology** - Network analysis, emergent properties\n"
            "5. **Conservation biology** - Biodiversity, population genetics\n\n"
            "**Advanced topics:**\n"
            "- CRISPR and genetic engineering\n"
            "- Stem cells and regeneration\n"
            "- Epigenetics and gene regulation\n"
            "- Evolutionary developmental biology\n\n"
            "Let's explore cutting-edge biology!"
        ),
    },
    "chemistry": {
        "beginner": (
            "🔰 **Beginner Level - Chemistry Fundamentals**\n\n"
            "Chemistry is the study of matter and reactions:\n"
            "1. **Atoms & elements** - Building blocks, periodic table basics\n"
            "2. **Compounds** - How atoms combine\n"
            "3. **Chemical reactions** - Breaking and forming bonds\n"
            "4. **Acids & bases** - pH scale, neutralization\n"
            "5. **States of matter** - Solid, liquid, gas\n\n"
            "**Basic concepts:**\n"
            "- Atomic number = number of protons\n"
            "- Valence electrons determine bonding\n"
            "- Reactions are always changing something\n\n"
            "What chemistry concept should we start with?"
        ),
        "intermediate": (
            "📚 **Intermediate Level - Chemical Processes**\n\n"
            "Understanding chemical transformations:\n"
            "1. **Balancing equations** - Mass conservation\n"
            "2. **Stoichiometry** - Calculating amounts of reactants/products\n"
            "3. **Bonding** - Ionic, covalent, metallic bonds\n"
            "4. **Solutions** - Concentration, dilution, molarity\n"
            "5. **Equilibrium** - When reactions go both ways\n\n"
            "**Problem-solving steps:**\n"
            "- Write the unbalanced equation\n"
            "- Balance atoms of each element\n"
            "- Use molar masses to convert grams to moles\n"
            "- Apply stoichiometric ratios\n\n"
            "Ready to solve chemistry problems?"
        ),
        "advanced": (
            "🎓 **Advanced Level - Advanced Chemistry**\n\n"
            "Exploring complex chemical systems:\n"
            "1. **Thermodynamics** - Enthalpy, entropy, free energy\n"
            "2. **Kinetics** - Reaction rates, activation energy, mechanisms\n"
            "3. **Electrochemistry** - Redox reactions, galvanic cells\n"
            "4. **Organic chemistry** - Functional groups, synthesis, mechanisms\n"
            "5. **Coordination chemistry** - Complex ions, crystal field theory\n\n"
            "**Advanced techniques:**\n"
            "- Quantum chemistry and bonding theory\n"
            "- Reaction mechanisms and intermediates\n"
            "- Spectroscopy for structure determination\n"
            "- Computational chemistry\n\n"
            "Let's tackle advanced chemistry!"
        ),
    },
}


def get_ai_explanation(topic, question, level):
    """Get AI explanation based on topic and level"""
    topic_lower = topic.lower()
    level_enum = ExplanationLevel(level)
    
    if topic_lower in STUDY_RESPONSES:
        return STUDY_RESPONSES[topic_lower].get(level, STUDY_RESPONSES[topic_lower].get("beginner"))
    
    # Fallback response
    return f"I'd love to help you understand {topic}! Could you ask a more specific question? For example: 'How does photosynthesis work?' or 'Explain electron configuration.'"


def save_conversation(user_email, topic, question, response, level):
    """Save conversation for learning history"""
    c.execute(
        "INSERT INTO conversation_history (user_email, topic, question, response, explanation_level, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (user_email, topic, question, response, level, str(datetime.now()))
    )
    conn.commit()


# =========================
# QUIZ GENERATION
# =========================
QUIZ_BANK = {
    "biology": [
        ("What is the powerhouse of the cell?", "Mitochondria", QuestionType.SHORT_ANSWER),
        ("What molecule carries genetic information?", "DNA", QuestionType.SHORT_ANSWER),
        ("What process do plants use to make food?", "Photosynthesis", QuestionType.SHORT_ANSWER),
        ("Mitochondria produces energy in the form of?", "ATP", QuestionType.SHORT_ANSWER),
        ("True or False: All cells have a nucleus.", "False", QuestionType.TRUE_FALSE),
    ],
    "math": [
        ("What is 12 × 8?", "96", QuestionType.SHORT_ANSWER),
        ("What is the square root of 81?", "9", QuestionType.SHORT_ANSWER),
        ("What is 15% of 200?", "30", QuestionType.SHORT_ANSWER),
        ("What is the value of π (pi) to 2 decimal places?", "3.14", QuestionType.SHORT_ANSWER),
        ("True or False: An isosceles triangle has all sides equal.", "False", QuestionType.TRUE_FALSE),
    ],
    "physics": [
        ("What is the SI unit of force?", "Newton", QuestionType.SHORT_ANSWER),
        ("What formula represents Newton's second law?", "F=ma", QuestionType.SHORT_ANSWER),
        ("What is the speed of light (m/s)?", "300000000", QuestionType.SHORT_ANSWER),
        ("What is the SI unit of energy?", "Joule", QuestionType.SHORT_ANSWER),
        ("True or False: Velocity and speed are the same thing.", "False", QuestionType.TRUE_FALSE),
    ],
    "chemistry": [
        ("What is the chemical symbol for water?", "H2O", QuestionType.SHORT_ANSWER),
        ("What is the atomic number of carbon?", "6", QuestionType.SHORT_ANSWER),
        ("What is the chemical symbol for gold?", "Au", QuestionType.SHORT_ANSWER),
        ("What gas do plants absorb for photosynthesis?", "CO2", QuestionType.SHORT_ANSWER),
        ("True or False: The pH of a neutral solution is 7.", "True", QuestionType.TRUE_FALSE),
    ],
    "history": [
        ("In what year did World War II end?", "1945", QuestionType.SHORT_ANSWER),
        ("Who was the first President of the United States?", "George Washington", QuestionType.SHORT_ANSWER),
        ("In what year did the Berlin Wall fall?", "1989", QuestionType.SHORT_ANSWER),
        ("Which empire was ruled by Julius Caesar?", "Roman", QuestionType.SHORT_ANSWER),
        ("True or False: World War I began in 1914.", "True", QuestionType.TRUE_FALSE),
    ],
}


def generate_quiz(topic):
    """Generate quiz for selected topic"""
    return QUIZ_BANK.get(topic.lower(), [])


def get_quiz_feedback(correct_answer, user_answer):
    """Generate feedback for quiz answer"""
    if user_answer.strip().lower() == correct_answer.strip().lower():
        return "✅ Correct!", True
    else:
        return f"❌ Incorrect. The correct answer is: {correct_answer}", False


# =========================
# REVISION & NOTES FUNCTIONS
# =========================
def save_notes(user_email, subject, content):
    """Save student notes"""
    c.execute(
        "INSERT INTO student_notes (user_email, subject, content, created_date) VALUES (?, ?, ?, ?)",
        (user_email, subject, content, str(date.today()))
    )
    conn.commit()


def get_user_notes(user_email):
    """Get all notes for user"""
    c.execute(
        "SELECT id, subject, content, created_date FROM student_notes WHERE user_email=? ORDER BY created_date DESC",
        (user_email,)
    )
    return c.fetchall()


def ai_generate_revision_plan(subjects, exam_date):
    """AI generates personalized revision plan"""
    days_until_exam = (datetime.strptime(exam_date, "%Y-%m-%d") - datetime.today()).days
    subjects_list = subjects.split(",")
    
    plan = f"**📚 Personalized Revision Plan**\n\n"
    plan += f"**Exam Date:** {exam_date} ({days_until_exam} days away)\n\n"
    plan += f"**Subjects to Cover:** {', '.join(subjects_list)}\n\n"
    plan += "**Weekly Schedule:**\n"
    
    for week in range(1, (days_until_exam // 7) + 2):
        plan += f"\n**Week {week}:**\n"
        for i, subject in enumerate(subjects_list):
            day = (week - 1) * 7 + (i % 7) + 1
            if day <= days_until_exam:
                plan += f"- Day {day}: {subject} - Review concepts and practice problems\n"
    
    plan += f"\n**Final Week:**\n"
    plan += "- Mock exams under timed conditions\n"
    plan += "- Review weak areas\n"
    plan += "- Light revision only\n"
    plan += "- Get good sleep before exam day\n"
    
    return plan


def ai_generate_summary(notes_content):
    """AI generates summary from notes"""
    summary = "**📋 AI-Generated Summary**\n\n"
    
    # Simple keyword extraction and organization
    lines = notes_content.split("\n")
    key_points = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
    
    summary += "**Key Points:**\n"
    for i, point in enumerate(key_points[:10], 1):
        summary += f"{i}. {point}\n"
    
    summary += "\n**Suggested Study Questions:**\n"
    summary += "1. What are the main concepts covered?\n"
    summary += "2. Which points are most important?\n"
    summary += "3. How do these concepts relate to each other?\n"
    summary += "4. What real-world examples illustrate these ideas?\n"
    
    return summary


def ai_generate_flashcards(notes_content):
    """AI generates flashcard questions from notes"""
    flashcards = []
    lines = notes_content.split("\n")
    
    for line in lines:
        if len(line.strip()) > 20:
            # Create a question-answer pair
            words = line.strip().split()
            if len(words) > 5:
                question = f"Explain: {' '.join(words[:5])}..."
                answer = line.strip()
                flashcards.append((question, answer))
    
    return flashcards[:10]  # Return first 10 flashcards


# =========================
# HOMEWORK ASSISTANCE
# =========================
def homework_assistant_response(subject, problem, struggle_area):
    """AI provides step-by-step homework help without giving final answer"""
    
    responses = {
        "math": (
            "🧮 **Math Problem-Solving Guide**\n\n"
            "I'll help you solve this without just giving you the answer!\n\n"
            "**Step 1: Understand the Problem**\n"
            "- What information are you given?\n"
            "- What are you asked to find?\n"
            "- Draw a diagram or write down all known values\n\n"
            "**Step 2: Plan Your Approach**\n"
            "- Which formula or method should you use?\n"
            "- Do you need multiple steps?\n"
            "- Check if similar problems exist\n\n"
            "**Step 3: Solve**\n"
            "- Show all your work\n"
            "- Do one operation at a time\n"
            "- Keep your work organized\n\n"
            "**Step 4: Check**\n"
            "- Does your answer make sense?\n"
            "- Check units\n"
            "- Verify with the original problem\n\n"
            "👉 **Now, tell me what your first attempt is, and I'll guide you from there!**"
        ),
        "science": (
            "🔬 **Science Problem-Solving Guide**\n\n"
            "Let me help you work through this!\n\n"
            "**Step 1: Identify the Concept**\n"
            "- What physics/chemistry/biology principle applies?\n"
            "- What formulas might you need?\n\n"
            "**Step 2: Gather Information**\n"
            "- List what you're given (with units)\n"
            "- Identify what you need to find\n"
            "- Are there standard constants you need?\n\n"
            "**Step 3: Set Up the Solution**\n"
            "- Write the relevant equation(s)\n"
            "- Substitute known values\n"
            "- Solve algebraically\n\n"
            "**Step 4: Interpret Results**\n"
            "- Do units make sense?\n"
            "- Is the magnitude reasonable?\n"
            "- What does this answer mean physically?\n\n"
            "👉 **What have you tried so far? Where are you stuck?**"
        ),
        "language": (
            "🌐 **Language Learning Help**\n\n"
            "I'm here to help you improve!\n\n"
            "**For Vocabulary:**\n"
            "- Learn word families (root + prefixes/suffixes)\n"
            "- Use the word in different sentences\n"
            "- Connect it to similar words in other languages\n\n"
            "**For Grammar:**\n"
            "- Identify the pattern or rule\n"
            "- Find examples in your textbook\n"
            "- Practice with similar sentences\n\n"
            "**For Writing:**\n"
            "- Plan your structure first\n"
            "- Write a draft\n"
            "- Check tense, agreement, and articles\n"
            "- Read it aloud for flow\n\n"
            "👉 **Share your attempt and let's work through it together!**"
        ),
        "coding": (
            "💻 **Coding Problem Help**\n\n"
            "Let's debug and solve this step by step!\n\n"
            "**Step 1: Break Down the Problem**\n"
            "- What is the input?\n"
            "- What is the desired output?\n"
            "- Can you split it into smaller parts?\n\n"
            "**Step 2: Choose Your Algorithm**\n"
            "- What approach suits this problem?\n"
            "- Time/space complexity considerations?\n\n"
            "**Step 3: Pseudocode First**\n"
            "- Write the logic in plain English\n"
            "- Think through edge cases\n"
            "- Then convert to actual code\n\n"
            "**Step 4: Test & Debug**\n"
            "- Test with sample inputs\n"
            "- Use print statements to debug\n"
            "- Fix one error at a time\n\n"
            "👉 **Show me your code and tell me what's not working!**"
        ),
    }
    
    default = (
        "📖 **Problem-Solving Approach**\n\n"
        "Rather than giving you the answer, let me guide you:\n\n"
        "1. **Understand** - Read the problem 2-3 times\n"
        "2. **Plan** - What method/formula applies?\n"
        "3. **Execute** - Work through it step-by-step\n"
        "4. **Verify** - Check your answer makes sense\n\n"
        "👉 **Tell me where specifically you're struggling, and I'll help!**"
    )
    
    for key in responses:
        if key.lower() in subject.lower():
            return responses[key]
    
    return default


# =========================
# GAMIFICATION - DAILY CHALLENGES
# =========================
def generate_daily_challenge(user_email):
    """Generate daily challenge for user"""
    today = str(date.today())
    
    # Check if challenge already exists today
    c.execute(
        "SELECT * FROM daily_challenges WHERE user_email=? AND challenge_date=?",
        (user_email, today)
    )
    if c.fetchone():
        return None  # Already have challenge today
    
    subjects = ["Math", "Science", "History", "Language"]
    challenge_types = ["Quick Quiz", "Problem Solving", "Concept Review"]
    
    subject = random.choice(subjects)
    challenge_type = random.choice(challenge_types)
    
    challenge_content = f"Today's {challenge_type}: {subject} - Answer 3 questions correctly to earn 50 XP!"
    
    c.execute(
        "INSERT INTO daily_challenges (user_email, challenge_date, subject, challenge_type, challenge_content) VALUES (?, ?, ?, ?, ?)",
        (user_email, today, subject, challenge_type, challenge_content)
    )
    conn.commit()
    
    return challenge_content


def complete_daily_challenge(user_email):
    """Mark daily challenge as complete and award XP"""
    today = str(date.today())
    
    c.execute(
        "UPDATE daily_challenges SET completed=1, xp_earned=50 WHERE user_email=? AND challenge_date=?",
        (user_email, today)
    )
    conn.commit()
    
    add_xp_points(user_email, 50)
    award_badge(user_email, "Daily Learner")


# =========================
# WELLNESS TRACKING
# =========================
def log_wellness(user_email, stress_level, engagement_level, study_hours, mood):
    """Log student wellness metrics"""
    c.execute(
        "INSERT INTO wellness_tracking (user_email, date, stress_level, engagement_level, study_hours, mood) VALUES (?, ?, ?, ?, ?, ?)",
        (user_email, str(date.today()), stress_level, engagement_level, study_hours, mood)
    )
    conn.commit()


def get_wellness_tips(stress_level, engagement_level):
    """Generate wellness tips based on metrics"""
    tips = "💪 **Wellness & Motivation Tips**\n\n"
    
    if stress_level >= 7:
        tips += "🟥 **High Stress Detected:**\n"
        tips += "- Take 5-minute breathing breaks every hour\n"
        tips += "- Try the 4-7-8 breathing technique\n"
        tips += "- Go for a quick walk\n"
        tips += "- Consider studying with friends\n\n"
    
    if engagement_level <= 3:
        tips += "🟧 **Low Engagement:**\n"
        tips += "- Try studying in a new location\n"
        tips += "- Study with a friend for accountability\n"
        tips += "- Gamify your learning - challenge yourself!\n"
        tips += "- Connect what you're learning to your interests\n\n"
    
    tips += "✨ **Daily Motivation:**\n"
    motivations = [
        "Every expert was once a beginner!",
        "Small consistent progress beats sporadic effort.",
        "You're closer to your goals than yesterday!",
        "Challenge yourself today, celebrate tomorrow!",
        "Your effort today shapes your future tomorrow!"
    ]
    tips += f"- {random.choice(motivations)}\n"
    
    return tips


# =========================
# SESSION STATE INIT
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = ""

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "explanation_level" not in st.session_state:
    st.session_state.explanation_level = "beginner"

# =========================
# AUTHENTICATION
# =========================
if not st.session_state.logged_in:

    st.title("🎓 EduMate AI - Enhanced")
    st.subheader("🚀 Smart Student AI Assistant with Advanced Features")

    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

    if menu == "Register":
        st.header("Create Account")

        fullname = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
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
    st.sidebar.title("🎓 EduMate AI Enhanced")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "🤖 AI Study Buddy",
            "📚 Homework Assistant",
            "🧠 Quiz Generator",
            "📝 Assignments",
            "📅 Timetable",
            "✍️ Notes & Revision",
            "🏆 Gamification",
            "💪 Wellness",
            "Analytics"
        ]
    )

    st.sidebar.success(f"Logged in as:\n{st.session_state.user_email}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

    # =========================
    # DASHBOARD
    # =========================
    if page == "Dashboard":
        st.title("📚 Student Dashboard")

        assignments = get_assignments(st.session_state.user_email)
        timetable = get_timetable(st.session_state.user_email)
        streak = get_or_update_streak(st.session_state.user_email)
        stats = get_user_stats(st.session_state.user_email)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("📚 Assignments", len(assignments))

        with col2:
            st.metric("🕐 Classes", len(timetable))

        with col3:
            st.metric("🔥 Streak", f"{streak} day{'s' if streak != 1 else ''}")

        if stats:
            with col4:
                st.metric("⭐ XP Points", stats[0])
            with col5:
                st.metric("📈 Level", stats[2])

        st.subheader("Upcoming Assignments")

        if assignments:
            today_str = str(date.today())
            rows = []
            for a in assignments:
                overdue = (a[3] < today_str and a[5] != "Completed")
                rows.append({
                    "Title": a[1],
                    "Subject": a[2],
                    "Due Date": a[3],
                    "Priority": a[4],
                    "Status": a[5],
                    "⚠️": "Overdue" if overdue else "On Track"
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No assignments yet!")

        st.subheader("💬 Daily Motivation")
        daily_seed = int(date.today().strftime("%Y%m%d"))
        motivations = [
            "Success starts with discipline! 💪",
            "Consistency beats intensity! 🎯",
            "Every expert was once a beginner! 🌟",
            "Your effort today shapes tomorrow! 🚀",
            "Small progress matters! 📈"
        ]
        st.success(motivations[daily_seed % len(motivations)])

    # =========================
    # AI STUDY BUDDY
    # =========================
    elif page == "🤖 AI Study Buddy":
        st.title("🤖 AI Study Buddy - Conversational Tutor")
        st.write("Your personal AI tutor that explains concepts step-by-step in your preferred complexity level.")

        col1, col2 = st.columns(2)

        with col1:
            subject = st.selectbox(
                "Select Subject",
                ["Math", "Physics", "Biology", "Chemistry"]
            )

        with col2:
            st.session_state.explanation_level = st.selectbox(
                "Explanation Level",
                ["Beginner", "Intermediate", "Advanced"],
                index=0
            ).lower()

        st.markdown("---")

        question = st.text_area(
            "Ask your question",
            placeholder="e.g., How does photosynthesis work? Can you explain it simply?"
        )

        if st.button("Get Explanation"):
            if not question.strip():
                st.warning("Please ask a question.")
            else:
                response = get_ai_explanation(subject, question, st.session_state.explanation_level)
                st.markdown(response)

                # Save conversation
                save_conversation(
                    st.session_state.user_email,
                    subject,
                    question,
                    response,
                    st.session_state.explanation_level
                )

                # Award XP for learning
                add_xp_points(st.session_state.user_email, 10)
                st.success("✅ +10 XP for learning!")

        st.markdown("---")
        st.caption("💡 **Features:** Follow-up questions supported • Simplified explanations available • 3 difficulty levels")

    # =========================
    # HOMEWORK ASSISTANT
    # =========================
    elif page == "📚 Homework Assistant":
        st.title("📚 AI Homework Assistant")
        st.write("Get step-by-step guidance without just getting the answer!")

        col1, col2 = st.columns(2)

        with col1:
            subject = st.selectbox(
                "Subject",
                ["Math", "Science", "Language", "Coding"],
                key="homework_subject"
            )

        with col2:
            struggle_area = st.text_input("Where are you stuck? (optional)")

        st.markdown("---")

        problem = st.text_area(
            "Describe your problem",
            placeholder="Paste your homework problem or question here..."
        )

        if st.button("Get Help"):
            if not problem.strip():
                st.warning("Please describe your problem.")
            else:
                response = homework_assistant_response(subject, problem, struggle_area)
                st.markdown(response)

                # Save to conversation history
                save_conversation(
                    st.session_state.user_email,
                    f"Homework: {subject}",
                    problem,
                    response,
                    "homework"
                )

                add_xp_points(st.session_state.user_email, 15)
                st.info("💡 This assistant guides you step-by-step without giving final answers directly!")

        st.markdown("---")
        st.caption("✨ **Supported:** Mathematics • Science (Physics, Chemistry, Biology) • Languages • Coding")

    # =========================
    # QUIZ GENERATOR
    # =========================
    elif page == "🧠 Quiz Generator":
        st.title("🧠 AI Quiz Generator")

        available_topics = list(QUIZ_BANK.keys())
        topic_input = st.selectbox(
            "Choose a Topic",
            [""] + [t.capitalize() for t in available_topics]
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Quiz"):
                if not topic_input:
                    st.warning("Please select a topic.")
                else:
                    questions = generate_quiz(topic_input)
                    st.session_state.quiz_topic = topic_input
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_answers = {i: "" for i in range(len(questions))}
                    st.session_state.quiz_submitted = False

        if st.session_state.quiz_questions:
            st.subheader(f"📝 Quiz: {st.session_state.quiz_topic}")

            with st.form("quiz_form"):
                for i, (question, _, q_type) in enumerate(st.session_state.quiz_questions):
                    st.write(f"**Q{i+1}. {question}**")

                    if q_type == QuestionType.TRUE_FALSE:
                        st.session_state.quiz_answers[i] = st.radio(
                            f"Answer for Q{i+1}",
                            ["True", "False"],
                            key=f"q_{i}"
                        )
                    else:
                        st.session_state.quiz_answers[i] = st.text_input(
                            f"Your answer for Q{i+1}",
                            key=f"q_{i}"
                        )

                submit_quiz = st.form_submit_button("Submit Quiz")

                if submit_quiz:
                    st.session_state.quiz_submitted = True

            if st.session_state.quiz_submitted:
                score = 0
                st.subheader("📊 Results")

                for i, (question, correct_answer, _) in enumerate(st.session_state.quiz_questions):
                    user_ans = str(st.session_state.quiz_answers.get(i, "")).strip().lower()
                    correct = correct_answer.strip().lower()
                    is_correct = user_ans == correct

                    if is_correct:
                        score += 1

                    icon = "✅" if is_correct else "❌"
                    st.write(f"{icon} **Q{i+1}:** {question}")
                    if not is_correct:
                        st.write(f"   Your answer: *{st.session_state.quiz_answers.get(i, '') or 'No answer'}*")
                        st.write(f"   Correct answer: **{correct_answer}**")

                total = len(st.session_state.quiz_questions)
                percentage = round((score / total) * 100)

                st.markdown(f"### 🏆 Score: {score}/{total} ({percentage}%)")

                # Award XP and badges
                xp_earned = min(100, percentage)
                add_xp_points(st.session_state.user_email, xp_earned)
                update_quiz_stats(st.session_state.user_email, percentage >= 60)

                if percentage == 100:
                    st.balloons()
                    st.success("🎉 Perfect Score! Outstanding work!")
                    award_badge(st.session_state.user_email, "Quiz Master")
                elif percentage >= 60:
                    st.success(f"✅ Great job! {percentage}%. Keep practicing!")
                    award_badge(st.session_state.user_email, "Quiz Achiever")
                else:
                    st.warning(f"Keep trying! {percentage}%. Review and try again.")

                st.info(f"✨ +{xp_earned} XP earned!")

                if st.button("🔄 Retake Quiz"):
                    st.session_state.quiz_submitted = False
                    st.rerun()

    # =========================
    # ASSIGNMENTS
    # =========================
    elif page == "📝 Assignments":
        st.title("📝 Assignment Tracker")

        with st.form("assignment_form"):
            title = st.text_input("Assignment Title")
            subject = st.text_input("Subject")
            due_date = st.date_input("Due Date", min_value=date.today())
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])

            submitted = st.form_submit_button("Add Assignment")

            if submitted:
                if not title.strip() or not subject.strip():
                    st.error("Title and Subject required.")
                else:
                    add_assignment(
                        st.session_state.user_email,
                        title.strip(),
                        subject.strip(),
                        str(due_date),
                        priority,
                        status
                    )
                    st.success(f"✅ '{title}' added!")

        st.subheader("Your Assignments")

        assignments = get_assignments(st.session_state.user_email)

        if assignments:
            for a in assignments:
                col1, col2 = st.columns([5, 1])
                with col1:
                    overdue = (str(a[3]) < str(date.today()) and a[5] != "Completed")
                    label = f"**{a[1]}** | {a[2]} | Due: {a[3]} | {a[4]} | {a[5]}"
                    if overdue:
                        label += " ⚠️"
                    st.markdown(label)
                with col2:
                    if st.button("🗑️", key=f"del_assign_{a[0]}"):
                        delete_assignment(a[0])
                        st.rerun()
        else:
            st.info("No assignments yet!")

    # =========================
    # TIMETABLE
    # =========================
    elif page == "📅 Timetable":
        st.title("📅 Timetable Manager")

        with st.form("timetable_form"):
            subject = st.text_input("Subject Name")
            day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")

            submitted = st.form_submit_button("Add Class")

            if submitted:
                if not subject.strip():
                    st.error("Subject name required.")
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
                    st.success(f"✅ Class added!")

        st.subheader("Weekly Timetable")

        timetable = get_timetable(st.session_state.user_email)

        if timetable:
            for entry in timetable:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{entry[2]}** | {entry[1]} | {entry[3]} – {entry[4]}")
                with col2:
                    if st.button("🗑️", key=f"del_tt_{entry[0]}"):
                        delete_timetable(entry[0])
                        st.rerun()
        else:
            st.info("No timetable entries yet!")

    # =========================
    # NOTES & REVISION
    # =========================
    elif page == "✍️ Notes & Revision":
        st.title("✍️ Smart Notes & Revision Assistant")

        tab1, tab2, tab3, tab4 = st.tabs(["My Notes", "AI Summary", "Flashcards", "Revision Plan"])

        with tab1:
            st.subheader("Save Your Study Notes")

            subject = st.text_input("Subject")
            notes = st.text_area("Your notes", placeholder="Paste or type your notes here...")

            if st.button("Save Notes"):
                if not subject.strip() or not notes.strip():
                    st.error("Subject and notes required.")
                else:
                    save_notes(st.session_state.user_email, subject, notes)
                    st.success("✅ Notes saved!")
                    add_xp_points(st.session_state.user_email, 5)

            st.markdown("---")
            st.subheader("Your Saved Notes")

            user_notes = get_user_notes(st.session_state.user_email)

            if user_notes:
                for note in user_notes:
                    st.markdown(f"**{note[1]}** ({note[3]})")
                    st.text(note[2][:200] + "..." if len(note[2]) > 200 else note[2])
                    st.divider()
            else:
                st.info("No notes yet!")

        with tab2:
            st.subheader("📋 AI-Generated Summaries")

            user_notes = get_user_notes(st.session_state.user_email)

            if user_notes:
                selected_note = st.selectbox(
                    "Select notes to summarize",
                    [f"{n[1]} ({n[3]})" for n in user_notes]
                )

                if st.button("Generate Summary"):
                    note_index = [f"{n[1]} ({n[3]})" for n in user_notes].index(selected_note)
                    summary = ai_generate_summary(user_notes[note_index][2])
                    st.markdown(summary)
                    add_xp_points(st.session_state.user_email, 10)
            else:
                st.info("Save notes first to generate summaries!")

        with tab3:
            st.subheader("🎴 AI-Generated Flashcards")

            user_notes = get_user_notes(st.session_state.user_email)

            if user_notes:
                selected_note = st.selectbox(
                    "Select notes for flashcards",
                    [f"{n[1]} ({n[3]})" for n in user_notes],
                    key="fc_select"
                )

                if st.button("Generate Flashcards"):
                    note_index = [f"{n[1]} ({n[3]})" for n in user_notes].index(selected_note)
                    flashcards = ai_generate_flashcards(user_notes[note_index][2])

                    for i, (q, a) in enumerate(flashcards):
                        with st.expander(f"📌 Flashcard {i+1}"):
                            st.write(f"**Q:** {q}")
                            st.write(f"**A:** {a}")

                    add_xp_points(st.session_state.user_email, 10)
            else:
                st.info("Save notes first!")

        with tab4:
            st.subheader("📚 Personalized Revision Plan")

            exam_name = st.text_input("Exam name")
            exam_date = st.date_input("Exam date")
            subjects_str = st.text_input("Subjects (comma-separated)")

            if st.button("Generate Revision Plan"):
                if not exam_name or not subjects_str:
                    st.error("Please fill in all fields.")
                else:
                    plan = ai_generate_revision_plan(subjects_str, str(exam_date))
                    st.markdown(plan)
                    add_xp_points(st.session_state.user_email, 15)

    # =========================
    # GAMIFICATION
    # =========================
    elif page == "🏆 Gamification":
        st.title("🏆 Gamified Learning System")

        stats = get_user_stats(st.session_state.user_email)

        if stats:
            xp, badges_str, level, quizzes_taken, quizzes_passed = stats

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("⭐ XP Points", xp)

            with col2:
                st.metric("📈 Level", level)

            with col3:
                st.metric("🎯 Quizzes Taken", quizzes_taken)

            with col4:
                pass_rate = round((quizzes_passed / quizzes_taken * 100)) if quizzes_taken > 0 else 0
                st.metric("✅ Pass Rate", f"{pass_rate}%")

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["Daily Challenges", "Badges", "Leaderboard"])

        with tab1:
            st.subheader("🎯 Daily Challenges")

            challenge = generate_daily_challenge(st.session_state.user_email)

            if challenge:
                st.info(challenge)

                if st.button("Complete Challenge"):
                    complete_daily_challenge(st.session_state.user_email)
                    st.success("🎉 Challenge completed! +50 XP earned!")
            else:
                st.success("✅ You've completed today's challenge! Come back tomorrow for more!")

        with tab2:
            st.subheader("🏅 Your Badges")

            if stats and stats[1]:
                badges = stats[1].split(",")
                cols = st.columns(3)
                for i, badge in enumerate(badges):
                    with cols[i % 3]:
                        st.markdown(f"🏅 **{badge}**")
            else:
                st.info("Complete challenges and quizzes to earn badges!")

        with tab3:
            st.subheader("🏆 Leaderboard")

            st.info("Top learners based on XP:")
            
            c.execute("SELECT user_email, xp_points FROM user_stats ORDER BY xp_points DESC LIMIT 10")
            leaderboard = c.fetchall()

            if leaderboard:
                for rank, (email, xp_pts) in enumerate(leaderboard, 1):
                    st.write(f"{rank}. {email}: ⭐ {xp_pts} XP")

    # =========================
    # WELLNESS
    # =========================
    elif page == "💪 Wellness":
        st.title("💪 Student Wellness & Motivation")

        st.subheader("📊 How are you feeling today?")

        col1, col2 = st.columns(2)

        with col1:
            stress_level = st.slider("Stress Level (1-10)", 1, 10, 5)
            engagement_level = st.slider("Engagement Level (1-10)", 1, 10, 7)

        with col2:
            study_hours = st.number_input("Hours studied today", 0.0, 24.0, 2.0)
            mood = st.selectbox("Current mood", ["Happy 😊", "Focused 🎯", "Tired 😴", "Stressed 😟", "Neutral 😐"])

        if st.button("Log Wellness Check"):
            log_wellness(st.session_state.user_email, stress_level, engagement_level, study_hours, mood)
            st.success("✅ Wellness logged!")

        st.markdown("---")
        st.subheader("💡 Personalized Wellness Tips")

        tips = get_wellness_tips(stress_level, engagement_level)
        st.markdown(tips)

        st.markdown("---")
        st.subheader("⚙️ Study Optimization")

        if study_hours > 5:
            st.warning("📌 You've been studying for a while! Take a break every 25 minutes (Pomodoro Technique).")
        elif study_hours < 1:
            st.info("📌 Try to get at least 1-2 hours of focused study today!")

        st.markdown("""
        **🎯 Study Tips:**
        - **Pomodoro:** 25 min study + 5 min break
        - **Active Recall:** Test yourself instead of re-reading
        - **Spaced Repetition:** Review after 1 day, 3 days, 1 week
        - **Deep Focus:** Study hardest subjects when fresh
        - **Sleep:** 7-9 hours for optimal memory consolidation
        """)

    # =========================
    # ANALYTICS
    # =========================
    elif page == "Analytics":
        st.title("📈 Student Analytics")

        assignments = get_assignments(st.session_state.user_email)

        if assignments:
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

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("By Priority")
                priority_counts = df["Priority"].value_counts()
                if not priority_counts.empty:
                    st.bar_chart(priority_counts)

            with col2:
                st.subheader("By Status")
                status_counts = df["Status"].value_counts()
                if not status_counts.empty:
                    st.bar_chart(status_counts)

            st.subheader("By Subject")
            subject_counts = df["Subject"].value_counts()
            if not subject_counts.empty:
                st.bar_chart(subject_counts)

        else:
            st.info("No data yet. Add assignments to see analytics!")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("🚀 EduMate AI Enhanced © 2026 | Smart Student AI Assistant with Advanced Features")
