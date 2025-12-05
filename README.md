# Content-Based File Organizer

An intelligent file organization system that automatically monitors your Downloads folder, analyzes file content using LLM, and organizes files with meaningful, descriptive names.

## Features

- 🔍 **Automatic Monitoring**: Watches your Downloads folder for new PDF and text files
- 📄 **Content Analysis**: Extracts text from PDFs and text files (first 1000 characters)
- 🤖 **Smart Naming**: Uses LLM to generate descriptive filenames based on content
- 📁 **Auto-Organization**: Moves renamed files to an organized folder structure
- 🔄 **Robust Processing**: Handles errors gracefully with retry logic
- ⚙️ **Flexible Configuration**: Supports both simulated and AWS Bedrock LLM modes

## Requirements

- Python 3.8 or higher
- pip package manager

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd content-based-file-organizer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

### 3. Configure the System

The system uses `config/config.yaml` for configuration. The default configuration works out of the box with simulated mode.

## Quick Start

### Running in Simulated Mode (No AWS Required)

The easiest way to get started is with simulated mode, which uses keyword extraction instead of a real LLM:

```bash
python main.py
```

This will:
1. Monitor your `~/Downloads` folder
2. Process new PDF and text files
3. Generate descriptive names using keyword extraction
4. Move organized files to `~/Downloads/Organized`

### Running with AWS Bedrock

To use Amazon Bedrock for more sophisticated filename generation:

1. **Configure AWS Credentials**:
```bash
aws configure
```

2. **Update Configuration** (optional):
Edit `config/config.yaml` to set Bedrock parameters:
```yaml
llm:
  mode: "bedrock"
  bedrock:
    model: "anthropic.claude-v2"
    region: "us-east-1"
```

3. **Run with Bedrock Mode**:
```bash
python main.py --llm-mode bedrock
```

## Usage Examples

### Example 1: Basic Usage with Default Settings

```bash
# Start monitoring with default configuration
python main.py
```

Output:
```
2024-12-06 10:30:15 - INFO - Starting Content-Based File Organizer
2024-12-06 10:30:15 - INFO - Monitoring: /Users/username/Downloads
2024-12-06 10:30:15 - INFO - LLM Mode: simulated
2024-12-06 10:30:15 - INFO - Press Ctrl+C to stop
```

### Example 2: Custom Configuration File

```bash
python main.py --config /path/to/custom_config.yaml
```

### Example 3: Override LLM Mode via Command Line

```bash
# Force simulated mode
python main.py --llm-mode simulated

# Force Bedrock mode
python main.py --llm-mode bedrock
```

### Example 4: Using Environment Variables

```bash
# Override configuration with environment variables
export DOWNLOADS_PATH="/path/to/custom/downloads"
export ORGANIZED_PATH="/path/to/custom/organized"
export LLM_MODE="bedrock"
export LOG_LEVEL="DEBUG"

python main.py
```

## Configuration

### Configuration File (config/config.yaml)

```yaml
monitoring:
  downloads_path: "~/Downloads"          # Folder to monitor
  organized_path: "~/Downloads/Organized" # Destination for organized files
  file_types: ["pdf", "txt"]             # File types to process

llm:
  mode: "simulated"                      # "simulated" or "bedrock"
  bedrock:
    model: "anthropic.claude-v2"         # Bedrock model ID
    region: "us-east-1"                  # AWS region
    max_tokens: 50                       # Max tokens for response

processing:
  content_sample_length: 1000            # Characters to extract for analysis
  retry_attempts: 3                      # Retry attempts for file operations
  retry_delay: 2                         # Delay between retries (seconds)

logging:
  level: "INFO"                          # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Environment Variables

Environment variables override configuration file settings:

| Variable | Description | Example |
|----------|-------------|---------|
| `DOWNLOADS_PATH` | Path to monitor | `/Users/me/Downloads` |
| `ORGANIZED_PATH` | Destination folder | `/Users/me/Documents/Organized` |
| `LLM_MODE` | LLM mode | `simulated` or `bedrock` |
| `BEDROCK_MODEL` | Bedrock model ID | `anthropic.claude-v2` |
| `BEDROCK_REGION` | AWS region | `us-east-1` |
| `LOG_LEVEL` | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Command Line Arguments

```bash
python main.py [OPTIONS]

Options:
  --config PATH       Path to custom configuration file
  --llm-mode MODE     Override LLM mode (simulated or bedrock)
  -h, --help          Show help message
```

## How It Works

1. **File Detection**: The system monitors your Downloads folder using the watchdog library
2. **Content Extraction**: When a PDF or text file is detected, the first 1000 characters are extracted
3. **Name Generation**: The content is sent to the LLM (simulated or Bedrock) to generate a descriptive filename
4. **File Organization**: The file is renamed and moved to the Organized folder
5. **Error Handling**: If errors occur (file in use, permission denied), the system retries automatically

### Processing Pipeline

```
Downloads Folder
       ↓
File Monitor (detects new files)
       ↓
Text Extractor (extracts content)
       ↓
LLM Service (generates filename)
       ↓
File Organizer (renames & moves)
       ↓
Organized Folder
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_*.py -k "not properties"

# Property-based tests only
pytest tests/test_*_properties.py

# Integration tests
pytest tests/test_integration.py
```

### Run Tests for Specific Component

```bash
pytest tests/test_text_extractor.py
pytest tests/test_llm_service.py
pytest tests/test_file_organizer.py
```

## Troubleshooting

### Issue: Files Not Being Detected

**Symptoms**: System runs but doesn't process new files

**Solutions**:
1. Verify the Downloads path exists:
   ```bash
   ls ~/Downloads
   ```
2. Check file types are supported (PDF or TXT)
3. Increase log level to DEBUG:
   ```bash
   export LOG_LEVEL="DEBUG"
   python main.py
   ```
4. Ensure files are fully downloaded before processing starts

### Issue: Permission Denied Errors

**Symptoms**: `PermissionError` or `OSError` in logs

**Solutions**:
1. Close any applications that have the file open
2. Check file permissions:
   ```bash
   ls -la ~/Downloads/filename.pdf
   ```
3. The system will automatically retry 3 times with 2-second delays
4. If persistent, manually move the file after closing other applications

### Issue: AWS Bedrock Connection Fails

**Symptoms**: `botocore.exceptions` errors or fallback to simulated mode

**Solutions**:
1. Verify AWS credentials are configured:
   ```bash
   aws sts get-caller-identity
   ```
2. Check IAM permissions include Bedrock access:
   - `bedrock:InvokeModel`
   - `bedrock:InvokeModelWithResponseStream`
3. Verify the region supports Bedrock:
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```
4. Test Bedrock connectivity:
   ```python
   import boto3
   client = boto3.client('bedrock-runtime', region_name='us-east-1')
   ```

### Issue: PDF Text Extraction Fails

**Symptoms**: Empty content or extraction errors for PDFs

**Solutions**:
1. Verify PDF is not password-protected
2. Check if PDF contains actual text (not scanned images)
3. Try opening the PDF in a reader to confirm it's not corrupted
4. For scanned PDFs, consider using OCR tools separately
5. Check logs for specific PyPDF2 errors

### Issue: Generated Filenames Are Generic

**Symptoms**: Files named with timestamps instead of descriptive names

**Solutions**:
1. This is the fallback behavior when LLM fails
2. In simulated mode, ensure files have meaningful content
3. In Bedrock mode, check API connectivity and quotas
4. Increase `content_sample_length` in config for more context
5. Review logs for LLM service errors

### Issue: File Conflicts (Duplicate Names)

**Symptoms**: Files being renamed with `_1`, `_2` suffixes

**Solutions**:
- This is expected behavior to prevent overwriting
- The system automatically appends numeric suffixes
- To avoid conflicts, periodically organize the Organized folder into subfolders
- Consider implementing custom organization rules (future enhancement)

### Issue: High Memory Usage

**Symptoms**: System slows down or crashes with large files

**Solutions**:
1. The system only extracts first 1000 characters by default
2. Adjust `content_sample_length` in config if needed
3. For very large PDFs, consider pre-processing to split them
4. Monitor system resources:
   ```bash
   top -p $(pgrep -f main.py)
   ```

### Issue: System Doesn't Stop with Ctrl+C

**Symptoms**: Process continues running after interrupt signal

**Solutions**:
1. Try Ctrl+C again (may need 2-3 attempts)
2. Force kill if necessary:
   ```bash
   pkill -f "python main.py"
   ```
3. Check for zombie processes:
   ```bash
   ps aux | grep main.py
   ```

## Logging

### Log Locations

Logs are written to stdout by default. To save logs to a file:

```bash
python main.py > organizer.log 2>&1
```

Or use log redirection:

```bash
python main.py 2>&1 | tee organizer.log
```

### Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Indication of potential issues
- **ERROR**: Serious problems that prevent specific operations

### Example Log Output

```
2024-12-06 10:30:15,123 - FileMonitor - INFO - File detected: invoice.pdf
2024-12-06 10:30:15,234 - TextExtractor - INFO - Extracted 856 characters from invoice.pdf
2024-12-06 10:30:15,456 - LLMService - INFO - Generated filename: monthly_invoice_november_2024.pdf
2024-12-06 10:30:15,567 - FileOrganizer - INFO - File organized: ~/Downloads/Organized/monthly_invoice_november_2024.pdf
```

## Development

### Project Structure

```
.
├── config/              # Configuration files
├── src/                 # Source code
│   ├── config.py        # Configuration management
│   ├── file_monitor.py  # File system monitoring
│   ├── text_extractor.py # Text extraction
│   ├── llm_service.py   # LLM integration
│   ├── file_organizer.py # File organization
│   └── file_processor.py # Processing orchestration
├── tests/               # Test suite
├── main.py              # Application entry point
└── README.md            # This file
```

### Running Tests During Development

```bash
# Run tests on file change (requires pytest-watch)
pip install pytest-watch
ptw

# Format code
black src/ tests/

# Type checking
mypy src/

# All quality checks
black src/ tests/ && mypy src/ && pytest
```

### Contributing

1. Write tests for new features
2. Ensure all tests pass: `pytest`
3. Format code with black: `black src/ tests/`
4. Run type checking: `mypy src/`
5. Update documentation as needed

## FAQ

**Q: Can I process existing files in my Downloads folder?**
A: Currently, the system only processes new files added after it starts. Batch processing of existing files is a planned future enhancement.

**Q: What file types are supported?**
A: Currently PDF and text files (.pdf, .txt). Support for DOCX and images with OCR is planned.

**Q: How much does AWS Bedrock cost?**
A: Bedrock pricing varies by model and region. Check [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) for details. Simulated mode is free.

**Q: Can I customize the organization structure?**
A: Currently, all files go to a single Organized folder. Custom categorization is a planned enhancement.

**Q: Is my file content sent to the cloud?**
A: In simulated mode, no. In Bedrock mode, only the first 1000 characters are sent to AWS Bedrock for processing.

**Q: Can I run this on Windows/Linux?**
A: Yes, the system is cross-platform and works on Windows, macOS, and Linux.

## License

[Add your license information here]

## Support

For issues, questions, or contributions, please [open an issue](link-to-issues) or contact [your-contact-info].

## Acknowledgments

- Built with [watchdog](https://github.com/gorakhargosh/watchdog) for file monitoring
- Uses [PyPDF2](https://github.com/py-pdf/pypdf) for PDF text extraction
- Powered by [AWS Bedrock](https://aws.amazon.com/bedrock/) for LLM capabilities
- Testing with [pytest](https://pytest.org/) and [Hypothesis](https://hypothesis.readthedocs.io/)
