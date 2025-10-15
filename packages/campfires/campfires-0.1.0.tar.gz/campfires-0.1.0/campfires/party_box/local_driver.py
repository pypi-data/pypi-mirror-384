"""
Local filesystem implementation of BoxDriver.
"""

import os
import aiofiles
import asyncio
from pathlib import Path
from typing import Union, BinaryIO, List, Dict, Any

from .box_driver import BoxDriver


class LocalDriver(BoxDriver):
    """
    Local filesystem implementation of the BoxDriver.
    
    Stores assets in a local directory with checksumming to prevent
    duplicate writes and automatic cleanup of old files.
    """
    
    def __init__(self, base_path: str = "./party_box", config: Dict[str, Any] = None):
        """
        Initialize the local driver.
        
        Args:
            base_path: Base directory for storing assets
            config: Additional configuration
        """
        super().__init__(config)
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.base_path / "images").mkdir(exist_ok=True)
        (self.base_path / "audio").mkdir(exist_ok=True)
        (self.base_path / "documents").mkdir(exist_ok=True)
        (self.base_path / "other").mkdir(exist_ok=True)
    
    async def put(self, key: str, data: Union[bytes, BinaryIO]) -> str:
        """
        Store an asset in the local filesystem.
        
        Args:
            key: Suggested filename for the asset
            data: Asset data as bytes or file-like object
            
        Returns:
            Unique hash for retrieving the asset
        """
        # Read data if it's a file-like object
        if hasattr(data, 'read'):
            if asyncio.iscoroutinefunction(data.read):
                content = await data.read()
            else:
                content = data.read()
        else:
            content = data
        
        # Generate hash for the content
        asset_hash = self.generate_hash(content)
        
        # Check if asset already exists (deduplication)
        if await self.exists(asset_hash):
            return asset_hash
        
        # Determine subdirectory based on file extension
        file_ext = Path(key).suffix.lower()
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
            subdir = "images"
        elif file_ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
            subdir = "audio"
        elif file_ext in ['.pdf', '.doc', '.docx', '.txt', '.md']:
            subdir = "documents"
        else:
            subdir = "other"
        
        # Create file path
        file_path = self.base_path / subdir / f"{asset_hash}{file_ext}"
        
        # Write file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Track metadata
        self._track_asset_metadata(asset_hash, {
            'original_key': key,
            'file_path': str(file_path),
            'size': len(content),
            'file_extension': file_ext,
            'subdirectory': subdir
        })
        
        return asset_hash
    
    async def get(self, asset_hash: str) -> str:
        """
        Retrieve an asset by its hash.
        
        Args:
            asset_hash: Unique hash of the asset
            
        Returns:
            File path to the asset
        """
        metadata = self.get_asset_metadata(asset_hash)
        
        if not metadata:
            # Try to find the file by searching all subdirectories
            for subdir in ["images", "audio", "documents", "other"]:
                subdir_path = self.base_path / subdir
                for file_path in subdir_path.glob(f"{asset_hash}.*"):
                    return str(file_path)
            
            raise FileNotFoundError(f"Asset not found: {asset_hash}")
        
        file_path = metadata.get('file_path')
        if file_path and Path(file_path).exists():
            return file_path
        else:
            raise FileNotFoundError(f"Asset file not found: {asset_hash}")
    
    async def get_bytes(self, asset_hash: str) -> bytes:
        """
        Retrieve an asset as bytes.
        
        Args:
            asset_hash: Unique hash of the asset
            
        Returns:
            Asset data as bytes
        """
        file_path = await self.get(asset_hash)
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def exists(self, asset_hash: str) -> bool:
        """
        Check if an asset exists.
        
        Args:
            asset_hash: Unique hash of the asset
            
        Returns:
            True if asset exists, False otherwise
        """
        try:
            await self.get(asset_hash)
            return True
        except FileNotFoundError:
            return False
    
    async def delete(self, asset_hash: str) -> bool:
        """
        Delete an asset.
        
        Args:
            asset_hash: Unique hash of the asset
            
        Returns:
            True if asset was deleted, False if not found
        """
        try:
            file_path = await self.get(asset_hash)
            Path(file_path).unlink()
            
            # Remove from metadata tracking
            self._asset_metadata.pop(asset_hash, None)
            
            return True
        except FileNotFoundError:
            return False
    
    async def list_assets(self) -> List[str]:
        """
        List all asset hashes.
        
        Returns:
            List of asset hashes
        """
        asset_hashes = set()
        
        # Scan all subdirectories
        for subdir in ["images", "audio", "documents", "other"]:
            subdir_path = self.base_path / subdir
            if subdir_path.exists():
                for file_path in subdir_path.iterdir():
                    if file_path.is_file():
                        # Extract hash from filename (before the extension)
                        asset_hash = file_path.stem
                        asset_hashes.add(asset_hash)
        
        return list(asset_hashes)
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """
        Get detailed storage information.
        
        Returns:
            Dictionary with storage details
        """
        stats = await self.get_stats()
        
        # Add local-specific information
        subdirs = {}
        total_files = 0
        
        for subdir in ["images", "audio", "documents", "other"]:
            subdir_path = self.base_path / subdir
            if subdir_path.exists():
                files = list(subdir_path.iterdir())
                file_count = len([f for f in files if f.is_file()])
                subdirs[subdir] = file_count
                total_files += file_count
        
        stats.update({
            'base_path': str(self.base_path),
            'subdirectories': subdirs,
            'total_files': total_files
        })
        
        return stats
    
    def get_asset_url(self, asset_hash: str) -> str:
        """
        Get a file:// URL for the asset.
        
        Args:
            asset_hash: Asset hash
            
        Returns:
            File URL string
        """
        try:
            # This is a synchronous wrapper for the async get method
            # In a real application, you might want to handle this differently
            metadata = self.get_asset_metadata(asset_hash)
            file_path = metadata.get('file_path')
            
            if file_path:
                return f"file://{Path(file_path).absolute()}"
            else:
                return f"file://{self.base_path.absolute()}/{asset_hash}"
        except Exception:
            return f"file://{self.base_path.absolute()}/{asset_hash}"
    
    async def cleanup_empty_dirs(self) -> None:
        """
        Remove empty subdirectories.
        """
        for subdir in ["images", "audio", "documents", "other"]:
            subdir_path = self.base_path / subdir
            if subdir_path.exists() and not any(subdir_path.iterdir()):
                try:
                    subdir_path.rmdir()
                except OSError:
                    pass  # Directory not empty or other error
    
    def __str__(self) -> str:
        """String representation of the driver."""
        return f"LocalDriver({self.base_path})"