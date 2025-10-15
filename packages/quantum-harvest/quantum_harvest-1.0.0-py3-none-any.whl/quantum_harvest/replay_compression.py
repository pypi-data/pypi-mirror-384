#!/usr/bin/env python3
"""
Replay File Compression Utilities

This module provides functions to compress and decompress replay files
while maintaining backward compatibility with existing JSON files.
"""

import json
import gzip
import os
from typing import Any, Dict, List, Union
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types and other non-serializable types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (bool, int, float, str, list, dict, type(None))):
            return obj
        return super().default(obj)


def compress_replay_data(data: List[Dict[str, Any]], file_path: str) -> str:
    """
    Compress replay data and save to a .json.gz file.
    
    Args:
        data: The replay data to compress
        file_path: Path where to save the compressed file
        
    Returns:
        The path to the saved compressed file
    """
    # Ensure the file has .json.gz extension
    if not file_path.endswith('.json.gz'):
        if file_path.endswith('.json'):
            file_path = file_path[:-5] + '.json.gz'
        else:
            file_path += '.json.gz'
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Compress and save
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
        json.dump(data, f, indent=2, cls=NumpyEncoder)
    
    return file_path


def decompress_replay_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Decompress replay data from a .json.gz file.
    
    Args:
        file_path: Path to the compressed file
        
    Returns:
        The decompressed replay data
    """
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def load_replay_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load replay data from either a compressed (.json.gz) or uncompressed (.json) file.
    This function automatically detects the file type and handles both formats.
    
    Args:
        file_path: Path to the replay file (compressed or uncompressed)
        
    Returns:
        The replay data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        Exception: For other errors during loading
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Replay file not found: {file_path}")
    
    # Check if file is compressed
    if file_path.endswith('.json.gz'):
        return decompress_replay_data(file_path)
    elif file_path.endswith('.json'):
        # Load uncompressed JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Try to detect file type by reading first few bytes
        with open(file_path, 'rb') as f:
            header = f.read(2)
            if header == b'\x1f\x8b':  # gzip magic number
                return decompress_replay_data(file_path)
            else:
                # Assume it's uncompressed JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)


def save_replay_data(data: List[Dict[str, Any]], file_path: str, compress: bool = True) -> str:
    """
    Save replay data to a file, optionally compressed.
    
    Args:
        data: The replay data to save
        file_path: Path where to save the file
        compress: Whether to compress the file (default: True)
        
    Returns:
        The path to the saved file
    """
    if compress:
        return compress_replay_data(data, file_path)
    else:
        # Save uncompressed JSON
        if not file_path.endswith('.json'):
            file_path += '.json'
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, cls=NumpyEncoder)
        
        return file_path


def get_compression_ratio(original_path: str, compressed_path: str) -> float:
    """
    Calculate the compression ratio between original and compressed files.
    
    Args:
        original_path: Path to the original file
        compressed_path: Path to the compressed file
        
    Returns:
        Compression ratio (compressed_size / original_size)
    """
    original_size = os.path.getsize(original_path)
    compressed_size = os.path.getsize(compressed_path)
    return compressed_size / original_size if original_size > 0 else 0.0


def is_compressed_file(file_path: str) -> bool:
    """
    Check if a file is compressed based on its extension or content.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is compressed, False otherwise
    """
    if file_path.endswith('.json.gz'):
        return True
    elif file_path.endswith('.json'):
        return False
    else:
        # Check file content
        try:
            with open(file_path, 'rb') as f:
                header = f.read(2)
                return header == b'\x1f\x8b'  # gzip magic number
        except:
            return False
