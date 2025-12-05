# Implementation Plan

- [x] 1. Set up project structure and dependencies





  - Create directory structure for the project (src, tests, config)
  - Create requirements.txt with all dependencies (watchdog, PyPDF2, boto3, pytest, hypothesis, pyyaml)
  - Create setup.py or pyproject.toml for package configuration
  - Create basic configuration file (config.yaml) with default settings
  - _Requirements: 7.4_

- [x] 2. Implement configuration management





  - Create Config class to load settings from YAML and environment variables
  - Implement validation for configuration values
  - Add support for default values and overrides
  - _Requirements: 7.1, 7.2, 7.4_

- [x] 2.1 Write unit tests for configuration loading


  - Test YAML parsing
  - Test environment variable overrides
  - Test validation logic
  - _Requirements: 7.4_

- [x] 3. Implement TextExtractor component


  - Create TextExtractor class with extract_text method
  - Implement PDF text extraction using PyPDF2
  - Implement text file reading with UTF-8 encoding
  - Add 1000-character truncation logic
  - Implement encoding fallback for text files (UTF-8, Latin-1, CP1252)
  - Add error handling for corrupted PDFs and encoding issues
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3.1 Write property test for text extraction length constraint


  - **Property 2: Text extraction length constraint**
  - **Validates: Requirements 2.3**



- [x] 3.2 Write unit tests for TextExtractor



  - Test PDF extraction with sample files
  - Test text file reading
  - Test encoding fallback logic
  - Test error handling for corrupted files
  - _Requirements: 2.1, 2.2, 2.4, 2.5_

- [x] 4. Implement LLMService component




  - Create LLMService class with mode selection (simulated/bedrock)
  - Implement simulated mode with keyword extraction heuristics
  - Implement Bedrock mode using boto3
  - Add fallback to timestamp-based naming on errors
  - Implement automatic fallback to simulated mode when credentials unavailable
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.1, 7.2, 7.3_

- [x] 4.1 Write property test for simulated mode filename generation


  - **Property 7: Simulated mode generates valid filenames**
  - **Validates: Requirements 7.5**

- [x] 4.2 Write unit tests for LLMService


  - Test simulated mode with various content samples
  - Test Bedrock mode with mocked boto3
  - Test fallback behavior
  - Test credential detection and mode switching
  - _Requirements: 3.3, 3.4, 3.5, 7.3_

- [x] 5. Implement FileOrganizer component

  - Create FileOrganizer class with organize_file method
  - Implement filename sanitization to remove invalid characters
  - Implement extension preservation logic
  - Implement file moving to Organized folder
  - Add directory creation if Organized folder doesn't exist
  - Implement conflict resolution with numeric suffixes
  - Add retry logic for permission errors (3 attempts, 2-second delays)
  - Add error handling for file not found and disk errors
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4_

- [x] 5.1 Write property test for filename sanitization


  - **Property 4: Filename sanitization removes invalid characters**
  - **Validates: Requirements 4.1**

- [x] 5.2 Write property test for extension preservation


  - **Property 3: Extension preservation during organization**
  - **Validates: Requirements 4.2**

- [x] 5.3 Write property test for conflict resolution


  - **Property 5: Conflict resolution with numeric suffixes**
  - **Validates: Requirements 4.5**

- [x] 5.4 Write property test for file organization location


  - **Property 6: File organization moves to correct location**
  - **Validates: Requirements 4.3**

- [x] 5.5 Write unit tests for FileOrganizer


  - Test sanitization with various invalid characters
  - Test conflict resolution
  - Test retry logic
  - Test directory creation
  - _Requirements: 4.1, 4.4, 4.5, 5.2_

- [x] 6. Implement logging system





  - Set up Python logging with configurable levels
  - Add logging to TextExtractor (character count)
  - Add logging to LLMService (original and generated filenames)
  - Add logging to FileOrganizer (final location)
  - Add error logging with full details (type, message, filename)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6.1 Write property test for detection logging


  - **Property 8: Detection logging includes required information**
  - **Validates: Requirements 6.1**

- [x] 6.2 Write property test for extraction logging

  - **Property 9: Extraction logging includes character count**
  - **Validates: Requirements 6.2**

- [x] 6.3 Write property test for organization logging

  - **Property 10: Organization logging includes final location**
  - **Validates: Requirements 6.4**

- [x] 6.4 Write property test for error logging

  - **Property 11: Error logging includes complete details**
  - **Validates: Requirements 6.5**
-

- [x] 7. Implement FileProcessor orchestrator




  - Create FileProcessor class to coordinate the pipeline
  - Implement process_file method that calls extractor, LLM service, and organizer
  - Add comprehensive error handling and logging
  - Ensure processing continues even after errors
  - _Requirements: 5.5_

- [x] 7.1 Write unit tests for FileProcessor


  - Test complete pipeline with mocked components
  - Test error handling and recovery
  - _Requirements: 5.5_

- [x] 8. Implement FileMonitor component





  - Create FileMonitor class using watchdog Observer
  - Implement file type filtering (PDF and text only)
  - Add event handler to trigger FileProcessor
  - Implement Downloads folder creation if it doesn't exist
  - Add start and stop methods for the monitor
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 8.1 Write property test for file type identification and filtering


  - **Property 1: File type identification and filtering**
  - **Validates: Requirements 1.3, 1.4**

- [x] 8.2 Write unit tests for FileMonitor


  - Test file type filtering
  - Test event detection
  - Test directory creation
  - _Requirements: 1.3, 1.4, 1.5_

- [x] 9. Create main application entry point





  - Create main.py with argument parsing (--config, --llm-mode)
  - Initialize all components with configuration
  - Start FileMonitor and keep application running
  - Add graceful shutdown handling (Ctrl+C)
  - _Requirements: 1.1_

- [x] 9.1 Write integration tests for complete system


  - Test end-to-end pipeline with real files
  - Test with both simulated and mocked Bedrock modes
  - Test error scenarios
  - _Requirements: 1.1, 1.2_

- [x] 10. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
-

- [x] 11. Create documentation and examples




  - Create README.md with setup instructions
  - Add usage examples for both simulated and Bedrock modes
  - Document configuration options
  - Add troubleshooting section
  - _Requirements: 7.4_

- [x] 12. Final checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
