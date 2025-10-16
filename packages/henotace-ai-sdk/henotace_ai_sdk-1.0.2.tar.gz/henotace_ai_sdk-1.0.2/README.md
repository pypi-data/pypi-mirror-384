# Henotace AI Python SDK

Official Python SDK for the Henotace AI API - your gateway to AI-powered tutoring and educational assistance.

## ✨ Features

- **🚀 Easy Integration**: Simple, intuitive API for Python applications
- **📚 Session Management**: Built-in support for managing student sessions and chat history
- **💾 Flexible Storage**: Pluggable storage connectors (in-memory, file, database, etc.)
- **⚡ Async Support**: Full async/await support for modern Python applications
- **🛡️ Error Handling**: Comprehensive error handling with custom exceptions
- **🔄 Rate Limiting**: Built-in retry logic and rate limit handling
- **🎯 Context Management**: Support for persistent context, personas, and user profiles
- **📦 Modular Architecture**: Clean, maintainable code structure matching Node.js SDK
- **🔧 Professional Logging**: Configurable logging with multiple levels
- **🗜️ History Compression**: Automatic chat history summarization for long conversations

## 📦 Installation

```bash
pip install henotace-ai-sdk
```

Or install from source:

```bash
git clone https://github.com/Davidoshin/henotace-python-sdk.git
cd henotace-python-sdk
pip install -e .
```

### Development Installation

For development with additional tools:

```bash
pip install -e .[dev]
```

This includes:
- `pytest` - Testing framework
- `pytest-asyncio` - Async testing support
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking

## 🚀 Quick Start

### Basic Usage (Programmatic)

```python
import asyncio
from henotace_ai import HenotaceAI, create_tutor, SessionSubject, InMemoryConnector

async def main():
    # Initialize the SDK with storage
    sdk = HenotaceAI(
        api_key="your_api_key_here",
        storage=InMemoryConnector()  # Optional: for session persistence
    )
    
    # Check API status
    if sdk.get_status_ok():
        print("✅ API is available")
    else:
        print("❌ API is not available")
        return
    
    # Create a tutor with subject information
    tutor = await create_tutor(
        sdk=sdk,
        student_id="student_123",
        tutor_name="Math Tutor",
        subject=SessionSubject(
            id="math",
            name="Mathematics", 
            topic="Algebra"
        )
    )
    
    # Send a message
    response = await tutor.send("Can you help me solve 2x + 5 = 13?")
    print(f"AI Response: {response}")
    
    # Continue the conversation
    response = await tutor.send("What's the first step?")
    print(f"AI Response: {response}")

# Run the example
asyncio.run(main())
```

### 🖥️ CLI Usage

Install editable and expose CLI:

```bash
pip install -e .[dev]
```

Then run:

```bash
export HENOTACE_API_KEY=your_key
henotace "Explain Pythagoras theorem"
```

Interactive REPL:

```bash
henotace
```

Advanced options:

```bash
henotace --student-id stu1 --tutor-name math --persona "You are a patient math tutor" "Solve x+2=5"
```

Available CLI options:
- `--api-key` - Your Henotace API key
- `--student-id` - Student identifier
- `--tutor-name` - Name for the AI tutor
- `--persona` - Custom tutor personality
- `--context` - Additional context lines

### 🎯 Advanced Usage with Context and Persona

```python
import asyncio
from henotace_ai import HenotaceAI, create_tutor, SessionSubject, InMemoryConnector

async def advanced_example():
    # Initialize SDK with custom configuration
    sdk = HenotaceAI(
        api_key="your_api_key_here",
        storage=InMemoryConnector(),
        default_persona="You are a helpful and patient tutor.",
        default_preset="tutor_default"
    )
    
    # Create a specialized tutor
    tutor = await create_tutor(
        sdk=sdk,
        student_id="student_456",
        tutor_name="Physics Tutor",
        subject=SessionSubject(
            id="physics",
            name="Physics",
            topic="Mechanics"
        ),
        grade_level="high_school",
        language="en"
    )
    
    # Set persona and context
    tutor.set_persona("You are an enthusiastic physics tutor who loves to use real-world examples and analogies to explain complex concepts.")
    tutor.set_context([
        "The student is in 11th grade and is learning about Newton's laws.",
        "They prefer visual explanations and step-by-step problem solving."
    ])
    
    # Set user profile
    tutor.set_user_profile({
        "name": "Alex",
        "grade": "11th",
        "learning_style": "visual",
        "difficulty_level": "intermediate"
    })
    
    # Configure history compression
    tutor.set_compression(
        max_turns=10,           # Keep last 10 messages
        max_summary_chars=800,  # Limit summary length
        checkpoint_every=5      # Compress every 5 messages
    )
    
    # Start tutoring session
    response = await tutor.send(
        "I'm confused about Newton's second law. Can you explain it?",
        context="We just covered Newton's first law in the previous lesson."
    )
    print(f"Tutor: {response}")
    
    # Check chat history
    history = tutor.history()
    print(f"Chat history has {len(history)} messages")

asyncio.run(advanced_example())
```

### 💾 Custom Storage Connector

```python
import asyncio
import json
from henotace_ai import HenotaceAI, create_tutor, StorageConnector, SessionStudent, SessionTutor, SessionChat

class FileStorageConnector(StorageConnector):
    """Example custom storage connector that saves to JSON files"""
    
    def __init__(self, file_path="sessions.json"):
        self.file_path = file_path
        self.data = {"students": []}
        self._load()
    
    def _load(self):
        try:
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {"students": []}
    
    def _save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def list_students(self):
        return [SessionStudent(**s) for s in self.data.get("students", [])]
    
    def upsert_student(self, student):
        students = self.data.get("students", [])
        # Find and update or add student
        for i, s in enumerate(students):
            if s["id"] == student.id:
                students[i] = student.__dict__
                break
        else:
            students.append(student.__dict__)
        self.data["students"] = students
        self._save()
    
    # Implement other required methods...

async def custom_storage_example():
    sdk = HenotaceAI(api_key="your_api_key_here")
    
    # Use custom storage
    storage = FileStorageConnector("my_sessions.json")
    
    tutor = await create_tutor(
        sdk=sdk,
        student_id="student_789",
        storage=storage
    )
    
    response = await tutor.send("Hello, I need help with chemistry!")
    print(f"Response: {response}")

asyncio.run(custom_storage_example())
```

## 🏗️ Architecture

The SDK follows a clean, modular architecture that matches the Node.js SDK:

```
src/henotace_ai/
├── __init__.py          # Main package exports
├── index.py             # HenotaceAI main class
├── tutor.py             # Tutor class and create_tutor factory
├── types.py             # All data classes and type definitions
├── logger.py            # Logging utilities (ConsoleLogger, NoOpLogger)
└── connectors/
    ├── __init__.py      # Connector exports
    └── inmemory.py      # InMemoryConnector implementation
```

### Key Components

- **`HenotaceAI`** - Main SDK client for API interactions
- **`Tutor`** - Lightweight session manager for chat conversations
- **`StorageConnector`** - Abstract interface for storage implementations
- **`SessionSubject`** - Subject information (id, name, topic)
- **`SessionChat`** - Individual chat messages with timestamps
- **`Logger`** - Configurable logging system

## 📚 API Reference

### HenotaceAI

Main client for interacting with the Henotace AI API.

#### Constructor

```python
HenotaceAI(
    api_key: str,
    base_url: str = "https://api.djtconcept.ng",
    timeout: int = 30,
    retries: int = 3,
    storage: Optional[StorageConnector] = None,
    default_persona: Optional[str] = None,
    default_preset: str = "tutor_default",
    default_user_profile: Optional[Dict[str, Any]] = None,
    default_metadata: Optional[Dict[str, Any]] = None,
    logging: Optional[Dict[str, Any]] = None
)
```

#### Methods

- `get_status()` - Check API status (returns full response)
- `get_status_ok()` - Quick status check (returns bool)
- `complete_chat(history, input_text, preset)` - Send chat completion request
- `set_base_url(url)` - Set custom base URL
- `get_config()` - Get current configuration
- `get_logger()` - Get logger instance

### Tutor

Lightweight tutor instance for managing chat sessions.

#### Constructor

```python
Tutor(
    sdk: HenotaceAI,
    student_id: str,
    tutor_id: str,
    storage: Optional[StorageConnector] = None
)
```

#### Methods

- `send(message, context, preset)` - Send message to tutor
- `set_context(context)` - Set persistent context
- `set_persona(persona)` - Set tutor persona
- `set_user_profile(profile)` - Set user profile
- `set_metadata(metadata)` - Set metadata
- `set_compression(**options)` - Configure history compression
- `history()` - Get chat history
- `compress_history()` - Manually compress old chat history
- `ids` - Get student and tutor IDs (property)

### StorageConnector

Abstract base class for storage implementations.

#### Required Methods

- `list_students()` - List all students
- `upsert_student(student)` - Create or update student
- `delete_student(student_id)` - Delete student
- `list_tutors(student_id)` - List tutors for student
- `upsert_tutor(student_id, tutor)` - Create or update tutor
- `delete_tutor(student_id, tutor_id)` - Delete tutor
- `list_chats(student_id, tutor_id)` - List chat messages
- `append_chat(student_id, tutor_id, chat)` - Add chat message
- `replace_chats(student_id, tutor_id, chats)` - Replace all chats

#### Built-in Implementations

- `InMemoryConnector` - In-memory storage for testing and development

## ⚙️ Configuration

### Environment Variables

```bash
export HENOTACE_API_KEY="your_api_key_here"
export HENOTACE_BASE_URL="https://api.djtconcept.ng"  # Optional
```

### SDK Configuration

```python
from henotace_ai import HenotaceAI, InMemoryConnector, LogLevel

sdk = HenotaceAI(
    api_key="your_api_key",
    base_url="https://api.djtconcept.ng",  # Optional
    timeout=30,  # Request timeout in seconds
    retries=3,   # Number of retries for failed requests
    storage=InMemoryConnector(),  # Optional storage connector
    default_persona="You are a helpful tutor.",
    default_preset="tutor_default",
    default_user_profile={"grade": "high_school"},
    logging={
        "enabled": True,
        "level": LogLevel.INFO,
        "logger": None  # Use default console logger
    }
)
```

### Logging Configuration

```python
from henotace_ai import HenotaceAI, LogLevel, ConsoleLogger, NoOpLogger

# Custom logger
custom_logger = ConsoleLogger(LogLevel.DEBUG)

sdk = HenotaceAI(
    api_key="your_key",
    logging={
        "enabled": True,
        "level": LogLevel.DEBUG,
        "logger": custom_logger
    }
)

# Disable logging
sdk = HenotaceAI(
    api_key="your_key",
    logging={"enabled": False}
)
```

## 🛡️ Error Handling

The SDK provides custom exceptions for different error types:

```python
from henotace_ai import HenotaceError, HenotaceAPIError, HenotaceNetworkError

try:
    response = await tutor.send("Hello!")
except HenotaceAPIError as e:
    print(f"API Error: {e}")
except HenotaceNetworkError as e:
    print(f"Network Error: {e}")
except HenotaceError as e:
    print(f"General Error: {e}")
```

### Exception Types

- **`HenotaceError`** - Base exception for all SDK errors
- **`HenotaceAPIError`** - API-specific errors (401, 429, 4xx, 5xx)
- **`HenotaceNetworkError`** - Network connectivity issues

### Retry Logic

The SDK automatically handles:
- **Rate Limiting** - Automatic retry with exponential backoff
- **Server Errors** - Retry on 5xx errors with configurable attempts
- **Network Issues** - Retry on connection failures

## 📖 Examples

Check the `examples/` directory for comprehensive examples:

- **`basic_usage.py`** - Basic SDK usage and setup
- **`advanced_features.py`** - Context, personas, user profiles, and history compression
- **`demo_server.py`** - Flask web demo with interactive UI
- **`templates/index.html`** - Web interface for testing

### Running Examples

```bash
# Basic usage example
python examples/basic_usage.py

# Advanced features demo
python examples/advanced_features.py

# Web demo server
python examples/demo_server.py
# Then visit http://localhost:5000
```

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src/henotace_ai tests/
```

## 🚀 Web Demo

The SDK includes a complete web demo:

```bash
# Start the demo server
python examples/demo_server.py

# Open your browser to http://localhost:5000
```

Features:
- ✨ Real-time AI chat interface
- 🎯 Session management
- 🔑 API key configuration
- 📚 Multiple subjects and grade levels
- 📱 Responsive design

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Davidoshin/henotace-python-sdk.git
cd henotace-python-sdk

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📚 **Documentation**: https://docs.henotace.ai/python-sdk
- 🐛 **Issues**: https://github.com/Davidoshin/henotace-python-sdk/issues
- 📧 **Email**: support@henotace.ai
- 💬 **Discord**: [Join our community](https://discord.gg/henotace)
