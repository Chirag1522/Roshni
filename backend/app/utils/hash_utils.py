"""
Hashing utilities for bill integrity and data verification.
"""
import hashlib
import json
from typing import Union

def sha256_hash(data: Union[str, dict, bytes]) -> str:
    """
    Generate SHA256 hash of data.
    
    Args:
        data: String, dict, or bytes to hash
        
    Returns:
        Hex string of SHA256 hash
    """
    if isinstance(data, dict):
        # Sort dict for consistent hashing
        data = json.dumps(data, sort_keys=True).encode()
    elif isinstance(data, str):
        data = data.encode()
    
    return hashlib.sha256(data).hexdigest()

def verify_hash(data: Union[str, dict, bytes], provided_hash: str) -> bool:
    """
    Verify data against provided hash.
    """
    calculated = sha256_hash(data)
    return calculated == provided_hash