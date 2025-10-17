# /#!/usr/bin/env python3

# # logger.py
# Author: Luxforge
# Modular logging setup for Python applications

import socket
from pathlib import Path
from datetime import datetime
from time import sleep
import os
from foundry.colours.colours import Colours

class Logger:
    """
    Logger sets up a standardized logging configuration.
    ARGS:
        name: Logger name (default: "luxforge")
        env_path: Path to the .env file for configuration (default: None, uses ./logger.env)
    METHODS:
        info(msg): Log an info message
        warning(msg): Log a warning message
        error(msg): Log an error message
        debug(msg): Log a debug message
        exception(msg): Log an exception message
    PROPERTIES:
        logger: The underlying logging.Logger instance
    ENVIRONMENT VARIABLES:
        LOG_DIR: Directory to store log files (default: "./logs")
        LOG_TO_FILE: Whether to log to a file (default: "True")
        LOG_TO_CONSOLE: Whether to log to console (default: "True")
        LOG_TO_API: Whether to log to API endpoints (default: "False")
        API_ENDPOINT: API endpoint URL (default: None)
        API_KEY: API key for authentication (default: None)
        LOG_TO_DB: Whether to log to a database (default: "False")
        DB_CONNECTION_STRING: Database connection string (default: None)
        LOGLEVEL: Logging level (default: "DEBUG")
        DATE_FORMAT: Date format for timestamps (default: "%Y-%m-%d %H:%M:%S.%f")
        NUMBER_OF_DIGITS_AFTER_DECIMAL: Number of decimal digits in timestamps (default: 3)
        MAX_LOG_SIZE_MB: Maximum log file size in MB before rotation (default: 5)
        MAX_LOG_BACKUP_COUNT: Number of backup log files to keep (default: 5)
    """
    # Standard logging levels, can be expanded if needed - add colours 
    LEVELS = {
        "DEBUG": (10, "gray"),
        "INFO": (20, None),
        "CHANGELOG": (25, "blue"),  # Custom level for changelog entries
        "WARNING": (30, "yellow"),
        "ERROR": (40, "orange"),
        "CRITICAL": (50, "red")
    }

    def __init__(self, env_path=None):
        # Initialize logger settings using environment variables
        
        if env_path is None:
            env_path = os.path.join(os.path.dirname(__file__), "..", "logger.env")

        # Set the node name and user
        self.node = socket.gethostname()
        self.user = os.getenv("USER") or os.getenv("USERNAME") or "unknown"

        # Set the local vars with defaults
        self.local_vars = {
            "log_dir": "./logs", 
            "log_to_file": True,
            "log_to_console": True,
            "log_to_api": False,
            "api_endpoint": None,
            "api_key": None,
            "log_to_db": False,
            "db_connection_string": None,
            "log_level": "DEBUG",
            "date_format": "%Y-%m-%d %H:%M:%S.%f",
            "number_of_digits_after_decimal": 3,
            "max_log_size_mb": 5,
            "max_log_backup_count": 5,
            "task_name": "init",
        }

        # Apply them to the class
        for var, default in self.local_vars.items():
            setattr(self, var, default)

        # Load environment variables from the specified .env file if it exists - despite the name, we won't inject into environment
        if os.path.exists(env_path):
            # Load the .env file
            for line in open(env_path):
                # Skip comments and empty lines
                if line.strip() and not line.startswith('#'):

                    # Load in the values
                    key, value = line.strip().split('=', 1)
                    self.__load_vars(key, value)
        
        # Create the dir if it does not exist
        os.makedirs(self.log_dir, exist_ok=True)

        # Set the base directory for logs
        self.base_dir = self.log_dir

        # Read configuration from environment variables with defaults
        self.date_format = os.getenv("DATE_FORMAT", "%Y-%m-%d %H:%M:%S.%f")
        self.decimal_digits = int(os.getenv("NUMBER_OF_DIGITS_AFTER_DECIMAL", 3))

        # Set the log to file and console flags
        self.__log_to_file = os.getenv("LOG_TO_FILE", "True").lower() == "true"
        self.__log_to_console = os.getenv("LOG_TO_CONSOLE", "True").lower() == "true"

        # Set the log level
        self.set_level(self.log_level)
        # Update the actual log directory
        self.__update_directory()

        # Set the initial log filename
        self.__update_filename()
        
        # Load max log size and backup settings
        self.max_log_size = int(os.getenv("MAX_LOG_SIZE_MB", 5))
        self.max_log_backup = int(os.getenv("MAX_LOG_BACKUP_COUNT", 5))

        # Post a log entry indicating initialization
        self.i(f"Logger initialized for node '{self.node}' by user '{self.user}'")
        self.i(f"Logging level set to {self.log_level}")

        # Show the current taskname
        self.task(self.task_name)

    def __load_vars(self,k,v):
        # Tie an environment variable to a class attribute with type conversion - ignore if not in our list
        k = k.lower()
        if k in self.local_vars:
            if v.lower() in ["true", "false"]:
                self[k] = v.lower() == "true"
            elif v.isdigit():
                self[k] = int(v)
            else:
                try:
                    self[k] = float(v)
                except ValueError:
                    setattr(self, k, v)
            
            # Apply this to dev only
            print(f"[FoundryLogger] Set {k} to {getattr(self, k)}")

    def __write(self, path, content, retries=3, timeout=1, encoding="utf-8"):
        for attempt in range(retries):
            try:
                with open(path, "a", encoding=encoding) as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"[luxforgeLogger] Write failed (attempt {attempt+1}): {e}")
                sleep(timeout)
        return False

    def __update_filename(self):

        # Set the timestamped log filename based on current task and time - it returns YYYYMMDD_HH00
        timestamp = datetime.now().strftime("%Y%m%d_%H00")

        # Update the log dir - just in case
        self.__update_directory()

        # Create a safe task tag for the filename
        task_tag = self.task_name.replace(" ", "_") if self.task_name else "untagged"
        self.filename = os.path.join(self.log_dir, f"{task_tag}_{timestamp}.log")
    
    def __update_directory(self):

        # Rebuild the log directory path based on base_dir / task / yyyy / yyyy-mm / yyyy-mm-dd
        year_path = datetime.now().strftime("%Y")
        month_path = datetime.now().strftime("%Y-%m")
        day_path = datetime.now().strftime("%Y-%m-%d")
        date_path = os.path.join(year_path, month_path, day_path)
        self.log_dir = os.path.join(self.base_dir, self.task_name, date_path)

        # Ensure the log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

    def task(self, task_name: str = None) -> str:
        # Method to set or get the current task name
        if task_name:
            self.i(f"Switching task from '{self.task_name}' to '{task_name}'")
            self.task_name = task_name
            # Update the filename to reflect the new task
            self.__update_filename()
            self.__update_directory()
        else:
            self.i(f"Set task to: {self.task_name}")
        return self.task_name

    def __formatted_timestamp(self) -> str:
        # Return the current timestamp formatted according to date_format and decimal_digits
        raw = datetime.now().strftime(self.date_format)
        if "%f" in self.date_format:
            split = raw.split(".")
            if len(split) == 2:
                micro = split[1][:self.decimal_digits]
                return f"{split[0]}.{micro}"
        return raw

    def log(self, message, level: str = None):
        # General logging method - logs if level is >= current level
        if level is None:
            level = "INFO" # Default to INFO if no level provided
        else:
            level = level.upper()
            if level not in self.LEVELS:
                level = "INFO"  # Default to INFO if unknown level
        level_int = self.LEVELS[level][0]

        # General logging method - logs if level is >= current level
        if level_int >= self.level[0]:
            self.__log(message, level)

    def __log(self, message: str = None, level: str = "INFO"):
        # Internal method to handle the actual logging
        level = level.upper()
        if level not in self.LEVELS:
            level = "INFO"  # Default to INFO if unknown level

        # Set the timestamp formatted correctly
        timestamp = self.__formatted_timestamp()
        node = self.node

        # Generate the log line
        line = f"[{timestamp}] [{node}] [{level}] {message}"

        # Log to file if enabled
        if self.log_to_file:

            # Ensure the filename is set and directory exists
            if not hasattr(self, 'filename'):
                self.__update_filename()
            
            # Ensure the log directory exists
            Path(self.filename).parent.mkdir(parents=True, exist_ok=True)
            
            # Append the log line to the file
            self.__write(self.filename, line + "\n", retries=5, timeout=1, encoding="utf-8")

        # Log to console if enabled
        if self.log_to_console:
            # Get the colour
            colour = self.LEVELS[level][1]
            
            # If its critical, make it bold
            if level == "CRITICAL":
                line = Colours.colour_text(line, colour, bold=True)
            else:
                line = Colours.colour_text(line, colour)
            print(line)

    def __find_by_level(self, int_level: int = 20) -> str:
        # Using the level numeric, return the key name. Default to INFO if not found
        return next((k for k, v in self.LEVELS.items() if v[0] == int_level), "INFO")

    def set_level(self, level) -> None:
        # Setter for log level

        # Level can be a string, int, tuple or none
        if isinstance(level, int):
            # Set the log level directly if it's an int - defaults to info if unknown
            key = self.__find_by_level(level)
            self.level = self.LEVELS.get(key, self.LEVELS["INFO"])
        
        elif isinstance(level, tuple) and len(level) == 2:
            # Set the log level directly if it's a tuple (int, colour)
            self.level = level

        elif isinstance(level, str):
            # Set the log level by name if it's a string
            self.level = self.LEVELS.get(level.upper(), self.LEVELS["INFO"])

        elif level is None:
            # Set the level to default if nothing requested
            self.level = self.LEVELS["INFO"]
        
        # Show the current level
        self.i(f"Log level set to {self.level} ({self.__find_by_level(self.level[0])})")
        
    # INFO level logging method
    def info(self, message):
        self.log(message, level="INFO")
    i = info # Alias for info
    inf = info # Alias for info
    information = info # Alias for info
    
    # WARNING level logging method
    def warning(self, message):
        self.log(message, level="WARNING")
    warn = warning # Alias for warning
    w = warning # Alias for warning

    # ERROR level logging method
    def error(self, message):
        self.log(message, level="ERROR")
    err = error # Alias for error
    e = error # Alias for error
    exception = error # Alias for error
    exc = error # Alias for error
    ex = error # Alias for error

    # DEBUG level logging method
    def debug(self, message):
        # If no message provided, return whether debug is enabled
        if message is None:
            return self.level == self.LEVELS["DEBUG"]
        self.log(message, level="DEBUG")
    dbg = debug # Alias for debug
    d = debug # Alias for debug
    
    # CRITICAL level logging method
    def critical(self, message):
        self.log(message, level="CRITICAL")
    crit = critical # Alias for critical
    c = critical # Alias for critical


    
    
    def test_logger_levels(self):
        timestamp = self.__formatted_timestamp()
        node = self.node
        task = "test_logger_levels"
        self.i(f"Testing logger levels at {timestamp} on node {node} for task {task}")
        self.task(task)
        self.i(f"Current log level set to {self.level}")
        self.level = self.LEVELS["DEBUG"]
        self.info("This is an info message.")
        self.warning("This is a warning message.")
        self.error("This is an error message.")
        self.debug("This is a debug message.")
        self.critical("This is a critical message.")
        
# Create a default logger instance for module-level use
logger = Logger()

if __name__ == "__main__":
    # Test the logger functionality
    print("[INFO] Testing logger functionality...")
    logger.test_logger_levels()