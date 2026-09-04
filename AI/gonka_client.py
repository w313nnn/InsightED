import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GONKA_API_KEY"),
    base_url="https://api.gonkarouter.io/v1"
)


def detect_misconceptions(questions, student_answers):
    student_data = "\n".join(
        f"Q{i + 1}: {question['question']}\n"
        f"Correct answer: {question['answer']}\n"
        f"Student answer: {student_answers[i]}"
        for i, question in enumerate(questions)
    )

    prompt = f"""
You are an educational AI assistant.

Analyze one student's responses to a multi-question quiz.

Quiz responses:
{student_data}

Identify the student's main misconceptions based on the questions they answered incorrectly.

Focus on:
1. Which concepts the student misunderstood.
2. WHY the student may have made those mistakes.
3. What the teacher should explain or reinforce.

Important:
- Do not treat each question as a different student.
- There is exactly ONE student.
- The student answered {len(questions)} questions.
- Only identify misconceptions from incorrect answers.
- If the student has multiple incorrect answers involving different concepts, identify the most important misconception patterns.
- "affected_students" should always be 1.
- "total_students" should always be 1.
- "percentage" should represent the percentage of this student's responses associated with the main misconception.

Return ONLY valid JSON. Do not include markdown, explanations, or code fences.

Use exactly this structure:

{{
  "misconception": "string",
  "affected_students": 1,
  "total_students": 1,
  "percentage": 0,
  "reason": "string",
  "intervention": "string",
  "teaching_explanation": "A clear explanation the teacher can use to explain the misunderstood concept to students."
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

    content = response.choices[0].message.content

    print("GONKA MISCONCEPTION RAW RESPONSE:")
    print(repr(content))

    if not content or not content.strip():
        raise ValueError("Gonka returned an empty response")

    content = content.strip()

    if "<think>" in content and "</think>" in content:
        content = content.split("</think>", 1)[1].strip()

    if content.startswith("```"):
        content = content.replace("```json", "").strip()
        content = content.replace("```", "", 1).strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gonka returned invalid JSON: {repr(content)}"
        ) from e

    required_fields = [
        "misconception",
        "affected_students",
        "total_students",
        "percentage",
        "reason",
        "intervention",
        "teaching_explanation"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(f"Invalid response: {field} field is missing")

    return result


def generate_quiz(subject, topic, student_level, language, difficulty, num_questions):
    prompt = f"""
You are an educational AI assistant.

Generate quiz questions based on the following requirements.

Subject:
{subject}

Topic:
{topic}

Student Level:
{student_level}

Language:
{language}

Difficulty:
{difficulty}

Number of questions:
{num_questions}

Important:
- Generate all questions and answer options in {language}.
- Questions must be appropriate for {student_level} students.
- Questions must be about the topic "{topic}" within the subject "{subject}".
- Questions must match the requested difficulty level.
- Avoid content that is too advanced or too simple for the specified student level.
- Avoid duplicate questions.
- Use clear and age-appropriate language.

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
- Questions must match the requested subject and topic.
- Questions must match the requested student level.
- Questions must match the requested language.
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

    content = response.choices[0].message.content

    print("GONKA RAW RESPONSE:")
    print(repr(content))

    if not content or not content.strip():
        raise ValueError("Gonka returned an empty response")

    content = content.strip()

    if "<think>" in content and "</think>" in content:
        content = content.split("</think>", 1)[1].strip()

    if content.startswith("```"):
        content = content.replace("```json", "").strip()
        content = content.replace("```", "", 1)
        content = content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gonka returned invalid JSON: {repr(content)}"
        ) from e

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
    questions = [
        {
            "question": "Which organelle in plant cells is responsible for carrying out photosynthesis?",
            "answer": "Chloroplast"
        },
        {
            "question": "What is the primary pigment in plants that absorbs light energy for photosynthesis?",
            "answer": "Chlorophyll a"
        },
        {
            "question": "In which part of the chloroplast do the light-dependent reactions take place?",
            "answer": "Thylakoid membranes"
        },
        {
            "question": "Which product of the light-dependent reactions is released as a gas?",
            "answer": "O2"
        },
        {
            "question": "During the Calvin cycle, carbon dioxide is initially converted into an organic molecule through which process?",
            "answer": "Carbon fixation"
        }
    ]

    student_answers = [
        "Mitochondria",
        "Chlorophyll a",
        "Stroma",
        "O2",
        "Transpiration"
    ]

    result = detect_misconceptions(
        questions,
        student_answers
    )

    print(result)
    print(type(result))
    print(result["percentage"])