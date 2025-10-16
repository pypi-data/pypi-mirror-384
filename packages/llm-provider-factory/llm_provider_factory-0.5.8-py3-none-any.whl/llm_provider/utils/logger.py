"""Logging utilities for LLM Provider Factory."""

import logging
import sys
from typing import Optional


class LLMProviderLogger:
    """Custom logger for LLM Provider Factory."""
    
    def __init__(self, name: str = "llm_provider", level: int = logging.INFO) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handler()
    
    def _setup_handler(self) -> None:
        """Setup console handler with formatter."""
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def debug(self, message: str, provider: Optional[str] = None) -> None:
        """Log debug message."""
        if provider:
            message = f"[{provider}] {message}"
        self.logger.debug(message)
    
    def info(self, message: str, provider: Optional[str] = None) -> None:
        """Log info message."""
        if provider:
            message = f"[{provider}] {message}"
        self.logger.info(message)
    
    def warning(self, message: str, provider: Optional[str] = None) -> None:
        """Log warning message."""
        if provider:
            message = f"[{provider}] {message}"
        self.logger.warning(message)
    
    def error(self, message: str, provider: Optional[str] = None) -> None:
        """Log error message."""
        if provider:
            message = f"[{provider}] {message}"
        self.logger.error(message)
    
    def critical(self, message: str, provider: Optional[str] = None) -> None:
        """Log critical message."""
        if provider:
            message = f"[{provider}] {message}"
        self.logger.critical(message)


# Global logger instance
logger = LLMProviderLogger()


def get_logger(name: str = "llm_provider") -> LLMProviderLogger:
    """Get logger instance for given name."""
    return LLMProviderLogger(name)