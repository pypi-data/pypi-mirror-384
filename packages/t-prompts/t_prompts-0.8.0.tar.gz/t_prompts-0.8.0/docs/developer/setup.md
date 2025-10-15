# Developer Setup

This guide will help you set up your development environment for contributing to t-prompts.

## Prerequisites

- **Python 3.14+** (required for t-string support)
- **Git**
- **UV** (Python package installer and project manager)

## Clone the Repository

```bash
git clone https://github.com/habemus-papadum/t-prompts.git
cd t-prompts
```

## Install UV

If you don't have UV installed, install it using:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on Windows:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

For more installation options, see the [UV documentation](https://docs.astral.sh/uv/).

## Set Up the Development Environment

Install all dependencies including optional extras:

```bash
uv sync --frozen --all-extras
```

This command:
- Uses `--frozen` to install exact versions from the lockfile
- Uses `--all-extras` to install all optional dependencies (image support, UI, etc.)

## Verify Installation

Run the test suite to verify everything is working:

```bash
uv run pytest
```

You should see all tests passing.

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_to_json.py

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/t_prompts
```

### Linting and Formatting

```bash
# Check code with ruff
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Building Documentation

```bash
# Serve documentation locally (auto-reloads on changes)
uv run mkdocs serve

# Build documentation
uv run mkdocs build
```

The documentation will be available at `http://127.0.0.1:8000/`.

### Running Jupyter Notebooks

```bash
# Start Jupyter
uv run jupyter lab

# Or convert a notebook to execute it
uv run jupyter nbconvert --to notebook --execute docs/demos/01-basic.ipynb
```

## Project Structure

```
t-prompts/
├── src/t_prompts/       # Main package source code
│   ├── core.py          # Core StructuredPrompt implementation
│   ├── parsing.py       # Format spec and render hint parsing
│   ├── text.py          # Text processing (dedenting)
│   └── exceptions.py    # Custom exceptions
├── tests/               # Test suite
├── docs/                # Documentation
│   ├── demos/           # Jupyter notebook tutorials
│   └── developer/       # Developer documentation
├── pyproject.toml       # Project configuration
└── uv.lock             # Dependency lockfile
```

## Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and add tests

3. Run tests and linting:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format .
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. Push and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

## Need Help?

- Check the [Architecture documentation](../Architecture.md) for design details
- See [toJSON Format Reference](to-json-format.md) for JSON export format
- Open an issue on GitHub for questions or bug reports

## Next Steps

- Read the [toJSON Format Reference](to-json-format.md) to understand the JSON export format
- Explore the [Architecture documentation](../Architecture.md) for system design
- Check out the [API Reference](../reference.md) for detailed API docs
