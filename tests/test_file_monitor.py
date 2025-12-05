"""Unit tests for FileMonitor component."""

import logging
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.file_monitor import FileMonitor, FileEventHandler, FileMonitorError
from src.file_processor import FileProcessor


# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestFileEventHandler:
    """Test FileEventHandler functionality."""
    
    def test_file_type_filtering_pdf(self):
        """Test that PDF files are processed."""
        mock_processor = Mock(spec=FileProcessor)
        handler = FileEventHandler(mock_processor)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a PDF file
            pdf_file = Path(temp_dir) / "test.pdf"
            pdf_file.write_text("test content")
            
            # Create mock event
            class MockEvent:
                def __init__(self, src_path):
                    self.src_path = src_path
                    self.is_directory = False
            
            event = MockEvent(str(pdf_file))
            
            # Trigger handler
            handler.on_created(event)
            
            # Small delay for processing
            time.sleep(0.6)
            
            # Verify processor was called
            mock_processor.process_file.assert_called_once()
    
    def test_file_type_filtering_txt(self):
        """Test that TXT files are processed."""
        mock_processor = Mock(spec=FileProcessor)
        handler = FileEventHandler(mock_processor)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a TXT file
            txt_file = Path(temp_dir) / "test.txt"
            txt_file.write_text("test content")
            
            class MockEvent:
                def __init__(self, src_path):
                    self.src_path = src_path
                    self.is_directory = False
            
            event = MockEvent(str(txt_file))
            handler.on_created(event)
            time.sleep(0.6)
            
            mock_processor.process_file.assert_called_once()
    
    def test_file_type_filtering_text_extension(self):
        """Test that .text files are processed."""
        mock_processor = Mock(spec=FileProcessor)
        handler = FileEventHandler(mock_processor)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .text file
            text_file = Path(temp_dir) / "test.text"
            text_file.write_text("test content")
            
            class MockEvent:
                def __init__(self, src_path):
                    self.src_path = src_path
                    self.is_directory = False
            
            event = MockEvent(str(text_file))
            handler.on_created(event)
            time.sleep(0.6)
            
            mock_processor.process_file.assert_called_once()
    
    def test_file_type_filtering_unsupported(self):
        """Test that unsupported file types are ignored."""
        mock_processor = Mock(spec=FileProcessor)
        handler = FileEventHandler(mock_processor)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create various unsupported files
            unsupported_files = [
                "test.doc",
                "test.docx",
                "test.jpg",
                "test.png",
                "test.zip"
            ]
            
            for filename in unsupported_files:
                file_path = Path(temp_dir) / filename
                file_path.write_text("test content")
                
                class MockEvent:
                    def __init__(self, src_path):
                        self.src_path = src_path
                        self.is_directory = False
                
                event = MockEvent(str(file_path))
                handler.on_created(event)
                time.sleep(0.1)
            
            # Verify processor was never called
            mock_processor.process_file.assert_not_called()
    
    def test_directory_events_ignored(self):
        """Test that directory creation events are ignored."""
        mock_processor = Mock(spec=FileProcessor)
        handler = FileEventHandler(mock_processor)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory
            test_dir = Path(temp_dir) / "test_directory"
            test_dir.mkdir()
            
            class MockEvent:
                def __init__(self, src_path):
                    self.src_path = src_path
                    self.is_directory = True
            
            event = MockEvent(str(test_dir))
            handler.on_created(event)
            
            # Verify processor was not called
            mock_processor.process_file.assert_not_called()
    
    def test_event_detection_logs_filename(self):
        """Test that file detection is logged with filename."""
        mock_processor = Mock(spec=FileProcessor)
        handler = FileEventHandler(mock_processor)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_file = Path(temp_dir) / "test_document.pdf"
            pdf_file.write_text("test content")
            
            class MockEvent:
                def __init__(self, src_path):
                    self.src_path = src_path
                    self.is_directory = False
            
            event = MockEvent(str(pdf_file))
            
            # Enable logging temporarily to capture log
            logging.disable(logging.NOTSET)
            with patch('src.file_monitor.logger') as mock_logger:
                handler.on_created(event)
                
                # Verify logging was called with filename
                mock_logger.info.assert_any_call("File detected: test_document.pdf")
            
            logging.disable(logging.CRITICAL)


class TestFileMonitor:
    """Test FileMonitor functionality."""
    
    def test_directory_creation(self):
        """Test that downloads folder is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_path = Path(temp_dir) / "downloads"
            
            # Verify directory doesn't exist yet
            assert not downloads_path.exists()
            
            mock_processor = Mock(spec=FileProcessor)
            monitor = FileMonitor(str(downloads_path), mock_processor)
            
            # Start monitoring
            monitor.start()
            
            # Verify directory was created
            assert downloads_path.exists()
            assert downloads_path.is_dir()
            
            # Clean up
            monitor.stop()
    
    def test_start_and_stop(self):
        """Test that monitor can be started and stopped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_path = Path(temp_dir) / "downloads"
            mock_processor = Mock(spec=FileProcessor)
            monitor = FileMonitor(str(downloads_path), mock_processor)
            
            # Start monitoring
            monitor.start()
            assert monitor.observer is not None
            assert monitor.observer.is_alive()
            
            # Stop monitoring
            monitor.stop()
            time.sleep(0.5)
            assert not monitor.observer.is_alive()
    
    def test_monitor_detects_new_files(self):
        """Test that monitor detects new files in the downloads folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_path = Path(temp_dir) / "downloads"
            mock_processor = Mock(spec=FileProcessor)
            monitor = FileMonitor(str(downloads_path), mock_processor)
            
            # Start monitoring
            monitor.start()
            time.sleep(0.5)  # Give observer time to start
            
            # Create a PDF file
            test_file = downloads_path / "test.pdf"
            test_file.write_text("test content")
            
            # Wait for event to be processed
            time.sleep(1.5)
            
            # Verify processor was called
            assert mock_processor.process_file.call_count >= 1
            
            # Clean up
            monitor.stop()
    
    def test_start_failure_handling(self):
        """Test that start method handles errors gracefully."""
        # Use an invalid path that will cause an error
        mock_processor = Mock(spec=FileProcessor)
        
        # Mock Path.mkdir to raise an exception
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
            monitor = FileMonitor("/invalid/path", mock_processor)
            
            with pytest.raises(FileMonitorError):
                monitor.start()
