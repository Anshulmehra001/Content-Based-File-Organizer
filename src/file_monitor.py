"""File monitoring component using watchdog for detecting new files."""

import logging
import time
from pathlib import Path
from typing import Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from src.file_processor import FileProcessor


logger = logging.getLogger(__name__)


class FileMonitorError(Exception):
    """Raised when file monitoring encounters an error."""
    pass


class FileEventHandler(FileSystemEventHandler):
    """Handles file system events for the FileMonitor."""
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.text'}
    
    def __init__(self, processor: FileProcessor):
        """Initialize the event handler.
        
        Args:
            processor: FileProcessor instance to handle detected files
        """
        super().__init__()
        self.processor = processor
    
    def on_created(self, event):
        """Handle file creation events.
        
        Args:
            event: FileSystemEvent from watchdog
        """
        # Ignore directory creation events
        if event.is_directory:
            return
        
        file_path = event.src_path
        path = Path(file_path)
        
        # Log detection with timestamp
        logger.info(f"File detected: {path.name}")
        
        # Check file type by extension
        extension = path.suffix.lower()
        
        if extension in self.SUPPORTED_EXTENSIONS:
            logger.info(f"Processing {extension} file: {path.name}")
            try:
                # Small delay to ensure file is fully written
                time.sleep(0.5)
                self.processor.process_file(file_path)
            except Exception as e:
                logger.error(
                    f"Error processing file - "
                    f"Type: {type(e).__name__}, Message: {e}, Filename: {path.name}"
                )
        else:
            logger.debug(f"Ignoring non-supported file type: {extension}")


class FileMonitor:
    """Monitors a directory for new PDF and text files.
    
    Uses watchdog's Observer pattern to detect file creation events
    and triggers processing for supported file types.
    """
    
    def __init__(self, downloads_path: str, processor: FileProcessor):
        """Initialize the file monitor.
        
        Args:
            downloads_path: Path to the downloads folder to monitor
            processor: FileProcessor instance to handle detected files
        """
        self.downloads_path = Path(downloads_path).expanduser()
        self.processor = processor
        self.observer = None
        self.event_handler = FileEventHandler(processor)
    
    def start(self) -> None:
        """Start monitoring the downloads folder.
        
        Creates the downloads folder if it doesn't exist and begins
        watching for file creation events.
        
        Raises:
            FileMonitorError: If monitoring fails to start
        """
        try:
            # Create downloads folder if it doesn't exist
            self.downloads_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Downloads folder ready: {self.downloads_path}")
            
            # Create and start observer
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler,
                str(self.downloads_path),
                recursive=False
            )
            self.observer.start()
            
            logger.info(f"File monitoring started for: {self.downloads_path}")
            
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
            raise FileMonitorError(f"Failed to start monitoring: {e}")
    
    def stop(self) -> None:
        """Stop monitoring the downloads folder.
        
        Gracefully stops the observer and waits for it to finish.
        """
        if self.observer and self.observer.is_alive():
            logger.info("Stopping file monitor...")
            self.observer.stop()
            self.observer.join(timeout=5)
            logger.info("File monitor stopped")
