# SkillForge

> AI-powered interactive learning CLI for developers

**SkillForge** helps developers learn new frameworks, tools, and technologies through hands-on practice in safe, simulated environments. Get personalized courses, step-by-step guidance, and real-time feedback—all from your terminal.

## Status

🚧 **Early Development** - Basic package structure is in place. Core features coming soon!

## Features (Planned)

- **Interactive Learning**: Step-by-step guided lessons with real-time feedback
- **AI-Powered**: Uses LLMs to generate personalized courses and provide adaptive feedback
- **Safe Sandbox**: Simulates command execution and file operations without actual system changes
- **Multi-Domain**: Support for learning PyTorch, Docker, Kubernetes, programming languages, and more

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
   pip install -e ".[dev]"
   ```

4. **Verify installation**
   ```bash
   skillforge --version
   skillforge --help
   ```

## Usage

### Basic Commands

```bash
# Start a learning session
skillforge learn "pytorch basics"

# Get help
skillforge --help

# Check version
skillforge --version
```

### Example Output

```
┌─────────────────────────────────────────────────────┐
│                   SkillForge                         │
│  Starting learning session!                          │
│                                                      │
│  Topic: pytorch basics                               │
│  Interactive: Yes                                    │
│                                                      │
│  Note: Full course generation coming in next phase   │
└─────────────────────────────────────────────────────┘
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black skillforge/ tests/
```

### Linting
```bash
ruff check skillforge/ tests/
```

### Type Checking
```bash
mypy skillforge/
```

## Roadmap

- [x] Phase 1: Basic package setup and CLI structure
- [ ] Phase 2: Data models (Course, Lesson, Exercise)
- [ ] Phase 3: LLM integration and course generation
- [ ] Phase 4: Command simulation engine
- [ ] Phase 5: Validation and feedback system
- [ ] Phase 6: Session persistence and progress tracking

## Project Structure

```
skillforge/
├── skillforge/          # Main package
│   ├── __init__.py     # Package initialization
│   └── cli.py          # CLI interface
├── pyproject.toml      # Project configuration
├── README.md           # This file
└── CLAUDE.md           # Development guide
```

## Contributing

This is currently a learning project. Contributions and suggestions are welcome!

## License

MIT License - see LICENSE file for details

## Learn More

For detailed architecture and development guidelines, see [CLAUDE.md](CLAUDE.md).
