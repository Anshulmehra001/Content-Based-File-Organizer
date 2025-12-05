"""Text extraction component for PDF and text files."""

import logging
from pathlib import Path
from typing import Optional
import PyPDF2


logger = logging.getLogger(__name__)


class TextExtractionError(Exception):
    """Raised when text extraction fails."""
    pass


class TextExtractor:
    """Extracts text content from PDF and text files.
    
    Supports:
    - PDF text extraction using PyPDF2
    - Text file reading with encoding fallback (UTF-8, Latin-1, CP1252)
    - Automatic truncation to first 1000 characters
    """
    
    def __init__(self, max_length: int = 1000):
        """Initialize the text extractor.
        
        Args:
            max_length: Maximum number of characters to extract (default: 1000)
        """
        self.max_length = max_length
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from a file.
        
        Args:
            file_path: Path to the file to extract text from
            
        Returns:
            Extracted text (truncated to max_length characters)
            
        Raises:
            TextExtractionError: If extraction fails
        """
        path = Path(file_path)
        
        if not path.exists():
            raise TextExtractionError(f"File not found: {file_path}")
        
        # Determine file type by extension
        extension = path.suffix.lower()
        
        try:
            if extension == ".pdf":
                text = self._extract_from_pdf(file_path)
            elif extension in [".txt", ".text"]:
                text = self._extract_from_text(file_path)
            else:
                raise TextExtractionError(f"Unsupported file type: {extension}")
            
            # Truncate to max_length
            truncated = text[:self.max_length]
            
            logger.info(f"Extracted {len(truncated)} characters from {path.name}")
            
            return truncated
            
        except TextExtractionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting text from {file_path}: {e}")
            raise TextExtractionError(f"Failed to extract text: {e}")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text
            
        Raises:
            TextExtractionError: If PDF is corrupted or unreadable
        """
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                # Extract text from all pages
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                text = " ".join(text_parts)
                
                if not text.strip():
                    logger.warning(f"No text extracted from PDF: {file_path}")
                    return ""
                
                return text
                
        except PyPDF2.errors.PdfReadError as e:
            logger.error(f"Corrupted or unreadable PDF: {file_path} - {e}")
            raise TextExtractionError(f"Corrupted PDF file: {e}")
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            raise TextExtractionError(f"Failed to read PDF: {e}")
    
    def _extract_from_text(self, file_path: str) -> str:
        """Extract text from a text file with encoding fallback.
        
        Tries encodings in order: UTF-8, Latin-1, CP1252
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Extracted text
            
        Raises:
            TextExtractionError: If all encoding attempts fail
        """
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                    logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                    return text
            except UnicodeDecodeError:
                logger.debug(f"Failed to read {file_path} with {encoding} encoding")
                continue
            except Exception as e:
                logger.error(f"Error reading text file {file_path} with {encoding}: {e}")
                continue
        
        # All encodings failed
        logger.error(f"Failed to read {file_path} with any supported encoding")
        raise TextExtractionError(
            f"Failed to read text file with encodings: {', '.join(encodings)}"
        )
