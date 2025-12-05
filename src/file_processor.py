"""File processor orchestrator that coordinates the complete processing pipeline."""

import logging
from pathlib import Path
from typing import Optional

from src.text_extractor import TextExtractor, TextExtractionError
from src.llm_service import LLMService, LLMServiceError
from src.file_organizer import FileOrganizer, FileOrganizerError


logger = logging.getLogger(__name__)


class FileProcessorError(Exception):
    """Raised when file processing encounters an error."""
    pass


class FileProcessor:
    """Orchestrates the complete file processing pipeline.
    
    Coordinates text extraction, LLM filename generation, and file organization.
    Ensures processing continues even after errors.
    """
    
    def __init__(
        self,
        extractor: TextExtractor,
        llm_service: LLMService,
        organizer: FileOrganizer
    ):
        """Initialize the file processor.
        
        Args:
            extractor: TextExtractor instance for extracting file content
            llm_service: LLMService instance for generating filenames
            organizer: FileOrganizer instance for organizing files
        """
        self.extractor = extractor
        self.llm_service = llm_service
        self.organizer = organizer
    
    def process_file(self, file_path: str) -> None:
        """Process a file through the complete pipeline.
        
        Steps:
        1. Extract text content from the file
        2. Generate descriptive filename using LLM
        3. Organize file with new name
        
        Processing continues even if errors occur at any stage.
        
        Args:
            file_path: Path to the file to process
        """
        path = Path(file_path)
        original_filename = path.name
        
        logger.info(f"Processing file: {original_filename}")
        
        try:
            # Step 1: Extract text content
            try:
                content_sample = self.extractor.extract_text(file_path)
                logger.debug(f"Extracted {len(content_sample)} characters from {original_filename}")
            except TextExtractionError as e:
                logger.error(
                    f"Text extraction failed - "
                    f"Type: {type(e).__name__}, Message: {e}, Filename: {original_filename}"
                )
                # Continue processing with empty content to trigger fallback naming
                content_sample = ""
            
            # Step 2: Generate descriptive filename
            try:
                new_name = self.llm_service.generate_filename(
                    content_sample,
                    original_filename=original_filename
                )
                logger.debug(f"Generated filename: {new_name} for {original_filename}")
            except LLMServiceError as e:
                logger.error(
                    f"Filename generation failed - "
                    f"Type: {type(e).__name__}, Message: {e}, Filename: {original_filename}"
                )
                # LLM service should have fallback, but if it raises, we need to handle it
                raise FileProcessorError(f"Failed to generate filename: {e}")
            
            # Step 3: Organize the file
            try:
                self.organizer.organize_file(file_path, new_name)
                logger.info(f"Successfully processed: {original_filename} -> {new_name}")
            except FileOrganizerError as e:
                logger.error(
                    f"File organization failed - "
                    f"Type: {type(e).__name__}, Message: {e}, Filename: {original_filename}"
                )
                raise FileProcessorError(f"Failed to organize file: {e}")
        
        except FileProcessorError:
            # Re-raise FileProcessorError to indicate processing failure
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.error(
                f"Unexpected error during processing - "
                f"Type: {type(e).__name__}, Message: {e}, Filename: {original_filename}"
            )
            raise FileProcessorError(f"Unexpected error: {e}")
