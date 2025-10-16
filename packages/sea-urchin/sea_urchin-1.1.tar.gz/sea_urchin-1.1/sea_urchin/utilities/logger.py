#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SeaUrchin Logging Utilities

This module provides a centralized logging system for the SeaUrchin package.
It replaces scattered print statements with proper logging that can be
configured by users for different levels of verbosity.

@author: SeaUrchin Development Team
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Union


class SeaUrchinLogger:
    """
    Centralized logging system for SeaUrchin package.

    This class provides a singleton-like logger that can be configured
    once and used throughout the SeaUrchin codebase.
    """

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SeaUrchinLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """Initialize the logger with default configuration."""
        self._logger = logging.getLogger('sea_urchin')
        self._logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if not self._logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            # Formatter for clean output
            formatter = logging.Formatter(
                '%(levelname)s: %(message)s'
            )
            console_handler.setFormatter(formatter)

            self._logger.addHandler(console_handler)

    def configure(self,
                  level: Union[str, int] = logging.INFO,
                  log_file: Optional[Union[str, Path]] = None,
                  format_string: Optional[str] = None):
        """
        Configure the logger with custom settings.

        Parameters
        ----------
        level : str or int, default=logging.INFO
            Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file : str or Path, optional
            Path to log file. If None, only console logging is used.
        format_string : str, optional
            Custom format string for log messages
        """
        # Convert string level to logging constant
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        self._logger.setLevel(level)

        # Clear existing handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # Default format
        if format_string is None:
            if level == logging.DEBUG:
                format_string = '%(levelname)s [%(name)s.%(funcName)s:%(lineno)d]: %(message)s'
            else:
                format_string = '%(levelname)s: %(message)s'

        formatter = logging.Formatter(format_string)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # File handler if requested
        if log_file is not None:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    def set_level(self, level: Union[str, int]):
        """Set the logging level."""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self._logger.setLevel(level)
        for handler in self._logger.handlers:
            handler.setLevel(level)

    def get_logger(self):
        """Get the configured logger instance."""
        return self._logger


# Global logger instance
_sea_urchin_logger = SeaUrchinLogger()


def get_logger():
    """
    Get the SeaUrchin logger instance.

    Returns
    -------
    logging.Logger
        Configured logger instance
    """
    return _sea_urchin_logger.get_logger()


def configure_logging(level: Union[str, int] = logging.INFO,
                      log_file: Optional[Union[str, Path]] = None,
                      format_string: Optional[str] = None):
    """
    Configure SeaUrchin logging system.

    Parameters
    ----------
    level : str or int, default=logging.INFO
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_file : str or Path, optional
        Path to log file. If None, only console logging is used.
    format_string : str, optional
        Custom format string for log messages

    Examples
    --------
    >>> from sea_urchin.utilities.logger import configure_logging
    >>> configure_logging(level='DEBUG', log_file='sea_urchin.log')
    """
    _sea_urchin_logger.configure(level, log_file, format_string)


def set_level(level: Union[str, int]):
    """
    Set the SeaUrchin logging level.

    Parameters
    ----------
    level : str or int
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Examples
    --------
    >>> from sea_urchin.utilities.logger import set_level
    >>> set_level('DEBUG')
    """
    _sea_urchin_logger.set_level(level)


# Convenience functions for common logging operations
def debug(msg, *args, **kwargs):
    """Log a debug message."""
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log an info message."""
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log a warning message."""
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log an error message."""
    get_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log a critical message."""
    get_logger().critical(msg, *args, **kwargs)


# Backward compatibility: provide print-like interface for gradual migration
def log_print(*args, level='INFO', **kwargs):
    """
    Print-like interface for logging.

    This function provides a drop-in replacement for print() statements
    that can be gradually migrated to proper logging levels.

    Parameters
    ----------
    *args : Any
        Arguments to log (same as print)
    level : str, default='INFO'
        Logging level to use
    **kwargs : Any
        Additional keyword arguments (end, sep, etc.)
    """
    # Convert print arguments to a single string
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '')

    message = sep.join(str(arg) for arg in args) + end

    # Remove trailing newline if present (logging adds its own)
    if message.endswith('\n'):
        message = message[:-1]

    # Map to appropriate logging function
    level_func = getattr(get_logger(), level.lower(), info)
    level_func(message)


def print_header():
    """
    Print a beautiful ASCII art header for SeaUrchin.
    """
    # Try to get version information
    try:
        import sea_urchin
        version = getattr(sea_urchin, '__version__', 'Unknown')
        date = getattr(sea_urchin, '__date__', '')
        author = getattr(sea_urchin, '__author__', '')
        
    except:
        version = 'Unknown'
        date = ''
        author = ''
    
    verline = f"Version {version}"
    autline = f"{author} @ Molecular Foundry"
    header = f"""
╔═════════════════════════════════════════════════════════════════════════════╗
║               ____               _   _          _     _                     ║
║              / ___|  ___  __ _  | | | |_ __ ___| |__ (_)_ __                ║
║              \___ \ / _ \/ _` | | | | | '__/ __| '_ \| | '_ \               ║
║               ___) |  __/ (_| | | |_| | | | (__| | | | | | | |              ║
║              |____/ \___|\__,_|  \___/|_|  \___|_| |_|_|_| |_|              ║
║{'':77}║
║{'☼ Coordination environment classification of MD data ☼':^77}║
║{'':77}║
║{verline:>37} | {date:<37}║
║{autline:^77}║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
    # Print header using standard print to ensure it always appears
    print(header)


def print_startup_info(verbose=True, log_level="INFO", log_file=None):
    """
    Print startup information with configuration details.

    Parameters
    ----------
    verbose : bool
        Whether verbose logging is enabled
    log_level : str
        Current logging level
    log_file : str or None
        Log file path if file logging is enabled
    """
    logger = get_logger()

    logger.debug("🔧 Configuration:")
    logger.debug(f"   • Verbose logging: {'✓ Enabled' if verbose else '✗ Disabled'}")
    logger.debug(f"   • Log level: {log_level}")

    if log_file:
        logger.debug(f"   • Log file: {log_file}")
    else:
        logger.debug("   • Log file: Console only")

    logger.info("☼ Ready to analyze molecular trajectories!")