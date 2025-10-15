"""
Abstract BoxDriver interface for Party Box storage backends.
"""

import hashlib
import time
from abc import ABC, abstractmethod
from typing import Union, BinaryIO, List, Dict, Any
from pathlib import Path


class BoxDriver(ABC):
    """
    Abstract base class for Party Box storage drivers.
    
    The Party Box stores assets (images, audio, etc.) and provides
    a driver-agnostic interface for different storage backends.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the box driver.
        
        Args:
            config: Configuration dictionary for the driver
        """
        self.config = config or {}
        self._asset_metadata = {}  # Track asset metadata
    
    @abstractmethod
    async def put(self, key: str, data: Union[bytes, BinaryIO]) -> str:
        """
        Store an asset and return a unique hash.
        
        Args:
            key: Suggested key/filename for the asset
            data: Asset data as bytes or file-like object
            
        Returns:
            Unique hash/key for retrieving the asset
        """
        pass
    
    @abstractmethod
    async def get(self, asset_hash: str) -> Union[str, bytes, BinaryIO]:
        """
        Retrieve an asset by its hash.
        
        Args:
            asset_hash: Unique hash/key of the asset
            
        Returns:
            Asset data, file path, or file-like object
        """
        pass
    
    @abstractmethod
    async def exists(self, asset_hash: str) -> bool:
        """
        Check if an asset exists.
        
        Args:
            asset_hash: Unique hash/key of the asset
            
        Returns:
            True if asset exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, asset_hash: str) -> bool:
        """
        Delete an asset.
        
        Args:
            asset_hash: Unique hash/key of the asset
            
        Returns:
            True if asset was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def list_assets(self) -> List[str]:
        """
        List all asset hashes.
        
        Returns:
            List of asset hashes
        """
        pass
    
    async def cleanup_old_assets(self, max_age_minutes: int = 20) -> int:
        """
        Remove assets older than the specified age.
        
        Args:
            max_age_minutes: Maximum age in minutes (default: 20)
            
        Returns:
            Number of assets deleted
        """
        current_time = time.time()
        max_age_seconds = max_age_minutes * 60
        deleted_count = 0
        
        try:
            assets = await self.list_assets()
            
            for asset_hash in assets:
                metadata = self._asset_metadata.get(asset_hash, {})
                created_time = metadata.get('created_time', current_time)
                
                if (current_time - created_time) > max_age_seconds:
                    if await self.delete(asset_hash):
                        deleted_count += 1
                        # Remove from metadata tracking
                        self._asset_metadata.pop(asset_hash, None)
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        return deleted_count
    
    def generate_hash(self, data: Union[bytes, str]) -> str:
        """
        Generate a hash for the given data.
        
        Args:
            data: Data to hash
            
        Returns:
            SHA-256 hash as hexadecimal string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()[:16]  # Use first 16 chars
    
    def _track_asset_metadata(self, asset_hash: str, metadata: Dict[str, Any]) -> None:
        """
        Track metadata for an asset.
        
        Args:
            asset_hash: Asset hash
            metadata: Metadata dictionary
        """
        self._asset_metadata[asset_hash] = {
            'created_time': time.time(),
            **metadata
        }
    
    def get_asset_metadata(self, asset_hash: str) -> Dict[str, Any]:
        """
        Get metadata for an asset.
        
        Args:
            asset_hash: Asset hash
            
        Returns:
            Metadata dictionary
        """
        return self._asset_metadata.get(asset_hash, {})
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        assets = await self.list_assets()
        total_assets = len(assets)
        
        # Calculate total size and age stats
        current_time = time.time()
        total_size = 0
        oldest_asset = current_time
        newest_asset = 0
        
        for asset_hash in assets:
            metadata = self.get_asset_metadata(asset_hash)
            created_time = metadata.get('created_time', current_time)
            size = metadata.get('size', 0)
            
            total_size += size
            oldest_asset = min(oldest_asset, created_time)
            newest_asset = max(newest_asset, created_time)
        
        return {
            'total_assets': total_assets,
            'total_size_bytes': total_size,
            'oldest_asset_age_seconds': current_time - oldest_asset if total_assets > 0 else 0,
            'newest_asset_age_seconds': current_time - newest_asset if total_assets > 0 else 0,
            'driver_type': self.__class__.__name__
        }
    
    def __str__(self) -> str:
        """String representation of the driver."""
        return f"{self.__class__.__name__}()"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}(config={self.config})"