"""Property-based tests for FileMonitor component."""

import logging
import tempfile
import time
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, settings

from src.file_monitor import FileMonitor, FileEventHandler
from src.file_processor import FileProcessor
from src.text_extractor import TextExtractor
from src.llm_service import LLMService
from src.file_organizer import FileOrganizer


# Disable logging during tests to reduce noise
logging.disable(logging.CRITICAL)


# Strategy for generating file extensions
@st.composite
def file_extension(draw):
    """Generate various file extensions."""
    # Mix of supported and unsupported extensions
    extensions = [
        '.pdf', '.txt', '.text',  # Supported
        '.doc', '.docx', '.jpg', '.png', '.zip', '.exe',  # Unsupported
        '.mp3', '.mp4', '.csv', '.json', '.xml', '.html'  # More unsupported
    ]
    return draw(st.sampled_from(extensions))


@st.composite
def filename_with_extension(draw):
    """Generate filenames with various extensions."""
    # Generate a base filename
    base = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=20
    ))
    ext = draw(file_extension())
    return f"{base}{ext}"


class TestFileTypeIdentificationAndFiltering:
    """Test file type identification and filtering properties."""
    
    # Feature: content-based-file-organizer, Property 1: File type identification and filtering
    # Validates: Requirements 1.3, 1.4
    @settings(max_examples=100, deadline=1000)  # 1 second deadline due to sleep in handler
    @given(filename=filename_with_extension())
    def test_file_type_filtering_property(self, filename):
        """
        Property: For any file added to the Downloads folder, the File Monitor should
        correctly identify its type by extension and only process PDF and text files
        while ignoring all other file types.
        
        This test verifies that:
        1. Supported file types (.pdf, .txt, .text) are identified correctly
        2. Unsupported file types are filtered out
        3. The event handler correctly determines which files to process
        """
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_path = Path(temp_dir) / "downloads"
            organized_path = Path(temp_dir) / "organized"
            downloads_path.mkdir()
            organized_path.mkdir()
            
            # Track which files were processed
            processed_files = []
            
            # Create a mock processor that tracks calls
            class MockProcessor:
                def process_file(self, file_path):
                    processed_files.append(file_path)
            
            mock_processor = MockProcessor()
            
            # Create event handler
            event_handler = FileEventHandler(mock_processor)
            
            # Create a test file
            test_file = downloads_path / filename
            test_file.write_text("test content")
            
            # Create a mock event
            class MockEvent:
                def __init__(self, src_path, is_directory=False):
                    self.src_path = src_path
                    self.is_directory = is_directory
            
            event = MockEvent(str(test_file), is_directory=False)
            
            # Trigger the event handler
            event_handler.on_created(event)
            
            # Small delay to allow processing
            time.sleep(0.1)
            
            # Get the file extension
            extension = Path(filename).suffix.lower()
            
            # Verify the property: only supported extensions should be processed
            supported_extensions = {'.pdf', '.txt', '.text'}
            
            if extension in supported_extensions:
                # File should have been processed
                assert len(processed_files) == 1, \
                    f"Supported file {filename} should be processed"
                assert str(test_file) in processed_files[0], \
                    f"Processed file path should match test file"
            else:
                # File should NOT have been processed
                assert len(processed_files) == 0, \
                    f"Unsupported file {filename} should be ignored"
    
    def test_directory_events_ignored(self):
        """Test that directory creation events are ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_path = Path(temp_dir) / "downloads"
            organized_path = Path(temp_dir) / "organized"
            downloads_path.mkdir()
            organized_path.mkdir()
            
            processed_files = []
            
            class MockProcessor:
                def process_file(self, file_path):
                    processed_files.append(file_path)
            
            mock_processor = MockProcessor()
            event_handler = FileEventHandler(mock_processor)
            
            # Create a directory
            test_dir = downloads_path / "test_directory"
            test_dir.mkdir()
            
            # Create mock directory event
            class MockEvent:
                def __init__(self, src_path, is_directory=True):
                    self.src_path = src_path
                    self.is_directory = is_directory
            
            event = MockEvent(str(test_dir), is_directory=True)
            
            # Trigger event handler
            event_handler.on_created(event)
            
            # Verify no processing occurred
            assert len(processed_files) == 0, \
                "Directory events should be ignored"
