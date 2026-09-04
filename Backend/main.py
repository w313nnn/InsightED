import json
from datetime import datetime

from fastapi import FastAPI

from AI.gonka_client import detect_misconceptions, generate_quiz
from Backend.database import get_connection, initialize_database


app = FastAPI()


# ============================================================
# DATABASE
# ============================================================

initialize_database()


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "MUBA2026 Backend is running!"
    }


# ============================================================
# CREATE QUIZ
# ============================================================

@app.post("/quiz")
def create_quiz(data: dict):

    questions = data["questions"]

    # These fields will be supplied by the Teacher Dashboard.
    # .get() keeps the endpoint temporarily compatible with
    # the current frontend while we update it later.
    subject = data.get("subject", "Unknown")
    topic = data.get("topic", "Unknown")
    student_level = data.get("student_level", "Unknown")
    language = data.get("language", "Unknown")
    difficulty = data.get("difficulty", "Unknown")
    num_questions = data.get("num_questions", len(questions))

    created_at = datetime.now().isoformat(timespec="seconds")

    connection = get_connection()
    cursor = connection.cursor()

    # IMPORTANT:
    # Do NOT delete previous quizzes.
    # Every new quiz is stored as a new record.

    cursor.execute(
        """
        INSERT INTO quizzes (
            subject,
            topic,
            student_level,
            language,
            difficulty,
            num_questions,
            questions,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subject,
            topic,
            student_level,
            language,
            difficulty,
            num_questions,
            json.dumps(questions),
            created_at
        )
    )

    quiz_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return {
        "message": "Quiz created successfully.",
        "quiz_id": quiz_id,
        "quiz": {
            "id": quiz_id,
            "subject": subject,
            "topic": topic,
            "student_level": student_level,
            "language": language,
            "difficulty": difficulty,
            "num_questions": num_questions,
            "questions": questions,
            "created_at": created_at
        }
    }


# ============================================================
# GET CURRENT QUIZ
# ============================================================

@app.get("/quiz")
def get_quiz():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            subject,
            topic,
            student_level,
            language,
            difficulty,
            num_questions,
            questions,
            created_at
        FROM quizzes
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    connection.close()

    if not row:
        return {}

    return {
        "id": row[0],
        "subject": row[1],
        "topic": row[2],
        "student_level": row[3],
        "language": row[4],
        "difficulty": row[5],
        "num_questions": row[6],
        "questions": json.loads(row[7]),
        "created_at": row[8]
    }


# ============================================================
# GET QUIZ HISTORY
# ============================================================

@app.get("/quizzes")
def get_quiz_history():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            subject,
            topic,
            student_level,
            language,
            difficulty,
            num_questions,
            questions,
            created_at
        FROM quizzes
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    quizzes = []

    for row in rows:
        quizzes.append({
            "id": row[0],
            "subject": row[1],
            "topic": row[2],
            "student_level": row[3],
            "language": row[4],
            "difficulty": row[5],
            "num_questions": row[6],
            "questions": json.loads(row[7]),
            "created_at": row[8]
        })

    return {
        "quizzes": quizzes
    }


# ============================================================
# GET ONE QUIZ BY ID
# ============================================================

@app.get("/quiz/{quiz_id}")
def get_quiz_by_id(quiz_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            subject,
            topic,
            student_level,
            language,
            difficulty,
            num_questions,
            questions,
            created_at
        FROM quizzes
        WHERE id = ?
        """,
        (quiz_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if not row:
        return {
            "error": "Quiz not found."
        }

    return {
        "id": row[0],
        "subject": row[1],
        "topic": row[2],
        "student_level": row[3],
        "language": row[4],
        "difficulty": row[5],
        "num_questions": row[6],
        "questions": json.loads(row[7]),
        "created_at": row[8]
    }


# ============================================================
# SUBMIT STUDENT ANSWERS
# ============================================================

@app.post("/student-answers")
def submit_student_answers(data: dict):

    answers = data["student_answers"]

    # Use the provided quiz_id if available.
    # If not provided, fall back to the latest quiz.
    quiz_id = data.get("quiz_id")

    # Attempt type tells us whether this is the
    # original quiz or a re-quiz.
    attempt_type = data.get("attempt_type", "initial")

    if attempt_type not in ["initial", "requiz"]:
        return {
            "error": "Invalid attempt type."
        }

    connection = get_connection()
    cursor = connection.cursor()

    # ------------------------------------------------
    # Find quiz ID if it was not provided
    # ------------------------------------------------

    if quiz_id is None:

        cursor.execute(
            """
            SELECT id
            FROM quizzes
            ORDER BY id DESC
            LIMIT 1
            """
        )

        quiz_row = cursor.fetchone()

        if not quiz_row:
            connection.close()

            return {
                "error": "No quiz has been created yet."
            }

        quiz_id = quiz_row[0]

    # ------------------------------------------------
    # Get the original quiz
    # ------------------------------------------------

    cursor.execute(
        """
        SELECT id, questions
        FROM quizzes
        WHERE id = ?
        """,
        (quiz_id,)
    )

    quiz_row = cursor.fetchone()

    if not quiz_row:
        connection.close()

        return {
            "error": "Quiz not found."
        }

    original_questions = json.loads(quiz_row[1])

    # ------------------------------------------------
    # Determine which questions belong to this attempt
    # ------------------------------------------------

    if attempt_type == "requiz":

        # Re-quiz questions are supplied by the Student Page.
        attempt_questions = data.get("attempt_questions")

        if not attempt_questions:
            connection.close()

            return {
                "error": "Re-quiz questions were not provided."
            }

    else:

        # Initial attempt uses the original quiz questions.
        attempt_questions = original_questions

    # ------------------------------------------------
    # Calculate the student's score
    # ------------------------------------------------

    score = 0

    for index, question in enumerate(attempt_questions):

        if index >= len(answers):
            continue

        if answers[index] == question["answer"]:
            score += 1

    total_questions = len(attempt_questions)

    submitted_at = datetime.now().isoformat(timespec="seconds")

    # ------------------------------------------------
    # Save the student attempt
    # ------------------------------------------------

    cursor.execute(
        """
        INSERT INTO student_attempts (
            quiz_id,
            answers,
            questions,
            score,
            total_questions,
            submitted_at,
            attempt_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            quiz_id,
            json.dumps(answers),
            json.dumps(attempt_questions),
            score,
            total_questions,
            submitted_at,
            attempt_type
        )
    )

    attempt_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return {
        "message": "Student answers saved successfully.",
        "attempt_id": attempt_id,
        "quiz_id": quiz_id,
        "student_answers": answers,
        "attempt_questions": attempt_questions,
        "score": score,
        "total_questions": total_questions,
        "submitted_at": submitted_at,
        "attempt_type": attempt_type
    }


# ============================================================
# GET STUDENT ANSWERS
# ============================================================

@app.get("/student-answers")
def get_student_answers():

    connection = get_connection()
    cursor = connection.cursor()

    # Get the latest attempt for the latest quiz
    cursor.execute(
        """
        SELECT
            id,
            quiz_id,
            answers,
            score,
            total_questions,
            submitted_at,
            attempt_type
        FROM student_attempts
        WHERE quiz_id = (
            SELECT id
            FROM quizzes
            ORDER BY id DESC
            LIMIT 1
        )
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    connection.close()

    if not row:
        return {
            "student_answers": [],
            "total_students": 0,
            "attempt_id": None
        }

    return {
        "student_answers": json.loads(row[2]),
        "total_students": 1,
        "attempt_id": row[0],
        "quiz_id": row[1],
        "score": row[3],
        "total_questions": row[4],
        "submitted_at": row[5],
        "attempt_type": row[6]
    }


# ============================================================
# GET ALL ATTEMPTS FOR A QUIZ
# ============================================================

@app.get("/quiz/{quiz_id}/attempts")
def get_quiz_attempts(quiz_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            quiz_id,
            answers,
            questions,
            score,
            total_questions,
            submitted_at,
            attempt_type
        FROM student_attempts
        WHERE quiz_id = ?
        ORDER BY id DESC
        """,
        (quiz_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    attempts = []

    for row in rows:

        attempt_questions = []

        if row[3]:
            attempt_questions = json.loads(row[3])

        attempts.append({
            "attempt_id": row[0],
            "quiz_id": row[1],
            "student_answers": json.loads(row[2]),
            "attempt_questions": attempt_questions,
            "score": row[4],
            "total_questions": row[5],
            "submitted_at": row[6],
            "attempt_type": row[7]
        })

    return {
        "quiz_id": quiz_id,
        "attempts": attempts
    }


# ============================================================
# AI MISCONCEPTION ANALYSIS
# ============================================================

@app.post("/analyze")
def analyze():

    connection = get_connection()
    cursor = connection.cursor()

    # Get latest quiz
    cursor.execute(
        """
        SELECT id, questions
        FROM quizzes
        ORDER BY id DESC
        LIMIT 1
        """
    )

    quiz_row = cursor.fetchone()

    if not quiz_row:
        connection.close()

        return {
            "error": "No quiz has been created yet."
        }

    quiz_id = quiz_row[0]
    current_questions = json.loads(quiz_row[1])

    # Get latest student attempt for this quiz
    cursor.execute(
        """
        SELECT answers
        FROM student_attempts
        WHERE quiz_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (quiz_id,)
    )

    answer_row = cursor.fetchone()

    connection.close()

    if not answer_row:
        return {
            "error": "No student answers have been submitted yet."
        }

    current_student_answers = json.loads(answer_row[0])

    # Send data to Gonka AI
    result = detect_misconceptions(
        current_questions,
        current_student_answers
    )

    # Save this analysis under the specific quiz
    analysis_connection = get_connection()
    analysis_cursor = analysis_connection.cursor()

    created_at = datetime.now().isoformat(timespec="seconds")

    analysis_cursor.execute(
        """
        INSERT INTO analyses (
            quiz_id,
            result,
            created_at
        )
        VALUES (?, ?, ?)
        """,
        (
            quiz_id,
            json.dumps(result),
            created_at
        )
    )

    analysis_connection.commit()
    analysis_connection.close()

    return result


# ============================================================
# GET SAVED AI ANALYSIS
# ============================================================

@app.get("/analysis")
def get_analysis():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT result
        FROM analyses
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    connection.close()

    if not row:
        return {}

    return json.loads(row[0])


# ============================================================
# GET AI ANALYSIS FOR A SPECIFIC QUIZ
# ============================================================

@app.get("/quiz/{quiz_id}/analysis")
def get_quiz_analysis(quiz_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            quiz_id,
            result,
            created_at
        FROM analyses
        WHERE quiz_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (quiz_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if not row:
        return {}

    return {
        "id": row[0],
        "quiz_id": row[1],
        "result": json.loads(row[2]),
        "created_at": row[3]
    }


# ============================================================
# GET COMPLETE QUIZ HISTORY
# ============================================================

@app.get("/quiz/{quiz_id}/history")
def get_quiz_history_details(quiz_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    # ------------------------------------------------
    # Get quiz information
    # ------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            subject,
            topic,
            student_level,
            language,
            difficulty,
            num_questions,
            questions,
            created_at
        FROM quizzes
        WHERE id = ?
        """,
        (quiz_id,)
    )

    quiz_row = cursor.fetchone()

    if not quiz_row:

        connection.close()

        return {
            "error": "Quiz not found."
        }

    # ------------------------------------------------
    # Get all student attempts for this quiz
    # ------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            quiz_id,
            answers,
            questions,
            score,
            total_questions,
            submitted_at,
            attempt_type
        FROM student_attempts
        WHERE quiz_id = ?
        ORDER BY id DESC
        """,
        (quiz_id,)
    )

    attempt_rows = cursor.fetchall()

    # ------------------------------------------------
    # Get latest AI analysis for this quiz
    # ------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            quiz_id,
            result,
            created_at
        FROM analyses
        WHERE quiz_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (quiz_id,)
    )

    analysis_row = cursor.fetchone()

    connection.close()

    # ------------------------------------------------
    # Format attempts
    # ------------------------------------------------

    attempts = []

    for row in attempt_rows:

        attempt_questions = []

        if row[3]:
            attempt_questions = json.loads(row[3])

        attempts.append({
            "attempt_id": row[0],
            "quiz_id": row[1],
            "student_answers": json.loads(row[2]),
            "attempt_questions": attempt_questions,
            "score": row[4],
            "total_questions": row[5],
            "submitted_at": row[6],
            "attempt_type": row[7]
        })

    # ------------------------------------------------
    # Format AI analysis
    # ------------------------------------------------

    analysis = None

    if analysis_row:

        analysis = {
            "id": analysis_row[0],
            "quiz_id": analysis_row[1],
            "result": json.loads(analysis_row[2]),
            "created_at": analysis_row[3]
        }

    # ------------------------------------------------
    # Return complete quiz history
    # ------------------------------------------------

    return {
        "quiz": {
            "id": quiz_row[0],
            "subject": quiz_row[1],
            "topic": quiz_row[2],
            "student_level": quiz_row[3],
            "language": quiz_row[4],
            "difficulty": quiz_row[5],
            "num_questions": quiz_row[6],
            "questions": json.loads(quiz_row[7]),
            "created_at": quiz_row[8]
        },
        "attempts": attempts,
        "analysis": analysis
    }


# ============================================================
# GENERATE QUIZ WITH GONKA AI
# ============================================================

@app.post("/generate-quiz")
def generate_quiz_endpoint(data: dict):

    subject = data["subject"]
    topic = data["topic"]
    student_level = data["student_level"]
    language = data["language"]
    difficulty = data["difficulty"]
    num_questions = data["num_questions"]

    result = generate_quiz(
        subject,
        topic,
        student_level,
        language,
        difficulty,
        num_questions
    )

    return result