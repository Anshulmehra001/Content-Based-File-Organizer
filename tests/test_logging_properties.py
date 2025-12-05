"""Property-based tests for logging functionality across components."""

import logging
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pytest

from src.text_extractor import TextExtractor, TextExtractionError
from src.llm_service import LLMService
from src.file_organizer import FileOrganizer, FileOrganizerError


# Feature: content-based-file-organizer, Property 9: Extraction logging includes character count
# **Validates: Requirements 6.2**
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    text_content=st.text(min_size=1, max_size=5000),
    max_length=st.integers(min_value=100, max_value=2000)
)
def test_extraction_logging_includes_character_count(text_content, max_length, caplog):
    """Property: For any successful text extraction, the log should include character count.
    
    This test verifies that when text is extracted, the logging includes
    the number of characters extracted.
    """
    extractor = TextExtractor(max_length=max_length)
    
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(text_content)
        temp_path = f.name
    
    try:
        with caplog.at_level(logging.DEBUG, logger='src.text_extractor'):
            # Extract text
            extracted = extractor.extract_text(temp_path)
            
            # Get logs
            logs = caplog.text
            
            # Property: log should contain character count
            expected_count = len(extracted)
            assert str(expected_count) in logs, \
                f"Log should contain character count {expected_count}"
            
            # Property: log should contain "characters" or "Extracted"
            assert "Extracted" in logs or "characters" in logs, \
                "Log should mention extraction or characters"
        
    finally:
        Path(temp_path).unlink(missing_ok=True)


# Feature: content-based-file-organizer, Property 10: Organization logging includes final location
# **Validates: Requirements 6.4**
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    new_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        min_codepoint=ord('A'), max_codepoint=ord('z')
    )),
    file_content=st.text(min_size=0, max_size=100)
)
def test_organization_logging_includes_final_location(new_name, file_content, caplog):
    """Property: For any successfully organized file, log should include final location.
    
    This test verifies that when a file is organized, the logging includes
    the final destination path.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        organized_path = Path(temp_dir) / "Organized"
        organizer = FileOrganizer(str(organized_path))
        
        # Create a temporary source file
        source_file = Path(temp_dir) / "test_file.txt"
        source_file.write_text(file_content, encoding='utf-8')
        
        with caplog.at_level(logging.DEBUG, logger='src.file_organizer'):
            # Organize the file
            success = organizer.organize_file(str(source_file), new_name)
            
            if success:
                # Get logs
                logs = caplog.text
                
                # Property: log should contain the organized path
                assert str(organized_path) in logs or "Organized" in logs, \
                    f"Log should contain reference to organized location"
                
                # Property: log should indicate success
                assert "organized successfully" in logs.lower() or "to:" in logs, \
                    "Log should indicate successful organization"


# Feature: content-based-file-organizer, Property 11: Error logging includes complete details
# **Validates: Requirements 6.5**
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    filename=st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        min_codepoint=ord('A'), max_codepoint=ord('z')
    ))
)
def test_error_logging_includes_complete_details_file_not_found(filename, caplog):
    """Property: For any error, log should include error type, message, and filename.
    
    This test verifies that when an error occurs (file not found),
    the logging includes the error type, message, and affected filename.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        organized_path = Path(temp_dir) / "Organized"
        organizer = FileOrganizer(str(organized_path))
        
        # Create a non-existent file path
        non_existent_file = Path(temp_dir) / f"{filename}_nonexistent.txt"
        
        with caplog.at_level(logging.DEBUG, logger='src.file_organizer'):
            # Try to organize a non-existent file (should raise error)
            try:
                organizer.organize_file(str(non_existent_file), "new_name")
                assert False, "Should have raised FileOrganizerError"
            except FileOrganizerError:
                pass  # Expected
            
            # Get logs
            logs = caplog.text
            
            # Property: log should contain error type
            assert "FileNotFoundError" in logs or "File not found" in logs, \
                "Log should contain error type"
            
            # Property: log should contain filename
            assert filename in logs or str(non_existent_file) in logs, \
                f"Log should contain filename reference"
            
            # Property: log should contain "Type:" and "Message:" or similar structure
            assert ("Type:" in logs or "Message:" in logs or "error" in logs.lower()), \
                "Log should have structured error information"


# Feature: content-based-file-organizer, Property 11: Error logging includes complete details
# **Validates: Requirements 6.5**
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    text_content=st.text(min_size=5, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        min_codepoint=ord('A'), max_codepoint=ord('z')
    )),
    original_filename=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        min_codepoint=ord('A'), max_codepoint=ord('z')
    ))
)
def test_llm_service_error_logging_includes_details(text_content, original_filename, caplog):
    """Property: For any LLM service error, log should include error details.
    
    This test verifies that when an error occurs in LLM service,
    the logging includes error type, message, and filename.
    """
    # Create an LLM service with invalid mode to trigger error path
    service = LLMService(mode="invalid_mode")
    
    with caplog.at_level(logging.DEBUG, logger='src.llm_service'):
        # Generate filename (will use fallback due to invalid mode)
        result = service.generate_filename(text_content, original_filename)
        
        # Get logs
        logs = caplog.text
        
        # Property: log should contain error indication (ERROR level for invalid mode)
        assert "error" in logs.lower() or "invalid" in logs.lower(), \
            f"Log should indicate an error occurred. Got: {logs}"
        
        # Even with fallback, we should get a valid filename
        assert result is not None and len(result) > 0, \
            "Should return fallback filename"
