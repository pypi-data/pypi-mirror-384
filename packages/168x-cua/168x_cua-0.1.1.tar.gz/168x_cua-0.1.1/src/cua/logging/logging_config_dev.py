import logging
import sys
from pathlib import Path


class ServerLogFilter(logging.Filter):
    """Custom filter to allow server.* and cua.* loggers at all levels, others only at WARNING+"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on logger name and level.
        
        Args:
            record: The log record to filter
            
        Returns:
            True if the record should be logged, False otherwise
        """
        # Allow all levels for loggers that start with 'cua' or are '__main__'
        if record.name.startswith('cua') or record.name == '__main__':
            return True
        
        # For all other loggers, only allow WARNING and above
        return record.levelno >= logging.WARNING


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
        'BOLD': '\033[1m',        # Bold
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors"""
        # Get the original formatted message
        formatted = super().format(record)
        
        # Add colors based on log level
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        bold = self.COLORS['BOLD']
        
        # Create clickable file path for VS Code
        try:
            # Get relative path from current working directory
            file_path = Path(record.pathname).relative_to(Path.cwd())
        except ValueError:
            # If can't make relative, use absolute path
            file_path = Path(record.pathname)
        
        clickable_location = f"{file_path}:{record.lineno}"
        
        # Format: [LEVEL] file:line - message
        if level_color:
            import datetime
            timestamp = datetime.datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
            formatted = (
                f"{timestamp} - {level_color}{bold}[{record.levelname}]{reset_color} "
                f"{level_color}{clickable_location}{reset_color} - {record.getMessage()}"
            )
        
        # Append exception stack trace for error records
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted


def setup_logging(level: str = "DEBUG") -> None:
    """
    Configure logging for the application.
    
    Args:
        level: The log level for server loggers (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get root logger and set to DEBUG - filtering will be done by ServerLogFilter
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # Handler accepts all levels
    
    # Create and set formatter
    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add custom filter to console handler
    server_filter = ServerLogFilter()
    console_handler.addFilter(server_filter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Configure server logger specifically
    server_logger = logging.getLogger('cua')
    server_logger.setLevel(numeric_level)
    
    # Prevent propagation to avoid double logging
    server_logger.propagate = True  # We want it to propagate to use our custom filter
    
    # Silence SQLAlchemy and Uvicorn loggers: route through our console handler and drop INFO
    for noisy in ('sqlalchemy', 'sqlalchemy.engine', 'sqlalchemy.engine.Engine'):
        lg = logging.getLogger(noisy)
        lg.setLevel(logging.WARNING)
        # Clear existing handlers and use our console handler with ServerLogFilter
        lg.handlers.clear()
        lg.addHandler(console_handler)
        lg.propagate = False
    
    # Log configuration success
    server_logger.info(f"Logging configured - CUA logs at {level.upper()} level")
    server_logger.debug("Debug logging enabled for CUA components")