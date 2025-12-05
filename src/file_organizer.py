"""
File organization module for renaming and moving files.
"""

import logging
import os
import re
import time
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class FileOrganizerError(Exception):
    """Base exception for FileOrganizer errors."""
    pass


class FileOrganizer:
    """
    Handles file organization including sanitization, renaming, and moving files.
    
    Attributes:
        organized_path: Path to the organized folder where files will be moved.
    """
    
    def __init__(self, organized_path: str):
        """
        Initialize FileOrganizer with destination path.
        
        Args:
            organized_path: Path to the organized folder.
        """
        self.organized_path = Path(organized_path).expanduser()
    
    def organize_file(self, file_path: str, new_name: str) -> bool:
        """
        Organize a file by sanitizing the name, preserving extension, and moving to organized folder.
        
        Args:
            file_path: Path to the file to organize.
            new_name: New name for the file (without extension).
        
        Returns:
            True if organization succeeded, False otherwise.
        
        Raises:
            FileOrganizerError: If file organization fails after retries.
        """
        source_path = Path(file_path)
        
        # Check if source file exists
        if not source_path.exists():
            logger.error(
                f"File not found - Type: FileNotFoundError, "
                f"Message: File does not exist, Filename: {file_path}"
            )
            raise FileOrganizerError(f"File not found: {file_path}")
        
        # Get original extension
        original_extension = source_path.suffix
        
        # Sanitize the new filename
        sanitized_name = self._sanitize_filename(new_name)
        
        # Preserve extension
        new_filename = f"{sanitized_name}{original_extension}"
        
        # Create organized folder if it doesn't exist
        self.organized_path.mkdir(parents=True, exist_ok=True)
        
        # Handle conflicts
        target_path = self.organized_path / new_filename
        target_path = self._handle_conflict(target_path)
        
        # Move file with retry logic
        success = self._move_with_retry(str(source_path), str(target_path))
        
        if success:
            logger.info(f"File organized successfully to: {target_path}")
        
        return success
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Remove invalid filesystem characters from filename.
        
        Args:
            filename: The filename to sanitize.
        
        Returns:
            Sanitized filename with invalid characters removed.
        """
        # Invalid characters for most filesystems: / \ : * ? " < > |
        # Also remove control characters (0x00-0x1F and 0x7F-0x9F)
        invalid_chars = r'[/\\:*?"<>|\x00-\x1f\x7f-\x9f]'
        sanitized = re.sub(invalid_chars, '', filename)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # If sanitization results in empty string, use default
        if not sanitized:
            sanitized = "unnamed"
        
        return sanitized
    
    def _handle_conflict(self, target_path: Path) -> Path:
        """
        Handle filename conflicts by appending numeric suffixes.
        
        Args:
            target_path: The target path that may conflict.
        
        Returns:
            A non-conflicting path with numeric suffix if needed.
        """
        if not target_path.exists():
            return target_path
        
        # Extract name and extension
        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        
        # Try numeric suffixes until we find a non-existing path
        counter = 1
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _move_with_retry(self, source: str, destination: str, retries: int = 3) -> bool:
        """
        Move file with retry logic for permission errors.
        
        Args:
            source: Source file path.
            destination: Destination file path.
            retries: Number of retry attempts (default: 3).
        
        Returns:
            True if move succeeded, False otherwise.
        """
        for attempt in range(retries):
            try:
                # Use os.rename for atomic move operation
                os.rename(source, destination)
                return True
            except PermissionError as e:
                if attempt < retries - 1:
                    logger.warning(
                        f"Permission error on attempt {attempt + 1}/{retries} for {source}, retrying..."
                    )
                    # Wait before retrying (2 seconds)
                    time.sleep(2)
                else:
                    # All retries exhausted
                    logger.error(
                        f"Permission error after {retries} attempts - "
                        f"Type: PermissionError, Message: {e}, Filename: {source}"
                    )
                    raise FileOrganizerError(
                        f"Permission error after {retries} attempts: {e}"
                    )
            except OSError as e:
                # Handle disk errors and other OS errors
                logger.error(
                    f"OS error during file move - "
                    f"Type: {type(e).__name__}, Message: {e}, Filename: {source}"
                )
                raise FileOrganizerError(f"OS error during file move: {e}")
        
        return False
