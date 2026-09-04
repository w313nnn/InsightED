import streamlit as st
import requests
BACKEND_URL = "http://127.0.0.1:8000"


def initialize_session_state():
    defaults = {
        "started": False,
        "question_index": 0,
        "answers": {},
        "score": 0,
        "quiz_submitted": False,
        "previous_score": None,
        "topic": "General Knowledge",
        "difficulty": "Easy",
        "num_questions": 5,
        "total_questions": 5,
        "generated_questions": [],
        "quiz_id": None,
        "first_quiz_score": None,
        "first_quiz_percentage": None,
        "first_quiz_answers": {},
        "first_quiz_questions": [],
        "first_quiz_incorrect_questions": [],
        "requiz_score": None,
        "requiz_percentage": None,
        "requiz_answers": {},
        "requiz_questions": [],
        "requiz_used_indexes": [],
        "requiz_attempt": 0,
        "is_requiz": False,
        "has_unfinished_quiz": False,
        "has_pending_requiz": False,
        "student_page": "home",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_question_widget_key(question_index, is_requiz=False):
    attempt_number = st.session_state.get("requiz_attempt", 0) if is_requiz else 0
    prefix = "requiz" if is_requiz else "firstquiz"
    return f"{prefix}_question_{attempt_number}_{question_index}"


def save_current_answer(question_index, widget_key):
    selected = st.session_state.get(widget_key)
    if selected is not None:
        st.session_state.answers[question_index] = selected


def get_quiz_questions():
    if st.session_state.get("is_requiz", False):
        if not st.session_state.get("requiz_questions"):
            st.session_state.requiz_questions = generate_requiz_questions()
        st.session_state.total_questions = len(st.session_state.requiz_questions)
        return st.session_state.requiz_questions

    generated_questions = st.session_state.get("generated_questions", [])
    if generated_questions:
        st.session_state.total_questions = len(generated_questions)
        return generated_questions

    st.session_state.total_questions = 0
    return []


def get_assigned_quiz():
    response = requests.get(
        f"{BACKEND_URL}/quiz",
        timeout=10,
    )

    response.raise_for_status()

    result = response.json()
    st.session_state.quiz_id = result.get("id")
    questions = result.get("questions", [])

    if not questions:
        raise ValueError("No questions were generated.")

    if len(questions) != st.session_state.num_questions:
        raise ValueError(
            f"Expected {st.session_state.num_questions} questions, "
            f"but received {len(questions)}."
        )

    for index, question in enumerate(questions, start=1):
        if not question.get("question"):
            raise ValueError(
                f"Question {index} is missing question text."
            )

        options = question.get("options", [])
        answer = question.get("answer")

        if len(options) != 4:
            raise ValueError(
                f"Question {index} does not have exactly 4 options."
            )

        if answer not in options:
            raise ValueError(
                f"Question {index} has an answer "
                f"that does not match its options."
            )

    return questions


def submit_student_answers(
    answers,
    attempt_type="initial",
    attempt_questions=None,
):
    response = requests.post(
        f"{BACKEND_URL}/student-answers",
        json={
            "quiz_id": st.session_state.quiz_id,
            "attempt_type": attempt_type,
            "student_answers": answers,
            "attempt_questions": attempt_questions,
        },
        timeout=10,
    )

    response.raise_for_status()



def generate_requiz_questions(exclude_indexes=None):
    # TODO: Replace local Re-Quiz generation with backend/Gonka API
    first_quiz_questions = list(st.session_state.get("first_quiz_questions", []))
    exclude_indexes = set(exclude_indexes or [])
    target_count = min(
        max(5, int(st.session_state.get("num_questions", 5))),
        len(first_quiz_questions),
    )
    weak_entries = list(st.session_state.get("first_quiz_incorrect_questions", []))

    weak_indexes = []
    for item in weak_entries:
        question_index = item.get("index")
        if isinstance(question_index, int) and 0 <= question_index < len(first_quiz_questions):
            weak_indexes.append(question_index)

    selected_indexes = []
    seen = set()

    for index in weak_indexes:
        if index not in exclude_indexes and index not in seen:
            seen.add(index)
            selected_indexes.append(index)
        if len(selected_indexes) >= target_count:
            break

    if len(selected_indexes) < target_count:
        for index in range(len(first_quiz_questions)):
            if index not in exclude_indexes and index not in seen:
                seen.add(index)
                selected_indexes.append(index)
            if len(selected_indexes) >= target_count:
                break

    if len(selected_indexes) < target_count:
        all_indexes = list(range(len(first_quiz_questions)))
        for index in all_indexes:
            if len(selected_indexes) >= target_count:
                break
            if index not in seen:
                seen.add(index)
                selected_indexes.append(index)

    selected_indexes = selected_indexes[:target_count]
    selected_questions = [first_quiz_questions[index] for index in selected_indexes]
    st.session_state.requiz_questions = selected_questions
    return selected_questions


def reset_quiz():
    st.session_state.question_index = 0
    st.session_state.answers = {}
    st.session_state.score = 0
    st.session_state.quiz_submitted = False


def save_and_exit_quiz():
    st.session_state.has_unfinished_quiz = True
    st.session_state.started = False
    st.rerun()


def save_requiz_for_later():
    st.session_state.has_pending_requiz = True
    st.session_state.started = False
    st.rerun()


def continue_quiz():
    st.session_state.started = True
    st.rerun()


def all_questions_answered():
    answers = st.session_state.get("answers", {})
    total_questions = st.session_state.total_questions

    for question_index in range(total_questions):
        if question_index not in answers or answers[question_index] is None:
            return False

    return True


def calculate_score(quiz_questions=None, answers=None):
    if quiz_questions is None:
        quiz_questions = get_quiz_questions()
    if answers is None:
        answers = st.session_state.answers

    total = 0
    for index, question in enumerate(quiz_questions):
        selected = answers.get(index)
        if selected == question["answer"]:
            total += 1
    return total


def save_first_attempt():
    quiz_questions = get_quiz_questions()
    answers = {index: value for index, value in st.session_state.answers.items() if value is not None}
    score = calculate_score(quiz_questions, answers)
    total_questions = len(quiz_questions)

    st.session_state.first_quiz_score = score
    st.session_state.first_quiz_percentage = round((score / total_questions) * 100) if total_questions else 0
    st.session_state.first_quiz_answers = answers.copy()
    st.session_state.first_quiz_questions = [question.copy() for question in quiz_questions]
    st.session_state.first_quiz_incorrect_questions = [
        {
            "index": index,
            "question": question["question"],
            "selected_answer": answers.get(index),
            "correct_answer": question["answer"],
        }
        for index, question in enumerate(quiz_questions)
        if answers.get(index) != question["answer"]
    ]


def save_requiz_attempt():
    quiz_questions = get_quiz_questions()
    answers = {index: value for index, value in st.session_state.answers.items() if value is not None}
    score = calculate_score(quiz_questions, answers)
    total_questions = len(quiz_questions)

    st.session_state.requiz_score = score
    st.session_state.requiz_percentage = round((score / total_questions) * 100) if total_questions else 0
    st.session_state.requiz_answers = answers.copy()
    st.session_state.requiz_questions = [question.copy() for question in quiz_questions]


def start_requiz():
    st.session_state.is_requiz = True
    st.session_state.requiz_attempt = st.session_state.get("requiz_attempt", 0) + 1
    st.session_state.requiz_used_indexes = []
    st.session_state.quiz_submitted = False
    st.session_state.question_index = 0
    st.session_state.answers = {}
    st.session_state.score = 0
    st.session_state.requiz_questions = generate_requiz_questions(exclude_indexes=st.session_state.requiz_used_indexes)
    st.session_state.total_questions = len(st.session_state.requiz_questions)
    st.session_state.started = True
    st.rerun()


def start_another_requiz():
    used_indexes = set(st.session_state.get("requiz_used_indexes", []))
    first_quiz_questions = st.session_state.get("first_quiz_questions", [])
    for question in st.session_state.get("requiz_questions", []):
        for index, source_question in enumerate(first_quiz_questions):
            if source_question == question:
                used_indexes.add(index)
                break

    st.session_state.requiz_used_indexes = sorted(used_indexes)
    st.session_state.is_requiz = True
    st.session_state.requiz_attempt = st.session_state.get("requiz_attempt", 0) + 1
    st.session_state.quiz_submitted = False
    st.session_state.question_index = 0
    st.session_state.answers = {}
    st.session_state.score = 0
    st.session_state.requiz_questions = generate_requiz_questions(exclude_indexes=st.session_state.requiz_used_indexes)
    st.session_state.total_questions = len(st.session_state.requiz_questions)
    st.rerun()


def exit_requiz():
    st.session_state.started = False
    st.session_state.is_requiz = False
    st.session_state.quiz_submitted = False
    st.session_state.has_pending_requiz = True
    st.rerun()


def start_new_quiz():
    for key in [
        "question_index",
        "answers",
        "score",
        "quiz_submitted",
        "previous_score",
        "topic",
        "difficulty",
        "num_questions",
        "total_questions",
        "generated_questions",
        "first_quiz_score",
        "first_quiz_percentage",
        "first_quiz_answers",
        "first_quiz_questions",
        "first_quiz_incorrect_questions",
        "requiz_score",
        "requiz_percentage",
        "requiz_answers",
        "requiz_questions",
        "requiz_used_indexes",
        "requiz_attempt",
        "is_requiz",
        "started",
        "has_unfinished_quiz",
        "has_pending_requiz",
    ]:
        st.session_state.pop(key, None)

    initialize_session_state()
    st.session_state.started = False
    st.session_state.is_requiz = False
    st.session_state.quiz_submitted = False
    st.rerun()


def performance_message(percent):
    if percent >= 80:
        return "Excellent work! Great job!"
    if percent >= 60:
        return "Nice effort! Keep going!"
    return "Keep practicing! You are improving."


def apply_custom_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #F5FBFE;
            --panel: #FFFFFF;
            --panel-soft: #EAF7FC;
            --line: #DDEFF7;
            --text: #123047;
            --muted: #64748B;
            --primary: #7EC8E3;
            --primary-strong: #5BAFD1;
            --primary-soft: rgba(126, 200, 227, 0.14);
            --secondary: #A7DDF2;
            --success: #22C55E;
            --success-soft: rgba(34, 197, 94, 0.10);
            --danger: #EF4444;
            --danger-soft: rgba(239, 68, 68, 0.10);
            --shadow: 0 18px 40px rgba(91, 146, 182, 0.12);
            --radius: 22px;
        }

        html, body {
            background: var(--bg);
            color: var(--text);
            font-family: "Segoe UI", sans-serif;
        }

        header[data-testid="stHeader"] {
            display: none;
        }

        div[data-testid="stToolbar"] {
            display: none;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
            margin-top: 0;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 0.25rem;
            padding-bottom: 2rem;
        }

        .main-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 0 1.2rem 0;
            margin-bottom: 36px;
            border-bottom: 1px solid rgba(123, 160, 188, 0.18);
        }

        .brand-wrap {
            display: flex;
            flex-direction: column;
            gap: 0.12rem;
        }

        .brand-title {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.12;
            letter-spacing: -0.05em;
            color: var(--text);
            margin: 0;
        }

        .brand-subtitle {
            font-size: 0.88rem;
            color: var(--muted);
            margin: 0;
            line-height: 1.5;
        }

        .portal-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--panel);
            color: var(--primary-strong);
            border: 1px solid rgba(99, 164, 197, 0.25);
            border-radius: 999px;
            padding: 0.62rem 1rem;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            box-shadow: 0 10px 24px rgba(94, 152, 189, 0.08);
        }

        .page-shell {
            max-width: 980px;
            margin: 0 auto;
        }

        .dashboard-card,
        .page-card,
        .result-card,
        .review-card,
        .form-card,
        .hero-card,
        .feature-tile {
            background: var(--panel);
            border: 1px solid rgba(125, 173, 201, 0.18);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
        }

        .section-tag {
            display: inline-block;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--primary-strong);
            background: var(--primary-soft);
            border-radius: 999px;
            padding: 0.42rem 0.8rem;
            margin-bottom: 0.8rem;
            line-height: 1.5;
        }

        .hero-title {
            font-size: clamp(2rem, 3vw, 3rem);
            font-weight: 800;
            letter-spacing: -0.05em;
            line-height: 1.18;
            color: var(--text);
            margin: 0 0 0.55rem 0;
        }

        .accent-text {
            color: var(--primary-strong);
        }

        .hero-subtitle {
            font-size: 1rem;
            color: var(--muted);
            margin: 0 0 1.05rem 0;
            line-height: 1.7;
            max-width: 560px;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: 1.25fr 0.75fr;
            gap: 1.35rem;
            align-items: stretch;
            margin-top: 0.65rem;
        }

        .feature-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 1rem;
        }

        .feature-tile {
            padding: 0.8rem 0.9rem;
            text-align: center;
            background: var(--panel);
            border-radius: 18px;
        }

        .feature-tile strong {
            display: block;
            color: var(--text);
            font-size: 0.9rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
            line-height: 1.5;
        }

        .feature-tile span {
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.5;
        }

        .quiz-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .quiz-badge {
            display: inline-flex;
            align-items: center;
            background: var(--primary-soft);
            color: var(--primary-strong);
            border: 1px solid rgba(91, 172, 209, 0.2);
            border-radius: 999px;
            padding: 0.42rem 0.8rem;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            line-height: 1.5;
        }

        .question-count {
            font-size: 0.92rem;
            color: var(--muted);
            font-weight: 700;
            line-height: 1.5;
        }

        .progress-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            color: var(--muted);
            font-size: 0.85rem;
            font-weight: 600;
            line-height: 1.5;
        }

        .manual-progress {
            width: 100%;
            height: 0.75rem;
            border-radius: 999px;
            background: rgba(126, 200, 227, 0.18);
            overflow: hidden;
            margin-bottom: 0.65rem;
        }

        .manual-progress-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(
                90deg,
                var(--primary) 0%,
                var(--primary-strong) 100%
            );
        }

        .stProgress > div > div {
            background: rgba(126, 200, 227, 0.18);
            border-radius: 999px;
            height: 0.72rem;
            overflow: hidden;
        }

        .stProgress > div > div > div {
            background: linear-gradient(
                90deg,
                var(--primary) 0%,
                var(--primary-strong) 100%
            );
            border-radius: 999px;
        }

        .question-card {
            background: var(--panel);
            border: 1px solid rgba(125, 173, 201, 0.18);
            border-radius: 20px;
            padding: 1.4rem 1.2rem;
            box-shadow: var(--shadow);
            margin-top: 0.8rem;
        }

        .question-title {
            font-size: clamp(1.2rem, 2vw, 1.7rem);
            font-weight: 700;
            line-height: 1.6;
            color: var(--text);
            margin: 0;
        }

        .stRadio > div {
            background: transparent;
            border: none;
            padding: 0;
        }

        .stRadio > div[role="radiogroup"] {
            display: grid;
            gap: 0.72rem;
            margin-top: 1.1rem;
        }

        .stRadio label {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            border: 1px solid rgba(125, 173, 201, 0.24);
            border-radius: 16px;
            background: linear-gradient(
                180deg,
                #ffffff 0%,
                #f6fbff 100%
            );
            padding: 0.9rem 1rem;
            margin: 0;
            color: #1f2937 !important;
            line-height: 1.6;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .stRadio label p,
        .stRadio label span,
        .stRadio label div {
            color: #1f2937 !important;
        }

        .stRadio label:hover {
            border-color: rgba(91, 172, 209, 0.6);
            box-shadow: 0 12px 22px rgba(91, 172, 209, 0.08);
        }

        .stRadio label:has(input:checked) {
            background: var(--primary-soft);
            border-color: rgba(91, 172, 209, 0.82);
            box-shadow: 0 12px 24px rgba(91, 172, 209, 0.12);
        }

        .stRadio input {
            accent-color: var(--primary-strong);
            width: 1.15rem;
            height: 1.15rem;
            margin: 0;
        }

        .result-card {
            padding: 1.45rem 1.3rem;
            margin-bottom: 1rem;
        }

        .score-display {
            font-size: clamp(2.6rem, 4vw, 4.1rem);
            font-weight: 800;
            letter-spacing: -0.06em;
            color: var(--primary-strong);
            line-height: 1.08;
            margin: 0.3rem 0 0.5rem 0;
        }

        .score-subtitle {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.8rem;
            line-height: 1.6;
        }

        .badge-success,
        .badge-neutral,
        .badge-warning {
            display: inline-flex;
            align-items: center;
            padding: 0.48rem 0.8rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            line-height: 1.5;
        }

        .badge-success {
            background: var(--success-soft);
            color: var(--success);
        }

        .badge-neutral {
            background: var(--primary-soft);
            color: var(--primary-strong);
        }

        .badge-warning {
            background: rgba(245, 158, 11, 0.12);
            color: #B45309;
        }

        .review-card {
            padding: 1.15rem 1.1rem;
            margin-top: 0.9rem;
        }

        .review-item {
            background: #F9FBFD;
            border: 1px solid rgba(125, 173, 201, 0.18);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
            line-height: 1.6;
        }

        .review-item:last-child {
            margin-bottom: 0;
        }

        .review-item strong {
            color: var(--text);
        }

        .progress-row {
            margin-top: 1rem;
            display: grid;
            gap: 0.7rem;
        }

        .comparison-inline {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text);
            line-height: 1.5;
        }


        /* =========================================================
           ALL BUTTONS
           Light blue background + white text
           ========================================================= */

        .stButton > button {
            border-radius: 12px !important;
            border: 1px solid #4A9FC2 !important;
            font-weight: 800 !important;
            padding: 0.8rem 1.15rem !important;
            min-height: 3rem !important;
            font-size: 1rem !important;
            transition: all 0.2s ease !important;
            box-shadow: none !important;
        }


        /* =========================================================
           PRIMARY BUTTONS
           Generate Quiz / Continue / Next / Submit / Re-Quiz
           ========================================================= */

        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"],
        div[data-testid="stFormSubmitButton"] button {
            background-color: #4A9FC2 !important;
            background: #4A9FC2 !important;
            background-image: none !important;
            color: #FFFFFF !important;
            border-color: #4A9FC2 !important;
        }

        .stButton > button[kind="primary"] *,
        .stButton > button[data-testid="baseButton-primary"] *,
        div[data-testid="stFormSubmitButton"] button * {
            color: #FFFFFF !important;
        }


        /* =========================================================
           SECONDARY BUTTONS
           Previous / Save & Exit / Start New Quiz
           ========================================================= */

        .stButton > button[kind="secondary"],
        .stButton > button[data-testid="baseButton-secondary"] {
            background-color: #4A9FC2 !important;
            background: #4A9FC2 !important;
            background-image: none !important;
            color: #FFFFFF !important;
            border-color: #4A9FC2 !important;
        }

        .stButton > button[kind="secondary"] *,
        .stButton > button[data-testid="baseButton-secondary"] * {
            color: #FFFFFF !important;
        }


        /* =========================================================
           BUTTON HOVER
           ========================================================= */

        .stButton > button:hover,
        .stButton > button[kind="primary"]:hover,
        .stButton > button[kind="secondary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover,
        .stButton > button[data-testid="baseButton-secondary"]:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #3688AD !important;
            background: #3688AD !important;
            background-image: none !important;
            color: #FFFFFF !important;
            border-color: #3688AD !important;
            transform: translateY(-1px);
        }

        .stButton > button:hover *,
        div[data-testid="stFormSubmitButton"] button:hover * {
            color: #FFFFFF !important;
        }


        /* =========================================================
           DISABLED BUTTONS
           Still light blue, but visually disabled
           ========================================================= */

        .stButton > button:disabled,
        div[data-testid="stFormSubmitButton"] button:disabled {
            background-color: #B7DCE9 !important;
            background: #B7DCE9 !important;
            background-image: none !important;
            color: #FFFFFF !important;
            border-color: #B7DCE9 !important;
            opacity: 0.75 !important;
            cursor: not-allowed !important;
            transform: none !important;
        }

        .stButton > button:disabled *,
        div[data-testid="stFormSubmitButton"] button:disabled * {
            color: #FFFFFF !important;
        }


        /* =========================================================
           WARNING / ALERT TEXT
           Makes yellow warning box readable
           ========================================================= */

        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span {
            color: #5B4A00 !important;
        }


        /* =========================================================
           DIFFICULTY DROPDOWN
           Easy / Medium / Hard
           ========================================================= */

        .stSelectbox div[data-baseweb="select"],
        .stSelectbox div[data-baseweb="select"] > div,
        .stSelectbox div[data-baseweb="select"] [role="combobox"] {
            background-color: #D9F1FA !important;
            background: #D9F1FA !important;
            background-image: none !important;
            color: #123047 !important;
            border-color: #A7DDF2 !important;
            box-shadow: none !important;
        }

        .stSelectbox div[data-baseweb="select"] *,
        .stSelectbox div[data-baseweb="select"] [role="combobox"] * {
            color: #123047 !important;
        }


        /* Dropdown menu */

        div[data-baseweb="popover"] {
            background-color: #FFFFFF !important;
            background: #FFFFFF !important;
        }

        div[data-baseweb="popover"] li {
            background-color: #FFFFFF !important;
            color: #123047 !important;
        }

        div[data-baseweb="popover"] li:hover {
            background-color: #D9F1FA !important;
            color: #123047 !important;
        }

        .stTextInput label,
        .stSelectbox label {
            line-height: 1.6;
            margin-bottom: 0.45rem;
            color: var(--text);
            font-weight: 600;
        }

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: rgba(91, 172, 209, 0.8);
            box-shadow: 0 0 0 3px rgba(126, 200, 227, 0.18);
        }

        .stSlider > div > div[data-testid="stKnob"] {
            background: var(--primary-strong);
        }

        .stSlider [data-testid="stTickBar"] {
            background: rgba(126, 200, 227, 0.18);
        }

        .stMetric {
            background: var(--panel-soft);
            border: 1px solid rgba(125, 173, 201, 0.18);
            border-radius: 16px;
            padding: 1rem;
            line-height: 1.5;
        }

        .stMetric [data-testid="stMetricLabel"],
        .stMetric [data-testid="stMetricLabel"] p,
        .stMetric [data-testid="stMetricLabel"] div,
        .stMetric [data-testid="stMetricLabel"] span {
            color: var(--text) !important;
            font-weight: 700 !important;
        }

        .stMetric [data-testid="stMetricValue"] {
            color: var(--text);
            font-weight: 800;
            line-height: 1.4;
        }

        div[data-testid="stVerticalBlock"] > div:has(> div > button) {
            gap: 0.6rem;
        }

        div[data-testid="stForm"] {
            background: var(--panel);
            border: 1px solid rgba(125, 173, 201, 0.18);
            border-radius: 22px;
            padding: 1.2rem;
            box-shadow: var(--shadow);
        }

        div[data-testid="stForm"] > div {
            gap: 0.7rem;
        }

        @media (max-width: 768px) {
            .main-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.8rem;
            }

            .hero-grid,
            .feature-row {
                grid-template-columns: 1fr;
            }

            .quiz-header {
                flex-direction: column;
                align-items: flex-start;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_learning_page():
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-tag">Learn & Grow</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-title">Review Your <span class="accent-text">Weak Areas</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-subtitle">'
        'Review the questions you found difficult and strengthen your understanding before trying the Re-Quiz.'
        '</div>',
        unsafe_allow_html=True,
    )

    incorrect_questions = st.session_state.get(
        "first_quiz_incorrect_questions",
        []
    )

    if not st.session_state.get("first_quiz_questions"):
        st.info(
            "Complete your first quiz to see the areas where you need more practice."
        )

    elif not incorrect_questions:
        st.success(
            "Great job! You answered every question correctly in your first quiz."
        )

        st.subheader("Keep Learning")

        st.write(
            "You demonstrated strong understanding of the current topic. "
            "You can still use the personalized Re-Quiz for extra practice."
        )

    else:
        st.subheader("Topics to Review")

        st.info(
            f"You have {len(incorrect_questions)} question(s) to review."
        )

        for item in incorrect_questions:
            question_index = item.get("index", 0)
            question_text = item.get("question", "")
            selected_answer = item.get("selected_answer")
            correct_answer = item.get("correct_answer")

            st.markdown(
                f"""
                <div class="review-item">
                    <strong>Q{question_index + 1}:</strong> {question_text}<br>
                    <span style="color: #EF4444;">
                        Your answer: {selected_answer or 'No answer selected'}
                    </span><br>
                    <span style="color: #22C55E;">
                        Correct answer: {correct_answer}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        st.subheader("What You Should Do Next")

        st.write(
            "Review the questions above, focus on the concepts you found difficult, "
            "and then take the personalized Re-Quiz to check your improvement."
        )

    st.write("")

    if st.button(
        "← Back to Learning Portal",
        use_container_width=True,
        type="secondary",
    ):
        st.session_state.student_page = "home"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_progress_page():
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-tag">Track Progress</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-title">Your <span class="accent-text">Learning Progress</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-subtitle">'
        'See how your performance changes from your first quiz to your personalized Re-Quiz.'
        '</div>',
        unsafe_allow_html=True,
    )

    first_percentage = st.session_state.get("first_quiz_percentage")
    requiz_percentage = st.session_state.get("requiz_percentage")

    if first_percentage is None:
        st.info(
            "You have not completed your first quiz yet. "
            "Complete the assigned quiz to start tracking your progress."
        )

    else:
        st.subheader("Performance")

        if requiz_percentage is None:
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "First Quiz",
                    f"{first_percentage}%"
                )

            with col2:
                st.metric(
                    "Re-Quiz",
                    "Not completed"
                )

            st.info(
                "Complete the personalized Re-Quiz to see your learning improvement."
            )

        else:
            improvement = requiz_percentage - first_percentage

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "First Quiz",
                    f"{first_percentage}%"
                )

            with col2:
                st.metric(
                    "Re-Quiz",
                    f"{requiz_percentage}%"
                )

            with col3:
                st.metric(
                    "Improvement",
                    f"{improvement:+d}%"
                )

            if improvement > 0:
                st.success(
                    f"Great progress! Your score improved by {improvement}%."
                )
            elif improvement == 0:
                st.info(
                    "Your score stayed the same. Keep practicing."
                )
            else:
                st.warning(
                    f"Your score decreased by {abs(improvement)}%. "
                    "Review your weak areas and try again."
                )

        st.divider()

        st.subheader("Progress Summary")

        if first_percentage >= 80:
            st.write(
                "You demonstrated strong understanding in your first quiz."
            )
        elif first_percentage >= 60:
            st.write(
                "You have a developing understanding of the topic."
            )
        else:
            st.write(
                "You have several areas that need more practice."
            )

    st.write("")

    if st.button(
        "← Back to Learning Portal",
        use_container_width=True,
        type="secondary",
    ):
        st.session_state.student_page = "home"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_history_page():
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-tag">Quiz History</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-title">Your <span class="accent-text">Quiz History</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-subtitle">'
        'Review quizzes you have completed, including your answers, '
        'scores, and previous attempts.'
        '</div>',
        unsafe_allow_html=True,
    )

    try:
        with st.spinner("Loading your quiz history..."):
            quiz_response = requests.get(
                f"{BACKEND_URL}/quizzes",
                timeout=10,
            )

            quiz_response.raise_for_status()

            quiz_data = quiz_response.json()
            quizzes = quiz_data.get("quizzes", [])

        completed_quizzes = []

        for quiz in quizzes:
            quiz_id = quiz.get("id")

            if quiz_id is None:
                continue

            history_response = requests.get(
                f"{BACKEND_URL}/quiz/{quiz_id}/history",
                timeout=10,
            )

            history_response.raise_for_status()

            history_data = history_response.json()

            attempts = history_data.get("attempts", [])

            # Only show quizzes that the student has completed.
            if attempts:
                completed_quizzes.append(history_data)

        if not completed_quizzes:
            st.info(
                "You have not completed any quizzes yet. "
                "Complete a quiz to see it here."
            )

        else:
            st.success(
                f"✅ {len(completed_quizzes)} completed quiz(es) found."
            )

            for history in completed_quizzes:
                quiz = history.get("quiz", {})
                attempts = history.get("attempts", [])

                quiz_id = quiz.get("id")
                subject = quiz.get("subject", "Unknown")
                topic = quiz.get("topic", "Unknown")
                student_level = quiz.get(
                    "student_level",
                    "Unknown",
                )
                language = quiz.get(
                    "language",
                    "Unknown",
                )
                difficulty = quiz.get(
                    "difficulty",
                    "Unknown",
                )
                questions = quiz.get("questions", [])

                st.divider()

                st.subheader(
                    f"Quiz #{quiz_id} — {topic}"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Subject",
                        subject,
                    )

                with col2:
                    st.metric(
                        "Level",
                        student_level,
                    )

                with col3:
                    st.metric(
                        "Difficulty",
                        difficulty,
                    )

                with col4:
                    st.metric(
                        "Questions",
                        len(questions),
                    )

                st.caption(
                    f"Language: {language}"
                )

                st.markdown("### Your Attempts")

                # Sort oldest to newest so initial attempt
                # appears before re-quiz.
                sorted_attempts = sorted(
                    attempts,
                    key=lambda attempt: attempt.get(
                        "submitted_at",
                        "",
                    ),
                )

                for attempt_number, attempt in enumerate(
                    sorted_attempts,
                    start=1,
                ):
                    score = attempt.get(
                        "score",
                        0,
                    )

                    total_questions = attempt.get(
                        "total_questions",
                        len(questions),
                    )

                    if total_questions > 0:
                        percentage = round(
                            (score / total_questions) * 100
                        )
                    else:
                        percentage = 0

                    attempt_type = attempt.get(
                        "attempt_type",
                        "Unknown",
                    )

                    submitted_at = attempt.get(
                        "submitted_at",
                        "Unknown",
                    )

                    student_answers = attempt.get(
                        "student_answers",
                        [],
                    )

                    attempt_label = (
                        "First Attempt"
                        if attempt_type == "initial"
                        else "Re-Quiz"
                    )

                    with st.expander(
                        f"{attempt_label} — "
                        f"{score}/{total_questions} "
                        f"({percentage}%)"
                    ):
                        st.write(
                            f"**Attempt:** {attempt_label}"
                        )

                        st.write(
                            f"**Score:** "
                            f"{score}/{total_questions}"
                        )

                        st.write(
                            f"**Percentage:** "
                            f"{percentage}%"
                        )

                        st.write(
                            f"**Completed:** "
                            f"{submitted_at}"
                        )

                        st.markdown(
                            "#### Answer Review"
                        )

                        attempt_questions = (
                            attempt.get("attempt_questions")
                            or questions
                        )

                        for index, question in enumerate(
                            attempt_questions
                        ):
                            student_answer = (
                                student_answers[index]
                                if index < len(student_answers)
                                else None
                            )

                            correct_answer = question.get(
                                "answer",
                                "",
                            )

                            is_correct = (
                                student_answer
                                == correct_answer
                            )

                            if is_correct:
                                answer_color = "#22C55E"
                            else:
                                answer_color = "#EF4444"

                            st.markdown(
                                f"""
                                <div class="review-item">
                                    <strong>
                                        Q{index + 1}:
                                    </strong>
                                    {question.get("question", "")}
                                    <br>
                                    <span style="color: {answer_color};">
                                        Your answer:
                                        {student_answer or "No answer selected"}
                                    </span>
                                    <br>
                                    <span style="color: #6B7280;">
                                        Correct answer:
                                        {correct_answer}
                                    </span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                analysis = history.get(
                    "analysis"
                )

                if analysis:
                    analysis_result = analysis.get(
                        "result",
                        {}
                    )

                    st.markdown(
                        "### AI Learning Feedback"
                    )

                    st.write(
                        "**Common Misconception:** "
                        f"{analysis_result.get('misconception', 'Not available')}"
                    )

                    st.write(
                        "**Root Cause:** "
                        f"{analysis_result.get('reason', 'Not available')}"
                    )

                    st.write(
                        "**Recommended Teaching Action:** "
                        f"{analysis_result.get('intervention', 'Not available')}"
                    )

                    st.write(
                        "**Teaching Explanation:** "
                        f"{analysis_result.get('teaching_explanation', 'Not available')}"
                    )

                else:
                    st.info(
                        "No AI learning analysis is available "
                        "for this quiz yet."
                    )

    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Cannot connect to the backend."
        )

    except requests.exceptions.RequestException as exc:
        st.error(
            f"❌ Unable to load quiz history: {exc}"
        )

    st.write("")

    if st.button(
        "← Back to Learning Portal",
        use_container_width=True,
        type="secondary",
    ):
        st.session_state.student_page = "home"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_start_screen():
    if st.session_state.get("student_page") == "progress":
        render_progress_page()
        return

    if st.session_state.get("student_page") == "learning":
        render_learning_page()
        return

    if st.session_state.get("student_page") == "history":
        render_history_page()
        return

    st.markdown('<div class="page-shell">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-tag">Learning Portal</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-title">Your <span class="accent-text">Assigned Quiz</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-subtitle">'
        'Complete the quiz assigned by your teacher and discover the areas '
        'where you can improve.'
        '</div>',
        unsafe_allow_html=True,
    )

    try:
        with st.spinner("Loading your assigned quiz..."):
            assigned_questions = get_assigned_quiz()

        st.session_state.generated_questions = assigned_questions
        st.session_state.total_questions = len(assigned_questions)

        st.success(
            f"✅ Your teacher has assigned a {len(assigned_questions)}-question quiz."
        )

        if st.session_state.get("has_pending_requiz", False):
            st.info(
                "A personalized Re-Quiz is available based on your previous answers."
            )

            if st.button(
                "Start Personalized Re-Quiz",
                use_container_width=True,
                type="primary",
            ):
                st.session_state.has_pending_requiz = False
                start_requiz()

        else:
            if st.button(
                "Start Assigned Quiz",
                use_container_width=True,
                type="primary",
            ):
                reset_quiz()
                st.session_state.started = True
                st.session_state.is_requiz = False
                st.rerun()

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the backend.")
        st.info(
            "Please make sure FastAPI is running using:\n\n"
            "`uvicorn Backend.main:app --reload`"
        )

    except requests.exceptions.RequestException as exc:
        st.error(f"❌ Unable to load the assigned quiz: {exc}")

    except ValueError as exc:
        st.warning(f"⚠️ {exc}")

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("Your Learning")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(
            "Teacher Assigned",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.student_page = "home"
            st.session_state.has_pending_requiz = False
            reset_quiz()
            st.session_state.is_requiz = False
            st.session_state.started = True
            st.rerun()

        st.caption("Take the quiz prepared for your class.")

    with col2:
        if st.button(
            "Track Progress",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.student_page = "progress"
            st.rerun()

        st.caption("Monitor your learning improvement.")

    with col3:
        if st.button(
            "Learn & Grow",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.student_page = "learning"
            st.rerun()

        st.caption("Review areas that need more practice.")

    with col4:
        if st.button(
            "Quiz History",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.student_page = "history"
            st.rerun()

        st.caption("Review your completed quizzes and progress.")

    st.markdown('</div>', unsafe_allow_html=True)


def render_quiz_screen():
    quiz_questions = get_quiz_questions()
    total_questions = len(quiz_questions)

    if total_questions == 0:
        st.warning("No questions available for this quiz yet.")
        return

    if st.session_state.question_index >= total_questions:
        st.session_state.question_index = max(0, total_questions - 1)

    current_question = quiz_questions[st.session_state.question_index]
    st.session_state.total_questions = total_questions

    progress = (st.session_state.question_index + 1) / total_questions
    progress_pct = int(round(progress * 100))

    st.markdown('<div class="page-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="quiz-header">
            <div class="quiz-badge">{st.session_state.topic} · {st.session_state.difficulty}</div>
            <div class="question-count">Question {st.session_state.question_index + 1} of {total_questions}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("is_requiz", False):
        st.markdown('<div class="section-tag">Personalized Re-Quiz</div>', unsafe_allow_html=True)
        st.caption("Personalized practice based on your previous answers.")

    st.markdown(
        f'''<div class="progress-label"><span>Progress</span><span>{progress_pct}% Complete</span></div>
        <div class="manual-progress"><div class="manual-progress-fill" style="width: {progress_pct}%"></div></div>''',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="question-title">' + current_question["question"] + '</div>', unsafe_allow_html=True)

    selected_value = st.session_state.answers.get(st.session_state.question_index)
    default_index = (
        current_question["options"].index(selected_value)
        if selected_value in current_question["options"]
        else None
    )

    widget_key = get_question_widget_key(
        st.session_state.question_index,
        is_requiz=st.session_state.get("is_requiz", False),
    )

    if current_question["options"]:
        selected_option = st.radio(
            "Choose one answer:",
            current_question["options"],
            index=default_index if default_index is not None else None,
            key=widget_key,
            label_visibility="collapsed",
            on_change=save_current_answer,
            args=(st.session_state.question_index, widget_key),
        )
    else:
        selected_option = st.text_input("Your answer", key=widget_key).strip()

    if selected_option:
        st.session_state.answers[st.session_state.question_index] = selected_option
    elif st.session_state.answers.get(st.session_state.question_index) is not None:
        st.session_state.answers.pop(st.session_state.question_index, None)

    answered_count = sum(
        1 for value in st.session_state.answers.values()
        if value is not None
    )
    st.caption(f"Answered: {answered_count}/{total_questions}")

    question_index = st.session_state.question_index

    # First question: Next only
    if question_index == 0:
        if st.button(
            "Next",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.question_index not in st.session_state.answers,
        ):
            st.session_state.question_index += 1
            st.rerun()

    # Last question: Previous + Submit
    elif question_index == total_questions - 1:
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Previous",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state.question_index -= 1
                st.rerun()

        with col2:
            submit_disabled = not all_questions_answered()

            if st.button(
                "Submit Quiz",
                disabled=submit_disabled,
                use_container_width=True,
                type="primary",
            ):
                if st.session_state.get("is_requiz", False):
                    save_requiz_attempt()
                    try:
                        submit_student_answers(
                            [
                                st.session_state.requiz_answers[index]
                                for index in range(
                                    len(st.session_state.requiz_questions)
                                )
                            ],
                            attempt_type="requiz",
                            attempt_questions=st.session_state.requiz_questions,
                        )
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Unable to submit your re-quiz answers: {exc}")
                        return
                else:
                    save_first_attempt()
                    try:
                        submit_student_answers(
                            [
                                st.session_state.first_quiz_answers[index]
                                for index in range(
                                    len(st.session_state.first_quiz_questions)
                                )
                            ],
                            attempt_type="initial",
                            attempt_questions=st.session_state.first_quiz_questions,
                        )
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Unable to submit your answers: {exc}")
                        return

                st.session_state.quiz_submitted = True
                st.rerun()

    # Middle questions: Previous + Next
    else:
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Previous",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state.question_index -= 1
                st.rerun()

        with col2:
            if st.button(
                "Next",
                use_container_width=True,
                type="primary",
                disabled=st.session_state.question_index not in st.session_state.answers,
            ):
                st.session_state.question_index += 1
                st.rerun()

    # Save & Exit is available on every question
    st.write("")

    if st.button(
        "Save & Exit Quiz",
        use_container_width=True,
        type="secondary",
    ):
        save_and_exit_quiz()

    st.markdown('</div>', unsafe_allow_html=True)


def render_result_screen():
    quiz_questions = get_quiz_questions()
    score = st.session_state.get("first_quiz_score")
    if score is None:
        save_first_attempt()
        score = st.session_state.first_quiz_score

    total_questions = len(quiz_questions)
    percentage = st.session_state.get("first_quiz_percentage", 0)
    correct_answers = score
    incorrect_answers = total_questions - score

    st.session_state.score = score

    st.markdown('<div class="page-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-tag">Your Quiz Result</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="score-display">{percentage}%</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="score-subtitle">{score} / {total_questions} correct</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="badge-success">' + performance_message(percentage) + '</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Correct Answers", correct_answers)
    with col2:
        st.metric("Incorrect Answers", incorrect_answers)

    st.write("")
    st.markdown('<div style="font-size: 1.1rem; font-weight: 700; color: #1F2937; margin-bottom: 0.4rem;">Areas to Improve</div>', unsafe_allow_html=True)
    if st.session_state.first_quiz_incorrect_questions:
        st.info(
            f"Weak areas identified: {len(st.session_state.first_quiz_incorrect_questions)} question(s) to review in your Re-Quiz. Your Re-Quiz will focus on the areas where you need more practice."
        )
    else:
        st.info("Excellent! You answered every question correctly. Your Re-Quiz will focus on extra practice.")

    st.subheader("Review Answers")

    for index, question in enumerate(quiz_questions):
        chosen_answer = st.session_state.first_quiz_answers.get(index)
        is_correct = chosen_answer == question["answer"]
        answer_color = "#22C55E" if is_correct else "#EF4444"

        st.markdown(
            f"""
            <div class="review-item">
                <strong>Q{index + 1}:</strong> {question['question']}<br>
                <span style='color: {answer_color};'>Your answer: {chosen_answer or 'No answer selected'}</span><br>
                <span style='color: #6B7280;'>Correct answer: {question['answer']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    col_requiz, col_save = st.columns(2)

    with col_save:
        if st.button(
            "Save Re-Quiz for Later",
            use_container_width=True,
            type="secondary",
        ):
            save_requiz_for_later()

    with col_requiz:
        if st.button(
            "Start Personalized Re-Quiz",
            use_container_width=True,
            type="primary",
        ):
            start_requiz()

    st.markdown('</div>', unsafe_allow_html=True)


def render_requiz_result_screen():
    save_requiz_attempt()
    first_score = st.session_state.get("first_quiz_percentage", 0)
    requiz_score = st.session_state.get("requiz_percentage", 0)
    improvement = requiz_score - first_score

    st.markdown('<div class="page-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-tag">Your Learning Progress</div>', unsafe_allow_html=True)

    col_first, arrow, col_requiz = st.columns([1.2, 0.35, 1.2])
    with col_first:
        st.markdown(f'<div class="comparison-inline">First Quiz</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-score" style="font-size: clamp(2.2rem, 4vw, 3rem);">{first_score}%</div>', unsafe_allow_html=True)
    with arrow:
        st.markdown('<div class="arrow" style="text-align: center;">→</div>', unsafe_allow_html=True)
    with col_requiz:
        st.markdown(f'<div class="comparison-inline">Re-Quiz</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-score" style="font-size: clamp(2.2rem, 4vw, 3rem);">{requiz_score}%</div>', unsafe_allow_html=True)

    if improvement > 0:
        improvement_text = f"+{improvement}% Improvement"
        badge_class = "badge-success"
        message = f"Great progress! Your score improved by {improvement}%."
    elif improvement == 0:
        improvement_text = f"{improvement}% Improvement"
        badge_class = "badge-neutral"
        message = "Your score stayed the same. Keep practicing."
    else:
        improvement_text = f"{improvement}% Improvement"
        badge_class = "badge-warning"
        message = "Keep practicing. Review your weak areas and try again."

    st.markdown(f'<div style="margin-top: 1rem; display: flex; justify-content: center;"><div class="{badge_class}">{improvement_text}</div></div>', unsafe_allow_html=True)
    st.write("")
    if improvement > 0:
        st.success(message)
    elif improvement == 0:
        st.info(message)
    else:
        st.warning(message)

    st.write("")
    st.write("")

    col_try, col_new, col_exit = st.columns(3)

    with col_try:
        if st.button(
            "Try Another Re-Quiz",
            use_container_width=True,
            type="primary",
        ):
            start_another_requiz()

    with col_new:
        if st.button(
            "Start New Quiz",
            use_container_width=True,
            type="secondary",
        ):
            start_new_quiz()

    with col_exit:
        if st.button(
            "Exit",
            use_container_width=True,
            type="secondary",
        ):
            exit_requiz()

    st.markdown('</div>', unsafe_allow_html=True)


def render_top_header():
    st.markdown(
        """
        <div class="main-header">
            <div class="brand-wrap">
                <div class="brand-title">LearnAI</div>
                <div class="brand-subtitle">Personalized Learning Assistant</div>
            </div>
            <div class="portal-badge">Student Portal</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="Student Quiz", page_icon="🎓", layout="wide")
    initialize_session_state()
    apply_custom_css()
    render_top_header()

    if not st.session_state.started:
        render_start_screen()
        return

    if st.session_state.get("is_requiz", False) and st.session_state.quiz_submitted:
        render_requiz_result_screen()
        return

    if st.session_state.quiz_submitted:
        render_result_screen()
        return

    render_quiz_screen()


if __name__ == "__main__":
    main()
