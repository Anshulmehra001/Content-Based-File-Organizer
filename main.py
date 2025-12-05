#!/usr/bin/env python3
"""Main entry point for the Content-Based File Organizer."""

import argparse
import logging
import signal
import sys
from pathlib import Path

from src.config import Config, ConfigurationError
from src.text_extractor import TextExtractor
from src.llm_service import LLMService
from src.file_organizer import FileOrganizer
from src.file_processor import FileProcessor
from src.file_monitor import FileMonitor


def setup_logging(log_level: str, log_format: str) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for log messages
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Content-Based File Organizer - Automatically organize files based on content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python main.py
  
  # Run with custom config file
  python main.py --config custom_config.yaml
  
  # Run in simulated mode
  python main.py --llm-mode simulated
  
  # Run with Bedrock (requires AWS credentials)
  python main.py --llm-mode bedrock
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--llm-mode',
        type=str,
        choices=['simulated', 'bedrock'],
        help='LLM mode to use (overrides config file)'
    )
    
    return parser.parse_args()


def main() -> int:
    """Main application entry point.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    try:
        # Check if config file exists
        config_path = Path(args.config)
        if config_path.exists():
            config = Config(config_path=str(config_path))
        else:
            print(f"Warning: Config file not found at {args.config}, using defaults")
            config = Config()
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    
    # Override LLM mode if specified on command line
    if args.llm_mode:
        # Temporarily override the config
        config._config['llm']['mode'] = args.llm_mode
    
    # Setup logging
    setup_logging(config.log_level, config.log_format)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Content-Based File Organizer Starting")
    logger.info("=" * 60)
    logger.info(f"Downloads folder: {config.downloads_path}")
    logger.info(f"Organized folder: {config.organized_path}")
    logger.info(f"LLM mode: {config.llm_mode}")
    logger.info(f"Supported file types: {', '.join(config.file_types)}")
    logger.info("=" * 60)
    
    # Initialize components
    try:
        # Text extractor
        extractor = TextExtractor(max_length=config.content_sample_length)
        logger.debug("TextExtractor initialized")
        
        # LLM service
        llm_service = LLMService(
            mode=config.llm_mode,
            bedrock_model=config.bedrock_model,
            bedrock_region=config.bedrock_region,
            max_tokens=config.bedrock_max_tokens
        )
        logger.debug(f"LLMService initialized in {llm_service.mode} mode")
        
        # File organizer
        organizer = FileOrganizer(organized_path=config.organized_path)
        logger.debug("FileOrganizer initialized")
        
        # File processor
        processor = FileProcessor(
            extractor=extractor,
            llm_service=llm_service,
            organizer=organizer
        )
        logger.debug("FileProcessor initialized")
        
        # File monitor
        monitor = FileMonitor(
            downloads_path=config.downloads_path,
            processor=processor
        )
        logger.debug("FileMonitor initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return 1
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        logger.info("\nShutdown signal received, stopping...")
        monitor.stop()
        logger.info("Application stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    try:
        monitor.start()
        logger.info("Monitoring active. Press Ctrl+C to stop.")
        
        # Keep the application running
        signal.pause()
        
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received, stopping...")
        monitor.stop()
        logger.info("Application stopped")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        monitor.stop()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
