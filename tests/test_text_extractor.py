"""Unit tests for TextExtractor component."""

import tempfile
from pathlib import Path
import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

from src.text_extractor import TextExtractor, TextExtractionError


class TestTextExtractor:
    """Unit tests for the TextExtractor class."""
    
    def test_extract_from_simple_text_file(self):
        """Test extraction from a simple UTF-8 text file."""
        extractor = TextExtractor(max_length=1000)
        content = "This is a simple test file.\nWith multiple lines."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = extractor.extract_text(temp_path)
            assert result == content
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_extract_from_pdf_file(self):
        """Test extraction from a PDF file."""
        extractor = TextExtractor(max_length=1000)
        test_text = "This is a test PDF document."
        
        # Create a simple PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            c.drawString(100, 750, test_text)
            c.save()
            
            with open(temp_path, 'wb') as pdf_file:
                pdf_file.write(pdf_buffer.getvalue())
            
            result = extractor.extract_text(temp_path)
            # PDF extraction may add spaces, so check if test text is in result
            assert test_text in result or result.replace(" ", "") == test_text.replace(" ", "")
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_truncation_to_max_length(self):
        """Test that text is truncated to max_length."""
        extractor = TextExtractor(max_length=50)
        content = "A" * 200  # 200 characters
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = extractor.extract_text(temp_path)
            assert len(result) == 50
            assert result == "A" * 50
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_encoding_fallback_latin1(self):
        """Test fallback to Latin-1 encoding when UTF-8 fails."""
        extractor = TextExtractor(max_length=1000)
        # Latin-1 specific character (not valid UTF-8)
        content = b"Caf\xe9"  # Café in Latin-1
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = extractor.extract_text(temp_path)
            assert "Caf" in result  # Should successfully read with fallback
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_encoding_fallback_cp1252(self):
        """Test fallback to CP1252 encoding."""
        extractor = TextExtractor(max_length=1000)
        # CP1252 specific character
        content = b"Smart quotes: \x93Hello\x94"  # CP1252 smart quotes
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = extractor.extract_text(temp_path)
            assert "Smart quotes" in result
            assert "Hello" in result
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_file_not_found_error(self):
        """Test error handling when file doesn't exist."""
        extractor = TextExtractor(max_length=1000)
        
        with pytest.raises(TextExtractionError, match="File not found"):
            extractor.extract_text("/nonexistent/file.txt")
    
    def test_unsupported_file_type(self):
        """Test error handling for unsupported file types."""
        extractor = TextExtractor(max_length=1000)
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(TextExtractionError, match="Unsupported file type"):
                extractor.extract_text(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_corrupted_pdf_error(self):
        """Test error handling for corrupted PDF files."""
        extractor = TextExtractor(max_length=1000)
        
        # Create a file with .pdf extension but invalid content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write("This is not a valid PDF file")
            temp_path = f.name
        
        try:
            with pytest.raises(TextExtractionError):
                extractor.extract_text(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_empty_text_file(self):
        """Test extraction from an empty text file."""
        extractor = TextExtractor(max_length=1000)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            result = extractor.extract_text(temp_path)
            assert result == ""
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_empty_pdf_file(self):
        """Test extraction from a PDF with no text."""
        extractor = TextExtractor(max_length=1000)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            # Create a PDF with no text content
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            c.showPage()  # Empty page
            c.save()
            
            with open(temp_path, 'wb') as pdf_file:
                pdf_file.write(pdf_buffer.getvalue())
            
            result = extractor.extract_text(temp_path)
            assert result == ""
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_multipage_pdf(self):
        """Test extraction from a multi-page PDF."""
        extractor = TextExtractor(max_length=1000)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            
            # Page 1
            c.drawString(100, 750, "Page 1 content")
            c.showPage()
            
            # Page 2
            c.drawString(100, 750, "Page 2 content")
            c.showPage()
            
            c.save()
            
            with open(temp_path, 'wb') as pdf_file:
                pdf_file.write(pdf_buffer.getvalue())
            
            result = extractor.extract_text(temp_path)
            assert "Page 1 content" in result or "Page1content" in result.replace(" ", "")
            assert "Page 2 content" in result or "Page2content" in result.replace(" ", "")
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_text_file_with_special_characters(self):
        """Test extraction from text file with special characters."""
        extractor = TextExtractor(max_length=1000)
        content = "Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = extractor.extract_text(temp_path)
            assert result == content
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_custom_max_length(self):
        """Test that custom max_length is respected."""
        extractor = TextExtractor(max_length=25)
        content = "This is a longer text that should be truncated"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = extractor.extract_text(temp_path)
            assert len(result) == 25
            assert result == content[:25]
        finally:
            Path(temp_path).unlink(missing_ok=True)
