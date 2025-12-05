"""
Unit tests for FileOrganizer component.
"""

import os
import tempfile
import time
from pathlib import Path
import pytest
from src.file_organizer import FileOrganizer, FileOrganizerError


class TestFilenameSanitization:
    """Tests for filename sanitization."""
    
    def test_sanitize_removes_forward_slash(self):
        """Test that forward slashes are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("file/name")
        assert "/" not in result
        assert result == "filename"
    
    def test_sanitize_removes_backslash(self):
        """Test that backslashes are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("file\\name")
        assert "\\" not in result
        assert result == "filename"
    
    def test_sanitize_removes_colon(self):
        """Test that colons are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("file:name")
        assert ":" not in result
        assert result == "filename"
    
    def test_sanitize_removes_asterisk(self):
        """Test that asterisks are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("file*name")
        assert "*" not in result
        assert result == "filename"
    
    def test_sanitize_removes_question_mark(self):
        """Test that question marks are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("file?name")
        assert "?" not in result
        assert result == "filename"
    
    def test_sanitize_removes_quotes(self):
        """Test that quotes are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename('file"name')
        assert '"' not in result
        assert result == "filename"
    
    def test_sanitize_removes_angle_brackets(self):
        """Test that angle brackets are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("file<>name")
        assert "<" not in result
        assert ">" not in result
        assert result == "filename"
    
    def test_sanitize_removes_pipe(self):
        """Test that pipes are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("file|name")
        assert "|" not in result
        assert result == "filename"
    
    def test_sanitize_removes_control_characters(self):
        """Test that control characters are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("file\x00\x1fname")
        assert "\x00" not in result
        assert "\x1f" not in result
        assert result == "filename"
    
    def test_sanitize_strips_leading_trailing_spaces(self):
        """Test that leading and trailing spaces are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("  filename  ")
        assert result == "filename"
    
    def test_sanitize_strips_leading_trailing_dots(self):
        """Test that leading and trailing dots are removed."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("..filename..")
        assert result == "filename"
    
    def test_sanitize_empty_string_returns_unnamed(self):
        """Test that empty string after sanitization returns 'unnamed'."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("///")
        assert result == "unnamed"
    
    def test_sanitize_only_spaces_returns_unnamed(self):
        """Test that only spaces returns 'unnamed'."""
        organizer = FileOrganizer("/tmp/organized")
        result = organizer._sanitize_filename("   ")
        assert result == "unnamed"


class TestConflictResolution:
    """Tests for filename conflict resolution."""
    
    def test_no_conflict_returns_original_path(self):
        """Test that when no conflict exists, original path is returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            organizer = FileOrganizer(tmpdir)
            target_path = Path(tmpdir) / "test.txt"
            result = organizer._handle_conflict(target_path)
            assert result == target_path
    
    def test_conflict_appends_numeric_suffix(self):
        """Test that conflicts result in numeric suffix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            organizer = FileOrganizer(tmpdir)
            
            # Create existing file
            existing = Path(tmpdir) / "test.txt"
            existing.write_text("existing")
            
            # Check conflict resolution
            target_path = Path(tmpdir) / "test.txt"
            result = organizer._handle_conflict(target_path)
            
            assert result != target_path
            assert result.name == "test_1.txt"
    
    def test_multiple_conflicts_increment_suffix(self):
        """Test that multiple conflicts increment the suffix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            organizer = FileOrganizer(tmpdir)
            
            # Create multiple existing files
            (Path(tmpdir) / "test.txt").write_text("1")
            (Path(tmpdir) / "test_1.txt").write_text("2")
            (Path(tmpdir) / "test_2.txt").write_text("3")
            
            # Check conflict resolution
            target_path = Path(tmpdir) / "test.txt"
            result = organizer._handle_conflict(target_path)
            
            assert result.name == "test_3.txt"


class TestDirectoryCreation:
    """Tests for directory creation."""
    
    def test_organize_creates_directory_if_not_exists(self):
        """Test that organized directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "test.txt"
            source_file.write_text("content")
            
            organized_dir = Path(tmpdir) / "organized"
            assert not organized_dir.exists()
            
            organizer = FileOrganizer(str(organized_dir))
            organizer.organize_file(str(source_file), "newname")
            
            assert organized_dir.exists()
            assert organized_dir.is_dir()


class TestRetryLogic:
    """Tests for retry logic on permission errors."""
    
    def test_organize_raises_error_on_missing_file(self):
        """Test that organizing a non-existent file raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            organizer = FileOrganizer(tmpdir)
            
            with pytest.raises(FileOrganizerError, match="File not found"):
                organizer.organize_file("/nonexistent/file.txt", "newname")


class TestFileOrganization:
    """Integration tests for complete file organization."""
    
    def test_organize_file_success(self):
        """Test successful file organization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "original.pdf"
            source_file.write_text("content")
            
            organized_dir = Path(tmpdir) / "organized"
            organizer = FileOrganizer(str(organized_dir))
            
            success = organizer.organize_file(str(source_file), "new_name")
            
            assert success
            assert not source_file.exists()
            assert (organized_dir / "new_name.pdf").exists()
    
    def test_organize_preserves_extension(self):
        """Test that file extension is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "original.txt"
            source_file.write_text("content")
            
            organized_dir = Path(tmpdir) / "organized"
            organizer = FileOrganizer(str(organized_dir))
            
            organizer.organize_file(str(source_file), "new_name")
            
            assert (organized_dir / "new_name.txt").exists()
    
    def test_organize_sanitizes_filename(self):
        """Test that filename is sanitized during organization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "original.pdf"
            source_file.write_text("content")
            
            organized_dir = Path(tmpdir) / "organized"
            organizer = FileOrganizer(str(organized_dir))
            
            organizer.organize_file(str(source_file), "bad/file*name")
            
            # Should sanitize to "badfilename"
            assert (organized_dir / "badfilename.pdf").exists()
