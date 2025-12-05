# Project Structure

## Directory Layout

```
.
├── config/              # Configuration files
│   └── config.yaml      # Main YAML configuration
├── src/                 # Source code
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   └── text_extractor.py # Text extraction from PDF/text files
├── tests/               # Test suite
│   ├── __init__.py
│   ├── test_config.py   # Unit tests for configuration
│   ├── test_text_extractor.py # Unit tests for text extraction
│   └── test_text_extractor_properties.py # Property-based tests
├── .hypothesis/         # Hypothesis test cache (generated)
├── .pytest_cache/       # Pytest cache (generated)
├── pyproject.toml       # Project metadata and build config
└── requirements.txt     # Python dependencies
```

## Code Organization

### src/
Contains all production code. Each module should:
- Have a single, clear responsibility
- Define custom exceptions at the top
- Use type hints for all function signatures
- Include comprehensive docstrings (Google style)
- Use property accessors for configuration values

### tests/
Test files mirror the source structure with `test_` prefix. Tests are organized into classes by feature area:
- `TestClassName` for grouping related tests
- Descriptive test method names: `test_<what>_<condition>_<expected>`
- Use pytest fixtures and monkeypatch for isolation
- Property-based tests in separate files with `_properties` suffix

## Naming Conventions

- **Modules**: lowercase with underscores (e.g., `text_extractor.py`)
- **Classes**: PascalCase (e.g., `TextExtractor`, `ConfigurationError`)
- **Functions/Methods**: lowercase with underscores (e.g., `extract_text`)
- **Constants**: UPPERCASE with underscores (e.g., `DEFAULTS`)
- **Private methods**: prefix with underscore (e.g., `_extract_from_pdf`)

## Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports

Separate each group with a blank line.
