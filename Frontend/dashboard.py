import streamlit as st
import requests


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = "http://localhost:8000"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Education AI",
    page_icon="🎓",
    layout="wide"
)


# ============================================================
# TEACHER NAVIGATION
# ============================================================

st.sidebar.title("🎓 Education AI")

page = st.sidebar.radio(
    "Teacher Menu",
    [
        "Overview",
        "Create Quiz",
        "My Quizzes",
        "Class Results",
        "AI Diagnosis"
    ]
)


# ============================================================
# SESSION STATE
# ============================================================

if "quiz_created" not in st.session_state:
    st.session_state.quiz_created = False

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "selected_quiz_id" not in st.session_state:
    st.session_state.selected_quiz_id = None


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🎓 Education AI")

st.caption(
    "AI-powered classroom misconception diagnosis"
)

st.divider()


# ============================================================
# MY QUIZZES PAGE
# ============================================================

if page == "My Quizzes":

    st.header("📚 My Quizzes")

    st.write(
        "View previous quizzes, student results, "
        "and AI diagnosis history."
    )

    try:

        # ------------------------------------------------
        # Get all quizzes
        # ------------------------------------------------

        response = requests.get(
            f"{BACKEND_URL}/quizzes",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        quizzes = data.get(
            "quizzes",
            []
        )

        if not quizzes:

            st.info(
                "No quizzes have been created yet."
            )

        else:

            st.success(
                f"✅ {len(quizzes)} quiz(es) found."
            )

            for quiz in quizzes:

                quiz_id = quiz.get("id")

                st.divider()

                st.subheader(
                    f"Quiz #{quiz_id} — "
                    f"{quiz.get('topic')}"
                )

                # ------------------------------------------------
                # QUIZ INFORMATION
                # ------------------------------------------------

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.write(
                        f"**Subject:** "
                        f"{quiz.get('subject')}"
                    )

                    st.write(
                        f"**Topic:** "
                        f"{quiz.get('topic')}"
                    )

                with col2:

                    st.write(
                        f"**Student Level:** "
                        f"{quiz.get('student_level')}"
                    )

                    st.write(
                        f"**Language:** "
                        f"{quiz.get('language')}"
                    )

                with col3:

                    st.write(
                        f"**Difficulty:** "
                        f"{quiz.get('difficulty')}"
                    )

                    st.write(
                        f"**Questions:** "
                        f"{quiz.get('num_questions')}"
                    )

                st.caption(
                    f"Created: {quiz.get('created_at')}"
                )

                # ------------------------------------------------
                # GET COMPLETE HISTORY FOR THIS QUIZ
                # ------------------------------------------------

                try:

                    history_response = requests.get(
                        f"{BACKEND_URL}/quiz/"
                        f"{quiz_id}/history",
                        timeout=10
                    )

                    history_response.raise_for_status()

                    history_data = (
                        history_response.json()
                    )

                except requests.exceptions.RequestException:

                    history_data = {
                        "attempts": [],
                        "analysis": None
                    }

                    st.warning(
                        "Unable to retrieve complete history "
                        f"for Quiz #{quiz_id}."
                    )

                # ------------------------------------------------
                # QUIZ QUESTIONS
                # ------------------------------------------------

                with st.expander(
                    "📝 View Quiz Questions"
                ):

                    questions = quiz.get(
                        "questions",
                        []
                    )

                    for index, question in enumerate(
                        questions,
                        start=1
                    ):

                        st.write(
                            f"**Question {index}:** "
                            f"{question.get('question')}"
                        )

                        options = question.get(
                            "options",
                            []
                        )

                        for option in options:

                            st.write(
                                f"- {option}"
                            )

                        st.write(
                            f"**Correct Answer:** "
                            f"{question.get('answer')}"
                        )

                # ------------------------------------------------
                # STUDENT RESULTS
                # ------------------------------------------------

                attempts = history_data.get(
                    "attempts",
                    []
                )

                with st.expander(
                    "👥 Student Results"
                ):

                    if not attempts:

                        st.info(
                            "No student attempts have been "
                            "recorded for this quiz yet."
                        )

                    else:

                        # Group attempts by student_id.
                        students = {}

                        for attempt in attempts:

                            student_id = attempt.get(
                                "student_id"
                            ) or "student_1"

                            if student_id not in students:
                                students[student_id] = []

                            students[student_id].append(
                                attempt
                            )

                        st.success(
                            f"✅ {len(attempts)} "
                            f"attempt(s) from "
                            f"{len(students)} student(s) found."
                        )

                        # Display each student only once.
                        for student_index, (
                            student_id,
                            student_attempts
                        ) in enumerate(
                            students.items(),
                            start=1
                        ):

                            st.divider()

                            st.write(
                                f"**Student {student_index}**"
                            )

                            # ------------------------------------------------
                            # SEPARATE ATTEMPTS
                            # ------------------------------------------------

                            initial_attempts = [
                                attempt
                                for attempt in student_attempts
                                if attempt.get("attempt_type") == "initial"
                            ]

                            requiz_attempts = [
                                attempt
                                for attempt in student_attempts
                                if attempt.get("attempt_type") == "requiz"
                            ]

                            # ------------------------------------------------
                            # FIRST ATTEMPT
                            # ------------------------------------------------

                            if initial_attempts:

                                first_attempt = min(
                                    initial_attempts,
                                    key=lambda attempt: attempt.get(
                                        "attempt_id",
                                        0
                                    )
                                )

                                score = first_attempt.get(
                                    "score",
                                    0
                                )

                                total_questions = first_attempt.get(
                                    "total_questions",
                                    0
                                )

                                if total_questions > 0:

                                    percentage = round(
                                        (score / total_questions) * 100
                                    )

                                else:

                                    percentage = 0

                                st.write(
                                    "**First Attempt**"
                                )

                                col1, col2, col3 = st.columns(3)

                                with col1:

                                    st.metric(
                                        "Score",
                                        f"{score} / "
                                        f"{total_questions}"
                                    )

                                with col2:

                                    st.metric(
                                        "Percentage",
                                        f"{percentage}%"
                                    )

                                with col3:

                                    st.metric(
                                        "Attempt Type",
                                        "Initial"
                                    )

                                st.caption(
                                    f"Submitted: "
                                    f"{first_attempt.get('submitted_at', '-')}"
                                )

                                with st.expander(
                                    "View First Attempt Answers"
                                ):

                                    answers = first_attempt.get(
                                        "student_answers",
                                        []
                                    )

                                    for question_index, answer in enumerate(
                                        answers,
                                        start=1
                                    ):

                                        st.write(
                                            f"Q{question_index}: "
                                            f"{answer}"
                                        )

                            else:

                                st.info(
                                    "No first attempt recorded."
                                )

                            # ------------------------------------------------
                            # RE-QUIZ ATTEMPTS
                            # ------------------------------------------------

                            if requiz_attempts:

                                st.write(
                                    "**Re-Quiz Attempts**"
                                )

                                requiz_attempts = sorted(
                                    requiz_attempts,
                                    key=lambda attempt: attempt.get(
                                        "attempt_id",
                                        0
                                    )
                                )

                                for requiz_index, attempt in enumerate(
                                    requiz_attempts,
                                    start=1
                                ):

                                    score = attempt.get(
                                        "score",
                                        0
                                    )

                                    total_questions = attempt.get(
                                        "total_questions",
                                        0
                                    )

                                    if total_questions > 0:

                                        percentage = round(
                                            (score / total_questions) * 100
                                        )

                                    else:

                                        percentage = 0

                                    with st.expander(
                                        f"Re-Quiz {requiz_index} — "
                                        f"{score}/{total_questions} "
                                        f"({percentage}%)"
                                    ):

                                        col1, col2, col3 = st.columns(3)

                                        with col1:

                                            st.metric(
                                                "Score",
                                                f"{score} / "
                                                f"{total_questions}"
                                            )

                                        with col2:

                                            st.metric(
                                                "Percentage",
                                                f"{percentage}%"
                                            )

                                        with col3:

                                            st.metric(
                                                "Attempt ID",
                                                attempt.get(
                                                    "attempt_id",
                                                    "-"
                                                )
                                            )

                                        st.caption(
                                            f"Submitted: "
                                            f"{attempt.get('submitted_at', '-')}"
                                        )

                                        answers = attempt.get(
                                            "student_answers",
                                            []
                                        )

                                        for question_index, answer in enumerate(
                                            answers,
                                            start=1
                                        ):

                                            st.write(
                                                f"Q{question_index}: "
                                                f"{answer}"
                                            )

                            else:

                                st.caption(
                                    "No re-quiz attempts recorded."
                                )

                # ------------------------------------------------
                # AI DIAGNOSIS HISTORY
                # ------------------------------------------------

                analysis = history_data.get(
                    "analysis"
                )

                with st.expander(
                    "🤖 AI Diagnosis"
                ):

                    if not analysis:

                        st.info(
                            "No AI diagnosis has been generated "
                            "for this quiz yet."
                        )

                    else:

                        analysis_result = analysis.get(
                            "result",
                            {}
                        )

                        misconception = analysis_result.get(
                            "misconception",
                            "No misconception recorded."
                        )

                        affected_students = analysis_result.get(
                            "affected_students",
                            0
                        )

                        total_students = analysis_result.get(
                            "total_students",
                            0
                        )

                        percentage = analysis_result.get(
                            "percentage",
                            0
                        )

                        reason = analysis_result.get(
                            "reason",
                            "No root cause recorded."
                        )

                        intervention = analysis_result.get(
                            "intervention",
                            "No teaching recommendation recorded."
                        )

                        teaching_explanation = analysis_result.get(
                            "teaching_explanation",
                            "No teaching explanation recorded."
                        )

                        st.warning(
                            "⚠️ Common misconception:\n\n"
                            f"{misconception}"
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            st.metric(
                                "Affected Students",
                                f"{affected_students} / "
                                f"{total_students}"
                            )

                            st.metric(
                                "Questions Linked to Misconception",
                                f"{percentage}%"
                            )

                        with col2:

                            st.write(
                                "**Possible Root Cause**"
                            )

                            st.write(
                                reason
                            )

                        st.divider()

                        st.write(
                            "**Recommended Teaching Action**"
                        )

                        st.info(
                            intervention
                        )

                        st.write(
                            "**Teaching Explanation**"
                        )

                        st.info(
                            teaching_explanation
                        )

                        st.caption(
                            f"Analysis created: "
                            f"{analysis.get('created_at', '-')}"
                        )

    except requests.exceptions.ConnectionError:

        st.error(
            "❌ Cannot connect to the backend."
        )

    except requests.exceptions.RequestException as exc:

        st.error(
            f"❌ Failed to load quiz history: {exc}"
        )

    st.stop()


# ============================================================
# OVERVIEW PAGE
# ============================================================

if page == "Overview":

    st.header("📊 Overview")

    st.write(
        "Welcome to Education AI. "
        "Monitor overall class understanding, "
        "identify students who need support, "
        "and track learning progress."
    )

    try:

        # ------------------------------------------------
        # GET ALL QUIZZES
        # ------------------------------------------------

        quiz_response = requests.get(
            f"{BACKEND_URL}/quizzes",
            timeout=10
        )

        quiz_response.raise_for_status()

        quiz_data = quiz_response.json()

        quizzes = quiz_data.get(
            "quizzes",
            []
        )

        if not quizzes:

            st.info(
                "No quizzes have been created yet."
            )

            st.stop()

        # ------------------------------------------------
        # SELECT QUIZ
        # ------------------------------------------------

        st.subheader("Select Quiz")

        quiz_options = {
            f"Quiz #{quiz.get('id')} — "
            f"{quiz.get('topic', 'Untitled Topic')}": quiz.get("id")
            for quiz in quizzes
        }

        quiz_ids = [
            quiz.get("id")
            for quiz in quizzes
        ]

        # Keep the previously selected quiz if it
        # still exists. Otherwise select the first quiz.
        if (
            "overview_quiz_id" not in st.session_state
            or st.session_state.overview_quiz_id not in quiz_ids
        ):

            st.session_state.overview_quiz_id = quiz_ids[0]

        selected_quiz_label = st.selectbox(
            "Choose a quiz to view class performance",
            list(quiz_options.keys()),
            index=quiz_ids.index(
                st.session_state.overview_quiz_id
            ),
            key="overview_quiz_selector"
        )

        selected_quiz_id = quiz_options[
            selected_quiz_label
        ]

        st.session_state.overview_quiz_id = (
            selected_quiz_id
        )

        # ------------------------------------------------
        # GET SELECTED QUIZ
        # ------------------------------------------------

        selected_quiz = next(
            (
                quiz
                for quiz in quizzes
                if quiz.get("id") == selected_quiz_id
            ),
            None
        )

        if not selected_quiz:

            st.error(
                "❌ Unable to find the selected quiz."
            )

            st.stop()

        # ------------------------------------------------
        # SELECTED QUIZ INFORMATION
        # ------------------------------------------------

        selected_quiz_subject = selected_quiz.get(
            "subject",
            "Not specified"
        )

        selected_quiz_topic = selected_quiz.get(
            "topic",
            "Untitled Topic"
        )

        selected_quiz_level = selected_quiz.get(
            "student_level",
            "Not specified"
        )

        selected_quiz_language = selected_quiz.get(
            "language",
            "Not specified"
        )

        selected_quiz_questions = selected_quiz.get(
            "num_questions",
            0
        )

        selected_quiz_difficulty = selected_quiz.get(
            "difficulty",
            "Not specified"
        )

        st.divider()

        st.subheader(
            f"Quiz #{selected_quiz_id} — "
            f"{selected_quiz_topic}"
        )

        st.caption(
            "Class overview is based on the first attempt "
            "submitted by each student for the selected quiz."
        )

        # ------------------------------------------------
        # QUIZ DETAILS
        # ------------------------------------------------

        st.markdown("### 📋 Quiz Details")

        detail_col1, detail_col2, detail_col3 = st.columns(3)

        with detail_col1:

            st.write(
                f"**Subject**  \n"
                f"{selected_quiz_subject}"
            )

            st.write(
                f"**Topic**  \n"
                f"{selected_quiz_topic}"
            )

        with detail_col2:

            st.write(
                f"**Student Level**  \n"
                f"{selected_quiz_level}"
            )

            st.write(
                f"**Language**  \n"
                f"{selected_quiz_language}"
            )

        with detail_col3:

            st.write(
                f"**Number of Questions**  \n"
                f"{selected_quiz_questions}"
            )

            st.write(
                f"**Difficulty**  \n"
                f"{selected_quiz_difficulty}"
            )

        # ------------------------------------------------
        # GET ATTEMPTS FOR SELECTED QUIZ
        # ------------------------------------------------

        attempt_response = requests.get(
            f"{BACKEND_URL}/quiz/"
            f"{selected_quiz_id}/attempts",
            timeout=10
        )

        attempt_response.raise_for_status()

        attempt_data = attempt_response.json()

        attempts = attempt_data.get(
            "attempts",
            []
        )

        # ------------------------------------------------
        # ONLY USE INITIAL ATTEMPTS
        # ------------------------------------------------

        initial_attempts = [
            attempt
            for attempt in attempts
            if attempt.get("attempt_type") == "initial"
        ]

        # ------------------------------------------------
        # GROUP INITIAL ATTEMPTS BY STUDENT
        # ------------------------------------------------

        students = {}

        for attempt in initial_attempts:

            student_id = (
                attempt.get("student_id")
                or "student_1"
            )

            if student_id not in students:

                students[student_id] = []

            students[student_id].append(
                attempt
            )

        # ------------------------------------------------
        # SELECT EARLIEST INITIAL ATTEMPT
        # FOR EACH STUDENT
        # ------------------------------------------------

        first_attempts = []

        for student_id, student_attempts in students.items():

            first_attempt = min(
                student_attempts,
                key=lambda attempt: attempt.get(
                    "attempt_id",
                    0
                )
            )

            first_attempts.append(
                first_attempt
            )

        # ------------------------------------------------
        # CLASS OVERVIEW
        # ------------------------------------------------

        st.divider()

        st.header("📊 Class Overview")

        total_students = len(
            first_attempts
        )

        total_score = 0
        total_possible = 0
        affected_students = 0

        for attempt in first_attempts:

            score = attempt.get(
                "score",
                0
            )

            total_questions = attempt.get(
                "total_questions",
                0
            )

            total_score += score
            total_possible += total_questions

            if total_questions > 0:

                student_percentage = round(
                    (score / total_questions) * 100
                )

                if student_percentage < 70:

                    affected_students += 1

        # ------------------------------------------------
        # MASTERY RATE
        # ------------------------------------------------

        if total_possible > 0:

            mastery_rate = round(
                (total_score / total_possible) * 100
            )

        else:

            mastery_rate = 0

        # ------------------------------------------------
        # SUPPORT RATE
        # ------------------------------------------------

        if total_students > 0:

            support_percentage = round(
                (affected_students / total_students) * 100
            )

        else:

            support_percentage = 0

        # ------------------------------------------------
        # CLASS OVERVIEW METRICS
        # ------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Students",
                total_students
            )

        with col2:

            st.metric(
                "Mastery Rate",
                f"{mastery_rate}%"
            )

        with col3:

            st.metric(
                "Needs Support",
                affected_students
            )

        with col4:

            st.metric(
                "Support Rate",
                f"{support_percentage}%"
            )

        # ------------------------------------------------
        # CLASS UNDERSTANDING
        # ------------------------------------------------

        st.divider()

        st.header("🧠 Class Understanding")

        well_understood = 0
        developing = 0
        needs_support = 0

        for attempt in first_attempts:

            score = attempt.get(
                "score",
                0
            )

            total_questions = attempt.get(
                "total_questions",
                0
            )

            if total_questions <= 0:

                continue

            student_percentage = round(
                (score / total_questions) * 100
            )

            if student_percentage >= 90:

                well_understood += 1

            elif student_percentage >= 70:

                developing += 1

            else:

                needs_support += 1

        col1, col2, col3 = st.columns(3)

        with col1:

            st.success(
                "🟢 Well Understood"
            )

            st.metric(
                "Students",
                well_understood
            )

        with col2:

            st.warning(
                "🟡 Developing"
            )

            st.metric(
                "Students",
                developing
            )

        with col3:

            st.error(
                "🔴 Needs Support"
            )

            st.metric(
                "Students",
                needs_support
            )

        # ------------------------------------------------
        # NO STUDENT DATA
        # ------------------------------------------------

        if total_students == 0:

            st.info(
                "No student attempts have been recorded "
                f"for Quiz #{selected_quiz_id} yet."
            )

    except requests.exceptions.ConnectionError:

        st.error(
            "❌ Cannot connect to the backend."
        )

        st.info(
            "Please make sure FastAPI is running:\n\n"
            "`uvicorn Backend.main:app --reload`"
        )

    except requests.exceptions.RequestException as exc:

        st.error(
            f"❌ Failed to load class overview: {exc}"
        )

    st.stop()


# ============================================================
# CLASS RESULTS PAGE
# ============================================================

if page == "Class Results":

    st.header("📊 Class Results")

    st.write(
        "Select a quiz and student to view individual performance."
    )

    try:

        # ------------------------------------------------
        # Get all quizzes
        # ------------------------------------------------

        quiz_response = requests.get(
            f"{BACKEND_URL}/quizzes",
            timeout=10
        )

        quiz_response.raise_for_status()

        quiz_data = quiz_response.json()

        quizzes = quiz_data.get(
            "quizzes",
            []
        )

        if not quizzes:

            st.info(
                "No quizzes have been created yet."
            )

        else:

            # ------------------------------------------------
            # SELECT QUIZ
            # ------------------------------------------------

            quiz_options = {
                f"Quiz #{quiz.get('id')} — "
                f"{quiz.get('topic')}": quiz.get("id")
                for quiz in quizzes
            }

            selected_quiz_label = st.selectbox(
                "Select Quiz",
                list(quiz_options.keys())
            )

            selected_quiz_id = quiz_options[
                selected_quiz_label
            ]

            st.divider()

            st.subheader(
                f"Results for Quiz #{selected_quiz_id}"
            )

            # ------------------------------------------------
            # GET ATTEMPTS FOR SELECTED QUIZ
            # ------------------------------------------------

            attempt_response = requests.get(
                f"{BACKEND_URL}/quiz/"
                f"{selected_quiz_id}/attempts",
                timeout=10
            )

            attempt_response.raise_for_status()

            attempt_data = attempt_response.json()

            attempts = attempt_data.get(
                "attempts",
                []
            )

            if not attempts:

                st.info(
                    "No students have completed this quiz yet."
                )

            else:

                # ------------------------------------------------
                # GROUP ATTEMPTS BY STUDENT
                # ------------------------------------------------

                students = {}

                for attempt in attempts:

                    student_id = attempt.get(
                        "student_id"
                    ) or "student_1"

                    if student_id not in students:

                        students[student_id] = []

                    students[student_id].append(
                        attempt
                    )

                # ------------------------------------------------
                # SELECT STUDENT
                # ------------------------------------------------

                student_options = {
                    f"Student {index} ({student_id})": student_id
                    for index, student_id
                    in enumerate(
                        students.keys(),
                        start=1
                    )
                }

                selected_student_label = st.selectbox(
                    "Select Student",
                    list(student_options.keys())
                )

                selected_student_id = student_options[
                    selected_student_label
                ]

                student_attempts = students[
                    selected_student_id
                ]

                st.success(
                    f"Showing results for {selected_student_label}"
                )

                st.divider()

                # ------------------------------------------------
                # STUDENT RESULTS
                # ------------------------------------------------

                st.subheader(
                    f"👤 {selected_student_label}"
                )

                # ------------------------------------------------
                # SEPARATE ATTEMPTS
                # ------------------------------------------------

                initial_attempts = [
                    attempt
                    for attempt in student_attempts
                    if attempt.get("attempt_type") == "initial"
                ]

                requiz_attempts = [
                    attempt
                    for attempt in student_attempts
                    if attempt.get("attempt_type") == "requiz"
                ]

                # ------------------------------------------------
                # FIRST ATTEMPT
                # ------------------------------------------------

                if initial_attempts:

                    first_attempt = min(
                        initial_attempts,
                        key=lambda attempt: attempt.get(
                            "attempt_id",
                            0
                        )
                    )

                    score = first_attempt.get(
                        "score",
                        0
                    )

                    total_questions = first_attempt.get(
                        "total_questions",
                        0
                    )

                    if total_questions > 0:

                        percentage = round(
                            (score / total_questions) * 100
                        )

                    else:

                        percentage = 0

                    st.write(
                        "### 📝 First Attempt"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.metric(
                            "Score",
                            f"{score} / {total_questions}"
                        )

                    with col2:

                        st.metric(
                            "Percentage",
                            f"{percentage}%"
                        )

                    with col3:

                        st.metric(
                            "Attempt Type",
                            "Initial"
                        )

                    st.caption(
                        f"Submitted: "
                        f"{first_attempt.get('submitted_at', '-')}"
                    )

                    with st.expander(
                        "View First Attempt Answers"
                    ):

                        answers = first_attempt.get(
                            "student_answers",
                            []
                        )

                        if answers:

                            for question_index, answer in enumerate(
                                answers,
                                start=1
                            ):

                                st.write(
                                    f"Q{question_index}: {answer}"
                                )

                        else:

                            st.info(
                                "No answers recorded."
                            )

                else:

                    st.info(
                        "No first attempt recorded."
                    )

                # ------------------------------------------------
                # RE-QUIZ ATTEMPTS
                # ------------------------------------------------

                st.divider()

                st.write(
                    "### 🔄 Re-Quiz Attempts"
                )

                if requiz_attempts:

                    requiz_attempts = sorted(
                        requiz_attempts,
                        key=lambda attempt: attempt.get(
                            "attempt_id",
                            0
                        )
                    )

                    for requiz_index, attempt in enumerate(
                        requiz_attempts,
                        start=1
                    ):

                        score = attempt.get(
                            "score",
                            0
                        )

                        total_questions = attempt.get(
                            "total_questions",
                            0
                        )

                        if total_questions > 0:

                            percentage = round(
                                (score / total_questions) * 100
                            )

                        else:

                            percentage = 0

                        with st.expander(
                            f"Re-Quiz {requiz_index} — "
                            f"{score}/{total_questions} "
                            f"({percentage}%)"
                        ):

                            col1, col2, col3 = st.columns(3)

                            with col1:

                                st.metric(
                                    "Score",
                                    f"{score} / {total_questions}"
                                )

                            with col2:

                                st.metric(
                                    "Percentage",
                                    f"{percentage}%"
                                )

                            with col3:

                                st.metric(
                                    "Attempt ID",
                                    attempt.get(
                                        "attempt_id",
                                        "-"
                                    )
                                )

                            st.caption(
                                f"Submitted: "
                                f"{attempt.get('submitted_at', '-')}"
                            )

                            answers = attempt.get(
                                "student_answers",
                                []
                            )

                            if answers:

                                for question_index, answer in enumerate(
                                    answers,
                                    start=1
                                ):

                                    st.write(
                                        f"Q{question_index}: {answer}"
                                    )

                            else:

                                st.info(
                                    "No answers recorded."
                                )

                else:

                    st.info(
                        "No re-quiz attempts recorded for this student."
                    )

    except requests.exceptions.ConnectionError:

        st.error(
            "❌ Cannot connect to the backend."
        )

    except requests.exceptions.RequestException as exc:

        st.error(
            f"❌ Failed to load class results: {exc}"
        )

    st.stop()


# ============================================================
# CREATE QUIZ
# ============================================================

if page == "Create Quiz":

    st.header("📝 Create Quiz")

    st.write(
        "Enter the learning details below. "
        "Gonka AI will generate a quiz for the class."
    )

    with st.form("quiz_form"):

        col1, col2 = st.columns(2)

        with col1:

            subject = st.text_input(
                "Subject",
                placeholder="Example: Biology"
            )

            topic = st.text_input(
                "Topic",
                placeholder="Example: Photosynthesis"
            )

            student_level = st.selectbox(
                "Student Level",
                [
                    "Primary",
                    "Lower Secondary",
                    "Upper Secondary",
                    "University"
                ]
            )

        with col2:

            language = st.selectbox(
                "Language",
                [
                    "English",
                    "Malay",
                    "Chinese"
                ]
            )

            num_questions = st.number_input(
                "Number of Questions",
                min_value=1,
                max_value=10,
                value=5,
                step=1
            )

            difficulty = st.selectbox(
                "Difficulty",
                [
                    "Easy",
                    "Medium",
                    "Hard"
                ]
            )

        create_quiz = st.form_submit_button(
            "🤖 Generate & Assign Quiz",
            type="primary"
        )


# ============================================================
# CREATE QUIZ REQUEST
# ============================================================

if page == "Create Quiz" and create_quiz:

    if not subject.strip():

        st.warning(
            "⚠️ Please enter the subject."
        )

    elif not topic.strip():

        st.warning(
            "⚠️ Please enter the topic."
        )

    else:

        try:

            # ------------------------------------------------
            # Step 1: Ask Gonka AI to generate the quiz
            # ------------------------------------------------

            with st.spinner(
                "🤖 Generating quiz with Gonka AI..."
            ):

                generate_response = requests.post(
                    f"{BACKEND_URL}/generate-quiz",
                    json={
                        "subject": subject.strip(),
                        "topic": topic.strip(),
                        "student_level": student_level,
                        "language": language,
                        "difficulty": difficulty,
                        "num_questions": int(num_questions)
                    },
                    timeout=120
                )

                generate_response.raise_for_status()

                generated_quiz = generate_response.json()

            questions = generated_quiz.get(
                "questions",
                []
            )

            if not questions:

                st.error(
                    "❌ AI did not generate any questions."
                )

            else:

                # ------------------------------------------------
                # Step 2: Store the generated quiz in the backend
                # ------------------------------------------------

                with st.spinner(
                    "📚 Assigning quiz to the class..."
                ):

                    create_response = requests.post(
                        f"{BACKEND_URL}/quiz",
                        json={
                            "subject": subject.strip(),
                            "topic": topic.strip(),
                            "student_level": student_level,
                            "language": language,
                            "difficulty": difficulty,
                            "num_questions": int(num_questions),
                            "questions": questions
                        },
                        timeout=10
                    )

                    create_response.raise_for_status()

                st.session_state.quiz_created = True

                # Clear previous AI analysis because
                # a new quiz has been created.
                st.session_state.analysis = None

                st.success(
                    "✅ Quiz generated and assigned successfully!"
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Cannot connect to the backend."
            )

            st.info(
                "Please start FastAPI using:\n\n"
                "`uvicorn Backend.main:app --reload`"
            )

        except requests.exceptions.Timeout:

            st.error(
                "❌ The request timed out."
            )

        except requests.exceptions.RequestException as exc:

            st.error(
                f"❌ Failed to generate quiz: {exc}"
            )

        except ValueError:

            st.error(
                "❌ Backend returned invalid data."
            )


# ============================================================
# STOP CREATE QUIZ PAGE
# ============================================================

if page == "Create Quiz":
    st.stop()

if page != "AI Diagnosis":
    st.stop()


# ============================================================
# AI DIAGNOSIS PAGE
# ============================================================

st.header("🔍 AI Diagnosis")

st.write(
    "Select a quiz to analyze student responses and identify "
    "common misconceptions."
)


# ============================================================
# GET ALL QUIZZES
# ============================================================

quizzes = []

try:

    quiz_response = requests.get(
        f"{BACKEND_URL}/quizzes",
        timeout=10
    )

    quiz_response.raise_for_status()

    quiz_data = quiz_response.json()

    quizzes = quiz_data.get(
        "quizzes",
        []
    )

except requests.exceptions.ConnectionError:

    st.error(
        "❌ Cannot connect to the backend."
    )

    st.info(
        "Make sure FastAPI is running:\n\n"
        "`uvicorn Backend.main:app --reload`"
    )

    st.stop()

except requests.exceptions.RequestException as exc:

    st.error(
        f"❌ Failed to load quizzes: {exc}"
    )

    st.stop()


# ============================================================
# NO QUIZZES
# ============================================================

if not quizzes:

    st.info(
        "No quizzes have been created yet."
    )

    st.stop()


# ============================================================
# SELECT QUIZ
# ============================================================

quiz_options = {
    f"Quiz #{quiz.get('id')} — "
    f"{quiz.get('topic')}": quiz.get("id")
    for quiz in quizzes
}

quiz_ids = [
    quiz.get("id")
    for quiz in quizzes
]


# Select the first quiz by default.
if (
    st.session_state.selected_quiz_id
    not in quiz_ids
):

    st.session_state.selected_quiz_id = quiz_ids[0]


selected_quiz_label = st.selectbox(
    "Select Quiz to Analyze",
    list(quiz_options.keys()),
    index=quiz_ids.index(
        st.session_state.selected_quiz_id
    )
)


selected_quiz_id = quiz_options[
    selected_quiz_label
]


# Save the selected quiz.
st.session_state.selected_quiz_id = (
    selected_quiz_id
)


# ============================================================
# GET SELECTED QUIZ DETAILS
# ============================================================

selected_quiz = next(
    (
        quiz
        for quiz in quizzes
        if quiz.get("id") == selected_quiz_id
    ),
    None
)


if not selected_quiz:

    st.error(
        "❌ Unable to find the selected quiz."
    )

    st.stop()


# ============================================================
# SELECTED QUIZ INFORMATION
# ============================================================

st.divider()

st.subheader(
    f"Quiz #{selected_quiz_id} — "
    f"{selected_quiz.get('topic')}"
)

col1, col2, col3 = st.columns(3)

with col1:

    st.write(
        f"**Subject:** "
        f"{selected_quiz.get('subject')}"
    )

    st.write(
        f"**Topic:** "
        f"{selected_quiz.get('topic')}"
    )

with col2:

    st.write(
        f"**Student Level:** "
        f"{selected_quiz.get('student_level')}"
    )

    st.write(
        f"**Language:** "
        f"{selected_quiz.get('language')}"
    )

with col3:

    st.write(
        f"**Difficulty:** "
        f"{selected_quiz.get('difficulty')}"
    )

    st.write(
        f"**Questions:** "
        f"{selected_quiz.get('num_questions')}"
    )


# ============================================================
# GET ATTEMPTS FOR SELECTED QUIZ
# ============================================================

attempts = []
initial_attempts = []

try:

    attempts_response = requests.get(
        f"{BACKEND_URL}/quiz/"
        f"{selected_quiz_id}/attempts",
        timeout=10
    )

    attempts_response.raise_for_status()

    attempts_data = attempts_response.json()

    attempts = attempts_data.get(
        "attempts",
        []
    )

    initial_attempts = [
        attempt
        for attempt in attempts
        if attempt.get("attempt_type") == "initial"
    ]

except requests.exceptions.RequestException:

    attempts = []
    initial_attempts = []


# ============================================================
# LOAD SAVED ANALYSIS FOR SELECTED QUIZ
# ============================================================

st.session_state.analysis = None

try:

    analysis_response = requests.get(
        f"{BACKEND_URL}/quiz/"
        f"{selected_quiz_id}/analysis",
        timeout=10
    )

    if analysis_response.status_code == 200:

        saved_analysis = (
            analysis_response.json()
        )

        if saved_analysis:

            st.session_state.analysis = (
                saved_analysis.get(
                    "result",
                    saved_analysis
                )
            )

except requests.exceptions.RequestException:

    st.session_state.analysis = None


# ============================================================
# STUDENT RESPONSE STATUS
# ============================================================

total_students = len(
    set(
        (
            attempt.get("student_id")
            or "student_1"
        )
        for attempt in initial_attempts
    )
)


if not initial_attempts:

    st.info(
        "ℹ️ No student responses have been submitted "
        "for this quiz yet."
    )

else:

    st.success(
        f"✅ {total_students} student(s) have completed "
        f"this quiz."
    )


# ============================================================
# AI ANALYSIS BUTTON
# ============================================================

if st.button(
    "🤖 Analyze Selected Quiz",
    type="primary"
):

    if not initial_attempts:

        st.warning(
            "⚠️ No student responses are available "
            "for this quiz yet."
        )

    else:

        with st.spinner(
            "Analyzing student responses with Gonka AI..."
        ):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/analyze",
                    json={
                        "quiz_id": selected_quiz_id
                    },
                    timeout=120
                )

                response.raise_for_status()

                result = response.json()

                if result.get("error"):

                    st.error(
                        f"❌ {result.get('error')}"
                    )

                else:

                    st.session_state.analysis = result

                    st.success(
                        "✅ AI analysis completed successfully!"
                    )

                    st.rerun()

            except requests.exceptions.ConnectionError:

                st.error(
                    "❌ Cannot connect to the backend."
                )

                st.info(
                    "Make sure FastAPI is running:\n\n"
                    "`uvicorn Backend.main:app --reload`"
                )

            except requests.exceptions.Timeout:

                st.error(
                    "❌ AI analysis timed out."
                )

            except requests.exceptions.RequestException as exc:

                st.error(
                    f"❌ AI analysis failed: {exc}"
                )

            except ValueError:

                st.error(
                    "❌ Backend returned invalid JSON."
                )


# ============================================================
# DISPLAY AI DIAGNOSIS
# ============================================================

result = st.session_state.analysis


if result:

    # Make sure the displayed analysis belongs to
    # the currently selected quiz.
    analysis_quiz_id = result.get(
        "quiz_id"
    )

    if (
        analysis_quiz_id is not None
        and analysis_quiz_id != selected_quiz_id
    ):

        st.session_state.analysis = None

        st.info(
            "No AI diagnosis has been generated "
            "for the selected quiz yet."
        )

        st.stop()

    misconception = result.get(
        "misconception",
        "No major misconception detected."
    )

    affected_students = result.get(
        "affected_students",
        0
    )

    total_students_from_ai = result.get(
        "total_students",
        total_students
    )

    percentage = result.get(
        "percentage",
        0
    )

    reason = result.get(
        "reason",
        "No explanation provided."
    )

    intervention = result.get(
        "intervention",
        "No intervention provided."
    )

    # ========================================================
    # MAIN MISCONCEPTION
    # ========================================================

    st.divider()

    st.warning(
        "⚠️ Common misconception detected:\n\n"
        f"{misconception}"
    )

    # ========================================================
    # AFFECTED STUDENTS + ROOT CAUSE
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "Affected Students"
        )

        st.metric(
            "Students affected",
            f"{affected_students} / "
            f"{total_students_from_ai}"
        )

        st.metric(
            "Questions Linked to Misconception",
            f"{percentage}%"
        )

    with col2:

        st.subheader(
            "Possible Root Cause"
        )

        st.write(
            reason
        )

    st.divider()

    # ========================================================
    # TEACHING RECOMMENDATION
    # ========================================================

    st.header(
        "💡 Recommended Teaching Action"
    )

    st.info(
        intervention
    )

    # ========================================================
    # TEACHING EXPLANATION
    # ========================================================

    st.header(
        "📖 Teaching Explanation"
    )

    teaching_explanation = result.get(
        "teaching_explanation",
        "No teaching explanation was generated."
    )

    st.info(
        teaching_explanation
    )

    st.divider()

    # ========================================================
    # LEARNING IMPROVEMENT
    # ========================================================

    st.header(
        "📈 Learning Improvement"
    )

    st.caption(
        "Learning improvement is calculated from "
        "the selected quiz's student attempts."
    )

    before_score = None
    after_score = None
    improvement = None

    try:

        attempts_response = requests.get(
            f"{BACKEND_URL}/quiz/"
            f"{selected_quiz_id}/attempts",
            timeout=10
        )

        if attempts_response.status_code == 200:

            attempts_data = (
                attempts_response.json()
            )

            attempts = attempts_data.get(
                "attempts",
                []
            )

            initial_attempts = [
                attempt
                for attempt in attempts
                if attempt.get("attempt_type") == "initial"
                and attempt.get("score") is not None
                and attempt.get("total_questions")
            ]

            requiz_attempts = [
                attempt
                for attempt in attempts
                if attempt.get("attempt_type") == "requiz"
                and attempt.get("score") is not None
                and attempt.get("total_questions")
            ]

            if initial_attempts:

                latest_initial = max(
                    initial_attempts,
                    key=lambda attempt: attempt.get(
                        "attempt_id",
                        0
                    )
                )

                before_score = round(
                    (
                        latest_initial["score"]
                        / latest_initial["total_questions"]
                    ) * 100
                )

            if requiz_attempts:

                latest_requiz = max(
                    requiz_attempts,
                    key=lambda attempt: attempt.get(
                        "attempt_id",
                        0
                    )
                )

                after_score = round(
                    (
                        latest_requiz["score"]
                        / latest_requiz["total_questions"]
                    ) * 100
                )

            if (
                before_score is not None
                and after_score is not None
            ):

                improvement = (
                    after_score - before_score
                )

    except requests.exceptions.RequestException:

        pass

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Before Intervention",
            f"{before_score}%"
            if before_score is not None
            else "Not available"
        )

    with col2:

        st.metric(
            "After Re-Quiz",
            f"{after_score}%"
            if after_score is not None
            else "Not completed"
        )

    with col3:

        st.metric(
            "Improvement",
            f"+{improvement}%"
            if (
                improvement is not None
                and improvement >= 0
            )
            else f"{improvement}%"
            if improvement is not None
            else "—"
        )

    st.divider()

    # ========================================================
    # GONKA VERIFICATION
    # ========================================================

    st.header(
        "🔗 AI Verification"
    )

    with st.expander(
        "View Gonka Verification Trail"
    ):

        st.write(
            "### Model Analysis"
        )

        st.success(
            "✓ AI analysis completed"
        )

        st.write(
            "Models Used:"
        )

        models_used = result.get(
            "models_used",
            []
        )

        if models_used:

            for model in models_used:

                st.code(
                    model
                )

        else:

            st.code(
                "Model information unavailable"
            )

        st.write(
            "Consensus Status:"
        )

        consensus_status = result.get(
            "consensus_status",
            "Consensus information unavailable."
        )

        if "Consensus reached" in consensus_status:

            st.success(
                f"✓ {consensus_status}"
            )

        else:

            st.warning(
                consensus_status
            )

        st.write(
            "Consensus Supporting Questions:"
        )

        consensus_questions = result.get(
            "consensus_questions",
            []
        )

        if consensus_questions:

            st.write(
                ", ".join(
                    f"Q{question}"
                    for question in consensus_questions
                )
            )

        else:

            st.write(
                "No overlapping supporting questions."
            )

else:

    st.info(
        "Select a quiz above and make sure students "
        "have submitted their answers. Then click "
        "**Analyze Selected Quiz**."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Education AI • Supporting teachers with "
    "AI-powered learning diagnosis"
)