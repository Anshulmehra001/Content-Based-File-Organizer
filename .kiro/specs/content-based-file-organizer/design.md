# Design Document

## Overview

The Content-Based File Organizer is a Python-based automation system that intelligently organizes files by analyzing their content. The system uses the watchdog library for file system monitoring, PyPDF2 for PDF text extraction, and an LLM (simulated or Amazon Bedrock) for generating descriptive filenames. The architecture follows a modular design with clear separation between monitoring, extraction, naming, and organization concerns.

## Architecture

The system follows an event-driven architecture with four main components:

1. **File Monitor** - Watches the Downloads folder using watchdog's Observer pattern
2. **Text Extractor** - Extracts text from PDF and text files
3. **LLM Service** - Generates descriptive filenames using either simulated logic or Amazon Bedrock
4. **File Organizer** - Handles file renaming, moving, and error recovery

```
┌─────────────────┐
│ Downloads Folder│
└────────┬────────┘
         │ (file created)
         ▼
┌─────────────────┐
│  File Monitor   │
│   (watchdog)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Text Extractor  │
│ (PyPDF2/open)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Service    │
│ (Simulated/     │
│  Bedrock)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ File Organizer  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Organized Folder │
└─────────────────┘
```

## Components and Interfaces

### FileMonitor

**Responsibilities:**
- Monitor Downloads folder for new PDF and text files
- Filter events to only process relevant file types
- Trigger processing pipeline for detected files

**Interface:**
```python
class FileMonitor:
    def __init__(self, downloads_path: str, processor: FileProcessor)
    def start() -> None
    def stop() -> None
```

### TextExtractor

**Responsibilities:**
- Extract text from PDF files using PyPDF2
- Read text files with proper encoding handling
- Return first 1000 characters as content sample

**Interface:**
```python
class TextExtractor:
    def extract_text(file_path: str) -> str
    def _extract_from_pdf(file_path: str) -> str
    def _extract_from_text(file_path: str) -> str
```

### LLMService

**Responsibilities:**
- Generate descriptive filenames from content samples
- Support both simulated and Bedrock modes
- Handle LLM failures with fallback naming

**Interface:**
```python
class LLMService:
    def __init__(self, mode: str = "simulated", bedrock_model: str = None)
    def generate_filename(content_sample: str) -> str
    def _simulate_filename(content_sample: str) -> str
    def _bedrock_filename(content_sample: str) -> str
```

### FileOrganizer

**Responsibilities:**
- Sanitize generated filenames
- Rename and move files to Organized folder
- Handle file conflicts and permission errors with retries

**Interface:**
```python
class FileOrganizer:
    def __init__(self, organized_path: str)
    def organize_file(file_path: str, new_name: str) -> bool
    def _sanitize_filename(filename: str) -> str
    def _handle_conflict(target_path: str) -> str
    def _move_with_retry(source: str, destination: str, retries: int = 3) -> bool
```

### FileProcessor

**Responsibilities:**
- Orchestrate the complete processing pipeline
- Coordinate between extractor, LLM service, and organizer
- Handle errors and logging

**Interface:**
```python
class FileProcessor:
    def __init__(self, extractor: TextExtractor, llm_service: LLMService, organizer: FileOrganizer)
    def process_file(file_path: str) -> None
```

## Data Models

### FileEvent
```python
@dataclass
class FileEvent:
    file_path: str
    file_type: str  # 'pdf' or 'txt'
    timestamp: datetime
```

### ProcessingResult
```python
@dataclass
class ProcessingResult:
    success: bool
    original_path: str
    new_path: Optional[str]
    error: Optional[str]
```

### LLMConfig
```python
@dataclass
class LLMConfig:
    mode: str  # 'simulated' or 'bedrock'
    bedrock_model: Optional[str]
    bedrock_region: Optional[str]
    max_tokens: int = 50
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: File type identification and filtering
*For any* file added to the Downloads folder, the File Monitor should correctly identify its type by extension and only process PDF and text files while ignoring all other file types.
**Validates: Requirements 1.3, 1.4**

### Property 2: Text extraction length constraint
*For any* PDF or text file, when text extraction succeeds, the returned content sample should contain at most 1000 characters regardless of the original file length.
**Validates: Requirements 2.3**

### Property 3: Extension preservation during organization
*For any* file being organized, the File Organizer should preserve the original file extension in the renamed file.
**Validates: Requirements 4.2**

### Property 4: Filename sanitization removes invalid characters
*For any* generated filename containing invalid filesystem characters (e.g., /, \, :, *, ?, ", <, >, |), the sanitization process should remove or replace these characters to produce a valid filename.
**Validates: Requirements 4.1**

### Property 5: Conflict resolution with numeric suffixes
*For any* file being moved to the Organized folder where a file with the same name already exists, the system should append a numeric suffix (e.g., _1, _2) to create a unique filename without overwriting.
**Validates: Requirements 4.5**

### Property 6: File organization moves to correct location
*For any* successfully processed file, the file should be moved from the Downloads folder to the Organized folder.
**Validates: Requirements 4.3**

### Property 7: Simulated mode generates valid filenames
*For any* content sample in simulated mode, the LLM Service should generate a non-empty filename using keyword extraction heuristics.
**Validates: Requirements 7.5**

### Property 8: Detection logging includes required information
*For any* file detected by the File Monitor, the log entry should contain both the filename and a timestamp.
**Validates: Requirements 6.1**

### Property 9: Extraction logging includes character count
*For any* successful text extraction, the log entry should include the number of characters extracted.
**Validates: Requirements 6.2**

### Property 10: Organization logging includes final location
*For any* successfully organized file, the log entry should include the final destination path.
**Validates: Requirements 6.4**

### Property 11: Error logging includes complete details
*For any* error that occurs during processing, the log entry should include the error type, error message, and the affected filename.
**Validates: Requirements 6.5**

## Error Handling

### File Access Errors
- **Permission Errors**: Implement retry logic with exponential backoff (3 attempts, 2-second delays)
- **File Not Found**: Catch and log when files are deleted during processing
- **File In Use**: Detect when files are locked by other processes and retry

### Text Extraction Errors
- **Corrupted PDFs**: Catch PyPDF2 exceptions and log detailed error information
- **Encoding Issues**: Try UTF-8, then Latin-1, then CP1252 before failing
- **Empty Files**: Handle files with no extractable text gracefully

### LLM Service Errors
- **API Failures**: Implement fallback to timestamp-based naming
- **Timeout**: Set reasonable timeout limits (30 seconds) for LLM calls
- **Invalid Responses**: Validate LLM output and use fallback if invalid

### File System Errors
- **Disk Full**: Catch and log disk space errors
- **Invalid Paths**: Validate and sanitize all file paths
- **Missing Directories**: Create required directories automatically

## Testing Strategy

### Unit Testing

The system will use **pytest** as the testing framework with the following test coverage:

**TextExtractor Tests:**
- Test PDF text extraction with sample PDFs
- Test text file reading with various encodings
- Test 1000-character truncation
- Test error handling for corrupted files

**LLMService Tests:**
- Test simulated mode filename generation
- Test Bedrock mode with mocked boto3 calls
- Test fallback behavior on errors
- Test mode switching

**FileOrganizer Tests:**
- Test filename sanitization with various invalid characters
- Test extension preservation
- Test conflict resolution with duplicate names
- Test retry logic for permission errors
- Test directory creation

**FileMonitor Tests:**
- Test file type filtering
- Test event detection
- Test integration with FileProcessor

### Property-Based Testing

The system will use **Hypothesis** for property-based testing. Each property test will run a minimum of 100 iterations to ensure robust validation across diverse inputs.

**Property Test Requirements:**
- Each property-based test must be tagged with a comment explicitly referencing the correctness property from this design document
- Tag format: `# Feature: content-based-file-organizer, Property {number}: {property_text}`
- Each correctness property must be implemented by a single property-based test
- Tests should use Hypothesis strategies to generate diverse test inputs

**Test Generators:**
- **Filenames**: Generate random filenames with various extensions and invalid characters
- **File Content**: Generate random text content of varying lengths
- **Paths**: Generate valid and edge-case file paths
- **Timestamps**: Generate random timestamps for testing

**Property Test Coverage:**
- File type identification and filtering (Property 1)
- Text extraction length constraint (Property 2)
- Extension preservation (Property 3)
- Filename sanitization (Property 4)
- Conflict resolution (Property 5)
- File organization location (Property 6)
- Simulated filename generation (Property 7)
- Logging properties (Properties 8-11)

### Integration Testing

- Test complete pipeline from file detection to organization
- Test with real PDF and text files
- Test error scenarios end-to-end
- Test with simulated and mocked Bedrock modes

## Configuration

### Environment Variables
```python
DOWNLOADS_PATH: str = "~/Downloads"  # Path to monitor
ORGANIZED_PATH: str = "~/Downloads/Organized"  # Destination folder
LLM_MODE: str = "simulated"  # "simulated" or "bedrock"
BEDROCK_MODEL: str = "anthropic.claude-v2"  # Bedrock model ID
BEDROCK_REGION: str = "us-east-1"  # AWS region
LOG_LEVEL: str = "INFO"  # Logging level
```

### Configuration File (config.yaml)
```yaml
monitoring:
  downloads_path: "~/Downloads"
  organized_path: "~/Downloads/Organized"
  file_types: ["pdf", "txt"]
  
llm:
  mode: "simulated"  # or "bedrock"
  bedrock:
    model: "anthropic.claude-v2"
    region: "us-east-1"
    max_tokens: 50
    
processing:
  content_sample_length: 1000
  retry_attempts: 3
  retry_delay: 2
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Dependencies

### Required Python Packages
- **watchdog** (^3.0.0): File system monitoring
- **PyPDF2** (^3.0.0): PDF text extraction
- **boto3** (^1.28.0): AWS Bedrock integration (optional)
- **pytest** (^7.4.0): Unit testing framework
- **hypothesis** (^6.92.0): Property-based testing framework
- **pyyaml** (^6.0): Configuration file parsing

### Optional Dependencies
- **pytest-cov**: Test coverage reporting
- **black**: Code formatting
- **mypy**: Type checking

## Deployment

### Running the System
```bash
# Install dependencies
pip install -r requirements.txt

# Run with default configuration
python main.py

# Run with custom config
python main.py --config custom_config.yaml

# Run in simulated mode
python main.py --llm-mode simulated

# Run with Bedrock (requires AWS credentials)
python main.py --llm-mode bedrock
```

### AWS Bedrock Setup (Optional)
1. Configure AWS credentials: `aws configure`
2. Ensure IAM permissions for Bedrock access
3. Set environment variables or update config.yaml
4. Test connection: `python -m scripts.test_bedrock`

## Future Enhancements

- Support for additional file types (DOCX, images with OCR)
- Custom organization rules based on content categories
- Web interface for monitoring and configuration
- Machine learning model for filename generation without LLM
- Batch processing for existing files
- Cloud storage integration (S3, Google Drive)
