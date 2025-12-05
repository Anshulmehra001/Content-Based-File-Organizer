# Requirements Document

## Introduction

The Content-Based File Organizer is an automated system that monitors a Downloads folder for new PDF and text files, extracts their content, uses an LLM to generate descriptive filenames based on the content, and organizes the files into a structured folder. This system eliminates manual file organization by intelligently renaming files based on what they contain rather than relying on generic filenames or extensions.

## Glossary

- **File Monitor**: The watchdog-based component that detects new files in the Downloads folder
- **Text Extractor**: The component that extracts text content from PDF and text files
- **LLM Service**: The service that generates descriptive filenames (simulated or Amazon Bedrock)
- **File Organizer**: The component that renames and moves files to the Organized folder
- **Downloads Folder**: The monitored directory where new files are detected
- **Organized Folder**: The destination directory where renamed files are moved
- **Content Sample**: The first 1000 characters of extracted text sent to the LLM

## Requirements

### Requirement 1

**User Story:** As a user, I want the system to automatically monitor my Downloads folder, so that new files are detected without manual intervention.

#### Acceptance Criteria

1. WHEN the system starts, THE File Monitor SHALL begin watching the Downloads folder for new file events
2. WHEN a new file is added to the Downloads folder, THE File Monitor SHALL detect the file creation event within 5 seconds
3. WHEN a file creation event occurs, THE File Monitor SHALL identify the file type by its extension
4. WHEN a non-PDF and non-text file is added, THE File Monitor SHALL ignore the file and continue monitoring
5. WHEN the Downloads folder does not exist, THE File Monitor SHALL create the folder and begin monitoring

### Requirement 2

**User Story:** As a user, I want the system to extract text content from PDF and text files, so that the content can be analyzed for intelligent naming.

#### Acceptance Criteria

1. WHEN a PDF file is detected, THE Text Extractor SHALL extract all text content using PyPDF2
2. WHEN a text file is detected, THE Text Extractor SHALL read the file content with UTF-8 encoding
3. WHEN text extraction succeeds, THE Text Extractor SHALL return the first 1000 characters as the Content Sample
4. WHEN a PDF file is corrupted or unreadable, THE Text Extractor SHALL handle the error gracefully and log the failure
5. WHEN a text file has encoding issues, THE Text Extractor SHALL attempt alternative encodings before failing

### Requirement 3

**User Story:** As a user, I want the system to generate descriptive filenames based on file content, so that files are named meaningfully rather than generically.

#### Acceptance Criteria

1. WHEN the Content Sample is available, THE LLM Service SHALL send the sample to the LLM for filename generation
2. WHEN the LLM responds, THE LLM Service SHALL extract a short descriptive filename from the response
3. WHEN using simulated mode, THE LLM Service SHALL generate a dummy descriptive filename based on simple heuristics
4. WHEN using Amazon Bedrock, THE LLM Service SHALL call the Bedrock API with the Content Sample and a filename generation prompt
5. WHEN the LLM fails to respond, THE LLM Service SHALL return a fallback filename with timestamp

### Requirement 4

**User Story:** As a user, I want files to be renamed and moved to an Organized folder, so that my Downloads folder stays clean and files are easy to find.

#### Acceptance Criteria

1. WHEN a descriptive filename is generated, THE File Organizer SHALL sanitize the filename to remove invalid characters
2. WHEN the sanitized filename is ready, THE File Organizer SHALL rename the file while preserving the original extension
3. WHEN the file is renamed, THE File Organizer SHALL move the file to the Organized folder
4. WHEN the Organized folder does not exist, THE File Organizer SHALL create the folder before moving files
5. WHEN a file with the same name exists in the Organized folder, THE File Organizer SHALL append a numeric suffix to avoid overwriting

### Requirement 5

**User Story:** As a user, I want the system to handle errors gracefully when files are in use, so that the system continues operating without crashes.

#### Acceptance Criteria

1. WHEN a file is currently open by another process, THE File Organizer SHALL detect the permission error
2. WHEN a permission error occurs, THE File Organizer SHALL retry the operation up to 3 times with 2-second delays
3. WHEN all retry attempts fail, THE File Organizer SHALL log the error and skip the file
4. WHEN a file is deleted before processing completes, THE File Organizer SHALL handle the missing file error gracefully
5. WHEN any unexpected error occurs, THE File Organizer SHALL log the error with full details and continue monitoring

### Requirement 6

**User Story:** As a user, I want the system to log its operations, so that I can understand what actions were taken and troubleshoot issues.

#### Acceptance Criteria

1. WHEN a file is detected, THE File Monitor SHALL log the filename and detection timestamp
2. WHEN text extraction completes, THE Text Extractor SHALL log the number of characters extracted
3. WHEN a filename is generated, THE LLM Service SHALL log the original and generated filenames
4. WHEN a file is successfully organized, THE File Organizer SHALL log the final location
5. WHEN any error occurs, THE system SHALL log the error type, message, and affected filename

### Requirement 7

**User Story:** As a developer, I want the system to support both simulated and real LLM modes, so that I can test without requiring AWS credentials.

#### Acceptance Criteria

1. WHEN the system is configured for simulated mode, THE LLM Service SHALL use a dummy function for filename generation
2. WHEN the system is configured for Bedrock mode, THE LLM Service SHALL use boto3 to call Amazon Bedrock
3. WHEN Bedrock credentials are not available, THE LLM Service SHALL fall back to simulated mode automatically
4. WHEN switching between modes, THE system SHALL not require code changes, only configuration updates
5. WHEN in simulated mode, THE LLM Service SHALL generate filenames using keyword extraction from the Content Sample
