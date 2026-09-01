# MUBA2026

MUBA2026 is an AI-powered educational prototype that helps educators identify common misconceptions in student responses and provides suggested teaching interventions.

## Project Structure

```text
MUBA2026/
├── AI/
├── Backend/
├── Frontend/
└── Docs/
```

## AI

The current prototype uses **DeepSeek through Gonka Router**.

```text
Student Responses
       ↓
   AI Analysis
       ↓
Misconception + Reason
       ↓
Teaching Intervention
```

The AI returns structured results including:

* Misconception
* Affected students
* Percentage
* Possible reason
* Teaching intervention

## Setup

Install the required Python packages:

```bash
pip install openai python-dotenv
```

Create a `.env` file in the project root:

```env
GONKA_API_KEY=your_api_key_here
```

Run the AI prototype:

```bash
python AI/gonka_client.py
```

## Development

The project uses feature branches for development.

```text
main
├── feature/misconception-detection
├── feature/backend-api
├── feature/frontend-dashboard
└── feature/backend-web3
```

Features should be developed, tested, and reviewed before being merged into `main`.

## Status

🚧 **Prototype / MVP Development**
