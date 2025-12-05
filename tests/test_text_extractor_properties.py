"""Property-based tests for TextExtractor component."""

import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

from src.text_extractor import TextExtractor


# Feature: content-based-file-organizer, Property 2: Text extraction length constraint
# **Validates: Requirements 2.3**
@settings(max_examples=100)
@given(
    text_content=st.text(min_size=0, max_size=5000),
    max_length=st.integers(min_value=100, max_value=2000)
)
def test_text_extraction_length_constraint_text_files(text_content, max_length):
    """Property: For any text file, extracted content should not exceed max_length.
    
    This test verifies that the TextExtractor correctly truncates text content
    to the specified maximum length, regardless of the original file size.
    """
    extractor = TextExtractor(max_length=max_length)
    
    # Create a temporary text file with the generated content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(text_content)
        temp_path = f.name
    
    try:
        # Extract text
        extracted = extractor.extract_text(temp_path)
        
        # Property: extracted text should not exceed max_length
        assert len(extracted) <= max_length, \
            f"Extracted text length {len(extracted)} exceeds max_length {max_length}"
        
        # Normalize line endings for comparison (Windows converts \r to \n in text mode)
        normalized_content = text_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # If original content is shorter than max_length, it should be preserved
        if len(normalized_content) <= max_length:
            assert extracted == normalized_content, \
                "Short content should be preserved (with normalized line endings)"
        else:
            # If original is longer, extracted should be exactly max_length
            assert len(extracted) == max_length, \
                f"Long content should be truncated to exactly {max_length} characters"
            # And should be a prefix of the normalized original
            assert normalized_content.startswith(extracted), \
                "Extracted text should be a prefix of original content"
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)


# Feature: content-based-file-organizer, Property 2: Text extraction length constraint
# **Validates: Requirements 2.3**
@settings(max_examples=100)
@given(
    text_content=st.text(min_size=0, max_size=5000, alphabet=st.characters(blacklist_categories=('Cs',))),
    max_length=st.integers(min_value=100, max_value=2000)
)
def test_text_extraction_length_constraint_pdf_files(text_content, max_length):
    """Property: For any PDF file, extracted content should not exceed max_length.
    
    This test verifies that the TextExtractor correctly truncates PDF text content
    to the specified maximum length.
    """
    extractor = TextExtractor(max_length=max_length)
    
    # Create a temporary PDF file with the generated content
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create PDF with reportlab
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        
        # Split text into lines to fit on page
        y_position = 750
        line_height = 15
        max_width = 500
        
        # Simple text wrapping
        words = text_content.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) * 6 < max_width:  # Rough character width estimate
                current_line = test_line
            else:
                if current_line:
                    c.drawString(50, y_position, current_line)
                    y_position -= line_height
                    if y_position < 50:
                        c.showPage()
                        y_position = 750
                current_line = word
        
        # Draw remaining text
        if current_line:
            c.drawString(50, y_position, current_line)
        
        c.save()
        
        # Write PDF to file
        with open(temp_path, 'wb') as pdf_file:
            pdf_file.write(pdf_buffer.getvalue())
        
        # Extract text
        extracted = extractor.extract_text(temp_path)
        
        # Property: extracted text should not exceed max_length
        assert len(extracted) <= max_length, \
            f"Extracted text length {len(extracted)} exceeds max_length {max_length}"
        
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)
