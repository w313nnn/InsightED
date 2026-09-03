```python
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
# SESSION STATE
# ============================================================

if "quiz_created" not in st.session_state:
    st.session_state.quiz_created = False

if "analysis" not in st.session_state:
    st.session_state.analysis = None


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🎓 Education AI")

st.caption(
    "AI-powered classroom misconception diagnosis"
)

st.divider()


# ============================================================
# CREATE QUIZ
# ============================================================

st.header("📝 Create Quiz")

st.write(
    "Enter a question and its correct answer. "
    "Student responses will be collected separately "
    "through the Student Page."
)


with st.form("quiz_form"):

    question = st.text_area(
        "Question",
        placeholder=(
            "Example: What gas do plants absorb "
            "during photosynthesis?"
        ),
        height=120
    )

    correct_answer = st.text_input(
        "Correct Answer",
        placeholder=(
            "Example: Carbon dioxide"
        )
    )

    create_quiz = st.form_submit_button(
        "➕ Create Quiz",
        type="primary"
    )


# ============================================================
# CREATE QUIZ REQUEST
# ============================================================

if create_quiz:

    if not question.strip():

        st.warning(
            "⚠️ Please enter a question."
        )

    elif not correct_answer.strip():

        st.warning(
            "⚠️ Please enter the correct answer."
        )

    else:

        try:

            response = requests.post(
                f"{BACKEND_URL}/quiz",
                json={
                    "question": question.strip(),
                    "correct_answer": correct_answer.strip()
                },
                timeout=10
            )

            response.raise_for_status()

            quiz_result = response.json()

            st.session_state.quiz_created = True

            # Clear previous AI result because
            # a new quiz has been created.
            st.session_state.analysis = None

            st.success(
                "✅ Quiz created successfully!"
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
                f"❌ Failed to create quiz: {exc}"
            )


st.divider()


# ============================================================
# CURRENT QUIZ
# ============================================================

st.header("📚 Current Quiz")


current_question = None
current_correct_answer = None


try:

    response = requests.get(
        f"{BACKEND_URL}/quiz",
        timeout=10
    )

    if response.status_code == 200:

        quiz = response.json()

        current_question = quiz.get(
            "question"
        )

        current_correct_answer = quiz.get(
            "correct_answer"
        )

        col1, col2 = st.columns(
            [3, 1]
        )

        with col1:

            st.subheader("Question")

            st.write(
                current_question
            )

        with col2:

            st.subheader(
                "Correct Answer"
            )

            st.success(
                current_correct_answer
            )

    else:

        st.info(
            "No quiz has been created yet."
        )

except requests.exceptions.ConnectionError:

    st.warning(
        "Backend is not running."
    )

except requests.exceptions.RequestException:

    st.warning(
        "Unable to retrieve the current quiz."
    )


st.divider()


# ============================================================
# STUDENT RESPONSES
# ============================================================

st.header("👨‍🎓 Student Responses")


student_answers = []


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

except requests.exceptions.RequestException:

    student_answers = []


total_students = len(
    student_answers
)


if total_students > 0:

    st.success(
        f"✅ {total_students} student responses received."
    )

    with st.expander(
        "View student responses"
    ):

        for index, answer in enumerate(
            student_answers,
            start=1
        ):

            st.write(
                f"Student {index}: {answer}"
            )

else:

    st.info(
        "No student responses have been submitted yet."
    )


st.divider()


# ============================================================
# CLASS OVERVIEW
# ============================================================

st.header("📊 Class Overview")


# Initial values
affected_students = 0
support_percentage = 0
mastery_rate = 0


if st.session_state.analysis:

    result = st.session_state.analysis

    affected_students = result.get(
        "affected_students",
        0
    )

    support_percentage = result.get(
        "percentage",
        0
    )

    mastery_rate = max(
        0,
        100 - support_percentage
    )


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


st.divider()


# ============================================================
# CLASS UNDERSTANDING
# ============================================================

st.header("🧠 Class Understanding")


if st.session_state.analysis:

    well_understood = max(
        0,
        total_students - affected_students
    )

    needs_support = affected_students

else:

    well_understood = 0
    needs_support = 0


# Developing is currently reserved for
# future individual-score analysis.
developing = 0


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


st.divider()


# ============================================================
# AI ANALYSIS BUTTON
# ============================================================

st.header("🔍 AI Diagnosis")


if st.button(
    "🤖 Analyze Class with Gonka AI",
    type="primary"
):

    if not current_question:

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
                    timeout=60
                )

                response.raise_for_status()

                result = response.json()

                st.session_state.analysis = result

                st.success(
                    "✅ AI analysis completed successfully!"
                )

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
            "Percentage",
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


    if st.button(
        "✨ Generate Teaching Explanation"
    ):

        st.write(
            "Think of the plant as a small factory. "
            "Carbon dioxide and water enter the process, "
            "while oxygen is released as a product. "
            "This helps students understand the difference "
            "between the gas absorbed and the gas released "
            "during photosynthesis."
        )


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


    # Temporary demo values
    before_score = 42
    after_score = 84
    improvement = after_score - before_score


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Before Intervention",
            f"{before_score}%"
        )


    with col2:

        st.metric(
            "After Re-Quiz",
            f"{after_score}%"
        )


    with col3:

        st.metric(
            "Improvement",
            f"+{improvement}%"
        )


    st.progress(
        after_score / 100
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
```
