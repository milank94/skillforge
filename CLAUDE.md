# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SkillForge** is an AI-powered CLI tool that creates interactive, personalized learning experiences for developers. It simulates safe environments where users can learn new frameworks, tools, and technologies through hands-on practice without risk of breaking anything.

### Core Value Proposition
- **Interactive Learning**: Step-by-step guided lessons with real-time feedback
- **AI-Powered**: Uses LLMs to generate personalized courses and provide adaptive feedback
- **Safe Sandbox**: Simulates command execution and file operations without actual system changes
- **Multi-Domain**: Support for learning PyTorch, Docker, Kubernetes, programming languages, CLI tools, and more

### Implementation Status

**Phase 1: Complete ✓** (Basic Package Setup + CLI + Tests)
- ✓ Modern Python packaging with pyproject.toml
- ✓ CLI framework with Typer
- ✓ Rich terminal formatting
- ✓ Basic `learn` command (placeholder implementation)
- ✓ Version display
- ✓ Comprehensive test suite (25 tests, 96% coverage)
- ✓ Development tooling configured (black, ruff, mypy, pytest)

**Phase 2: Complete ✓** (Data Models)
- ✓ Pydantic models for Course, Lesson, Exercise
- ✓ Configuration models (AppConfig, LLMConfig)
- ✓ Enums for constants (Difficulty, LLMProvider, ProgressStatus, SessionState)
- ✓ Progress tracking models (CourseProgress, LessonProgress, ExerciseProgress)
- ✓ Session management (LearningSession)
- ✓ Model helper methods (navigation, calculation, state management)
- ✓ Serialization utilities (to/from JSON, file I/O)

**Phase 3: Not Started** (LLM Integration)
- ⏳ LLM client abstraction
- ⏳ Course generator
- ⏳ Command simulator
- ⏳ Validator engine

**Phase 4: Not Started** (Interactive Learning)
- ⏳ Interactive session loop
- ⏳ Progress tracking
- ⏳ Feedback system

---

## Development Commands

### Setup
```bash
# Create virtual environment (Python 3.9+)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# IMPORTANT: Upgrade pip first (pyproject.toml-only packaging requires pip 21.3+)
python3 -m pip install --upgrade pip

# Install dependencies
pip install -e ".[dev]"  # Editable install with dev dependencies
```

**Note**: On macOS, use `python3` explicitly. The pip upgrade is required for pyproject.toml-only packaging (no setup.py).

### Development
```bash
# Run the CLI locally
python -m skillforge learn "topic"

# Format code
black skillforge/ tests/

# Lint code
ruff check skillforge/ tests/

# Type checking
mypy skillforge/

# Run all tests
pytest

# Run specific test file
pytest tests/test_course_generator.py

# Run with coverage
pytest --cov=skillforge --cov-report=html
```

### Distribution
```bash
# Build package
python -m build

# Test upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Test installation
pipx install skillforge
```

---

## Project Goals

### Learning Objectives for Developer
1. Learn Python package development and distribution (PyPI)
2. Integrate AI frameworks (OpenAI/Anthropic APIs)
3. Build agentic systems with LLMs
4. Create production-quality CLI tools
5. Practice open-source project management

### Product Objectives
1. Create a useful tool for the developer community
2. Build something portfolio-worthy
3. Solve the "learning new tools is overwhelming" problem
4. Enable safe, interactive exploration of complex technologies

---

## Technical Architecture

### Tech Stack
```
Core (Implemented):
- Python 3.9+ ✓
- typer (CLI framework) ✓
- rich (terminal UI/formatting) ✓
- pytest + pytest-cov (testing) ✓
- black, ruff, mypy (code quality) ✓

Core (Planned):
- anthropic or openai SDK (LLM integration)
- pydantic (data validation and settings)

Optional/Future:
- textual (TUI/GUI)
- langchain (agentic orchestration)
- sqlite3 (progress persistence)
- docker (for isolated execution - future)
```

### Distribution:
- Primary: PyPI (pip, pipx, uv)
- Package format: Modern pyproject.toml (PEP 621)

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Interface                         │
│                    (click/typer + rich)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                    Course Generator                          │
│              (LLM-powered, agentic)                         │
│  • Analyzes topic                                           │
│  • Creates curriculum                                        │
│  • Generates exercises                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                 Simulation Engine                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Command    │  │     File     │  │   Output     │     │
│  │  Simulator   │  │   System     │  │  Generator   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                  Validation Engine                           │
│              (LLM-powered evaluation)                        │
│  • Checks command correctness                               │
│  • Evaluates code quality                                    │
│  • Provides hints and feedback                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
skillforge/
├── skillforge/                 # Main package
│   ├── __init__.py            ✓ IMPLEMENTED (version, author, email)
│   ├── cli.py                 ✓ IMPLEMENTED (CLI entry point with typer)
│   ├── core/                  ⏳ TODO
│   │   ├── __init__.py
│   │   ├── course_generator.py    # LLM-based course creation
│   │   ├── simulator.py           # Command/file simulation
│   │   ├── validator.py           # Exercise validation
│   │   └── session.py             # Session management
│   ├── agents/                ⏳ TODO
│   │   ├── __init__.py
│   │   ├── teacher.py             # Main teaching agent
│   │   └── evaluator.py           # Code evaluation agent
│   ├── models/                ✓ IMPLEMENTED
│   │   ├── __init__.py            ✓ (exports all models)
│   │   ├── enums.py               ✓ (Difficulty, LLMProvider, ProgressStatus, SessionState)
│   │   ├── course.py              ✓ (Course model)
│   │   ├── lesson.py              ✓ (Lesson, Exercise models)
│   │   ├── config.py              ✓ (AppConfig, LLMConfig)
│   │   ├── progress.py            ✓ (CourseProgress, LessonProgress, ExerciseProgress)
│   │   └── session.py             ✓ (LearningSession)
│   ├── templates/             ⏳ TODO
│   │   └── course_templates/      # Pre-built course templates
│   └── utils/                 ✓ IMPLEMENTED
│       ├── __init__.py            ✓ (exports serialization functions)
│       ├── serialization.py       ✓ (save/load models to/from JSON)
│       ├── llm_client.py          ⏳ TODO (LLM API wrapper)
│       └── output.py              ⏳ TODO (Rich formatting helpers)
├── tests/
│   ├── __init__.py            ✓ IMPLEMENTED
│   ├── test_package.py        ✓ IMPLEMENTED (8 tests: metadata, imports)
│   ├── test_cli.py            ✓ IMPLEMENTED (17 tests: CLI commands)
│   ├── test_models.py         ✓ IMPLEMENTED (76 tests: all data models)
│   ├── test_serialization.py  ✓ IMPLEMENTED (32 tests: serialization utilities)
│   ├── test_course_generator.py  ⏳ TODO
│   ├── test_simulator.py     ⏳ TODO
│   └── test_validator.py     ⏳ TODO
├── docs/                      ⏳ TODO
│   ├── getting-started.md
│   ├── architecture.md
│   └── contributing.md
├── examples/                  ⏳ TODO
│   └── sample_courses/
├── pyproject.toml             ✓ IMPLEMENTED (Modern Python packaging)
├── README.md                  ✓ IMPLEMENTED
├── LICENSE                    ✓ IMPLEMENTED (MIT)
├── CLAUDE.md                  ✓ IMPLEMENTED (This file)
└── .gitignore                 ✓ IMPLEMENTED
```

**Current Test Coverage**: 133 tests, 97% code coverage (239 statements in skillforge/)

---

## Key Design Decisions

### 1. LLM Provider
**Decision**: Support both Anthropic (Claude) and OpenAI
**Rationale**: 
- Developer wants to learn both APIs
- Users may prefer one over the other
- Fallback if one service is down

**Implementation**: Abstract LLM client interface

### 2. CLI Framework
**Decision**: `typer` ✓ IMPLEMENTED
**Rationale**:
- `typer` has better type hints (uses Pydantic)
- Automatic help generation
- Good integration with modern Python
- Rich integration for beautiful terminal output
- Easy to migrate to `click` if needed (Typer is built on Click)

### 3. Simulation Strategy
**Decision**: Mock/simulate, don't execute actual commands
**Rationale**:
- Safety first - no risk to user's system
- Works offline once course is generated
- Faster than real execution
- Enables "what-if" exploration

**Implementation**: Pattern matching + LLM-generated outputs for unknown commands

### 4. Course Storage
**Decision**: Start with in-memory, add persistence in Phase 2
**Rationale**:
- Simpler MVP
- Focus on core learning experience first
- Can add SQLite or JSON file storage later

---

## Core Workflows

### Workflow 1: Starting a New Course
```bash
$ skillforge learn "pytorch basics"

1. User runs command
2. CLI parses topic
3. Course Generator agent:
   - Queries LLM: "Create a 5-lesson curriculum for PyTorch basics"
   - Parses structured response (JSON)
   - Creates Course object with Lessons
4. Session starts with Lesson 1
5. User interacts with prompts
6. Validator checks each response
7. Progress to next lesson when complete
```

### Workflow 2: Interactive Learning Step
```bash
> import torch
✓ Great! torch imported

1. User enters command/code
2. Simulator checks if it's a known pattern
   - If known: Return pre-defined output
   - If unknown: Ask LLM "What would this output be?"
3. Validator evaluates correctness
   - Uses LLM: "Did user accomplish the goal?"
4. Generate feedback
   - Positive reinforcement
   - Hints if struggling
   - Next step suggestion
```

### Workflow 3: Code Exercise Validation
```python
# User creates train.py
1. User writes code in simulated file
2. Validator sends to LLM:
   - "Evaluate this PyTorch training code"
   - "Does it meet these objectives: [...]"
3. LLM returns:
   - Correctness score
   - Specific feedback
   - Suggestions for improvement
4. Display results with rich formatting
```

---

## LLM Integration Patterns

### Key Principles
- **Structured Output**: Use JSON mode for course generation to ensure parseable responses
- **Clear Context**: Always provide topic, current step, and learning objectives in prompts
- **Specific Constraints**: Request specific feedback formats (e.g., yes/no/partial, percentage scores)
- **Consistent Tone**: Maintain encouraging, teacher-like tone across all interactions
- **Cost Optimization**: Cache common patterns and simulate known commands without LLM calls

### Integration Points
1. **Course Generator** (`core/course_generator.py`): Generates curriculum structure from topic
2. **Command Simulator** (`core/simulator.py`): Falls back to LLM for unknown command outputs
3. **Validator** (`core/validator.py`): Evaluates user responses and provides feedback
4. **Evaluator Agent** (`agents/evaluator.py`): Comprehensive code quality assessment

**Note**: Detailed prompt templates are documented inline in the respective modules.

---

## Configuration

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...

# Optional
SKILLFORGE_DATA_DIR=~/.skillforge
SKILLFORGE_LLM_PROVIDER=anthropic  # or openai
SKILLFORGE_MODEL=claude-sonnet-4-5-20250929
```

### User Configuration File
```yaml
# ~/.skillforge/config.yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.7

simulation:
  command_delay: 0.5  # seconds (for realism)
  show_thinking: false  # show LLM reasoning

appearance:
  theme: monokai
  show_progress_bar: true
```

---

## Target CLI Commands

> **Note**: These are the planned commands for the final product. Update this section as features are implemented.

```bash
# Start a new course
skillforge learn "docker fundamentals"

# Resume previous session
skillforge resume

# List available topics
skillforge topics

# Get help on a topic
skillforge info pytorch

# Create custom course
skillforge create --topic "FastAPI basics" --lessons 7

# Export progress
skillforge export progress.json

# Settings
skillforge config set llm.provider anthropic
```

---

## Testing Strategy

### Implemented Tests (Phase 1) ✓
**25 tests, 96% coverage**

**test_package.py** (8 tests):
- Package metadata (version, author, email)
- Module imports and structure
- Version format validation (semantic versioning)

**test_cli.py** (17 tests):
- Version flag display (`--version`, `-v`)
- Help functionality (`--help`, no args, command help)
- Learn command with various inputs
- Interactive/non-interactive modes
- Output formatting with Rich
- Error handling for invalid commands

**Coverage Details**:
- 28/29 statements covered in skillforge/
- Only uncovered line: `if __name__ == "__main__": app()` (boilerplate, intentionally not tested)

### Planned Tests (Future Phases)

**Unit Tests**:
- Course generation with mocked LLM responses
- Command simulation pattern matching
- Validation logic and feedback generation
- File system simulation operations

**Integration Tests**:
- Full course flow end-to-end (with mocked LLM)
- CLI command parsing and execution
- Session persistence and resumption

**Manual Testing**:
- Real LLM integration with various topics
- User experience flow testing
- Performance with different course types

**Coverage Target**: >80% for all modules (currently at 96%)

---

## Notes for Claude Code

### Development Principles
1. **Start simple**: MVP first, features later
2. **Type hints everywhere**: Use modern Python typing
3. **Test as you go**: Don't accumulate technical debt
4. **Document inline**: Clear docstrings and comments
5. **User experience matters**: Rich formatting, clear messages

### Code Style
- Follow PEP 8
- Use `black` for formatting (line length: 88)
- Use `ruff` for linting
- Type hints with `mypy` validation (strict mode)
- Docstrings in Google style

### Critical Implementation Notes
- **API Keys**: Never commit API keys. Always use environment variables or config files listed in `.gitignore`
- **Error Handling**: All LLM calls must have retry logic with exponential backoff
- **User Data**: Never log or store user inputs that might contain sensitive information
- **Offline Mode**: Simulate known commands without LLM calls to reduce API costs and enable offline usage
- **Rate Limiting**: Implement rate limiting and respect API provider limits
- **Validation**: Always validate and sanitize user inputs before processing

### When Working on This Project
1. Always check this file for context
2. Reference the architecture diagram
3. Consider the phase we're in (MVP vs features)
4. Think about the end user experience
5. Keep security in mind (API keys, user data)

### Common Patterns to Follow
```python
# Use rich for output
from rich.console import Console
console = Console()
console.print("[bold green]Success![/bold green]")

# Use pydantic for models
from pydantic import BaseModel
class Lesson(BaseModel):
    title: str
    objectives: list[str]

# Use typer for CLI
import typer
app = typer.Typer()

@app.command()
def learn(topic: str):
    """Start a new learning session"""
    ...
```

---

## Resources

### Documentation Links
- [Typer Docs](https://typer.tiangolo.com/)
- [Rich Docs](https://rich.readthedocs.io/)
- [Anthropic API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Python Packaging Guide](https://packaging.python.org/)

### Similar Projects (for inspiration)
- Exercism (code practice platform)
- Katacoda (interactive tutorials)
- Learn X in Y minutes
- Codecademy CLI tools

---

**Last Updated**: 2025-11-10
**Project Status**: Phase 1 Complete ✓ (Basic Setup + CLI + Tests)

---

## Changelog

### Phase 1 - Basic Setup (2025-11-10) ✓
- Created modern Python package with pyproject.toml (no setup.py)
- Implemented CLI with Typer and Rich formatting
- Added `learn` command (placeholder implementation)
- Added version display functionality
- Created comprehensive test suite (25 tests, 96% coverage)
- Configured development tooling (black, ruff, mypy, pytest)
- Branch: `feature/basic-setup` merged to `main`

### Phase 2 - Data Models (2025-11-26) - Complete ✓
- ✓ Baseline Pydantic models (Course, Lesson, Exercise)
- ✓ Configuration models (AppConfig, LLMConfig)
- ✓ Enums (Difficulty, LLMProvider, ProgressStatus, SessionState)
- ✓ Progress tracking models (CourseProgress, LessonProgress, ExerciseProgress)
- ✓ Session management (LearningSession)
- ✓ Model helper methods (navigation, calculation, state management)
- ✓ Serialization utilities (to_dict, to_json, from_dict, from_json, save_to_file, load_from_file)
- Comprehensive test suite expanded (133 tests, 97% coverage)
- All quality checks passing (black, ruff, mypy, pytest)
- Branch: `feature/phase2-data-models` (active)

### Next Steps
- Phase 3: LLM integration (course generator, simulator, validator)
- Phase 4: Interactive learning session loop

---

When working on SkillForge, always reference this document for architectural context and design decisions.
