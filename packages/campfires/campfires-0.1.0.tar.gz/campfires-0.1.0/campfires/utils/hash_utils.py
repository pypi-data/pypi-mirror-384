"""
Hash and checksum utilities for asset management and data integrity.
"""

import hashlib
import hmac
import secrets
import base64
import logging
from typing import Union, BinaryIO, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


def generate_hash(
    data: Union[str, bytes, Path], 
    algorithm: str = 'sha256',
    encoding: str = 'utf-8'
) -> str:
    """
    Generate a hash for the given data.
    
    Args:
        data: Data to hash (string, bytes, or file path)
        algorithm: Hash algorithm to use (sha256, sha1, md5, etc.)
        encoding: Encoding for string data
        
    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.new(algorithm)
    
    if isinstance(data, str):
        hasher.update(data.encode(encoding))
    elif isinstance(data, bytes):
        hasher.update(data)
    elif isinstance(data, Path):
        # Hash file contents
        try:
            with open(data, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        except Exception as e:
            logger.error(f"Error hashing file {data}: {e}")
            raise
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")
    
    return hasher.hexdigest()


def generate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Generate a hash for a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hexadecimal hash string
    """
    return generate_hash(Path(file_path), algorithm)


def verify_checksum(
    data: Union[str, bytes, Path], 
    expected_hash: str, 
    algorithm: str = 'sha256',
    encoding: str = 'utf-8'
) -> bool:
    """
    Verify data against an expected hash.
    
    Args:
        data: Data to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm used
        encoding: Encoding for string data
        
    Returns:
        True if hash matches, False otherwise
    """
    try:
        actual_hash = generate_hash(data, algorithm, encoding)
        return hmac.compare_digest(actual_hash.lower(), expected_hash.lower())
    except Exception as e:
        logger.error(f"Error verifying checksum: {e}")
        return False


def verify_file_checksum(
    file_path: Union[str, Path], 
    expected_hash: str, 
    algorithm: str = 'sha256'
) -> bool:
    """
    Verify a file against an expected hash.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected hash value
        algorithm: Hash algorithm used
        
    Returns:
        True if hash matches, False otherwise
    """
    return verify_checksum(Path(file_path), expected_hash, algorithm)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        Base64-encoded token string
    """
    token_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(token_bytes).decode('ascii').rstrip('=')


def generate_uuid_hash(data: str, namespace: str = "campfires") -> str:
    """
    Generate a UUID-like hash from data and namespace.
    
    Args:
        data: Data to hash
        namespace: Namespace for the hash
        
    Returns:
        UUID-formatted hash string
    """
    combined = f"{namespace}:{data}"
    hash_bytes = hashlib.sha256(combined.encode('utf-8')).digest()
    
    # Format as UUID (8-4-4-4-12)
    hex_string = hash_bytes[:16].hex()
    return f"{hex_string[:8]}-{hex_string[8:12]}-{hex_string[12:16]}-{hex_string[16:20]}-{hex_string[20:32]}"


def hash_stream(stream: BinaryIO, algorithm: str = 'sha256', chunk_size: int = 8192) -> str:
    """
    Generate hash for a stream of data.
    
    Args:
        stream: Binary stream to hash
        algorithm: Hash algorithm to use
        chunk_size: Size of chunks to read
        
    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.new(algorithm)
    
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        hasher.update(chunk)
    
    return hasher.hexdigest()


def generate_content_hash(content: str, metadata: dict = None) -> str:
    """
    Generate a hash that includes both content and metadata.
    
    Args:
        content: Main content to hash
        metadata: Optional metadata to include in hash
        
    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.sha256()
    
    # Hash content
    hasher.update(content.encode('utf-8'))
    
    # Hash metadata if provided
    if metadata:
        # Sort keys for consistent hashing
        sorted_items = sorted(metadata.items())
        for key, value in sorted_items:
            hasher.update(f"{key}:{value}".encode('utf-8'))
    
    return hasher.hexdigest()


def generate_torch_id(claim: str, source: str, timestamp: float) -> str:
    """
    Generate a unique ID for a Torch based on its content.
    
    Args:
        claim: The torch claim/content
        source: Source campfire identifier
        timestamp: Timestamp of creation
        
    Returns:
        Unique torch ID
    """
    combined = f"{claim}:{source}:{timestamp}"
    return generate_hash(combined)[:16]  # Use first 16 characters


def generate_asset_id(file_path: Union[str, Path], content_hash: str = None) -> str:
    """
    Generate a unique ID for an asset.
    
    Args:
        file_path: Path to the asset file
        content_hash: Optional pre-computed content hash
        
    Returns:
        Unique asset ID
    """
    path = Path(file_path)
    
    if content_hash is None:
        try:
            content_hash = generate_file_hash(path)
        except Exception:
            # Fallback to path-based hash if file doesn't exist
            content_hash = generate_hash(str(path))
    
    # Combine filename and content hash
    combined = f"{path.name}:{content_hash}"
    return generate_hash(combined)[:12]  # Use first 12 characters


class HashValidator:
    """
    Utility class for validating hashes and checksums.
    """
    
    SUPPORTED_ALGORITHMS = {
        'md5': 32,
        'sha1': 40,
        'sha224': 56,
        'sha256': 64,
        'sha384': 96,
        'sha512': 128,
    }
    
    @classmethod
    def is_valid_hash(cls, hash_string: str, algorithm: str = None) -> bool:
        """
        Check if a hash string is valid.
        
        Args:
            hash_string: Hash string to validate
            algorithm: Expected algorithm (optional)
            
        Returns:
            True if hash is valid format
        """
        if not isinstance(hash_string, str):
            return False
        
        # Check if it's hexadecimal
        try:
            int(hash_string, 16)
        except ValueError:
            return False
        
        # Check length if algorithm specified
        if algorithm:
            expected_length = cls.SUPPORTED_ALGORITHMS.get(algorithm.lower())
            if expected_length and len(hash_string) != expected_length:
                return False
        
        return True
    
    @classmethod
    def detect_algorithm(cls, hash_string: str) -> Optional[str]:
        """
        Detect the hash algorithm based on string length.
        
        Args:
            hash_string: Hash string to analyze
            
        Returns:
            Detected algorithm name or None
        """
        if not cls.is_valid_hash(hash_string):
            return None
        
        length = len(hash_string)
        for algorithm, expected_length in cls.SUPPORTED_ALGORITHMS.items():
            if length == expected_length:
                return algorithm
        
        return None
    
    @classmethod
    def validate_file_integrity(
        cls, 
        file_path: Union[str, Path], 
        expected_hash: str, 
        algorithm: str = None
    ) -> dict:
        """
        Validate file integrity and return detailed results.
        
        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm (auto-detected if None)
            
        Returns:
            Dictionary with validation results
        """
        path = Path(file_path)
        result = {
            'file_path': str(path),
            'file_exists': path.exists(),
            'expected_hash': expected_hash,
            'actual_hash': None,
            'algorithm': algorithm,
            'valid': False,
            'error': None
        }
        
        if not result['file_exists']:
            result['error'] = 'File does not exist'
            return result
        
        # Auto-detect algorithm if not provided
        if not algorithm:
            algorithm = cls.detect_algorithm(expected_hash)
            if not algorithm:
                result['error'] = 'Could not detect hash algorithm'
                return result
            result['algorithm'] = algorithm
        
        try:
            actual_hash = generate_file_hash(path, algorithm)
            result['actual_hash'] = actual_hash
            result['valid'] = verify_checksum(path, expected_hash, algorithm)
        except Exception as e:
            result['error'] = str(e)
        
        return result


# Convenience functions for common operations
def quick_hash(data: Union[str, bytes]) -> str:
    """Quick SHA256 hash for simple data."""
    return generate_hash(data, 'sha256')


def quick_file_hash(file_path: Union[str, Path]) -> str:
    """Quick SHA256 hash for a file."""
    return generate_file_hash(file_path, 'sha256')


def secure_compare(a: str, b: str) -> bool:
    """Securely compare two strings to prevent timing attacks."""
    return hmac.compare_digest(a, b)