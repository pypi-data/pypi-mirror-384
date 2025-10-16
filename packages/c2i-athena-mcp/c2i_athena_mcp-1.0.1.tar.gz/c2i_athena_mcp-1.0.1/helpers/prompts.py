"""
File utilities for reading instruction and configuration files.
"""

import os


def read_instruction_file(filename: str, instructions_dir: str = None) -> str:
    """
    Read instruction files from the instructions directory.
    
    General utility function for loading markdown instruction files that contain
    methodologies, guidelines, or reference documentation. Supports both specific
    filenames and flexible directory paths.
    
    Args:
        filename: Name of the instruction file (e.g., "methodology.md")
        instructions_dir: Optional custom path to instructions directory.
                         Defaults to 'instructions' subdirectory relative to server.py.
    
    Returns:
        str: Complete content of the instruction file
        
    Raises:
        FileNotFoundError: If the instruction file cannot be found
        Exception: For other file reading errors
        
    Example:
        content = read_instruction_file("mrd_detection_rate_calculation.md")
        content = read_instruction_file("custom_guide.md", "/path/to/custom/dir")
    """
    if instructions_dir is None:
        # Default to instructions subdirectory relative to the athena_mcp_server directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from utils to athena_mcp_server directory, then to instructions
        athena_mcp_server_dir = os.path.dirname(current_dir)
        instructions_dir = os.path.join(athena_mcp_server_dir, "instructions")
    
    file_path = os.path.join(instructions_dir, filename)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Instruction file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()