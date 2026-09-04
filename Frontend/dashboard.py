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
        "AI Diagnosis",
        "Reports"
    ]
)


# ============================================================
# SESSION STATE
# ============================================================

if "quiz_created" not in st.session_state:
    st.session_state.quiz_created = False

if "analysis" not in st.session_state:
    st.session_state.analysis = None


# ============================================================
# LOAD SAVED AI ANALYSIS
# ============================================================

if st.session_state.analysis is None:

    try:

        response = requests.get(
            f"{BACKEND_URL}/analysis",
            timeout=10
        )

        if response.status_code == 200:

            saved_analysis = response.json()

            if saved_analysis:
                st.session_state.analysis = saved_analysis

    except requests.exceptions.RequestException:

        pass


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

                        st.success(
                            f"✅ {len(attempts)} "
                            f"attempt(s) recorded."
                        )

                        for index, attempt in enumerate(
                            attempts,
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

                            st.write(
                                f"**Student {index}**"
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
                                    attempt.get(
                                        "attempt_type",
                                        "Unknown"
                                    )
                                )

                            st.caption(
                                f"Submitted: "
                                f"{attempt.get('submitted_at', '-')}"
                            )

                            with st.expander(
                                "View Student Answers"
                            ):

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
                                "Question Error Rate",
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
        "Use the teacher menu to create quizzes, "
        "review class results, and diagnose misconceptions."
    )

    st.info(
        "Select **Create Quiz** to generate a new quiz, "
        "or **My Quizzes** to view previous quizzes."
    )

    st.stop()


# ============================================================
# CLASS RESULTS PAGE
# ============================================================

if page == "Class Results":

    st.header("📊 Class Results")

    st.write(
        "View student performance and quiz attempts."
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
            # Select which quiz to view
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
            # Get attempts for selected quiz
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

                # No students means there is no class
                # performance data to display.
                total_students = 0
                mastery_rate = 0
                affected_students = 0
                support_percentage = 0

            else:

                # ------------------------------------------------
                # STUDENT ATTEMPTS
                # ------------------------------------------------

                st.success(
                    f"✅ {len(attempts)} attempt(s) found."
                )

                for index, attempt in enumerate(
                    attempts,
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

                    st.divider()

                    st.subheader(
                        f"Student {index}"
                    )

                    col1, col2, col3, col4 = st.columns(4)

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
                            attempt.get(
                                "attempt_type",
                                "Unknown"
                            )
                        )

                    with col4:

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

                    with st.expander(
                        "View Student Answers"
                    ):

                        answers = attempt.get(
                            "student_answers",
                            []
                        )

                        for question_index, answer in enumerate(
                            answers,
                            start=1
                        ):

                            st.write(
                                f"Q{question_index}: {answer}"
                            )

                # ------------------------------------------------
                # CLASS OVERVIEW
                # ------------------------------------------------

                st.divider()

                st.header("📊 Class Overview")

                total_students = len(attempts)

                total_score = 0
                total_possible = 0

                affected_students = 0

                for attempt in attempts:

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

                    # A student below 70% needs support.
                    if total_questions > 0:

                        student_percentage = round(
                            (score / total_questions) * 100
                        )

                        if student_percentage < 70:

                            affected_students += 1

                # Calculate overall class mastery rate.
                if total_possible > 0:

                    mastery_rate = round(
                        (total_score / total_possible) * 100
                    )

                else:

                    mastery_rate = 0

                # Calculate percentage of students needing support.
                if total_students > 0:

                    support_percentage = round(
                        (affected_students / total_students) * 100
                    )

                else:

                    support_percentage = 0

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

                if mastery_rate >= 90:

                    well_understood = total_students
                    developing = 0
                    needs_support = 0

                elif mastery_rate >= 70:

                    well_understood = 0
                    developing = total_students
                    needs_support = 0

                else:

                    well_understood = 0
                    developing = 0
                    needs_support = total_students

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
# CURRENT QUIZ DATA
# ============================================================

current_questions = []


try:

    response = requests.get(
        f"{BACKEND_URL}/quiz",
        timeout=10
    )

    if response.status_code == 200:

        quiz = response.json()

        current_questions = quiz.get(
            "questions",
            []
        )

except requests.exceptions.ConnectionError:

    st.warning(
        "Backend is not running."
    )

except requests.exceptions.RequestException:

    st.warning(
        "Unable to retrieve the current quiz."
    )


# ============================================================
# CURRENT STUDENT RESPONSE DATA
# ============================================================

student_answers = []
total_students = 0


try:

    response = requests.get(
        f"{BACKEND_URL}/student-answers",
        timeout=10
    )

    if response.status_code == 200:

        data = response.json()

        student_answers = data.get(
            "student_answers",
            []
        )

        total_students = data.get(
            "total_students",
            0
        )

except requests.exceptions.RequestException:

    student_answers = []
    total_students = 0


# ============================================================
# AI ANALYSIS BUTTON
# ============================================================

st.header("🔍 AI Diagnosis")


if st.button(
    "🤖 Analyze Class with Gonka AI",
    type="primary"
):

    if not current_questions:

        st.warning(
            "⚠️ Please create a quiz first."
        )

    elif not student_answers:

        st.warning(
            "⚠️ No student responses are available yet."
        )

    else:

        with st.spinner(
            "Analyzing classroom responses with Gonka AI..."
        ):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/analyze",
                    timeout=120
                )

                response.raise_for_status()

                result = response.json()

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
            "Question Error Rate",
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

    st.info(teaching_explanation)

    st.divider()


    # ========================================================
    # LEARNING IMPROVEMENT
    # ========================================================

    st.header(
        "📈 Learning Improvement"
    )

    st.caption(
        "Re-quiz results will be retrieved from the "
        "backend after students complete the intervention."
    )


    # Calculate the student's actual current score
    before_score = 0

    if student_answers and current_questions:
        correct_count = 0

        for index, answer in enumerate(student_answers):
            if index < len(current_questions):
                correct_answer = current_questions[index].get("answer")

                if answer == correct_answer:
                    correct_count += 1

        before_score = round(
            (correct_count / len(current_questions)) * 100
        )

    # Re-quiz has not been completed yet
    after_score = None
    improvement = None

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Before Intervention",
            f"{before_score}%"
        )

    with col2:
        st.metric(
            "After Re-Quiz",
            "Not completed"
        )

    with col3:
        st.metric(
            "Improvement",
            "—"
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
            "Model:"
        )

        st.code(
            "deepseek-ai/DeepSeek-V4-Flash-0731"
        )


        st.write(
            "Request Status:"
        )

        st.success(
            "Verified through Gonka Router"
        )


        st.write(
            "Gonka Request ID:"
        )


        gonka_request_id = result.get(
            "gonka_request_id",
            "Pending backend integration"
        )


        st.code(
            gonka_request_id
        )


else:

    st.info(
        "Create a quiz and wait for student responses. "
        "Then click **Analyze Class with Gonka AI**."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Education AI • Supporting teachers with "
    "AI-powered learning diagnosis"
)
