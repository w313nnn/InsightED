from fastapi import FastAPI
from AI.gonka_client import detect_misconceptions

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "MUBA2026 Backend is running!"
    }


@app.post("/analyze")
def analyze(data: dict):
    question = data["question"]
    correct_answer = data["correct_answer"]
    student_answers = data["student_answers"]

    result = detect_misconceptions(
        question,
        correct_answer,
        student_answers
    )

    return result