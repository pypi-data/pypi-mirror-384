"""
Utility functions and constants for MSBench analysis.
"""
import json
import re
from typing import List, Dict
import pandas as pd
import zipfile
from tempfile import TemporaryDirectory
from pathlib import Path


class ZipNotFoundError(FileNotFoundError):
    """zipfile.ZipFile not found, or not a zip file"""


class BadZipError(RuntimeError):
    """zipfile.BadZipFile """


# Constants
CLS_OUTPUT_REPORT = "msbench_cls_analysis_report.xlsx"
CLS_ERROR_BLOCK_PATTERN = re.compile(r"(╭\s*Error on Agent[\s\S]*?╰[\s\S]*?╯)", re.MULTILINE)
CLS_ERROR_TYPE_PATTERN = re.compile(r'\[([^\]]+)\]')
CLS_COLUMNS = ["File Name", "Error Information", "Error Type"]

TRAJECTORY_OUTPUT_REPORT = "msbench_trajectory_analysis_report.xlsx"
TRAJECTORY_TOOL_CALL_ERROR_PREFIX = "Tool call failed with error:"
TRAJECTORY_COLUMNS = ["File Name", "Total Steps", "Failed Step", "Failed Tool Call ID", "Failed Tool Name", "Error Message", "Final Response Type", "Final Response"]

# Comparison report columns
COMPARISON_TASK_COLUMNS = ["Task Name", "Steps (Zip1)", "Steps (Zip2)", "Step Difference", "Status (Zip1)", "Status (Zip2)"]
COMPARISON_TOOL_COLUMNS = ["Tool Name", "Usage (Zip1)", "Usage (Zip2)", "Usage Difference"]

# Error prefix patterns for categorization
ERROR_PREFIXES = [
    "Code mapper might be in a loop",
    "Error executing command",
    "Failed to read file",
    "Error executing command",
    "Error: Path is outside of workspace folders",
    "File already exists",
    "Error processing workspace folder file",
    "Error: Invalid input path",
    "File does not exist",
    "Failed to map code for uri file",
    "Error: ENOENT: no such file or directory"
]


def norm_path(path: str) -> str:
    """Normalize the path to use forward slashes"""
    return Path(path).expanduser().resolve(strict=False)


def table_markdown(rows, columns):
    """Convert rows and columns to markdown table format"""
    df = pd.DataFrame(rows, columns=columns)
    return df.to_markdown(index=False)


def safe_extract(
        zip_ref: zipfile.ZipFile,
        target_dir: Path,
        ignore_error: bool = False
) -> None:
    """
    Safely extract files from a zip file to the target directory.
    Returns True if any errors occurred, False if all succeeded.
    """
    error_occurred = False
    for member in zip_ref.namelist():
        mpath = Path(member)
        if mpath.is_absolute() or ".." in mpath.parts:
            if ignore_error:
                continue
            raise BadZipError(f"Illegal member: {member}")

        try:
            zip_ref.extract(member, target_dir)
        except Exception as e:
            if ignore_error:
                continue
            raise RuntimeError(f"extract {member}: {e}")
    return error_occurred


def extract_error_prefix_from_message(error_message: str, prefixes: List[str] = None) -> str:
    """
    Extract error prefix from error message based on predefined patterns.
    
    Args:
        error_message: The error message to analyze
        prefixes: List of prefixes to match against. If None, uses ERROR_PREFIXES
    
    Returns:
        The matched prefix or error message itself if no match found
    """
    
    if prefixes is None:
        prefixes = ERROR_PREFIXES
    
    # Clean the message first
    message = str(error_message).strip()
    
    # Try to match each prefix
    for prefix in prefixes:
        if message.startswith(prefix):
            return prefix
        # Also check if prefix appears at the beginning after common prefixes
        if message.find(prefix) == 0 or message.find(f'"{prefix}') == 0:
            return prefix
    
    # Fallback: try to extract first line as prefix
    first_line = message.split('\n')[0].strip()
    if ':' in first_line:
        return first_line.split(':', 1)[0].strip()
    
    return message