"""Integration tests for the complete Content-Based File Organizer system."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from src.config import Config
from src.text_extractor import TextExtractor
from src.llm_service import LLMService
from src.file_organizer import FileOrganizer
from src.file_processor import FileProcessor
from src.file_monitor import FileMonitor


class TestEndToEndPipeline:
    """Test the complete pipeline from file detection to organization."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as downloads_dir:
            organized_dir = Path(downloads_dir) / "Organized"
            yield Path(downloads_dir), organized_dir
    
    @pytest.fixture
    def components(self, temp_dirs):
        """Initialize all system components."""
        downloads_dir, organized_dir = temp_dirs
        
        extractor = TextExtractor(max_length=1000)
        llm_service = LLMService(mode="simulated")
        organizer = FileOrganizer(organized_path=str(organized_dir))
        processor = FileProcessor(
            extractor=extractor,
            llm_service=llm_service,
            organizer=organizer
        )
        
        return {
            'extractor': extractor,
            'llm_service': llm_service,
            'organizer': organizer,
            'processor': processor,
            'downloads_dir': downloads_dir,
            'organized_dir': organized_dir
        }
    
    def create_test_pdf(self, file_path: Path, content: str) -> None:
        """Create a test PDF file with given content.
        
        Args:
            file_path: Path where PDF should be created
            content: Text content to include in PDF
        """
        c = canvas.Canvas(str(file_path), pagesize=letter)
        c.drawString(100, 750, content)
        c.save()
    
    def create_test_text_file(self, file_path: Path, content: str) -> None:
        """Create a test text file with given content.
        
        Args:
            file_path: Path where text file should be created
            content: Text content to write
        """
        file_path.write_text(content, encoding='utf-8')
    
    def test_complete_pipeline_with_pdf(self, components):
        """Test end-to-end processing of a PDF file."""
        downloads_dir = components['downloads_dir']
        organized_dir = components['organized_dir']
        processor = components['processor']
        
        # Create a test PDF
        pdf_path = downloads_dir / "test_document.pdf"
        content = "This is a test document about machine learning and artificial intelligence"
        self.create_test_pdf(pdf_path, content)
        
        # Process the file
        processor.process_file(str(pdf_path))
        
        # Verify file was moved to organized folder
        assert not pdf_path.exists(), "Original file should be moved"
        assert organized_dir.exists(), "Organized folder should be created"
        
        # Check that a PDF file exists in organized folder
        organized_files = list(organized_dir.glob("*.pdf"))
        assert len(organized_files) == 1, "Exactly one PDF should be in organized folder"
        
        # Verify the file has a descriptive name (not the original name)
        organized_file = organized_files[0]
        assert organized_file.name != "test_document.pdf", "File should be renamed"
        assert organized_file.suffix == ".pdf", "Extension should be preserved"
    
    def test_complete_pipeline_with_text_file(self, components):
        """Test end-to-end processing of a text file."""
        downloads_dir = components['downloads_dir']
        organized_dir = components['organized_dir']
        processor = components['processor']
        
        # Create a test text file
        txt_path = downloads_dir / "notes.txt"
        content = "Important meeting notes about project planning and development strategy"
        self.create_test_text_file(txt_path, content)
        
        # Process the file
        processor.process_file(str(txt_path))
        
        # Verify file was moved to organized folder
        assert not txt_path.exists(), "Original file should be moved"
        assert organized_dir.exists(), "Organized folder should be created"
        
        # Check that a text file exists in organized folder
        organized_files = list(organized_dir.glob("*.txt"))
        assert len(organized_files) == 1, "Exactly one text file should be in organized folder"
        
        # Verify the file has a descriptive name
        organized_file = organized_files[0]
        assert organized_file.name != "notes.txt", "File should be renamed"
        assert organized_file.suffix == ".txt", "Extension should be preserved"
    
    def test_simulated_mode_processing(self, components):
        """Test processing with simulated LLM mode."""
        downloads_dir = components['downloads_dir']
        organized_dir = components['organized_dir']
        processor = components['processor']
        
        # Verify we're in simulated mode
        assert components['llm_service'].mode == "simulated"
        
        # Create and process a file
        txt_path = downloads_dir / "document.txt"
        content = "Python programming tutorial for beginners learning software development"
        self.create_test_text_file(txt_path, content)
        
        processor.process_file(str(txt_path))
        
        # Verify processing succeeded
        assert not txt_path.exists()
        organized_files = list(organized_dir.glob("*.txt"))
        assert len(organized_files) == 1
        
        # Verify filename contains keywords from content
        organized_file = organized_files[0]
        filename_lower = organized_file.stem.lower()
        # Should contain some keywords from the content
        assert any(keyword in filename_lower for keyword in ['python', 'programming', 'tutorial', 'beginners', 'learning', 'software', 'development'])
    
    def test_mocked_bedrock_mode_processing(self, components):
        """Test processing with mocked Bedrock mode."""
        downloads_dir = components['downloads_dir']
        organized_dir = components['organized_dir']
        
        # Create LLM service in bedrock mode with mocked client
        with patch('boto3.client') as mock_boto_client:
            # Mock Bedrock response
            mock_client = Mock()
            mock_response = {
                'body': Mock()
            }
            mock_response['body'].read.return_value = b'{"completion": "Financial_Report_Q4"}'
            mock_client.invoke_model.return_value = mock_response
            mock_boto_client.return_value = mock_client
            
            # Create LLM service with bedrock mode
            llm_service = LLMService(
                mode="bedrock",
                bedrock_model="anthropic.claude-v2",
                bedrock_region="us-east-1"
            )
            llm_service._bedrock_client = mock_client
            
            # Create processor with bedrock LLM service
            processor = FileProcessor(
                extractor=components['extractor'],
                llm_service=llm_service,
                organizer=components['organizer']
            )
            
            # Create and process a file
            txt_path = downloads_dir / "report.txt"
            content = "Quarterly financial report showing revenue growth and profit margins"
            self.create_test_text_file(txt_path, content)
            
            processor.process_file(str(txt_path))
            
            # Verify Bedrock was called
            assert mock_client.invoke_model.called
            
            # Verify file was processed
            assert not txt_path.exists()
            organized_files = list(organized_dir.glob("*.txt"))
            assert len(organized_files) == 1
            
            # Verify filename matches Bedrock response
            organized_file = organized_files[0]
            assert "Financial_Report_Q4" in organized_file.stem


class TestErrorScenarios:
    """Test error handling in the complete system."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as downloads_dir:
            organized_dir = Path(downloads_dir) / "Organized"
            yield Path(downloads_dir), organized_dir
    
    @pytest.fixture
    def components(self, temp_dirs):
        """Initialize all system components."""
        downloads_dir, organized_dir = temp_dirs
        
        extractor = TextExtractor(max_length=1000)
        llm_service = LLMService(mode="simulated")
        organizer = FileOrganizer(organized_path=str(organized_dir))
        processor = FileProcessor(
            extractor=extractor,
            llm_service=llm_service,
            organizer=organizer
        )
        
        return {
            'extractor': extractor,
            'llm_service': llm_service,
            'organizer': organizer,
            'processor': processor,
            'downloads_dir': downloads_dir,
            'organized_dir': organized_dir
        }
    
    def test_empty_file_processing(self, components):
        """Test processing of an empty file."""
        downloads_dir = components['downloads_dir']
        organized_dir = components['organized_dir']
        processor = components['processor']
        
        # Create an empty text file
        txt_path = downloads_dir / "empty.txt"
        txt_path.write_text("", encoding='utf-8')
        
        # Process should succeed with fallback naming
        processor.process_file(str(txt_path))
        
        # Verify file was still processed
        assert not txt_path.exists()
        organized_files = list(organized_dir.glob("*.txt"))
        assert len(organized_files) == 1
        
        # Should use fallback naming (timestamp-based)
        organized_file = organized_files[0]
        assert "document_" in organized_file.stem
    
    def test_corrupted_pdf_processing(self, components):
        """Test processing of a corrupted PDF file."""
        downloads_dir = components['downloads_dir']
        organized_dir = components['organized_dir']
        processor = components['processor']
        
        # Create a fake corrupted PDF (just text content with .pdf extension)
        pdf_path = downloads_dir / "corrupted.pdf"
        pdf_path.write_text("This is not a valid PDF file", encoding='utf-8')
        
        # Processing should handle the error gracefully
        # The extractor will fail, but processor should continue with fallback
        processor.process_file(str(pdf_path))
        
        # File should still be organized with fallback name
        assert not pdf_path.exists()
        organized_files = list(organized_dir.glob("*.pdf"))
        assert len(organized_files) == 1
    
    def test_file_conflict_resolution(self, components):
        """Test handling of filename conflicts."""
        downloads_dir = components['downloads_dir']
        organized_dir = components['organized_dir']
        processor = components['processor']
        
        # Create first file
        txt_path1 = downloads_dir / "doc1.txt"
        content = "Python programming tutorial"
        txt_path1.write_text(content, encoding='utf-8')
        
        processor.process_file(str(txt_path1))
        
        # Create second file with same content (will generate same name)
        txt_path2 = downloads_dir / "doc2.txt"
        txt_path2.write_text(content, encoding='utf-8')
        
        processor.process_file(str(txt_path2))
        
        # Both files should be in organized folder with different names
        organized_files = list(organized_dir.glob("*.txt"))
        assert len(organized_files) == 2, "Both files should be organized"
        
        # Verify names are different (one should have numeric suffix)
        names = [f.name for f in organized_files]
        assert len(set(names)) == 2, "Files should have unique names"
    
    def test_missing_file_error(self, components):
        """Test handling of missing file error."""
        processor = components['processor']
        
        # Try to process a non-existent file
        from src.file_processor import FileProcessorError
        
        with pytest.raises(FileProcessorError):
            processor.process_file("/nonexistent/file.txt")


class TestFileMonitorIntegration:
    """Test FileMonitor integration with the processing pipeline."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as downloads_dir:
            organized_dir = Path(downloads_dir) / "Organized"
            yield Path(downloads_dir), organized_dir
    
    @pytest.fixture
    def monitor_components(self, temp_dirs):
        """Initialize components including FileMonitor."""
        downloads_dir, organized_dir = temp_dirs
        
        extractor = TextExtractor(max_length=1000)
        llm_service = LLMService(mode="simulated")
        organizer = FileOrganizer(organized_path=str(organized_dir))
        processor = FileProcessor(
            extractor=extractor,
            llm_service=llm_service,
            organizer=organizer
        )
        monitor = FileMonitor(
            downloads_path=str(downloads_dir),
            processor=processor
        )
        
        return {
            'monitor': monitor,
            'downloads_dir': downloads_dir,
            'organized_dir': organized_dir
        }
    
    def test_monitor_starts_and_stops(self, monitor_components):
        """Test that FileMonitor can start and stop cleanly."""
        monitor = monitor_components['monitor']
        
        # Start monitoring
        monitor.start()
        assert monitor.observer is not None
        assert monitor.observer.is_alive()
        
        # Stop monitoring
        monitor.stop()
        time.sleep(0.5)  # Give it time to stop
        assert not monitor.observer.is_alive()
    
    def test_monitor_creates_downloads_folder(self, monitor_components):
        """Test that FileMonitor creates downloads folder if missing."""
        monitor = monitor_components['monitor']
        downloads_dir = monitor_components['downloads_dir']
        
        # Remove the downloads directory
        if downloads_dir.exists():
            import shutil
            shutil.rmtree(downloads_dir)
        
        # Start monitoring should create it
        monitor.start()
        assert downloads_dir.exists()
        
        monitor.stop()
    
    def test_monitor_detects_and_processes_file(self, monitor_components):
        """Test that FileMonitor detects new files and processes them."""
        monitor = monitor_components['monitor']
        downloads_dir = monitor_components['downloads_dir']
        organized_dir = monitor_components['organized_dir']
        
        # Start monitoring
        monitor.start()
        
        # Create a new file in downloads
        txt_path = downloads_dir / "test_monitor.txt"
        txt_path.write_text("Test content for monitoring", encoding='utf-8')
        
        # Wait for processing (watchdog needs time to detect and process)
        time.sleep(2)
        
        # Stop monitoring
        monitor.stop()
        
        # Verify file was processed
        assert not txt_path.exists(), "File should be moved from downloads"
        
        # Check organized folder
        if organized_dir.exists():
            organized_files = list(organized_dir.glob("*.txt"))
            assert len(organized_files) >= 1, "File should be in organized folder"
