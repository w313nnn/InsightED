# InsightED

InsightED is an AI-powered educational platform designed to help teachers identify student misconceptions and provide targeted learning support.

Unlike traditional quiz systems that mainly report marks and correct/incorrect answers, InsightED focuses on understanding **why students are making mistakes**. The system analyses student responses, identifies common misconceptions, summarizes class understanding, and provides recommended teaching interventions.

## Live Demo

### Teacher Dashboard

**Try InsightED:** [InsightED Teacher Dashboard](https://insighted-ai-education.streamlit.app/)

### Student Page

**Try InsightED Student Page:** [InsightED Student Page](https://insighted-ai-education-student.streamlit.app/)

The platform supports both teachers and students throughout the learning cycle:

```text
Create Quiz
    ↓
Students Take Quiz
    ↓
Collect Student Responses
    ↓
AI Misconception Detection
    ↓
Class Understanding
    ↓
Teaching Intervention
    ↓
Personalized Re-Quiz
    ↓
Measure Learning Improvement
```

## Gonka Router Integration

InsightED uses **Gonka Router** as its AI inference layer for AI-powered quiz generation and student misconception analysis.

### Why Gonka Router?

The core purpose of InsightED is not only to determine whether a student answered a question correctly, but to identify **why the student is making mistakes** and provide teachers with actionable teaching recommendations.

Gonka Router enables InsightED to use AI inference through an OpenAI-compatible API while supporting multiple AI models for cross-verification of misconception evidence.

### AI Workflow

```text
Teacher creates a quiz
        ↓
Gonka Router
        ↓
DeepSeek generates quiz questions
        ↓
Students complete the quiz
        ↓
Student responses + correct answers
        ↓
┌───────────────────────┐
│     Gonka Router      │
├───────────┬───────────┤
│ DeepSeek  │  MiniMax  │
└───────────┴───────────┘
        ↓
Compare supporting questions
        ↓
Consensus / disagreement detected
        ↓
Teacher receives AI Diagnosis
```

### Multi-Model Cross-Verification

For misconception detection, InsightED sends the same student response data to two models through Gonka Router:

* **DeepSeek:** `deepseek-ai/DeepSeek-V4-Flash-0731`
* **MiniMax:** `MiniMaxAI/MiniMax-M2.7`

Each model independently identifies the student's main misconception and provides supporting question numbers.

InsightED then compares the supporting questions identified by both models.

When both models identify the same supporting questions, the system reports **consensus**. When they identify different supporting questions, the system records the **disagreement** and uses the DeepSeek analysis as the primary diagnosis.

This provides a simple multi-model cross-verification mechanism rather than relying on a single AI model for misconception analysis.

### Misconception Analysis Output

The AI diagnosis includes:

* Main misconception
* Supporting questions
* Affected students
* Percentage of responses associated with the misconception
* Reason for the misconception
* Recommended teaching intervention
* Teaching explanation that the teacher can use in class
* Model consensus status
* Models used for the analysis

### Gonka API

InsightED connects to Gonka Router through its OpenAI-compatible API:

```text
https://api.gonkarouter.io/v1
```

The Gonka Router API is used for the AI inference required by the application's quiz-generation and misconception-detection workflows.

### Gonka's Role in InsightED

Gonka Router is part of the application's core AI pipeline rather than an additional feature.

The system uses Gonka-powered inference to move from:

**Student answers → Misconception identification → Explanation of why → Teaching intervention**

This allows InsightED to go beyond conventional quiz systems that only report student scores and instead provide teachers with AI-assisted insight into **why students misunderstand concepts**.

## Team Members

InsightED was developed by a four-member team, with each member responsible for a core component of the platform:

| Team Member        | Responsibility                                                                                                                                     |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Lee Wei En**     | **AI + Gonka** — Gonka Router integration, AI quiz generation, misconception detection, local-context explanations, and overall system integration |
| **Teh Hui Min**    | **Teacher Dashboard** — Class Understanding, 🟢🟡🔴 understanding indicators, and AI Diagnosis display                                             |
| **Chan Xiang Wei** | **Student Page** — Student quiz, personalized re-quiz, and learning improvement display                                                            |
| **See Jia Yee**    | **Backend + Web3** — FastAPI backend, database, API development, and Learning Credential / Web3 integration                                        |
