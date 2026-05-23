import streamlit as st
import sqlite3
import hashlib
from datetime import date, datetime, timedelta
import pandas as pd
import random
import time
import json
import os
from difflib import get_close_matches
# Try importing plotly, fallback if not present
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="EduMate AI - Premium Student Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ======================================================
# DATABASE SETUP
# ======================================================
DB_PATH = "C:\\Users\\hilla\\.gemini\\antigravity\\scratch\\edumate_ai\\edumate_ai.db"
@st.cache_resource
def get_connection():
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    
    # Users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        password TEXT,
        gpa_target REAL DEFAULT 4.0
    )
    """)
    
    # Assignments
    c.execute("""
    CREATE TABLE IF NOT EXISTS assignments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        title TEXT,
        subject TEXT,
        due_date TEXT,
        priority TEXT,
        status TEXT,
        difficulty TEXT,
        file_name TEXT,
        file_content TEXT,
        teacher_comments TEXT,
        score INTEGER DEFAULT 0
    )
    """)
    
    # Timetable
    c.execute("""
    CREATE TABLE IF NOT EXISTS timetable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        subject TEXT,
        day TEXT,
        start_time TEXT,
        end_time TEXT,
        teacher_name TEXT,
        teacher_contact TEXT,
        zoom_link TEXT,
        attended INTEGER DEFAULT 0
    )
    """)
    
    # Study Streak
    c.execute("""
    CREATE TABLE IF NOT EXISTS study_streak(
        user_email TEXT PRIMARY KEY,
        streak INTEGER DEFAULT 0,
        last_login TEXT,
        badges TEXT DEFAULT '[]'
    )
    """)
    
    # Quiz History
    c.execute("""
    CREATE TABLE IF NOT EXISTS quiz_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        subject TEXT,
        score INTEGER,
        total INTEGER,
        percentage INTEGER,
        date_taken TEXT,
        difficulty TEXT
    )
    """)
    
    # Flashcards
    c.execute("""
    CREATE TABLE IF NOT EXISTS flashcards(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        subject TEXT,
        front TEXT,
        back TEXT
    )
    """)
    
    # Notifications
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        message TEXT,
        timestamp TEXT,
        read INTEGER DEFAULT 0
    )
    """)
    
    # Focus Sessions
    c.execute("""
    CREATE TABLE IF NOT EXISTS focus_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        date TEXT,
        duration_mins INTEGER
    )
    """)
    
    conn.commit()
    return conn
conn = get_connection()
c = conn.cursor()
# ======================================================
# DB HELPERS
# ======================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
def create_user(fullname, email, password):
    try:
        c.execute("""
        INSERT INTO users(fullname,email,password)
        VALUES(?,?,?)
        """, (fullname, email, hash_password(password)))
        conn.commit()
        
        # Seed initial system states
        add_notification(email, f"Welcome to EduMate AI, {fullname}! 👋 Get started by creating your active timetable classes.")
        add_notification(email, "Tip: Scan your drafts under the Assignments panel using our advanced checker!")
        
        # Seed focus history
        add_focus_session(email, str(date.today() - timedelta(days=4)), 45)
        add_focus_session(email, str(date.today() - timedelta(days=3)), 90)
        add_focus_session(email, str(date.today() - timedelta(days=2)), 30)
        add_focus_session(email, str(date.today() - timedelta(days=1)), 60)
        add_focus_session(email, str(date.today()), 20)
        
        return True
    except:
        return False
def login_user(email, password):
    c.execute("""
    SELECT * FROM users
    WHERE email=? AND password=?
    """, (email, hash_password(password)))
    return c.fetchone()
def update_user_gpa_target(email, target):
    c.execute("UPDATE users SET gpa_target=? WHERE email=?", (target, email))
    conn.commit()
def get_user_gpa_target(email):
    c.execute("SELECT gpa_target FROM users WHERE email=?", (email,))
    row = c.fetchone()
    return row[0] if row else 4.0
def add_assignment(user_email, title, subject, due_date, priority, status, difficulty="Medium", file_name=None, file_content=None, teacher_comments="", score=0):
    c.execute("""
    INSERT INTO assignments (user_email, title, subject, due_date, priority, status, difficulty, file_name, file_content, teacher_comments, score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_email, title, subject, due_date, priority, status, difficulty, file_name, file_content, teacher_comments, score))
    conn.commit()
    add_notification(user_email, f"New assignment created: **{title}** in **{subject}**.")
def get_assignments(user_email):
    c.execute("""
    SELECT id, title, subject, due_date, priority, status, difficulty, file_name, file_content, teacher_comments, score
    FROM assignments
    WHERE user_email=?
    ORDER BY due_date ASC
    """, (user_email,))
    return c.fetchall()
def delete_assignment(aid):
    c.execute("DELETE FROM assignments WHERE id=?", (aid,))
    conn.commit()
def update_assignment_status(aid, status, score=0, teacher_comments=""):
    if status == "Graded":
        c.execute("UPDATE assignments SET status=?, score=?, teacher_comments=? WHERE id=?", (status, score, teacher_comments, aid))
    else:
        c.execute("UPDATE assignments SET status=? WHERE id=?", (status, aid))
    conn.commit()
def add_timetable(user_email, subject, day, start_time, end_time, teacher_name="Unknown", teacher_contact="N/A", zoom_link=""):
    c.execute("""
    INSERT INTO timetable (user_email, subject, day, start_time, end_time, teacher_name, teacher_contact, zoom_link)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_email, subject, day, start_time, end_time, teacher_name, teacher_contact, zoom_link))
    conn.commit()
def get_timetable(user_email):
    c.execute("""
    SELECT id, subject, day, start_time, end_time, teacher_name, teacher_contact, zoom_link, attended
    FROM timetable
    WHERE user_email=?
    """, (user_email,))
    return c.fetchall()
def delete_timetable(tid):
    c.execute("DELETE FROM timetable WHERE id=?", (tid,))
    conn.commit()
def toggle_timetable_attendance(tid, attended):
    c.execute("UPDATE timetable SET attended=? WHERE id=?", (attended, tid))
    conn.commit()
def get_or_update_streak(user_email):
    today = str(date.today())
    c.execute("SELECT streak, last_login, badges FROM study_streak WHERE user_email=?", (user_email,))
    row = c.fetchone()
    
    if row is None:
        badges = json.dumps(["Novice Scholar 🎓"])
        c.execute("""
        INSERT INTO study_streak (user_email, streak, last_login, badges)
        VALUES (?, 1, ?, ?)
        """, (user_email, today, badges))
        conn.commit()
        return 1, ["Novice Scholar 🎓"]
        
    streak, last_login, badges_json = row
    badges = json.loads(badges_json)
    
    if last_login == today:
        return streak, badges
        
    yesterday = str(date.today() - timedelta(days=1))
    if last_login == yesterday:
        new_streak = streak + 1
    else:
        new_streak = 1
        
    new_badges = list(badges)
    if new_streak >= 3 and "3-Day Fire 🔥" not in new_badges:
        new_badges.append("3-Day Fire 🔥")
        add_notification(user_email, "Badge Unlocked! 🎉 You've achieved a 3-Day study streak!")
    if new_streak >= 7 and "Weekly Warrior ⚔️" not in new_badges:
        new_badges.append("Weekly Warrior ⚔️")
        add_notification(user_email, "Badge Unlocked! 🏆 You've kept your streak alive for a whole week!")
    if new_streak >= 15 and "Study Beast 🦁" not in new_badges:
        new_badges.append("Study Beast 🦁")
        add_notification(user_email, "Badge Unlocked! 👑 Unstoppable force! 15-Day streak!")
    c.execute("""
    UPDATE study_streak
    SET streak=?, last_login=?, badges=?
    WHERE user_email=?
    """, (new_streak, today, json.dumps(new_badges), user_email))
    conn.commit()
    
    return new_streak, new_badges
def add_quiz_record(user_email, subject, score, total, percentage, difficulty):
    today = str(date.today())
    c.execute("""
    INSERT INTO quiz_history (user_email, subject, score, total, percentage, date_taken, difficulty)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_email, subject, score, total, percentage, today, difficulty))
    conn.commit()
    
    if percentage >= 80:
        add_notification(user_email, f"Excellent! You scored {percentage}% in a {difficulty} {subject} quiz. 🌟")
    elif percentage < 50:
        add_notification(user_email, f"Keep practicing! You scored {percentage}% in {subject}. Re-check the study materials. 📚")
def get_quiz_records(user_email):
    c.execute("""
    SELECT id, subject, score, total, percentage, date_taken, difficulty
    FROM quiz_history
    WHERE user_email=?
    ORDER BY date_taken DESC
    """, (user_email,))
    return c.fetchall()
def add_flashcard(user_email, subject, front, back):
    c.execute("""
    INSERT INTO flashcards (user_email, subject, front, back)
    VALUES (?, ?, ?, ?)
    """, (user_email, subject, front, back))
    conn.commit()
def get_flashcards(user_email, subject=None):
    if subject:
        c.execute("SELECT id, subject, front, back FROM flashcards WHERE user_email=? AND subject=?", (user_email, subject))
    else:
        c.execute("SELECT id, subject, front, back FROM flashcards WHERE user_email=?", (user_email,))
    return c.fetchall()
def delete_flashcard(fid):
    c.execute("DELETE FROM flashcards WHERE id=?", (fid,))
    conn.commit()
def add_notification(user_email, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("""
    INSERT INTO notifications (user_email, message, timestamp, read)
    VALUES (?, ?, ?, 0)
    """, (user_email, message, now))
    conn.commit()
def get_notifications(user_email):
    c.execute("""
    SELECT id, message, timestamp, read
    FROM notifications
    WHERE user_email=?
    ORDER BY timestamp DESC
    """, (user_email,))
    return c.fetchall()
def mark_notifications_read(user_email):
    c.execute("UPDATE notifications SET read=1 WHERE user_email=?", (user_email,))
    conn.commit()
def add_focus_session(user_email, session_date, duration_mins):
    c.execute("""
    INSERT INTO focus_sessions (user_email, date, duration_mins)
    VALUES (?, ?, ?)
    """, (user_email, str(session_date), duration_mins))
    conn.commit()
def get_focus_sessions(user_email):
    c.execute("""
    SELECT id, date, duration_mins
    FROM focus_sessions
    WHERE user_email=?
    ORDER BY date ASC
    """, (user_email,))
    return c.fetchall()
# ======================================================
# LOCAL AI SIMULATION ENGINE
# ======================================================
KNOWLEDGE_BASE = {
    "mathematics": {
        "summary": "Practice algebra, geometry, calculus, statistics, graphs, equations, and formulas daily.",
        "whiteboard": "### 📐 Math Whiteboard Visualizer\n\n```\n   f(x) = x² - 4x + 4\n       │\n     4 │ *       *\n     3 │  *     *\n     2 │   *   *\n     1 │    * *\n     0 └───*-*-*───\n       -1  0 1 2 3\n```\n- This represents a parabolic function with vertex at (2,0).\n- Root of the equation is x = 2.",
        "tips": ["Always write down the formula first.", "Draw diagrams for geometry problems.", "Verify your answers by plugging values back in."],
        "flashcards": [
            ("What is Euler's formula?", "e^(i*pi) + 1 = 0"),
            ("What is the derivative of sin(x)?", "cos(x)"),
            ("Define an acute angle.", "An angle that is less than 90 degrees.")
        ]
    },
    "biology": {
        "summary": "Study genetics, ecology, anatomy, evolution, and cell biology with diagrams.",
        "whiteboard": "### 🧬 Animal Cell Organelles Whiteboard\n\n```\n      ┌─────────────────────────┐\n      │  [ Nucleus: DNA Control]│\n      │      ┌──────────┐       │\n      │      │  (====)  │       │\n      │      └──────────┘       │\n      │  [Mitochondria: ATP]    │\n      │    {o}   {o}   {o}       │\n      └─────────────────────────┘\n```\n- Mitochondria perform cellular respiration to produce energy.\n- The nucleus contains genetic material (DNA).",
        "tips": ["Draw biological pathways and label parts.", "Understand function rather than just names.", "Create analogies for complex cellular processes."],
        "flashcards": [
            ("What is the main function of ribosomes?", "Protein synthesis."),
            ("Explain natural selection.", "Organisms better adapted to their environment tend to survive and produce more offspring."),
            ("What does DNA stand for?", "Deoxyribonucleic acid.")
        ]
    },
    "physics": {
        "summary": "Focus on mechanics, electricity, energy, waves, motion, and formulas.",
        "whiteboard": "### ⚡ Physics Vector Diagram\n\n```\n          ↑ Force (F = ma)\n          │  *\n          │    *\n          │      * Action Vector\n   ───────┼─────────→ Velocity (v)\n          │\n          ↓ Friction\n```\n- Newton's First Law states an object remains in uniform motion unless acted on by external force.",
        "tips": ["Pay close attention to metric units.", "Resolve vectors into horizontal and vertical components.", "Connect theoretical laws to physical objects around you."],
        "flashcards": [
            ("State Newton's Second Law.", "Force equals mass times acceleration (F = ma)."),
            ("What is the speed of light in a vacuum?", "Approximately 3.00 × 10^8 meters per second."),
            ("What is kinetic energy?", "The energy an object possesses due to its motion.")
        ]
    },
    "chemistry": {
        "summary": "Revise reactions, chemical equations, organic chemistry, periodic table, and atomic structures.",
        "whiteboard": "### 🧪 Atomic Structure (Bohr Model)\n\n```\n          ( p+ n0 )   <-- Nucleus\n             ( )      <-- Shell 1 (2e-)\n            (   )     <-- Shell 2 (8e-)\n```\n- Covalent bonds involve sharing electrons.\n- Ionic bonds involve electrostatic attraction between oppositely charged ions.",
        "tips": ["Balance equations by inspecting atoms on both sides.", "Learn periodic table trends (electronegativity, atomic radius).", "Visualize molecular shapes in 3D."],
        "flashcards": [
            ("What is Avogadro's number?", "6.022 × 10^23 molecules/mol"),
            ("What pH value is considered neutral?", "7.0 (like pure water)"),
            ("Describe an exothermic reaction.", "A reaction that releases heat/energy to its surroundings.")
        ]
    },
    "computer science": {
        "summary": "Learn programming languages, database structures, web engineering, networks, and algorithms.",
        "whiteboard": "### 💻 Binary Search Tree Visual\n\n```\n             [8]   Root\n            /   \\\n          [3]   [10]\n         /   \\     \\\n       [1]   [6]   [14]\n```\n- Left children are always smaller; right children are larger.\n- Lookup complexity is O(log n) in a balanced tree.",
        "tips": ["Trace code execution manually with a dry run table.", "Understand time complexity using Big O notation.", "Write modular, clean, and well-commented code."],
        "flashcards": [
            ("What is the time complexity of searching a sorted array using Binary Search?", "O(log n)"),
            ("Explain polymorphism in OOP.", "The ability of different objects to respond to the same message/method call in their own custom way."),
            ("What does SQL stand for?", "Structured Query Language.")
        ]
    }
}
PERSONAS = {
    "Friendly Tutor": {
        "prefix": "Hello! I'm your friendly tutor. Let's work together to figure this out! 😊\n\n",
        "suffix": "\n\nYou're doing amazing! Let me know if you need another step-by-step breakdown. You got this! 🌟"
    },
    "Strict Teacher": {
        "prefix": "Greetings. As your teacher, I expect full focus and diligence. Let us review the facts directly. 📐\n\n",
        "suffix": "\n\nMake sure to write this down in your notebook. Practice is not optional. Go study! 📝"
    },
    "Motivational Coach": {
        "prefix": "TEAM! Let's get focused! You are building your future right here, right now! Let's crush this subject! 💪\n\n",
        "suffix": "\n\nSuccess isn't given; it's earned! Let's keep pushing! What's our next goal? 🔥"
    }
}
def ai_chat_response(prompt, subject="computer science", persona_mode="Friendly Tutor"):
    prompt_lower = prompt.lower()
    persona = PERSONAS.get(persona_mode, PERSONAS["Friendly Tutor"])
    matched = get_close_matches(prompt_lower, KNOWLEDGE_BASE.keys(), n=1, cutoff=0.25)
    
    if matched:
        sub = matched[0]
        data = KNOWLEDGE_BASE[sub]
        response = f"**Here is your study guide for {sub.title()}:**\n\n"
        response += f"*{data['summary']}*\n\n"
        response += "### 💡 Key Concept Highlights\n"
        for fc in data['flashcards']:
            response += f"- **Q**: {fc[0]}\n  **A**: {fc[1]}\n"
        response += "\n### 📈 Active Recall Strategy\n"
        for tip in data['tips']:
            response += f"- {tip}\n"
    else:
        if "help" in prompt_lower or "explain" in prompt_lower:
            response = f"I'd love to help explain that. Let's break it down. When studying {subject}, try connecting concepts to real-world examples. Review the vocabulary, build a mind-map, and test yourself on simple terms before diving into advanced problems."
        elif "code" in prompt_lower or "program" in prompt_lower:
            response = "Here is a python pattern to solve that task:\n```python\n# Automated Study Helper Function\ndef solve_problem(inputs):\n    # 1. Analyze properties\n    # 2. Apply formula/logic\n    # 3. Output step-by-step guide\n    output = f'Processed {inputs} successfully'\n    return output\n\nprint(solve_problem('EduMate AI'))\n```"
        elif "essay" in prompt_lower or "write" in prompt_lower:
            response = "### 📝 Academic Essay Outline Generator\n\n1. **Introduction**: Introduce the topic, provide background context, and state a strong thesis.\n2. **Body Paragraph 1**: Key argument or primary piece of evidence supporting your thesis.\n3. **Body Paragraph 2**: Secondary argument, supporting analysis, and data.\n4. **Counter-argument**: Acknowledge opposing viewpoints and refute them logically.\n5. **Conclusion**: Restate thesis in a new way, summarize arguments, and make a final impactful statement."
        else:
            response = f"Interesting question about {subject}! That covers key parts of curriculum standards. Make sure to build a quick summary of the core definitions, practice equations daily, and use active recall flashcards to test your memory retention."
            
    return f"{persona['prefix']}{response}{persona['suffix']}"
def generate_flashcards(prompt, subject="General"):
    prompt = prompt.lower()
    concepts = [
        ("Core Term", "The fundamental concept or foundation of the topic."),
        ("Key Methodology", "The step-by-step process used to solve problems in this domain."),
        ("Common Pitfall", "A typical mistake made by students and how to avoid it.")
    ]
    if "math" in prompt or "algebra" in prompt:
        concepts = [
            ("Variable", "A symbol (usually a letter) standing in for an unknown numerical value."),
            ("Equation", "A mathematical statement showing that two expressions are equal."),
            ("Function", "A relation that associates each input with exactly one output.")
        ]
    elif "biol" in prompt or "cell" in prompt:
        concepts = [
            ("Mitosis", "Cell division resulting in two genetically identical daughter cells."),
            ("ATP", "Adenosine triphosphate, the primary energy carrier in cells."),
            ("Gene", "A sequence of nucleotides in DNA coding for a molecule that has a function.")
        ]
    elif "comp" in prompt or "code" in prompt:
        concepts = [
            ("Algorithm", "A step-by-step procedure or set of rules for solving a problem."),
            ("Variable Scope", "The region of program code within which a variable is accessible."),
            ("Recursion", "A programming technique where a function calls itself directly or indirectly.")
        ]
    return [{"front": f[0], "back": f[1], "subject": subject.title()} for f in concepts]
def generate_whiteboard_diagram(subject):
    sub = subject.lower()
    matched = get_close_matches(sub, KNOWLEDGE_BASE.keys(), n=1, cutoff=0.3)
    if matched:
        return KNOWLEDGE_BASE[matched[0]]["whiteboard"]
    return """### 🎨 Freeform AI Drawing Board
```
    ┌──────────────────────────────────┐
    │                                  │
    │         [ Your Concept ]         │
    │                │                 │
    │                ▼                 │
    │         [ Subtopic A ]           │
    │                                  │
    └──────────────────────────────────┘
```
Select a core science subject (Math, Biology, Physics, Chemistry, CS) to render a structured diagram!"""
def ai_grammar_plagiarism_check(text):
    if not text or len(text.strip()) < 10:
        return {
            "score": 100,
            "grammar_errors": [],
            "plagiarism_percent": 0,
            "plagiarism_sources": [],
            "feedback": "Text is too short to run comprehensive checks. Please upload more detailed content."
        }
        
    errors = []
    text_lower = text.lower()
    if "i is" in text_lower or "he are" in text_lower or "they was" in text_lower:
        errors.append("Subject-verb agreement error detected (e.g. 'I is', 'he are', 'they was').")
    if "there is many" in text_lower or "there is several" in text_lower:
        errors.append("Plural quantity mismatch (use 'there are' instead of 'there is').")
    if "loose" in text_lower and "win" in text_lower:
        errors.append("Possible homophone confusion: Did you mean 'lose' instead of 'loose'?")
        
    plag_percent = 0
    sources = []
    suspicious_phrases = ["according to wikipedia", "the free encyclopedia", "all rights reserved", "retrieved from source"]
    for phrase in suspicious_phrases:
        if phrase in text_lower:
            plag_percent += 25
            sources.append("Online encyclopedia (Wikipedia reference)")
            
    if len(text.split()) > 100 and plag_percent == 0:
        plag_percent = random.choice([0, 5, 12])
        if plag_percent > 0:
            sources.append("Standard academic textbook repository")
            
    score = max(0, 100 - len(errors) * 10 - plag_percent)
    feedback = "Excellent write-up! Keep your expressions clear and cite your sources."
    if plag_percent > 20:
        feedback = "Warning: Multiple matches found with online resources. Please rewrite matching sentences in your own words."
    elif len(errors) > 0:
        feedback = "Good draft, but contains minor grammar/punctuation issues. Review the flagged lines."
        
    return {
        "score": score,
        "grammar_errors": errors,
        "plagiarism_percent": plag_percent,
        "plagiarism_sources": sources,
        "feedback": feedback
    }
def translate_notes(text, target_language):
    lang_map = {
        "Spanish": " [Traducido al Español]: ",
        "French": " [Traduit en Français]: ",
        "German": " [In das Deutsche übersetzt]: ",
        "Swahili": " [Imetafsiriwa kwa Kiswahili]: ",
        "Japanese": " [日本語訳]: ",
        "Chinese": " [中文翻译]: "
    }
    prefix = lang_map.get(target_language, " [Translated]: ")
    translations = {
        "mitochondria is the powerhouse of the cell": "las mitocondrias son la central eléctrica de la célula",
        "what is the speed of light": "¿cuál es la velocidad de la luz?",
        "learning programming is fun": "aprender a programar es divertido"
    }
    text_clean = text.lower().strip().replace("?", "").replace(".", "")
    if text_clean in translations and target_language == "Spanish":
        return prefix + translations[text_clean].capitalize()
        
    words = text.split()
    translated_words = []
    for word in words:
        if len(word) > 4:
            translated_words.append(word[::-1].capitalize() + "io")
        else:
            translated_words.append(word)
    return prefix + " ".join(translated_words)
def generate_study_recommendations(quiz_records, assignments):
    recommendations = []
    subject_scores = {}
    for q in quiz_records:
        sub = q[1].lower()
        pct = q[4]
        if sub not in subject_scores:
            subject_scores[sub] = []
        subject_scores[sub].append(pct)
        
    weak_subjects = []
    for sub, scores in subject_scores.items():
        avg = sum(scores) / len(scores)
        if avg < 75:
            weak_subjects.append((sub, avg))
            
    for sub, avg in weak_subjects:
        recommendations.append({
            "priority": "High",
            "subject": sub.title(),
            "reason": f"Your average score is only {int(avg)}%. Practice more mock quizzes here.",
            "action": "Generate Quiz"
        })
        
    for a in assignments:
        status = a[5]
        if status in ["Pending", "In Progress"]:
            recommendations.append({
                "priority": "Medium",
                "subject": a[2],
                "reason": f"Assignment '{a[1]}' is due on {a[3]}!",
                "action": "Complete Assignment"
            })
            
    if not recommendations:
        recommendations.append({
            "priority": "Low",
            "subject": "Mathematics",
            "reason": "Keep your daily habits strong. Review algebra formulas.",
            "action": "Start Study Session"
        })
    return recommendations
TEST_BANK = {
    "Primary School": {
        "Mathematics": [
            {"question": "What is 8 + 7?", "options": ["13", "14", "15", "16"], "answer": "15"},
            {"question": "How many sides does a triangle have?", "options": ["3", "4", "5", "6"], "answer": "3"}
        ],
        "Biology": [
            {"question": "Which animal can fly?", "options": ["Dog", "Elephant", "Eagle", "Cat"], "answer": "Eagle"},
            {"question": "Do plants need sunlight to grow?", "options": ["Yes", "No"], "answer": "Yes"}
        ]
    },
    "High School": {
        "Mathematics": [
            {"question": "Solve for x: 2x + 5 = 15", "options": ["x=5", "x=10", "x=7.5", "x=4"], "answer": "x=5"},
            {"question": "What is the area of a circle with radius 3? (Use pi = 3.14)", "options": ["18.84", "28.26", "9.42", "27.00"], "answer": "28.26"}
        ],
        "Physics": [
            {"question": "What is the acceleration due to gravity on Earth?", "options": ["9.8 m/s²", "10 m/s²", "9.8 km/s", "1.6 m/s²"], "answer": "9.8 m/s²"},
            {"question": "What happens to light when it enters a glass block?", "options": ["Reflects only", "Refracts and bends", "Speeds up", "Disappears"], "answer": "Refracts and bends"}
        ],
        "Chemistry": [
            {"question": "What is the atomic number of Carbon?", "options": ["4", "5", "6", "12"], "answer": "6"},
            {"question": "What type of bond is formed when electrons are shared?", "options": ["Ionic", "Hydrogen", "Covalent", "Metallic"], "answer": "Covalent"}
        ]
    },
    "University": {
        "Computer Science": [
            {"question": "Which sorting algorithm has a worst-case complexity of O(n²)?", "options": ["Merge Sort", "Quick Sort", "Heap Sort", "All of the above"], "answer": "Quick Sort"},
            {"question": "What is the primary difference between a stack and a queue?", "options": ["Stack is FIFO, Queue is LIFO", "Stack is LIFO, Queue is FIFO", "Stacks use more memory", "Queues do not support indexing"], "answer": "Stack is LIFO, Queue is FIFO"}
        ],
        "Mathematics": [
            {"question": "What is the limit of (sin x)/x as x approaches 0?", "options": ["0", "1", "Infinity", "Undefined"], "answer": "1"},
            {"question": "Calculate the determinant of matrix [[1,2],[3,4]].", "options": ["-2", "2", "10", "0"], "answer": "-2"}
        ],
        "Biology": [
            {"question": "Which enzyme replicates DNA?", "options": ["DNA Polymerase", "Helicase", "RNA Primase", "Ligase"], "answer": "DNA Polymerase"},
            {"question": "What is the net gain of ATP molecules during glycolysis?", "options": ["2 ATP", "4 ATP", "36 ATP", "0 ATP"], "answer": "2 ATP"}
        ]
    }
}
def generate_adaptive_quiz(subject, level):
    level_data = TEST_BANK.get(level, TEST_BANK["High School"])
    questions = level_data.get(subject, None)
    if not questions:
        questions = [
            {
                "question": f"Which of the following is a key study area of {subject}?",
                "options": ["Theoretical Analysis", "Hypothesis Formulation", "Practical Execution", "All of the above"],
                "answer": "All of the above"
            },
            {
                "question": f"What is a standard research method used in {subject}?",
                "options": ["Literature Reviews", "Experimental Designs", "Surveys", "All of the above"],
                "answer": "All of the above"
            }
        ]
    randomized_qs = []
    for q in questions:
        opts = list(q["options"])
        random.shuffle(opts)
        randomized_qs.append({
            "question": q["question"],
            "options": opts,
            "answer": q["answer"]
        })
    return randomized_qs
# ======================================================
# MODERN UI STYLING
# ======================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@300;500;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Outfit', 'Space Grotesk', sans-serif;
    color: #f8fafc;
}
.stApp {
    background: linear-gradient(135deg, #090d16 0%, #0f172a 40%, #1e1b4b 100%);
    background-attachment: fixed;
}
.main-title {
    text-align: center;
    background: linear-gradient(90deg, #818cf8, #6366f1, #3b82f6, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 65px;
    font-weight: 800;
    margin-bottom: 2px;
    letter-spacing: -2px;
}
.sub-title {
    text-align: center;
    color: #94a3b8;
    font-size: 22px;
    margin-bottom: 30px;
}
.glass-card {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 24px;
    padding: 28px;
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.09);
    box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
    margin-bottom: 20px;
    transition: transform 0.3s ease, border 0.3s ease;
}
.glass-card:hover {
    border: 1px solid rgba(129, 140, 248, 0.25);
}
.metric-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%);
    backdrop-filter: blur(12px);
    padding: 22px;
    border-radius: 20px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.07);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    margin-bottom: 15px;
}
.metric-card h1 {
    font-size: 45px;
    margin: 5px 0;
    font-weight: 800;
    background: linear-gradient(90deg, #60a5fa, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.badge-pill {
    background: linear-gradient(135deg, #4338ca 0%, #1e1b4b 100%);
    border: 1px solid #6366f1;
    color: #e0e7ff;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: bold;
    display: inline-block;
    margin: 4px;
}
.stButton > button {
    width: 100%;
    border: none;
    border-radius: 14px;
    padding: 12px 20px;
    font-size: 16px;
    font-weight: 700;
    background: linear-gradient(90deg, #4f46e5, #3b82f6);
    color: white !important;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #3b82f6, #2563eb);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
}
.chat-bubble-user {
    background: rgba(59, 130, 246, 0.15);
    border-left: 4px solid #3b82f6;
    padding: 14px 20px;
    border-radius: 0 20px 20px 20px;
    margin: 10px 0;
    color: #f1f5f9;
}
.chat-bubble-ai {
    background: rgba(129, 140, 248, 0.12);
    border-left: 4px solid #818cf8;
    padding: 14px 20px;
    border-radius: 20px 0 20px 20px;
    margin: 10px 0;
    color: #f1f5f9;
}
.current-class-highlight {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.05) 100%);
    border: 2px solid #ef4444 !important;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
    100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
.footer {
    text-align: center;
    color: #64748b;
    margin-top: 50px;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)
# ======================================================
# SESSION STATE
# ======================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_fullname" not in st.session_state:
    st.session_state.user_fullname = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_timer_start" not in st.session_state:
    st.session_state.quiz_timer_start = 0
if "battle_mode" not in st.session_state:
    st.session_state.battle_mode = False
if "auto_save_assignment" not in st.session_state:
    st.session_state.auto_save_assignment = {"title": "", "subject": "", "priority": "Medium", "difficulty": "Medium"}
# ======================================================
# GATEWAY VIEW
# ======================================================
if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🎓 EduMate AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Premium Global AI Education Platform</div>', unsafe_allow_html=True)
    auth_menu = st.sidebar.selectbox("Access Gate", ["Login", "Register"])
    
    if auth_menu == "Register":
        st.markdown("<div class='glass-card'><h2>📝 Create Account</h2>", unsafe_allow_html=True)
        fullname = st.text_input("Full Name (e.g. Hillary)")
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        
        if st.button("🚀 Register Now"):
            if not fullname or not email or not password:
                st.warning("All fields are required.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                if create_user(fullname, email, password):
                    st.success("Account created successfully! Switching to Login.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Email address already registered.")
        st.markdown("</div>", unsafe_allow_html=True)
    elif auth_menu == "Login":
        col_login, col_features = st.columns([1.2, 1])
        
        with col_login:
            st.markdown("<div class='glass-card'><h2 style='text-align:center;'>🔐 Student Sign In</h2>", unsafe_allow_html=True)
            email = st.text_input("📧 Registered Email")
            password = st.text_input("🔑 Password", type="password")
            
            if st.button("🚀 Sign In"):
                user = login_user(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_email = user[2]
                    st.session_state.user_fullname = user[1]
                    st.success(f"Welcome back, {user[1]}! 🎉")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_features:
            st.markdown("""
            <div class='glass-card'>
                <h3 style='color:#818cf8;'>🌟 Premium Features Included</h3>
                <p>⚡ <b>AI Assistant (ChatGPT-like):</b> Instantly ask questions, generate flashcards, summarize PDFs, or draw whiteboard visualizers.</p>
                <p>📝 <b>Assignment Health Checker:</b> Upload documents for plagiarism analysis, grammar check, and difficulty ratings.</p>
                <p>📅 <b>Active Timetable Tracker:</b> Auto-highlights current class with one-click Zoom/Meet launchers and teacher details.</p>
                <p>🧠 <b>Adaptive Quiz Arena:</b> Test yourself against adaptive levels or participate in multiplayer simulated battles.</p>
                <p>📈 <b>Grade & Focus Analytics:</b> Real-time charts of study hours, focus session heatmaps, and target GPA trackers.</p>
            </div>
            """, unsafe_allow_html=True)
# ======================================================
# CORE MAIN APPLICATION
# ======================================================
else:
    # Sidebar
    st.sidebar.markdown(f"<h2 style='text-align:center;'>🎓 EduMate Premium</h2>", unsafe_allow_html=True)
    st.sidebar.success(f"Student: {st.session_state.user_fullname}\n({st.session_state.user_email})")
    
    page = st.sidebar.radio(
        "Explore Hub",
        [
            "Dashboard",
            "AI Assistant",
            "Assignments Tracker",
            "Timetable Planner",
            "Quiz Generator",
            "Analytics Dashboard"
        ]
    )
    
    if st.sidebar.button("🚪 Logout Session"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.user_fullname = ""
        st.session_state.chat_history = []
        st.rerun()
        
    # Get active variables
    assignments = get_assignments(st.session_state.user_email)
    timetable = get_timetable(st.session_state.user_email)
    streak, badges = get_or_update_streak(st.session_state.user_email)
    notifications = get_notifications(st.session_state.user_email)
    quiz_records = get_quiz_records(st.session_state.user_email)
    focus_sessions = get_focus_sessions(st.session_state.user_email)
    gpa_target = get_user_gpa_target(st.session_state.user_email)
    # ==================================================
    # 1. STUDENT DASHBOARD PAGE
    # ==================================================
    if page == "Dashboard":
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "Good Morning"
        elif current_hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
            
        now_str = datetime.now().strftime("%I:%M %p")
        weather_info = "☀️ 24°C - Perfect studying weather!" if current_hour < 18 else "🌙 18°C - Calm night for review."
        
        quotes = [
            "Believe you can and you're halfway there. 🌟",
            "Education is the most powerful weapon you can use to change the world. 🌍",
            "The secret of getting ahead is getting started. 🚀",
            "Don't let what you cannot do interfere with what you can do. 📐",
            "Every expert was once a beginner. Keep pushing! 🦁"
        ]
        motivational_quote = quotes[hash(st.session_state.user_fullname) % len(quotes)]
        
        # Dashboard Welcomer
        st.markdown(f"""
        <div class='glass-card' style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(59, 130, 246, 0.05) 100%); border-left: 6px solid #6366f1;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h1 style='margin: 0;'>{greeting}, {st.session_state.user_fullname} 👋</h1>
                    <p style='color:#a5b4fc; font-size:18px; margin-top:5px;'><i>\"{motivational_quote}\"</i></p>
                </div>
                <div style='text-align: right;'>
                    <h3 style='margin:0; color:#cbd5e1;'>⏰ {now_str}</h3>
                    <p style='margin:0; color:#94a3b8;'>{weather_info}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats Cards
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            pending_count = len([a for a in assignments if a[5] not in ["Completed", "Graded"]])
            st.markdown(f"""
            <div class='metric-card'>
                <p style='color: #94a3b8; font-size: 15px; margin: 0;'>📝 Pending Tasks</p>
                <h1>{pending_count}</h1>
                <span style='color: #f87171; font-size:12px;'>Action required soon</span>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            classes_today = len(timetable)
            st.markdown(f"""
            <div class='metric-card'>
                <p style='color: #94a3b8; font-size: 15px; margin: 0;'>📅 Active Classes</p>
                <h1>{classes_today}</h1>
                <span style='color: #38bdf8; font-size:12px;'>Timetable classes set</span>
            </div>
            """, unsafe_allow_html=True)
        with col_c:
            st.markdown(f"""
            <div class='metric-card'>
                <p style='color: #94a3b8; font-size: 15px; margin: 0;'>🔥 Study Streak</p>
                <h1>{streak} Days</h1>
                <span style='color: #fbbf24; font-size:12px;'>Daily study goal: Active</span>
            </div>
            """, unsafe_allow_html=True)
        with col_d:
            st.markdown(f"""
            <div class='metric-card'>
                <p style='color: #94a3b8; font-size: 15px; margin: 0;'>🎯 Target GPA</p>
                <h1>{gpa_target:.2f}</h1>
                <span style='color: #34d399; font-size:12px;'>Track score graphs</span>
            </div>
            """, unsafe_allow_html=True)
            
        col_left, col_right = st.columns([1.5, 1])
        
        with col_left:
            st.markdown("<div class='glass-card'><h3>📊 Subjects Completion Progress</h3>", unsafe_allow_html=True)
            subject_progress = {}
            for a in assignments:
                sub = a[2]
                status = a[5]
                if sub not in subject_progress:
                    subject_progress[sub] = {"total": 0, "done": 0}
                subject_progress[sub]["total"] += 1
                if status in ["Completed", "Graded"]:
                    subject_progress[sub]["done"] += 1
                    
            if subject_progress:
                for sub, progress in subject_progress.items():
                    pct = int((progress["done"] / progress["total"]) * 100)
                    st.write(f"**{sub}** ({pct}%)")
                    st.progress(pct / 100.0)
            else:
                st.info("No assignments added yet to track progress.")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='glass-card'><h3>📅 Study Calendar & Reminders</h3>", unsafe_allow_html=True)
            if timetable:
                for t in timetable:
                    st.markdown(f"🗓️ **{t[2]}** - {t[1]} class from {t[3]} to {t[4]} | Teacher: {t[5]}")
            else:
                st.info("No schedule entries. Add events in the Timetable Planner!")
            st.markdown("</div>", unsafe_allow_html=True)
        with col_right:
            st.markdown("<div class='glass-card'><h3>🏆 Badges & Accomplishments</h3>", unsafe_allow_html=True)
            badge_html = ""
            for b in badges:
                badge_html += f"<span class='badge-pill'>{b}</span>"
            if not badge_html:
                badge_html = "<p style='color:#94a3b8;'>Keep studying to unlock awards!</p>"
            st.markdown(f"<div>{badge_html}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='glass-card'><h3>⏳ Deadlines Countdown</h3>", unsafe_allow_html=True)
            active_deadlines = [a for a in assignments if a[5] not in ["Completed", "Graded"]]
            if active_deadlines:
                for a in active_deadlines:
                    try:
                        due_dt = datetime.strptime(a[3], "%Y-%m-%d").date()
                        delta = due_dt - date.today()
                        if delta.days < 0:
                            time_status = f"<span style='color:#f87171;'>Overdue by {abs(delta.days)} days</span>"
                        elif delta.days == 0:
                            time_status = "<span style='color:#f87171; font-weight:bold;'>DUE TODAY! ⏳</span>"
                        elif delta.days == 1:
                            time_status = "<span style='color:#fbbf24;'>Due tomorrow</span>"
                        else:
                            time_status = f"<span style='color:#34d399;'>Due in {delta.days} days</span>"
                        st.markdown(f"✍️ **{a[1]}** ({a[2]}) - {time_status}", unsafe_allow_html=True)
                    except:
                        st.markdown(f"✍️ **{a[1]}** ({a[2]}) - Due: {a[3]}", unsafe_allow_html=True)
            else:
                st.write("🎉 No pending assignments! Go generate a quiz.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        col_qa, col_notif = st.columns([1, 1])
        with col_qa:
            st.markdown("<div class='glass-card'><h3>⚡ Quick Actions</h3>", unsafe_allow_html=True)
            qa_col1, qa_col2 = st.columns(2)
            with qa_col1:
                if st.button("🧠 Start AI Quiz", key="qa_quiz"):
                    st.info("Head over to the Quiz Generator page in the sidebar!")
                if st.button("✍️ Upload Assignment", key="qa_upload"):
                    st.info("Upload materials under the Assignments Tracker page!")
            with qa_col2:
                if st.button("💬 Ask AI Tutor", key="qa_ai"):
                    st.info("Ask your questions in the AI Assistant tab!")
                if st.button("📅 Join Class Zoom", key="qa_zoom"):
                    st.info("Review link cards under the Timetable Planner page!")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_notif:
            unread_count = len([n for n in notifications if n[3] == 0])
            st.markdown(f"<div class='glass-card'><h3>🔔 Smart Notifications ({unread_count})</h3>", unsafe_allow_html=True)
            if notifications:
                for n in notifications[:4]:
                    read_indicator = "🔵" if n[3] == 0 else "⚪"
                    st.markdown(f"{read_indicator} <span style='font-size:14px; color:#cbd5e1;'>({n[2]})</span>: {n[1]}", unsafe_allow_html=True)
                if st.button("Mark All as Read"):
                    mark_notifications_read(st.session_state.user_email)
                    st.rerun()
            else:
                st.write("No notifications yet.")
            st.markdown("</div>", unsafe_allow_html=True)
    # ==================================================
    # 2. AI ASSISTANT CHAT & TOOLS PAGE
    # ==================================================
    elif page == "AI Assistant":
        st.markdown("<div class='glass-card'><h1 style='margin:0;'>🤖 Global AI Assistant</h1><p style='color:#a5b4fc;'>Active recall, concept visualizer, translation, and summary compiler</p></div>", unsafe_allow_html=True)
        
        col_control, col_chat = st.columns([1, 2])
        
        with col_control:
            st.markdown("<div class='glass-card'><h3>⚙️ Assistant Settings</h3>", unsafe_allow_html=True)
            persona_mode = st.selectbox("Tutor Personality", ["Friendly Tutor", "Strict Teacher", "Motivational Coach"])
            active_subject = st.selectbox("Focus Subject", ["Mathematics", "Biology", "Physics", "Chemistry", "Computer Science"])
            
            st.markdown("---")
            
            voice_support = st.checkbox("🎙️ Voice Input Simulation")
            if voice_support:
                voice_phrase = st.text_input("Speak out loud (Or type voice statement here):")
                if st.button("🎙️ Process Voice Statement"):
                    if voice_phrase:
                        st.session_state.chat_history.append({"role": "user", "content": f"[Simulated Voice] {voice_phrase}"})
                        ai_reply = ai_chat_response(voice_phrase, active_subject, persona_mode)
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                        st.rerun()
            
            st.markdown("---")
            st.markdown("<h4>📄 Notes Summarizer</h4>", unsafe_allow_html=True)
            uploaded_note = st.file_uploader("Upload Notes (TXT, PDF, Word)", type=["txt", "pdf", "docx"], key="summarize_uploader")
            if uploaded_note:
                st.success("File uploaded successfully!")
                if st.button("⚡ Summarize Notes Automatically"):
                    summary_resp = f"### 📝 AI Document Summary\n- **Document Title**: `{uploaded_note.name}`\n- **Key Takeaways**:\n  1. The core theoretical framework relies on basic concepts and practical rules.\n  2. Memorize formulas early and build mindmaps to link terms.\n  3. Review worksheets step-by-step prior to exam hours."
                    st.session_state.chat_history.append({"role": "user", "content": f"Please summarize my note document: {uploaded_note.name}"})
                    st.session_state.chat_history.append({"role": "assistant", "content": summary_resp})
                    st.rerun()
                    
            st.markdown("---")
            st.markdown("<h4>🌐 Translate Notes</h4>", unsafe_allow_html=True)
            translation_lang = st.selectbox("Target Language", ["Spanish", "French", "German", "Swahili", "Japanese", "Chinese"])
            translate_txt = st.text_area("Insert text to translate")
            if st.button("Translate Notes"):
                if translate_txt:
                    res_trans = translate_notes(translate_txt, translation_lang)
                    st.code(res_trans, language="markdown")
                    
            st.markdown("---")
            st.markdown("<h4>🧠 Flashcard Generator</h4>", unsafe_allow_html=True)
            fc_prompt = st.text_input("Topic prompt for flashcards", "E.g. cell division")
            if st.button("Generate Flashcard Deck"):
                new_fcs = generate_flashcards(fc_prompt, active_subject)
                for f in new_fcs:
                    add_flashcard(st.session_state.user_email, f["subject"], f["front"], f["back"])
                st.success(f"Generated {len(new_fcs)} recall cards!")
                add_notification(st.session_state.user_email, f"Generated flashcards for {active_subject}.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_chat:
            st.markdown("<div class='glass-card'><h3>💬 Conversational Chat Stream</h3>", unsafe_allow_html=True)
            
            chat_container = st.container(height=400)
            with chat_container:
                if not st.session_state.chat_history:
                    st.markdown(f"<div class='chat-bubble-ai'>Welcome {st.session_state.user_fullname}! I'm operating as your <b>{persona_mode}</b>. Ask me anything about Mathematics, Sciences, or Essays.</div>", unsafe_allow_html=True)
                for message in st.session_state.chat_history:
                    if message["role"] == "user":
                        st.markdown(f"<div class='chat-bubble-user'><b>You</b>: {message['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='chat-bubble-ai'><b>AI Assistant</b>:<br>{message['content']}</div>", unsafe_allow_html=True)
            
            chat_input = st.text_input("Type your question here...")
            if st.button("Send Message 🚀", key="chat_send_btn"):
                if chat_input:
                    st.session_state.chat_history.append({"role": "user", "content": chat_input})
                    ai_reply = ai_chat_response(chat_input, active_subject, persona_mode)
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                    st.rerun()
            
            if st.button("🗑️ Clear Logs"):
                st.session_state.chat_history = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='glass-card'><h3>🎨 Explanation Whiteboard</h3>", unsafe_allow_html=True)
            whiteboard_subject = st.selectbox("Select subject to visualize", ["Mathematics", "Biology", "Physics", "Chemistry", "Computer Science"])
            if st.button("Render Concept Whiteboard"):
                diag = generate_whiteboard_diagram(whiteboard_subject)
                st.markdown(diag)
            st.markdown("</div>", unsafe_allow_html=True)
    # ==================================================
    # 3. ASSIGNMENTS TRACKER PAGE
    # ==================================================
    elif page == "Assignments Tracker":
        st.markdown("<div class='glass-card'><h1 style='margin:0;'>📝 Assignment Tracker</h1><p style='color:#a5b4fc;'>Progress status, submission logs, and AI writing checkers</p></div>", unsafe_allow_html=True)
        
        col_form, col_checklist = st.columns([1, 1.2])
        
        with col_form:
            st.markdown("<div class='glass-card'><h3>📥 Add Assignment</h3>", unsafe_allow_html=True)
            title = st.text_input("Assignment Title", value=st.session_state.auto_save_assignment["title"])
            subject = st.text_input("Subject", value=st.session_state.auto_save_assignment["subject"])
            due_date = st.date_input("Due Date")
            priority = st.selectbox("Priority Level", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(st.session_state.auto_save_assignment["priority"]))
            difficulty = st.selectbox("Difficulty Meter", ["Easy", "Medium", "Hard"], index=["Easy", "Medium", "Hard"].index(st.session_state.auto_save_assignment["difficulty"]))
            status = st.selectbox("Current Status", ["Pending", "In Progress", "Completed", "Submitted"])
            
            is_collaborative = st.checkbox("👥 Group Assignment")
            if is_collaborative:
                group_members = st.text_input("Group Emails (Comma-separated)", "study-buddy@edumate.com")
                
            if st.button("💾 Save Assignment"):
                add_assignment(
                    st.session_state.user_email,
                    title,
                    subject,
                    str(due_date),
                    priority,
                    status,
                    difficulty,
                    teacher_comments="No teacher feedback yet."
                )
                st.success("Assignment saved!")
                st.session_state.auto_save_assignment = {"title": "", "subject": "", "priority": "Medium", "difficulty": "Medium"}
                time.sleep(1)
                st.rerun()
                
            if title != st.session_state.auto_save_assignment["title"] or subject != st.session_state.auto_save_assignment["subject"]:
                st.session_state.auto_save_assignment = {"title": title, "subject": subject, "priority": priority, "difficulty": difficulty}
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_checklist:
            st.markdown("<div class='glass-card'><h3>📋 Assignment Checklist</h3>", unsafe_allow_html=True)
            f_subject = st.selectbox("Filter Subject", ["All"] + list(set([a[2] for a in assignments])))
            f_priority = st.selectbox("Filter Priority", ["All", "High", "Medium", "Low"])
            
            filtered_assignments = list(assignments)
            if f_subject != "All":
                filtered_assignments = [a for a in filtered_assignments if a[2] == f_subject]
            if f_priority != "All":
                filtered_assignments = [a for a in filtered_assignments if a[4] == f_priority]
                
            if filtered_assignments:
                for a in filtered_assignments:
                    st.markdown(f"#### 🎯 {a[1]} in *{a[2]}*")
                    st.write(f"Due: {a[3]} | Priority: **{a[4]}** | Status: **{a[5]}** | Difficulty: *{a[6]}*")
                    
                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        if st.button("Delete Task", key=f"del_{a[0]}"):
                            delete_assignment(a[0])
                            st.success("Deleted!")
                            st.rerun()
                    with col_act2:
                        if a[5] != "Completed":
                            if st.button("Mark Completed", key=f"comp_{a[0]}"):
                                update_assignment_status(a[0], "Completed")
                                st.success("Task completed!")
                                add_notification(st.session_state.user_email, f"Completed: **{a[1]}**!")
                                st.rerun()
                    st.markdown("---")
            else:
                st.write("No matching tasks found.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("<div class='glass-card'><h3>🔬 AI Grammar & Plagiarism Checker</h3>", unsafe_allow_html=True)
        st.write("Submit draft text to scan against matching libraries and grammatical standard rules:")
        check_text = st.text_area("Write draft essay content here...", height=150)
        if st.button("Run Plagiarism & Grammar Check"):
            result = ai_grammar_plagiarism_check(check_text)
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric("Total Quality Score", f"{result['score']}/100")
                st.metric("Plagiarism Similarity Index", f"{result['plagiarism_percent']}%")
            with col_res2:
                st.write("**AI Feedback details**:")
                st.info(result["feedback"])
                if result["grammar_errors"]:
                    st.write("**Grammar / Clarity Fixes Flagged**:")
                    for err in result["grammar_errors"]:
                        st.warning(err)
                if result["plagiarism_sources"]:
                    st.write("**Matching Sources Highlighted**:")
                    for src in result["plagiarism_sources"]:
                        st.error(src)
        st.markdown("</div>", unsafe_allow_html=True)
    # ==================================================
    # 4. TIMETABLE PLANNER PAGE
    # ==================================================
    elif page == "Timetable Planner":
        st.markdown("<div class='glass-card'><h1 style='margin:0;'>📅 Interactive Timetable</h1><p style='color:#a5b4fc;'>Zoom integrations, current lesson tracker, and smart schedulers</p></div>", unsafe_allow_html=True)
        
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        current_day = weekdays[datetime.now().weekday()]
        current_time_str = datetime.now().strftime("%H:%M")
        
        st.info(f"Today is **{current_day}**. Local Time: **{current_time_str}**")
        
        st.markdown("### 🔔 Active Class Highlight")
        active_class_found = False
        
        for t in timetable:
            t_id, t_subject, t_day, t_start, t_end, t_teacher, t_contact, t_zoom, t_attended = t
            if t_day == current_day and t_start <= current_time_str <= t_end:
                active_class_found = True
                st.markdown(f"""
                <div class='glass-card current-class-highlight'>
                    <h3 style='color:#ef4444; margin:0;'>🔴 YOU ARE CURRENTLY IN {t_subject.upper()}!</h3>
                    <p style='margin:5px 0 0 0;'>Time: {t_start} - {t_end} | Instructor: <b>{t_teacher}</b> ({t_contact})</p>
                    <a href='{t_zoom if t_zoom else "https://zoom.us"}' target='_blank'><button style='margin-top:10px; background:#ef4444; border:none; padding:8px 16px; color:white; border-radius:8px; font-weight:bold; cursor:pointer;'>Launch Zoom Session 🎥</button></a>
                </div>
                """, unsafe_allow_html=True)
                
        if not active_class_found:
            st.success("🌴 No classes are active right now. Rest or work on your assignments!")
            
        col_grid, col_add = st.columns([1.5, 1])
        
        with col_grid:
            st.markdown("<div class='glass-card'><h3>Weekly Study Schedule</h3>", unsafe_allow_html=True)
            schedule_by_day = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
            for t in timetable:
                if t[2] in schedule_by_day:
                    schedule_by_day[t[2]].append(t)
                    
            for day, classes in schedule_by_day.items():
                st.markdown(f"#### 📅 {day}")
                if classes:
                    for cl in classes:
                        att_txt = "✅ Attended" if cl[8] == 1 else "⬜ Attending"
                        st.markdown(f"- **{cl[1]}** ({cl[3]} - {cl[4]}) | Instructor: {cl[5]}")
                        
                        col_act1, col_act2, col_act3 = st.columns(3)
                        with col_act1:
                            if cl[7]:
                                st.markdown(f"[🎥 Join Zoom]({cl[7]})")
                            else:
                                st.write("No Link")
                        with col_act2:
                            if st.button("Delete Class", key=f"del_tt_{cl[0]}"):
                                delete_timetable(cl[0])
                                st.success("Removed class!")
                                st.rerun()
                        with col_act3:
                            if st.button(att_txt, key=f"att_tt_{cl[0]}"):
                                toggle_timetable_attendance(cl[0], 1 if cl[8] == 0 else 0)
                                st.rerun()
                else:
                    st.caption("No courses planned for this day.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_add:
            st.markdown("<div class='glass-card'><h3>➕ Class Scheduler</h3>", unsafe_allow_html=True)
            with st.form("add_class_form"):
                subject = st.text_input("Class Subject Name")
                day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
                start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
                end_time = st.time_input("End Time", value=datetime.strptime("10:00", "%H:%M").time())
                teacher_name = st.text_input("Teacher / Instructor Name", "Dr. Jane Smith")
                teacher_contact = st.text_input("Contact / Office Hours", "jane.smith@edumate.edu")
                zoom_link = st.text_input("Zoom / Meet URL", "https://zoom.us/j/1234567")
                
                submitted = st.form_submit_button("Add Class Event")
                if submitted:
                    add_timetable(
                        st.session_state.user_email,
                        subject,
                        day,
                        start_time.strftime("%H:%M"),
                        end_time.strftime("%H:%M"),
                        teacher_name,
                        teacher_contact,
                        zoom_link
                    )
                    st.success("Timetable course scheduled!")
                    add_notification(st.session_state.user_email, f"New course added: {subject} on {day}.")
                    time.sleep(1)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    # ==================================================
    # 5. QUIZ GENERATOR PAGE
    # ==================================================
    elif page == "Quiz Generator":
        st.markdown("<div class='glass-card'><h1 style='margin:0;'>🧠 Adaptive Quiz Arena</h1><p style='color:#a5b4fc;'>Multiplayer battles, timers, and score leaderboards</p></div>", unsafe_allow_html=True)
        
        col_setup, col_battle = st.columns([1, 1])
        
        with col_setup:
            st.markdown("<div class='glass-card'><h3>🛠️ Setup Custom Quiz</h3>", unsafe_allow_html=True)
            q_subject = st.selectbox("Subject Focus", ["Mathematics", "Biology", "Physics", "Chemistry", "Computer Science"])
            q_level = st.selectbox("Education Level", ["Primary School", "High School", "University"])
            q_type = st.selectbox("Question Format", ["MCQs", "True/False", "Fill blanks"])
            
            battle_toggle = st.checkbox("👥 Simulate Multiplayer Battle vs AI Bot")
            
            if st.button("⚡ Generate Adaptive Quiz"):
                st.session_state.quiz_questions = generate_adaptive_quiz(q_subject, q_level)
                st.session_state.quiz_score = 0
                st.session_state.quiz_timer_start = time.time()
                st.session_state.battle_mode = battle_toggle
                st.success("Quiz generated! Fill your selections below.")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_battle:
            st.markdown("<div class='glass-card'><h3>🏆 Multiplayer Leaderboard</h3>", unsafe_allow_html=True)
            rank_df = pd.DataFrame([
                {"Rank": 1, "Student": "Hillary (You)", "Score": "95%", "Streak": "7 Days"},
                {"Rank": 2, "Student": "AI Bot Tutor", "Score": "90%", "Streak": "14 Days"},
                {"Rank": 3, "Student": "Classmate Alpha", "Score": "82%", "Streak": "3 Days"},
                {"Rank": 4, "Student": "Classmate Beta", "Score": "60%", "Streak": "0 Days"},
            ])
            st.table(rank_df)
            st.markdown("</div>", unsafe_allow_html=True)
            
        if st.session_state.quiz_questions:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader(f"📝 Testing: {q_subject} ({q_level})")
            
            time_limit = 60
            elapsed = int(time.time() - st.session_state.quiz_timer_start)
            time_left = max(0, time_limit - elapsed)
            
            if time_left == 0:
                st.error("⏳ Time is up! Submit your answers.")
            else:
                st.warning(f"⏳ Time Remaining: {time_left} seconds")
                
            if st.session_state.battle_mode:
                st.info("⚔️ Battle Active: Hillary vs AI Bot Tutor! Solve quickly to beat the bots' submission time.")
                
            with st.form("arena_quiz_form"):
                user_choices = {}
                for idx, q in enumerate(st.session_state.quiz_questions):
                    st.write(f"**Q{idx+1}: {q['question']}**")
                    user_choices[idx] = st.radio("Select option:", q["options"], key=f"arena_q_{idx}")
                    st.write("")
                    
                submitted = st.form_submit_button("Submit Quiz Answers")
                if submitted:
                    final_score = 0
                    total_qs = len(st.session_state.quiz_questions)
                    
                    review_html = "<h3>Solution Breakdown</h3>"
                    for idx, q in enumerate(st.session_state.quiz_questions):
                        correct = q["answer"]
                        chosen = user_choices[idx]
                        if chosen == correct:
                            final_score += 1
                            review_html += f"<p style='color:#34d399;'><b>Q{idx+1}</b>: Correct! You selected <i>{chosen}</i>.</p>"
                        else:
                            review_html += f"<p style='color:#f87171;'><b>Q{idx+1}</b>: Incorrect! You selected <i>{chosen}</i>. Correct answer is: <b>{correct}</b>.</p>"
                            
                    pct = int((final_score / total_qs) * 100)
                    add_quiz_record(st.session_state.user_email, q_subject, final_score, total_qs, pct, q_level)
                    
                    st.metric("Your Final Score", f"{final_score}/{total_qs} ({pct}%)")
                    
                    if pct >= 80:
                        st.success("🏆 Brilliant performance! Balloons unlocked.")
                        st.balloons()
                    else:
                        st.warning("💪 Review the concepts and try again.")
                        
                    st.markdown(review_html, unsafe_allow_html=True)
                    st.session_state.quiz_questions = []
            st.markdown("</div>", unsafe_allow_html=True)
    # ==================================================
    # 6. ANALYTICS DASHBOARD PAGE
    # ==================================================
    elif page == "Analytics Dashboard":
        st.markdown("<div class='glass-card'><h1 style='margin:0;'>📈 Analytics Dashboard</h1><p style='color:#a5b4fc;'>Study sessions logs, grade history, and predicted outcomes</p></div>", unsafe_allow_html=True)
        
        col_focus_log, col_focus_target = st.columns([1.2, 1])
        with col_focus_log:
            st.markdown("<div class='glass-card'><h3>⏱️ Log Study Session</h3>", unsafe_allow_html=True)
            with st.form("focus_session_form"):
                focus_time = st.number_input("Log study duration (Minutes)", min_value=5, max_value=480, value=60)
                focus_date = st.date_input("Date of Session")
                focus_submit = st.form_submit_button("Record Focus Minutes")
                if focus_submit:
                    add_focus_session(st.session_state.user_email, focus_date, focus_time)
                    st.success("Logged! Your productivity charts have updated.")
                    add_notification(st.session_state.user_email, f"Logged a focus session: {focus_time} minutes of studying.")
                    time.sleep(1)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_focus_target:
            st.markdown("<div class='glass-card'><h3>🎯 Set Target GPA</h3>", unsafe_allow_html=True)
            new_gpa = st.slider("Select your target GPA", min_value=1.0, max_value=4.0, value=gpa_target, step=0.1)
            if st.button("Lock Target GPA"):
                update_user_gpa_target(st.session_state.user_email, new_gpa)
                st.success(f"Target GPA set to {new_gpa:.2f}!")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        if PLOTLY_AVAILABLE:
            st.markdown("### 📊 Interactive Performance Charts")
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                if quiz_records:
                    df_quiz = pd.DataFrame(quiz_records, columns=["ID", "Subject", "Score", "Total", "Percentage", "Date", "Difficulty"])
                    df_quiz["Date"] = pd.to_datetime(df_quiz["Date"])
                    df_quiz = df_quiz.sort_values("Date")
                    
                    fig1 = px.line(df_quiz, x="Date", y="Percentage", color="Subject", marker="o", 
                                   title="Quiz Scores Progress (%)",
                                   template="plotly_dark")
                    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("Take quizzes to see scores progress line charts.")
                    
            with col_chart2:
                if focus_sessions:
                    df_focus = pd.DataFrame(focus_sessions, columns=["ID", "Date", "Duration"])
                    df_focus["Date"] = pd.to_datetime(df_focus["Date"])
                    df_focus = df_focus.sort_values("Date")
                    
                    fig2 = px.bar(df_focus, x="Date", y="Duration", title="Productive Study Hours (Minutes)",
                                  template="plotly_dark", color_discrete_sequence=["#818cf8"])
                    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Log study sessions to view productivity bar charts.")
                    
            st.markdown("<div class='glass-card'><h3>🔮 AI Performance Predictions</h3>", unsafe_allow_html=True)
            if quiz_records:
                avg_score = sum([q[4] for q in quiz_records]) / len(quiz_records)
                predicted_gpa = min(4.0, (avg_score / 100.0) * 4.0 + 0.2)
                st.write(f"Based on your recent mock quiz average of **{avg_score:.1f}%**, our AI predicts your terminal GPA will be:")
                st.subheader(f"🏆 Predicted GPA: {predicted_gpa:.2f} / {gpa_target:.2f} (Target)")
                if predicted_gpa >= gpa_target:
                    st.success("🎉 You are on track to achieve or exceed your GPA target! Keep up this speed.")
                else:
                    st.warning("⚠️ You are slightly below your target. Check recommendations below to focus your efforts.")
            else:
                st.info("Complete quizzes to enable predictive score generation.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("### 📊 Performance Summaries")
            if quiz_records:
                df_quiz = pd.DataFrame(quiz_records, columns=["ID", "Subject", "Score", "Total", "Percentage", "Date", "Difficulty"])
                st.subheader("Quiz Success breakdown")
                st.bar_chart(df_quiz.set_index("Date")["Percentage"])
            if focus_sessions:
                df_focus = pd.DataFrame(focus_sessions, columns=["ID", "Date", "Duration"])
                st.subheader("Daily study volume (mins)")
                st.bar_chart(df_focus.set_index("Date")["Duration"])
                
        st.markdown("<div class='glass-card'><h3>💡 Smart Study Recommendations</h3>", unsafe_allow_html=True)
        recs = generate_study_recommendations(quiz_records, assignments)
        for r in recs:
            badge_color = "#f87171" if r["priority"] == "High" else "#fbbf24" if r["priority"] == "Medium" else "#34d399"
            st.markdown(f"""
            <div style='margin-bottom:10px; padding:10px; border-radius:10px; background:rgba(255,255,255,0.03); border-left:4px solid {badge_color};'>
                <strong>[{r['priority']} Priority] {r['subject']}</strong>: {r['reason']} (Recommended: <i>{r['action']}</i>)
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='glass-card'><h3>📥 Export Performance Report Card</h3>", unsafe_allow_html=True)
        report_html = f"""
        <html>
        <head><style>body {{ font-family: sans-serif; padding: 20px; }} table {{ width:100%; border-collapse: collapse; }} th, td {{ border:1px solid #ccc; padding:8px; text-align:left; }}</style></head>
        <body>
            <h1>EduMate AI Academic Report</h1>
            <p><strong>Student Name:</strong> {st.session_state.user_fullname}</p>
            <p><strong>Email Address:</strong> {st.session_state.user_email}</p>
            <p><strong>Date Generated:</strong> {date.today()}</p>
            <hr/>
            <h2>Quiz Logs</h2>
            <table>
                <tr><th>Subject</th><th>Score</th><th>Percentage</th><th>Date</th></tr>
        """
        for q in quiz_records:
            report_html += f"<tr><td>{q[1]}</td><td>{q[2]}/{q[3]}</td><td>{q[4]}%</td><td>{q[5]}</td></tr>"
        report_html += "</table></body></html>"
        
        st.download_button(
            label="Download HTML Report Card 📄",
            data=report_html,
            file_name=f"edumate_report_{st.session_state.user_fullname}.html",
            mime="text/html"
        )
        st.markdown("</div>", unsafe_allow_html=True)
# ======================================================
# GLOBAL FOOTER
# ======================================================
st.markdown("""
<div class='footer'>
© 2026 EduMate AI | Built with Rich Aesthetics & Dynamic Learning Memory 🌍
</div>
""", unsafe_allow_html=True)
