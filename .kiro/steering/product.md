# Product Overview

Content-Based File Organizer is an automated file organization system that monitors a downloads folder, extracts text content from files (PDF and text), and uses LLM-based analysis to generate meaningful filenames and organize files into appropriate folders.

## Key Features

- Monitors downloads folder for new PDF and text files
- Extracts text content from files (first 1000 characters)
- Uses LLM (simulated or AWS Bedrock) to generate descriptive filenames
- Automatically organizes files into categorized folders
- Configurable via YAML and environment variables
- Supports retry logic for robust processing

## Target Use Case

Automatically organize downloaded documents with meaningful names based on their content, eliminating manual file management overhead.
