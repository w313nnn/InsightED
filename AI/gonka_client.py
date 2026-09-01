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
