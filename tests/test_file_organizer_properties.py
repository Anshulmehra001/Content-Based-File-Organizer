"""
Property-based tests for FileOrganizer component.
"""

import os
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings
from src.file_organizer import FileOrganizer


# Feature: content-based-file-organizer, Property 4: Filename sanitization removes invalid characters
# Validates: Requirements 4.1
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_sanitization_removes_invalid_characters(filename: str):
    """
    Property: For any generated filename containing invalid filesystem characters,
    the sanitization process should remove or replace these characters to produce a valid filename.
    """
    organizer = FileOrganizer("/tmp/organized")
    
    # Sanitize the filename
    sanitized = organizer._sanitize_filename(filename)
    
    # Invalid characters that should not appear in sanitized filename
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    # Check that no invalid characters remain
    for char in invalid_chars:
        assert char not in sanitized, f"Invalid character '{char}' found in sanitized filename"
    
    # Check that result is not empty (should default to "unnamed" if needed)
    assert len(sanitized) > 0, "Sanitized filename should not be empty"



# Feature: content-based-file-organizer, Property 3: Extension preservation during organization
# Validates: Requirements 4.2
@given(
    filename=st.text(min_size=1, max_size=50),
    extension=st.sampled_from(['.pdf', '.txt', '.doc', '.docx', '.jpg', '.png'])
)
@settings(max_examples=100)
def test_extension_preservation(filename: str, extension: str):
    """
    Property: For any file being organized, the FileOrganizer should preserve
    the original file extension in the renamed file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temporary file with the given extension
        source_dir = Path(tmpdir) / "source"
        source_dir.mkdir()
        source_file = source_dir / f"original{extension}"
        source_file.write_text("test content")
        
        # Create organizer with temp organized path
        organized_dir = Path(tmpdir) / "organized"
        organizer = FileOrganizer(str(organized_dir))
        
        # Organize the file (sanitization will handle any invalid characters in filename)
        success = organizer.organize_file(str(source_file), filename)
        
        # Check that organization succeeded
        assert success, "File organization should succeed"
        
        # Find the organized file
        organized_files = list(organized_dir.glob(f"*{extension}"))
        assert len(organized_files) > 0, "Organized file should exist"
        
        # Check that the extension is preserved
        organized_file = organized_files[0]
        assert organized_file.suffix == extension, f"Extension should be preserved as {extension}"



# Feature: content-based-file-organizer, Property 5: Conflict resolution with numeric suffixes
# Validates: Requirements 4.5
@given(
    filename=st.text(min_size=1, max_size=50),
    extension=st.sampled_from(['.pdf', '.txt']),
    num_conflicts=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100)
def test_conflict_resolution_with_numeric_suffixes(filename: str, extension: str, num_conflicts: int):
    """
    Property: For any file being moved to the Organized folder where a file with the same name
    already exists, the system should append a numeric suffix to create a unique filename.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        source_dir.mkdir()
        
        organized_dir = Path(tmpdir) / "organized"
        organizer = FileOrganizer(str(organized_dir))
        
        # Sanitize the filename to get what it will actually be
        sanitized = organizer._sanitize_filename(filename)
        expected_base = f"{sanitized}{extension}"
        
        # Create multiple files with the same desired name
        organized_files = []
        for i in range(num_conflicts):
            source_file = source_dir / f"file_{i}{extension}"
            source_file.write_text(f"content {i}")
            
            success = organizer.organize_file(str(source_file), filename)
            assert success, f"File organization should succeed for file {i}"
            
            # Find the newly created file
            all_files = sorted(organized_dir.glob(f"*{extension}"))
            organized_files.append(all_files[-1])
        
        # Check that we have the expected number of files
        assert len(organized_files) == num_conflicts, "Should have created all files"
        
        # Check that all filenames are unique
        filenames = [f.name for f in organized_files]
        assert len(filenames) == len(set(filenames)), "All filenames should be unique"
        
        # Check that the first file has the base name (or "unnamed" if sanitization resulted in empty)
        if sanitized == "unnamed":
            assert filenames[0] == f"unnamed{extension}", "First file should have base name"
        else:
            assert filenames[0] == expected_base or filenames[0].startswith(sanitized), \
                "First file should have base name or start with sanitized name"
        
        # Check that subsequent files have numeric suffixes
        if num_conflicts > 1:
            for i, fname in enumerate(filenames[1:], start=1):
                # Should contain a numeric suffix pattern
                assert '_' in fname or fname == expected_base, \
                    f"File {i} should have numeric suffix or be the base name"



# Feature: content-based-file-organizer, Property 6: File organization moves to correct location
# Validates: Requirements 4.3
@given(
    filename=st.text(min_size=1, max_size=50),
    extension=st.sampled_from(['.pdf', '.txt', '.doc'])
)
@settings(max_examples=100)
def test_file_organization_moves_to_correct_location(filename: str, extension: str):
    """
    Property: For any successfully processed file, the file should be moved from
    the source folder to the Organized folder.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create source file in a "downloads" directory
        downloads_dir = Path(tmpdir) / "downloads"
        downloads_dir.mkdir()
        source_file = downloads_dir / f"original{extension}"
        source_file.write_text("test content")
        
        # Create organizer with separate organized path
        organized_dir = Path(tmpdir) / "organized"
        organizer = FileOrganizer(str(organized_dir))
        
        # Verify source file exists before organization
        assert source_file.exists(), "Source file should exist before organization"
        
        # Organize the file
        success = organizer.organize_file(str(source_file), filename)
        
        # Check that organization succeeded
        assert success, "File organization should succeed"
        
        # Check that source file no longer exists in downloads
        assert not source_file.exists(), "Source file should be moved (not exist in original location)"
        
        # Check that file exists in organized folder
        organized_files = list(organized_dir.glob(f"*{extension}"))
        assert len(organized_files) > 0, "File should exist in organized folder"
        
        # Verify the organized file is in the correct directory
        organized_file = organized_files[0]
        assert organized_file.parent == organized_dir, "File should be in the organized directory"
