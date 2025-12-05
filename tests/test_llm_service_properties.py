"""Property-based tests for LLM service."""

import pytest
from hypothesis import given, strategies as st, settings

from src.llm_service import LLMService


# Feature: content-based-file-organizer, Property 7: Simulated mode generates valid filenames
# **Validates: Requirements 7.5**
@settings(max_examples=100)
@given(content=st.text(min_size=1, max_size=5000))
def test_simulated_mode_generates_valid_filenames(content):
    """Property test: For any content sample in simulated mode, 
    the LLM Service should generate a non-empty filename using keyword extraction heuristics.
    
    This validates that simulated mode always produces a valid filename regardless of input.
    """
    # Arrange
    llm_service = LLMService(mode="simulated")
    
    # Act
    filename = llm_service.generate_filename(content)
    
    # Assert
    # 1. Filename should not be empty
    assert filename, f"Generated filename should not be empty for content: {content[:100]}"
    
    # 2. Filename should be a string
    assert isinstance(filename, str), "Generated filename should be a string"
    
    # 3. Filename should not contain invalid filesystem characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        assert char not in filename, f"Filename should not contain invalid character: {char}"
    
    # 4. Filename should not be just whitespace
    assert filename.strip(), "Filename should not be just whitespace"
