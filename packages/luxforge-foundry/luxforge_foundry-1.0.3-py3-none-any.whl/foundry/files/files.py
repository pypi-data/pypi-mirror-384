#!/usr/bin/env python3

# files.py
# Author: Luxforge
# File and directory utilities

import os
import time
from pathlib import Path
from foundry.logger.logger import logger
from typing import List

def write_file(filepath, data, retries=5, timeout=2, encoding="utf-8"):
    """
    Write data to a file with retry logic and timeout between attempts.
    
    ARGS:
        filepath (str or Path): Destination file path
        data (str): Data to write
        retries (int): Number of retry attempts
        timeout (int or float): Seconds to wait between retries
        encoding (str): File encoding (default: utf-8)
    
    RETURNS:
        bool: True if write succeeded, False otherwise
    """
    # VALIDATE INPUTS
    if retries == 0:
        logger.warning(f"Retries set to 0, no further attempts will be made to write the file: {filepath}")
        return False

    # Ensure filepath is a Path object
    filepath = Path(filepath)

    # Ensure the parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Recursively attempt to write the file

    try:
        with open(filepath, "w", encoding=encoding) as f:
            f.write(data)
    except Exception as e:
        
        # Log the error and retry
        logger.error(f"Failed to write to {filepath}. Retries pending:{retries}. Error: {e}")
        time.sleep(timeout)

        return write_file(filepath, data, retries - 1, timeout, encoding)
    logger.info(f"Successfully wrote to {filepath}")
    return True

def read_file(filepath: str | Path, encoding: str="utf-8", retries: int=5, timeout: int=2) -> str | None:
    """
    Read data from a file.
    
    ARGS:
        filepath (str or Path): Source file path
        encoding (str): File encoding (default: utf-8)
        retries (int): Number of retry attempts (default: 5)
        timeout (int or float): Seconds to wait between retries (default: 2)
    RETURNS:
        str: File contents, or None if read failed

    """
    # VALIDATE INPUTS
    
    if retries == 0:
        logger.warning(f"Out of retries, no further attempts will be made to read the file: {filepath}")
        return None
    
    # Ensure filepath is a Path object
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error(f"File does not exist: {filepath}")
        return None

    # Recursively attempt to read the file    
    try:
        with open(filepath, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:

        logger.error(f"Failed to read from {filepath}. Error: {e}")
        time.sleep(timeout)
        return read_file(filepath, encoding, retries - 1, timeout)

    logger.info(f"Successfully read from {filepath}")
    return True

def find_all_files(directory: str | Path, pattern: str="*") -> List[Path]:
    """
    Recursively find all files in a directory matching a pattern.
    
    ARGS:
        directory (str or Path): Root directory to search
        pattern (str): Glob pattern to match files (default: "*")
    
    RETURNS:
        list of Path: List of matching file paths
    """
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory does not exist or is not a directory: {directory}")
        return []
    
    logger.info(f"Searching for files in {directory} matching pattern '{pattern}'")
    return [p.resolve() for p in directory.rglob(pattern)]