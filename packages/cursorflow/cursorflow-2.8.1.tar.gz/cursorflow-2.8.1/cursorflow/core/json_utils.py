"""
JSON Serialization Utilities

Handles conversion of numpy and other non-standard types to JSON-safe Python types.
Essential for mockup comparison and any feature using PIL/numpy for image analysis.
"""

import json
from typing import Any
from pathlib import Path


def safe_json_serialize(obj: Any) -> Any:
    """
    Convert any Python/numpy type to JSON-safe type
    
    Handles:
    - numpy scalars (bool_, int_, float_)
    - numpy arrays (ndarray)
    - Other non-serializable types (converts to string)
    
    Args:
        obj: Any object that might not be JSON serializable
        
    Returns:
        JSON-safe Python type
    """
    # numpy scalars (bool_, int64, float64, etc.)
    if hasattr(obj, 'item'):
        return obj.item()
    
    # numpy arrays
    if hasattr(obj, 'tolist'):
        return obj.tolist()
    
    # Fallback for anything else
    return str(obj)


def safe_json_dump(data: Any, file_path: str, indent: int = 2) -> None:
    """
    Safely dump data to JSON file with numpy type handling
    
    Args:
        data: Data to serialize
        file_path: Path to output file
        indent: JSON indentation level
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent, default=safe_json_serialize)