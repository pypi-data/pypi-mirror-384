
# Copyright (C) 2025 The Agent A Open Source Project
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import os
import sys
from pathlib import Path

_status_tracker = {}

CODE_FILE_EXTENSIONS = {
    '.ada', '.aj', '.apl', '.applescript', '.as', '.asm', '.awk', '.bas', 
    '.bash', '.c', '.carbon', '.cfg', '.cl', '.clj', '.cljs', '.cob', '.conf', 
    '.config', '.cpp', '.cs', '.css', '.csv', '.d', '.dart', '.elm', '.erl', 
    '.ex', '.exs', '.f90', '.fs', '.fth', '.go', '.groovy', '.h', '.hpp', 
    '.hs', '.html', '.idr', '.ini', '.java', '.jl', '.js', '.json', '.jsx', 
    '.kt', '.lgo', '.lisp', '.log', '.lua', '.m', '.md', '.ml', '.mod', 
    '.mojo', '.nim', '.nix', '.pas', '.php', '.pl', '.pro', '.py', '.r', 
    '.rb', '.red', '.rkt', '.rs', '.scala', '.scm', '.sh', '.sim', '.sql', 
    '.st', '.swift', '.ts', '.tsx', '.tsv', '.txt', '.vb', '.vbs', '.xml', 
    '.yaml', '.yml', '.zig', '.zsh', '.toml'
}

def update_status(file_path: str, message: str, is_final: bool = False):
    """
    Prints a status message for a file, overwriting the previous status for the same file.
    """
    global _status_tracker
    
    full_message = f" - {file_path}... {message}"
    
    is_first_update = file_path not in _status_tracker
    prefix = "" if is_first_update else "\r"
    
    last_len = _status_tracker.get(file_path, 0)
    
    # Pad with spaces to overwrite the previous line completely
    padded_message = full_message.ljust(last_len)
    
    sys.stdout.write(f"{prefix}{padded_message}")
    
    _status_tracker[file_path] = len(full_message)
    
    if is_final:
        sys.stdout.write("\n")
        del _status_tracker[file_path]
    
    sys.stdout.flush()

def get_file_hash(file_path):
    """Calculates the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def discover_mimetype(file_path: str) -> str | None:
    """
    Determines the mimetype of a file, treating code files as plain text.
    Returns 'text/plain' for code files or files without extensions, 
    otherwise None to allow for SDK inference.
    """
    _, extension = os.path.splitext(file_path)
    if not extension or extension.lower() in CODE_FILE_EXTENSIONS:
        return 'text/plain'
    return None

def format_file_size(bytes_count: int) -> str:
    """
    Converts byte count to human-readable format (B, KB, MB, GB).
    
    Args:
        bytes_count: Integer byte count
        
    Returns:
        Formatted string like "5.2KB", "1.3MB", "2.1GB"
    """
    if bytes_count <= 0:
        return "0B"
    
    if bytes_count < 1024:
        return f"{bytes_count}B"
    elif bytes_count < 1024 ** 2:
        return f"{bytes_count / 1024:.1f}KB"
    elif bytes_count < 1024 ** 3:
        return f"{bytes_count / (1024 ** 2):.1f}MB"
    else:
        return f"{bytes_count / (1024 ** 3):.1f}GB"

def format_token_count(token_count: int) -> str:
    """
    Formats token count in K/M notation for readability.
    
    Args:
        token_count: Integer token count
        
    Returns:
        Formatted string like "1.2K", "500", "2.5M"
    """
    if token_count <= 0:
        return "0"
    
    if token_count < 1000:
        return str(token_count)
    elif token_count < 1000000:
        return f"{token_count / 1000:.1f}K"
    else:
        return f"{token_count / 1000000:.1f}M"

def calculate_file_size(file_path: str) -> int:
    """
    Safely calculates the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes, or 0 if file doesn't exist or is inaccessible
    """
    try:
        p = Path(file_path)
        if p.is_file():
            return os.path.getsize(file_path)
        return 0
    except OSError:
        return 0

def estimate_tokens(bytes_count: int) -> int:
    """
    Estimates token count from byte count using 4 bytes per token heuristic.
    
    Args:
        bytes_count: File size in bytes
        
    Returns:
        Estimated token count
    """
    if bytes_count <= 0:
        return 0
    return bytes_count // 4
