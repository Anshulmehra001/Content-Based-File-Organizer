"""Unit tests for FileProcessor orchestrator."""

import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

from src.file_processor import FileProcessor, FileProcessorError
from src.text_extractor import TextExtractionError
from src.llm_service import LLMServiceError
from src.file_organizer import FileOrganizerError


class TestFileProcessor:
    """Test suite for FileProcessor class."""
    
    @pytest.fixture
    def mock_extractor(self):
        """Create a mock TextExtractor."""
        extractor = Mock()
        extractor.extract_text = Mock(return_value="Sample content for testing")
        return extractor
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLMService."""
        llm_service = Mock()
        llm_service.generate_filename = Mock(return_value="Generated_Filename")
        return llm_service
    
    @pytest.fixture
    def mock_organizer(self):
        """Create a mock FileOrganizer."""
        organizer = Mock()
        organizer.organize_file = Mock(return_value=True)
        return organizer
    
    @pytest.fixture
    def processor(self, mock_extractor, mock_llm_service, mock_organizer):
        """Create a FileProcessor with mocked components."""
        return FileProcessor(mock_extractor, mock_llm_service, mock_organizer)
    
    def test_process_file_success(self, processor, mock_extractor, mock_llm_service, mock_organizer):
        """Test successful file processing through complete pipeline."""
        file_path = "/path/to/test_file.pdf"
        
        # Process the file
        processor.process_file(file_path)
        
        # Verify all components were called in order
        mock_extractor.extract_text.assert_called_once_with(file_path)
        mock_llm_service.generate_filename.assert_called_once_with(
            "Sample content for testing",
            original_filename="test_file.pdf"
        )
        mock_organizer.organize_file.assert_called_once_with(
            file_path,
            "Generated_Filename"
        )
    
    def test_process_file_with_extraction_error(
        self, processor, mock_extractor, mock_llm_service, mock_organizer
    ):
        """Test that processing continues with empty content when extraction fails."""
        file_path = "/path/to/corrupted.pdf"
        
        # Simulate extraction error
        mock_extractor.extract_text.side_effect = TextExtractionError("Corrupted PDF")
        
        # Process should continue with empty content
        processor.process_file(file_path)
        
        # Verify LLM service was called with empty content
        mock_llm_service.generate_filename.assert_called_once_with(
            "",
            original_filename="corrupted.pdf"
        )
        
        # Verify organizer was still called
        mock_organizer.organize_file.assert_called_once()
    
    def test_process_file_with_llm_error(
        self, processor, mock_extractor, mock_llm_service, mock_organizer
    ):
        """Test that processing fails when LLM service raises an error."""
        file_path = "/path/to/test.pdf"
        
        # Simulate LLM error
        mock_llm_service.generate_filename.side_effect = LLMServiceError("API failure")
        
        # Processing should raise FileProcessorError
        with pytest.raises(FileProcessorError, match="Failed to generate filename"):
            processor.process_file(file_path)
        
        # Verify organizer was not called
        mock_organizer.organize_file.assert_not_called()
    
    def test_process_file_with_organizer_error(
        self, processor, mock_extractor, mock_llm_service, mock_organizer
    ):
        """Test that processing fails when file organization fails."""
        file_path = "/path/to/test.pdf"
        
        # Simulate organizer error
        mock_organizer.organize_file.side_effect = FileOrganizerError("Permission denied")
        
        # Processing should raise FileProcessorError
        with pytest.raises(FileProcessorError, match="Failed to organize file"):
            processor.process_file(file_path)
    
    def test_process_file_logs_extraction_error(
        self, processor, mock_extractor, mock_llm_service, caplog
    ):
        """Test that extraction errors are logged with proper details."""
        file_path = "/path/to/bad.pdf"
        
        # Simulate extraction error
        mock_extractor.extract_text.side_effect = TextExtractionError("Cannot read PDF")
        
        with caplog.at_level(logging.ERROR):
            processor.process_file(file_path)
        
        # Verify error was logged
        assert "Text extraction failed" in caplog.text
        assert "TextExtractionError" in caplog.text
        assert "bad.pdf" in caplog.text
    
    def test_process_file_logs_llm_error(
        self, processor, mock_extractor, mock_llm_service, caplog
    ):
        """Test that LLM errors are logged with proper details."""
        file_path = "/path/to/test.pdf"
        
        # Simulate LLM error
        mock_llm_service.generate_filename.side_effect = LLMServiceError("Bedrock timeout")
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileProcessorError):
                processor.process_file(file_path)
        
        # Verify error was logged
        assert "Filename generation failed" in caplog.text
        assert "LLMServiceError" in caplog.text
        assert "test.pdf" in caplog.text
    
    def test_process_file_logs_organizer_error(
        self, processor, mock_extractor, mock_llm_service, mock_organizer, caplog
    ):
        """Test that organizer errors are logged with proper details."""
        file_path = "/path/to/test.pdf"
        
        # Simulate organizer error
        mock_organizer.organize_file.side_effect = FileOrganizerError("Disk full")
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileProcessorError):
                processor.process_file(file_path)
        
        # Verify error was logged
        assert "File organization failed" in caplog.text
        assert "FileOrganizerError" in caplog.text
        assert "test.pdf" in caplog.text
    
    def test_process_file_logs_success(
        self, processor, mock_extractor, mock_llm_service, mock_organizer, caplog
    ):
        """Test that successful processing is logged."""
        file_path = "/path/to/document.pdf"
        
        with caplog.at_level(logging.INFO):
            processor.process_file(file_path)
        
        # Verify success was logged
        assert "Processing file: document.pdf" in caplog.text
        assert "Successfully processed" in caplog.text
    
    def test_process_file_handles_unexpected_errors(
        self, processor, mock_extractor, mock_llm_service, mock_organizer
    ):
        """Test that unexpected errors are caught and wrapped."""
        file_path = "/path/to/test.pdf"
        
        # Simulate unexpected error
        mock_extractor.extract_text.side_effect = RuntimeError("Unexpected issue")
        
        # Should raise FileProcessorError
        with pytest.raises(FileProcessorError, match="Unexpected error"):
            processor.process_file(file_path)
    
    def test_process_file_with_empty_content(
        self, processor, mock_extractor, mock_llm_service, mock_organizer
    ):
        """Test processing with empty extracted content."""
        file_path = "/path/to/empty.txt"
        
        # Return empty content
        mock_extractor.extract_text.return_value = ""
        
        # Should still process successfully
        processor.process_file(file_path)
        
        # Verify LLM was called with empty content
        mock_llm_service.generate_filename.assert_called_once_with(
            "",
            original_filename="empty.txt"
        )
        
        # Verify organizer was called
        mock_organizer.organize_file.assert_called_once()
    
    def test_process_file_passes_original_filename_to_llm(
        self, processor, mock_extractor, mock_llm_service, mock_organizer
    ):
        """Test that original filename is passed to LLM service for logging."""
        file_path = "/downloads/important_document.pdf"
        
        processor.process_file(file_path)
        
        # Verify original filename was passed
        call_args = mock_llm_service.generate_filename.call_args
        assert call_args[1]['original_filename'] == "important_document.pdf"
    
    def test_process_file_recovery_after_extraction_error(
        self, processor, mock_extractor, mock_llm_service, mock_organizer
    ):
        """Test that processing recovers and continues after extraction error."""
        file_path = "/path/to/problematic.pdf"
        
        # Simulate extraction error
        mock_extractor.extract_text.side_effect = TextExtractionError("Read error")
        
        # Process should complete without raising
        processor.process_file(file_path)
        
        # Verify all subsequent steps were executed
        assert mock_llm_service.generate_filename.called
        assert mock_organizer.organize_file.called
