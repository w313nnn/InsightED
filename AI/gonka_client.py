import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GONKA_API_KEY"),
    base_url="https://api.gonkarouter.io/v1"
)


def detect_misconceptions(question, correct_answer, student_answers):
    student_data = "\n".join(
        f"Student {i + 1}: {answer}"
        for i, answer in enumerate(student_answers)
    )

    prompt = f"""
You are an educational AI assistant.

Analyze the following student quiz responses.

Question:
{question}

Correct answer:
{correct_answer}

Student answers:
{student_data}

Identify the main misconception among the students.

Return ONLY valid JSON. Do not include markdown, explanations, or code fences.

Use exactly this structure:

{{
  "misconception": "string",
  "affected_students": 0,
  "total_students": 0,
  "percentage": 0,
  "reason": "string",
  "intervention": "string"
}}
"""

    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash-0731",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return json.loads(response.choices[0].message.content)


def generate_quiz(topic, difficulty, num_questions):
    prompt = f"""
You are an educational AI assistant.

Generate quiz questions based on the following requirements.

Topic:
{topic}

Difficulty:
{difficulty}

Number of questions:
{num_questions}

Return ONLY valid JSON.
Do not include markdown, explanations, or code fences.

Use exactly this structure:

{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "answer": "Correct answer"
    }}
  ]
}}

Requirements:
- Return exactly {num_questions} questions.
- Each question must have exactly 4 options.
- Each question must have only one correct answer.
- The answer must exactly match one of the options.
- Questions must match the requested topic.
- Questions must match the requested difficulty.
- Avoid duplicate questions.
"""

    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash-0731",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = json.loads(response.choices[0].message.content)

    if "questions" not in result:
        raise ValueError("Invalid response: questions field is missing")

    questions = result["questions"]

    if len(questions) != num_questions:
        raise ValueError("Invalid response: incorrect number of questions")

    seen_questions = []

    for question in questions:
        if "question" not in question:
            raise ValueError("Invalid response: question field is missing")

        if "options" not in question:
            raise ValueError("Invalid response: options field is missing")

        if "answer" not in question:
            raise ValueError("Invalid response: answer field is missing")

        if len(question["options"]) != 4:
            raise ValueError(
                "Invalid response: each question must have 4 options"
            )

        if question["answer"] not in question["options"]:
            raise ValueError(
                "Invalid response: answer does not match an option"
            )

        if question["question"] in seen_questions:
            raise ValueError("Invalid response: duplicate question")

        seen_questions.append(question["question"])

    return result


if __name__ == "__main__":
    question = "What gas do plants absorb during photosynthesis?"
    correct_answer = "Carbon dioxide"

    student_answers = [
        "Carbon dioxide",
        "Oxygen",
        "Oxygen",
        "Carbon dioxide",
        "Oxygen",
        "Carbon dioxide",
        "Oxygen",
        "Carbon dioxide",
        "Oxygen",
        "Carbon dioxide"
    ]

    result = detect_misconceptions(
        question,
        correct_answer,
        student_answers
    )

    print(result)
    print(type(result))
    print(result["percentage"])