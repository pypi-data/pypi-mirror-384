"""
Logging configuration for coverage tools.

Provides colored console logging with different levels and formatting
to provide clear, color-coded output for better user experience.
"""

import logging
import sys
# No typing imports needed for Python 3.11+ union syntax


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[0;37m',    # White
        'INFO': '\033[0;34m',     # Blue
        'WARNING': '\033[1;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'SUCCESS': '\033[0;32m',  # Green
        'STEP': '\033[0;36m',     # Cyan
    }
    
    RESET = '\033[0m'  # Reset color
    
    def format(self, record):
        # Add color to the level name
        level_name = record.levelname
        if hasattr(record, 'level_name'):
            level_name = record.level_name
            
        color = self.COLORS.get(level_name, '')
        record.colored_levelname = f"{color}[{level_name}]{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        return formatted


def setup_logging(level: str = "INFO", use_colors: bool = True) -> logging.Logger:
    """
    Set up logging configuration for coverage tools.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        use_colors: Whether to use colored output
        
    Returns:
        Configured logger instance
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger('coverage_tools')
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    
    # Set formatter
    if use_colors and sys.stdout.isatty():
        formatter = ColoredFormatter('%(colored_levelname)s %(message)s')
    else:
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (defaults to 'coverage_tools')
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name or 'coverage_tools')


# Add custom log levels
def add_success_level():
    """Add SUCCESS log level."""
    logging.SUCCESS = 25
    logging.addLevelName(logging.SUCCESS, 'SUCCESS')
    
    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(logging.SUCCESS):
            self._log(logging.SUCCESS, message, args, **kwargs)
    
    logging.Logger.success = success


def add_step_level():
    """Add STEP log level."""
    logging.STEP = 35
    logging.addLevelName(logging.STEP, 'STEP')
    
    def step(self, message, *args, **kwargs):
        if self.isEnabledFor(logging.STEP):
            self._log(logging.STEP, message, args, **kwargs)
    
    logging.Logger.step = step


# Initialize custom levels
add_success_level()
add_step_level()
