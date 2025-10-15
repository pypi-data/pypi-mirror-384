# Henotace AI SDK for Python

A Python SDK for integrating with Henotace AI's educational API. This SDK provides easy access to AI tutoring, assessment grading, content generation, and educational games.

## Features

- 🤖 **AI Tutoring**: Create and manage AI tutoring sessions
- 📝 **Assessment Grading**: Grade assessments using AI
- 📚 **Content Generation**: Generate educational content
- 🎮 **Educational Games**: Access educational games and questions
- 🔐 **Secure Authentication**: API key-based authentication
- 📊 **Usage Tracking**: Built-in usage tracking and rate limiting

## Installation

```bash
pip install henotace-ai-sdk
```

## Quick Start

```python
from henotace_sdk import HenotaceSDK

# Initialize the SDK
sdk = HenotaceSDK(
    api_key="your-api-key-here",
    base_url="https://api.djtconcept.ng/api/external"  # Production URL
)

# Create a tutoring session
session = sdk.create_tutoring_session(
    subject="Mathematics",
    grade_level="Grade 10",
    student_id="student123"
)

# Send a message to the AI tutor
response = sdk.send_chat_message(
    session_id=session["session_id"],
    message="Can you help me solve this quadratic equation: x² + 5x + 6 = 0?"
)

print(response["response"])
```

## API Reference

### Initialization

```python
sdk = HenotaceSDK(api_key, base_url)
```

**Parameters:**
- `api_key` (str): Your API key from Henotace AI
- `base_url` (str): Base URL for the API (default: localhost for development)

### Tutoring Sessions

#### Create Tutoring Session
```python
session = sdk.create_tutoring_session(subject, grade_level, student_id)
```

#### Send Chat Message
```python
response = sdk.send_chat_message(session_id, message)
```

#### End Tutoring Session
```python
result = sdk.end_tutoring_session(session_id)
```

### Assessment Grading

```python
grade = sdk.grade_assessment(
    question="What is the capital of France?",
    student_answer="Paris",
    correct_answer="Paris"
)
```

### Content Generation

```python
content = sdk.generate_content(
    content_type="lesson_plan",
    subject="Science",
    grade_level="Grade 8",
    topic="Photosynthesis"
)
```

### Educational Games

#### Get Game Questions
```python
questions = sdk.get_game_questions(game_id=1)
```

#### Submit Game Answers
```python
result = sdk.submit_game_answers(
    game_id=1,
    answers=[
        {"question_id": 1, "answer": "A"},
        {"question_id": 2, "answer": "B"}
    ]
)
```

## Error Handling

The SDK raises `HenotaceAPIError` for API-related errors:

```python
from henotace_sdk import HenotaceAPIError

try:
    response = sdk.send_chat_message(session_id, message)
except HenotaceAPIError as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/henotace/henotace-ai-sdk-python.git
cd henotace-ai-sdk-python
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black henotace_sdk.py
flake8 henotace_sdk.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@henotace.ai
- 📖 Documentation: https://docs.henotace.ai
- 🐛 Issues: https://github.com/henotace/henotace-ai-sdk-python/issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### 1.0.0
- Initial release
- AI tutoring sessions
- Assessment grading
- Content generation
- Educational games support
