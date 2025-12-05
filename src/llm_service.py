"""LLM service for generating descriptive filenames from content."""

import logging
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when LLM service encounters an error."""
    pass


class LLMService:
    """Generates descriptive filenames using LLM or simulated mode.
    
    Supports two modes:
    - simulated: Uses keyword extraction heuristics
    - bedrock: Uses Amazon Bedrock API (requires boto3 and AWS credentials)
    """
    
    def __init__(
        self,
        mode: str = "simulated",
        bedrock_model: Optional[str] = None,
        bedrock_region: Optional[str] = None,
        max_tokens: int = 50
    ):
        """Initialize the LLM service.
        
        Args:
            mode: Operating mode ("simulated" or "bedrock")
            bedrock_model: Bedrock model identifier (required for bedrock mode)
            bedrock_region: AWS region for Bedrock (required for bedrock mode)
            max_tokens: Maximum tokens for LLM response
        """
        self.mode = mode
        self.bedrock_model = bedrock_model
        self.bedrock_region = bedrock_region
        self.max_tokens = max_tokens
        self._bedrock_client = None
        
        # Attempt to initialize Bedrock client if in bedrock mode
        if self.mode == "bedrock":
            self._initialize_bedrock()
    
    def _initialize_bedrock(self) -> None:
        """Initialize Bedrock client and handle credential issues."""
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, PartialCredentialsError
            
            try:
                self._bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=self.bedrock_region
                )
                # Test credentials by making a simple call
                logger.info(f"Bedrock client initialized for region {self.bedrock_region}")
            except (NoCredentialsError, PartialCredentialsError) as e:
                logger.warning(
                    f"AWS credentials not available: {e}. Falling back to simulated mode."
                )
                self.mode = "simulated"
                self._bedrock_client = None
        except ImportError:
            logger.warning("boto3 not installed. Falling back to simulated mode.")
            self.mode = "simulated"
            self._bedrock_client = None

    def generate_filename(self, content_sample: str, original_filename: str = None) -> str:
        """Generate a descriptive filename from content sample.
        
        Args:
            content_sample: Text content to analyze
            original_filename: Original filename (for logging purposes)
            
        Returns:
            Generated filename (without extension)
        """
        if not content_sample or not content_sample.strip():
            logger.warning("Empty content sample provided, using fallback filename")
            return self._fallback_filename()
        
        try:
            if self.mode == "simulated":
                filename = self._simulate_filename(content_sample)
            elif self.mode == "bedrock":
                filename = self._bedrock_filename(content_sample)
            else:
                logger.error(f"Invalid mode: {self.mode}")
                return self._fallback_filename()
            
            if original_filename:
                logger.info(f"Generated filename: {filename} (original: {original_filename})")
            else:
                logger.info(f"Generated filename: {filename}")
            return filename
            
        except Exception as e:
            logger.error(
                f"Error generating filename - "
                f"Type: {type(e).__name__}, Message: {e}, "
                f"Filename: {original_filename if original_filename else 'unknown'}"
            )
            return self._fallback_filename()
    
    def _simulate_filename(self, content_sample: str) -> str:
        """Generate filename using keyword extraction heuristics.
        
        Args:
            content_sample: Text content to analyze
            
        Returns:
            Generated filename based on keywords
        """
        # Clean the content
        content = content_sample.strip()
        
        # Extract potential keywords (words with 4+ characters, excluding common words)
        common_words = {
            'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have',
            'will', 'your', 'are', 'not', 'but', 'can', 'was', 'were',
            'been', 'has', 'had', 'does', 'did', 'would', 'could', 'should',
            'about', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'under', 'again', 'further', 'then', 'once'
        }
        
        # Split into words and filter
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        keywords = [w for w in words if w not in common_words]
        
        # Take first 3-5 unique keywords
        unique_keywords = []
        seen = set()
        for word in keywords:
            if word not in seen:
                unique_keywords.append(word)
                seen.add(word)
            if len(unique_keywords) >= 5:
                break
        
        # If we have keywords, use them
        if unique_keywords:
            # Capitalize first letter of each word
            filename = "_".join(word.capitalize() for word in unique_keywords[:3])
            return filename
        
        # Fallback: use first few words
        first_words = content.split()[:3]
        if first_words:
            filename = "_".join(word.capitalize() for word in first_words)
            # Remove non-alphanumeric characters
            filename = re.sub(r'[^a-zA-Z0-9_]', '', filename)
            if filename:
                return filename
        
        # Last resort fallback
        return self._fallback_filename()

    def _bedrock_filename(self, content_sample: str) -> str:
        """Generate filename using Amazon Bedrock.
        
        Args:
            content_sample: Text content to analyze
            
        Returns:
            Generated filename from Bedrock
            
        Raises:
            LLMServiceError: If Bedrock call fails
        """
        if not self._bedrock_client:
            logger.warning("Bedrock client not available, falling back to simulated mode")
            return self._simulate_filename(content_sample)
        
        try:
            import json
            
            # Construct prompt for filename generation
            prompt = f"""Based on the following text content, generate a short, descriptive filename (3-5 words, no file extension). 
Use underscores between words. Only respond with the filename, nothing else.

Content:
{content_sample[:500]}

Filename:"""
            
            # Prepare request body based on model
            if "claude" in self.bedrock_model.lower():
                body = json.dumps({
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": self.max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
                })
            else:
                # Generic format for other models
                body = json.dumps({
                    "prompt": prompt,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7,
                })
            
            # Call Bedrock
            response = self._bedrock_client.invoke_model(
                modelId=self.bedrock_model,
                body=body
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract filename based on model response format
            if "claude" in self.bedrock_model.lower():
                filename = response_body.get('completion', '').strip()
            else:
                filename = response_body.get('text', '').strip()
            
            # Clean up the filename
            filename = filename.split('\n')[0]  # Take first line only
            filename = re.sub(r'[^a-zA-Z0-9_\s-]', '', filename)  # Remove special chars
            filename = re.sub(r'\s+', '_', filename)  # Replace spaces with underscores
            
            if filename:
                logger.info(f"Bedrock generated filename: {filename}")
                return filename
            else:
                logger.warning("Bedrock returned empty filename, using fallback")
                return self._fallback_filename()
                
        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            raise LLMServiceError(f"Failed to generate filename with Bedrock: {e}")
    
    def _fallback_filename(self) -> str:
        """Generate a fallback filename with timestamp.
        
        Returns:
            Timestamp-based filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"document_{timestamp}"
        logger.info(f"Using fallback filename: {filename}")
        return filename
