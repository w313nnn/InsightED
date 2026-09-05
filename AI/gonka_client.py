import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

deepseek_client = OpenAI(
    api_key=os.getenv("GONKA_API_KEY"),
    base_url="https://api.gonkarouter.io/v1"
)

minimax_client = OpenAI(
    api_key=os.getenv("GONKA_API_KEY"),
    base_url="https://api.gonkarouter.io/v1",
    timeout=60.0
)

DEEPSEEK_MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"
MINIMAX_MODEL = "MiniMaxAI/MiniMax-M2.7"


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
- "supporting_questions" must contain the question numbers that provide evidence for the main misconception.
- Only include questions the student answered incorrectly.
- Use question numbers starting from 1.
- If the main misconception is supported by Q1, Q3, and Q5, return [1, 3, 5].

Return ONLY valid JSON. Do not include markdown, explanations, or code fences.

Use exactly this structure:

{{
  "misconception": "string",
  "supporting_questions": [1, 3, 5],
  "affected_students": 1,
  "total_students": 1,
  "percentage": 0,
  "reason": "string",
  "intervention": "string",
  "teaching_explanation": "A clear explanation the teacher can use to explain the misunderstood concept to students."
}}
"""

    def analyze_with_model(client, model_name):
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content

        print(f"GONKA {model_name} RAW RESPONSE:")
        print(repr(content))

        if not content or not content.strip():
            raise ValueError(
                f"{model_name} returned an empty response"
            )

        content = content.strip()

        # Remove complete <think>...</think> sections.
        if "<think>" in content:
            if "</think>" in content:
                content = content.split("</think>", 1)[1].strip()
            else:
                raise ValueError(
                    f"{model_name} returned an incomplete "
                    "<think> response without JSON."
                )

        # Remove markdown code fences if present.
        if content.startswith("```"):
            content = content.replace("```json", "", 1).strip()

            if content.endswith("```"):
                content = content[:-3].strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"{model_name} returned invalid JSON: "
                f"{repr(content)}"
            ) from e

        required_fields = [
            "misconception",
            "supporting_questions",
            "affected_students",
            "total_students",
            "percentage",
            "reason",
            "intervention",
            "teaching_explanation"
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(
                    f"{model_name} response is missing: {field}"
                )

        return result

    # ============================================================
    # RUN DEEPSEEK
    # ============================================================

    deepseek_result = None

    try:
        deepseek_result = analyze_with_model(
            deepseek_client,
            DEEPSEEK_MODEL
        )

    except Exception as exc:
        print(
            f"DEEPSEEK ANALYSIS FAILED: {exc}"
        )


    # ============================================================
    # RUN MINIMAX
    # ============================================================

    minimax_result = None

    try:
        minimax_result = analyze_with_model(
            minimax_client,
            MINIMAX_MODEL
        )

    except Exception as exc:
        print(
            f"MINIMAX ANALYSIS FAILED: {exc}"
        )


    # ============================================================
    # CHECK MODEL RESULTS
    # ============================================================

    if deepseek_result is None and minimax_result is None:

        raise ValueError(
            "Both DeepSeek and MiniMax failed to return "
            "a valid analysis."
        )


    # ============================================================
    # BOTH MODELS SUCCEEDED
    # ============================================================

    if (
        deepseek_result is not None
        and minimax_result is not None
    ):

        print("DEEPSEEK ANALYSIS:")
        print(deepseek_result)

        print("MINIMAX ANALYSIS:")
        print(minimax_result)

        deepseek_questions = set(
            deepseek_result["supporting_questions"]
        )

        minimax_questions = set(
            minimax_result["supporting_questions"]
        )

        if deepseek_questions == minimax_questions:

            consensus_status = (
                "Consensus reached between DeepSeek and MiniMax "
                "on the supporting questions for the main misconception."
            )

        else:

            consensus_status = (
                "DeepSeek and MiniMax identified different supporting "
                "questions for the main misconception. DeepSeek analysis "
                "was selected as the primary diagnosis."
            )

        final_result = deepseek_result

        final_result["consensus_questions"] = sorted(
            deepseek_questions.intersection(
                minimax_questions
            )
        )

        final_result["consensus_status"] = consensus_status

        final_result["models_used"] = [
            DEEPSEEK_MODEL,
            MINIMAX_MODEL
        ]

        return final_result


    # ============================================================
    # ONLY DEEPSEEK SUCCEEDED
    # ============================================================

    if deepseek_result is not None:

        print("DEEPSEEK ANALYSIS:")
        print(deepseek_result)

        deepseek_result["consensus_questions"] = []

        deepseek_result["consensus_status"] = (
            "DeepSeek analysis completed, but MiniMax "
            "verification was unavailable."
        )

        deepseek_result["models_used"] = [
            DEEPSEEK_MODEL
        ]

        return deepseek_result


    # ============================================================
    # ONLY MINIMAX SUCCEEDED
    # ============================================================

    print("MINIMAX ANALYSIS:")
    print(minimax_result)

    minimax_result["consensus_questions"] = []

    minimax_result["consensus_status"] = (
        "MiniMax analysis completed, but DeepSeek "
        "verification was unavailable."
    )

    minimax_result["models_used"] = [
        MINIMAX_MODEL
    ]

    return minimax_result


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

    response = deepseek_client.chat.completions.create(
        model=DEEPSEEK_MODEL,
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