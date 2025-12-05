# Technology Stack

## Build System

- **Build Backend**: setuptools (PEP 517 compliant)
- **Python Version**: >=3.8
- **Package Manager**: pip

## Core Dependencies

- **watchdog** (>=3.0.0): File system monitoring
- **PyPDF2** (>=3.0.0): PDF text extraction
- **boto3** (>=1.28.0): AWS Bedrock integration
- **pyyaml** (>=6.0): YAML configuration parsing
- **reportlab** (>=4.0.0): PDF generation/manipulation

## Testing & Development

- **pytest** (>=7.4.0): Unit testing framework
- **hypothesis** (>=6.92.0): Property-based testing
- **pytest-cov**: Code coverage
- **black**: Code formatting (line length: 100)
- **mypy**: Static type checking

## Common Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run property-based tests
pytest tests/test_text_extractor_properties.py
```

### Code Quality
```bash
# Format code with black
black src/ tests/

# Type checking with mypy
mypy src/

# Run all quality checks
black src/ tests/ && mypy src/ && pytest
```

### Installation
```bash
# Install package in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install from requirements
pip install -r requirements.txt
```

## Configuration

Configuration is managed via:
1. YAML file (`config/config.yaml`)
2. Environment variables (override YAML)
3. Defaults (fallback)

Environment variables follow pattern: `SECTION_KEY` (e.g., `LLM_MODE`, `DOWNLOADS_PATH`)
