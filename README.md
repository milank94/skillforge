# SkillForge

> AI-powered interactive learning CLI for developers

**SkillForge** helps developers learn new frameworks, tools, and technologies through hands-on practice in safe, simulated environments. Get personalized courses, step-by-step guidance, and real-time feedback—all from your terminal.

## Status

🚧 **Active Development** - Core LLM integration complete. Interactive learning session coming next!

## Features

- **AI-Powered Course Generation**: Uses Anthropic (Claude) or OpenAI (GPT-4) to generate personalized learning curricula with intelligent caching
- **Safe Command Simulation**: Simulates shell, Python, git, Docker, and kubectl commands with a virtual file system — no risk to your system
- **Exercise Validation**: Pattern matching + LLM-powered evaluation with progressive hints and constructive feedback
- **Rich Terminal UI**: Beautiful course overviews, progress indicators, and formatted output using Rich
- **Multi-Provider Support**: Works with both Anthropic and OpenAI APIs

## Installation

### Development Setup

**Requirements**: Python 3.12 or higher

1. **Clone the repository**
   ```bash
   git clone https://github.com/milank94/skillforge.git
   cd skillforge
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in editable mode**
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

4. **Set up API key**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   # or
   export OPENAI_API_KEY=sk-...
   ```

5. **Verify installation**
   ```bash
   skillforge --version
   skillforge --help
   ```

## Usage

### Generate a Course

```bash
# Start a learning session (uses Anthropic by default)
skillforge learn "pytorch basics"

# Specify difficulty and lesson count
skillforge learn "docker fundamentals" --difficulty intermediate --lessons 7

# Use OpenAI instead
skillforge learn "kubernetes" --provider openai

# Non-interactive mode (just display the course)
skillforge learn "git basics" --no-interactive
```

### Cache Management

```bash
# View cache info
skillforge cache-info

# Clear cached courses
skillforge cache-clear
```

## Configuration

### Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...       # Anthropic API key
OPENAI_API_KEY=sk-...              # OpenAI API key
SKILLFORGE_LLM_PROVIDER=anthropic  # Default provider (anthropic or openai)
SKILLFORGE_MODEL=claude-sonnet-4-5-20250929  # Model to use
SKILLFORGE_TEMPERATURE=0.7         # Generation temperature
SKILLFORGE_DATA_DIR=~/.skillforge  # Data directory
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_simulator.py

# Run integration tests (requires API keys)
pytest -m integration
```

### Code Quality
```bash
# Format code
black skillforge/ tests/

# Lint code
ruff check skillforge/ tests/

# Type checking
mypy skillforge/
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              CLI Interface                   │
│           (typer + rich)                     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│           Course Generator                   │
│     (LLM-powered, hash-based caching)       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│          Command Simulator                   │
│  (pattern matching + LLM fallback)          │
│  Virtual file system, shell, Python,        │
│  git, docker, kubectl simulation            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│          Exercise Validator                  │
│  (pattern matching + LLM evaluation)        │
│  Progressive hints, score feedback          │
└─────────────────────────────────────────────┘
```

## Roadmap

- [x] Phase 1: Basic package setup and CLI structure
- [x] Phase 2: Data models (Course, Lesson, Exercise, Progress)
- [x] Phase 3: LLM integration (course generator, simulator, validator)
- [ ] Phase 4: Interactive learning session loop and progress tracking

## Project Structure

```
skillforge/
├── skillforge/              # Main package
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # CLI interface (typer + rich)
│   ├── core/                # Core functionality
│   │   ├── course_generator.py  # LLM-based course creation
│   │   ├── simulator.py         # Command simulation engine
│   │   └── validator.py         # Exercise validation engine
│   ├── models/              # Pydantic data models
│   │   ├── course.py            # Course, Lesson, Exercise
│   │   ├── config.py            # AppConfig, LLMConfig
│   │   ├── enums.py             # Difficulty, LLMProvider, etc.
│   │   ├── progress.py          # Progress tracking
│   │   └── session.py           # Learning session
│   └── utils/               # Utilities
│       ├── llm_client.py        # Anthropic + OpenAI clients
│       └── serialization.py     # JSON serialization
├── tests/                   # 279 tests, 93% coverage
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── CLAUDE.md                # Development guide
```

## Contributing

This is currently a learning project. Contributions and suggestions are welcome!

## License

MIT License - see LICENSE file for details

## Learn More

For detailed architecture and development guidelines, see [CLAUDE.md](CLAUDE.md).
