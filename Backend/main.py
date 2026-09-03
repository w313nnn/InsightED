from fastapi import FastAPI
from AI.gonka_client import detect_misconceptions, generate_quiz

app = FastAPI()

# Temporary in-memory storage
current_quiz = {}
student_answers = []


@app.get("/")
def home():
    return {
        "message": "MUBA2026 Backend is running!"
    }


@app.post("/quiz")
def create_quiz(data: dict):
    global current_quiz

    current_quiz = {
        "question": data["question"],
        "correct_answer": data["correct_answer"]
    }

    return current_quiz


@app.get("/quiz")
def get_quiz():
    return current_quiz


@app.post("/student-answers")
def submit_student_answers(data: dict):
    global student_answers

    student_answers = data["student_answers"]

    return {
        "message": "Student answers saved successfully.",
        "student_answers": student_answers
    }


@app.get("/student-answers")
def get_student_answers():
    return {
        "student_answers": student_answers
    }


@app.post("/analyze")
def analyze(data: dict):
    question = data["question"]
    correct_answer = data["correct_answer"]
    student_answers_data = data["student_answers"]

    result = detect_misconceptions(
        question,
        correct_answer,
        student_answers_data
    )

    return result


@app.post("/generate-quiz")
def generate_quiz_endpoint(data: dict):
    topic = data["topic"]
    difficulty = data["difficulty"]
    num_questions = data["num_questions"]

    result = generate_quiz(
        topic,
        difficulty,
        num_questions
    )

    return result