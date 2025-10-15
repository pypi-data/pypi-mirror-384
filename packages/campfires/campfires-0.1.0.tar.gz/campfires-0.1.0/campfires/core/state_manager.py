"""
State management for Campfires using SQLite.
"""

import sqlite3
import asyncio
import aiosqlite
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

from .torch import Torch


logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages persistent state for campfires using SQLite.
    
    Stores torch history, campfire states, processing metrics,
    and other persistent data needed for the framework.
    """
    
    def __init__(self, db_path: str = "campfires_state.db"):
        """
        Initialize the state manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_lock = asyncio.Lock()
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize the database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            await db.commit()
        
        logger.info(f"State manager initialized with database: {self.db_path}")
    
    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        """Create database tables."""
        
        # Torches table for storing torch history
        await db.execute("""
            CREATE TABLE IF NOT EXISTS torches (
                torch_id TEXT PRIMARY KEY,
                claim TEXT NOT NULL,
                path TEXT,
                confidence REAL NOT NULL,
                metadata TEXT,  -- JSON
                timestamp TEXT NOT NULL,
                source_campfire TEXT,
                channel TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT
            )
        """)
        
        # Campfires table for storing campfire states
        await db.execute("""
            CREATE TABLE IF NOT EXISTS campfires (
                name TEXT PRIMARY KEY,
                is_running BOOLEAN NOT NULL,
                config TEXT,  -- JSON
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                processed_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0
            )
        """)
        
        # Processing history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                torch_id TEXT NOT NULL,
                campfire_name TEXT NOT NULL,
                camper_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                success BOOLEAN,
                error_message TEXT,
                processing_time_ms INTEGER,
                FOREIGN KEY (torch_id) REFERENCES torches (torch_id),
                FOREIGN KEY (campfire_name) REFERENCES campfires (name)
            )
        """)
        
        # Assets table for tracking Party Box assets
        await db.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_hash TEXT PRIMARY KEY,
                original_key TEXT NOT NULL,
                file_path TEXT,
                size_bytes INTEGER,
                content_type TEXT,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                metadata TEXT  -- JSON
            )
        """)
        
        # MCP messages table for debugging and audit
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mcp_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                message_type TEXT NOT NULL,
                data TEXT NOT NULL,  -- JSON
                timestamp TEXT NOT NULL,
                direction TEXT NOT NULL  -- 'sent' or 'received'
            )
        """)
        
        # Create indexes for better performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_torches_timestamp ON torches (timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_torches_campfire ON torches (source_campfire)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_torches_channel ON torches (channel)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_processing_history_torch ON processing_history (torch_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_processing_history_campfire ON processing_history (campfire_name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_assets_accessed ON assets (last_accessed)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_mcp_messages_channel ON mcp_messages (channel)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_mcp_messages_timestamp ON mcp_messages (timestamp)")
    
    async def save_torch(self, torch: Torch) -> None:
        """
        Save a torch to the database.
        
        Args:
            torch: Torch to save
        """
        async with self.db_lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO torches 
                    (torch_id, claim, path, confidence, metadata, timestamp, 
                     source_campfire, channel, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    torch.torch_id,
                    torch.claim,
                    torch.path,
                    torch.confidence,
                    json.dumps(torch.metadata),
                    torch.timestamp.isoformat(),
                    torch.source_campfire,
                    torch.channel,
                    datetime.utcnow().isoformat(),
                    torch.get_expiry_time().isoformat() if torch.get_expiry_time() else None
                ))
                await db.commit()
    
    async def get_torch(self, torch_id: str) -> Optional[Torch]:
        """
        Retrieve a torch by ID.
        
        Args:
            torch_id: Torch ID to retrieve
            
        Returns:
            Torch if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT torch_id, claim, path, confidence, metadata, timestamp, 
                       source_campfire, channel
                FROM torches WHERE torch_id = ?
            """, (torch_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return Torch(
                        torch_id=row[0],
                        claim=row[1],
                        path=row[2],
                        confidence=row[3],
                        metadata=json.loads(row[4]) if row[4] else {},
                        timestamp=datetime.fromisoformat(row[5]),
                        source_campfire=row[6],
                        channel=row[7]
                    )
                return None
    
    async def get_torches_by_campfire(
        self, 
        campfire_name: str, 
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Torch]:
        """
        Get torches from a specific campfire.
        
        Args:
            campfire_name: Name of the campfire
            limit: Maximum number of torches to return
            since: Only return torches after this timestamp
            
        Returns:
            List of torches
        """
        query = """
            SELECT torch_id, claim, path, confidence, metadata, timestamp, 
                   source_campfire, channel
            FROM torches 
            WHERE source_campfire = ?
        """
        params = [campfire_name]
        
        if since:
            query += " AND timestamp > ?"
            params.append(since.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                torches = []
                for row in rows:
                    torch = Torch(
                        torch_id=row[0],
                        claim=row[1],
                        path=row[2],
                        confidence=row[3],
                        metadata=json.loads(row[4]) if row[4] else {},
                        timestamp=datetime.fromisoformat(row[5]),
                        source_campfire=row[6],
                        channel=row[7]
                    )
                    torches.append(torch)
                
                return torches
    
    async def save_campfire_state(
        self, 
        name: str, 
        is_running: bool, 
        config: Dict[str, Any] = None
    ) -> None:
        """
        Save campfire state.
        
        Args:
            name: Campfire name
            is_running: Whether campfire is running
            config: Campfire configuration
        """
        async with self.db_lock:
            async with aiosqlite.connect(self.db_path) as db:
                now = datetime.utcnow().isoformat()
                
                await db.execute("""
                    INSERT OR REPLACE INTO campfires 
                    (name, is_running, config, created_at, last_active, processed_count, error_count)
                    VALUES (?, ?, ?, 
                            COALESCE((SELECT created_at FROM campfires WHERE name = ?), ?),
                            ?,
                            COALESCE((SELECT processed_count FROM campfires WHERE name = ?), 0),
                            COALESCE((SELECT error_count FROM campfires WHERE name = ?), 0))
                """, (
                    name, is_running, json.dumps(config or {}), 
                    name, now, now, name, name
                ))
                await db.commit()
    
    async def get_campfire_state(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get campfire state.
        
        Args:
            name: Campfire name
            
        Returns:
            Campfire state dictionary or None
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT name, is_running, config, created_at, last_active, 
                       processed_count, error_count
                FROM campfires WHERE name = ?
            """, (name,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'name': row[0],
                        'is_running': bool(row[1]),
                        'config': json.loads(row[2]) if row[2] else {},
                        'created_at': datetime.fromisoformat(row[3]),
                        'last_active': datetime.fromisoformat(row[4]),
                        'processed_count': row[5],
                        'error_count': row[6]
                    }
                return None
    
    async def record_processing_start(
        self, 
        torch_id: str, 
        campfire_name: str, 
        camper_name: str
    ) -> int:
        """
        Record the start of torch processing.
        
        Args:
            torch_id: Torch being processed
            campfire_name: Campfire doing the processing
            camper_name: Camper doing the processing
            
        Returns:
            Processing record ID
        """
        async with self.db_lock:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO processing_history 
                    (torch_id, campfire_name, camper_name, started_at)
                    VALUES (?, ?, ?, ?)
                """, (torch_id, campfire_name, camper_name, datetime.utcnow().isoformat()))
                
                record_id = cursor.lastrowid
                await db.commit()
                return record_id
    
    async def record_processing_complete(
        self, 
        record_id: int, 
        success: bool, 
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> None:
        """
        Record the completion of torch processing.
        
        Args:
            record_id: Processing record ID
            success: Whether processing succeeded
            error_message: Error message if failed
            processing_time_ms: Processing time in milliseconds
        """
        async with self.db_lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE processing_history 
                    SET completed_at = ?, success = ?, error_message = ?, processing_time_ms = ?
                    WHERE id = ?
                """, (
                    datetime.utcnow().isoformat(),
                    success,
                    error_message,
                    processing_time_ms,
                    record_id
                ))
                await db.commit()
                
                # Update campfire counters
                if success:
                    await db.execute("""
                        UPDATE campfires 
                        SET processed_count = processed_count + 1, last_active = ?
                        WHERE name = (SELECT campfire_name FROM processing_history WHERE id = ?)
                    """, (datetime.utcnow().isoformat(), record_id))
                else:
                    await db.execute("""
                        UPDATE campfires 
                        SET error_count = error_count + 1, last_active = ?
                        WHERE name = (SELECT campfire_name FROM processing_history WHERE id = ?)
                    """, (datetime.utcnow().isoformat(), record_id))
                
                await db.commit()
    
    async def save_asset_metadata(
        self, 
        asset_hash: str, 
        original_key: str, 
        file_path: Optional[str] = None,
        size_bytes: Optional[int] = None,
        content_type: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Save asset metadata.
        
        Args:
            asset_hash: Asset hash
            original_key: Original filename/key
            file_path: Path to stored file
            size_bytes: File size in bytes
            content_type: MIME content type
            metadata: Additional metadata
        """
        async with self.db_lock:
            async with aiosqlite.connect(self.db_path) as db:
                now = datetime.utcnow().isoformat()
                
                await db.execute("""
                    INSERT OR REPLACE INTO assets 
                    (asset_hash, original_key, file_path, size_bytes, content_type, 
                     created_at, last_accessed, access_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 
                            COALESCE((SELECT access_count FROM assets WHERE asset_hash = ?), 0),
                            ?)
                """, (
                    asset_hash, original_key, file_path, size_bytes, content_type,
                    now, now, asset_hash, json.dumps(metadata or {})
                ))
                await db.commit()
    
    async def record_asset_access(self, asset_hash: str) -> None:
        """
        Record an asset access.
        
        Args:
            asset_hash: Asset hash
        """
        async with self.db_lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE assets 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE asset_hash = ?
                """, (datetime.utcnow().isoformat(), asset_hash))
                await db.commit()
    
    async def log_mcp_message(
        self, 
        message_id: str, 
        channel: str, 
        message_type: str, 
        data: Dict[str, Any], 
        direction: str
    ) -> None:
        """
        Log an MCP message for debugging.
        
        Args:
            message_id: Message ID
            channel: Channel name
            message_type: Message type
            data: Message data
            direction: 'sent' or 'received'
        """
        async with self.db_lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO mcp_messages 
                    (message_id, channel, message_type, data, timestamp, direction)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    message_id, channel, message_type, 
                    json.dumps(data), datetime.utcnow().isoformat(), direction
                ))
                await db.commit()
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Clean up old data from the database.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()
        
        stats = {}
        
        async with self.db_lock:
            async with aiosqlite.connect(self.db_path) as db:
                # Clean up old torches
                cursor = await db.execute("""
                    DELETE FROM torches WHERE timestamp < ? OR expires_at < ?
                """, (cutoff_str, datetime.utcnow().isoformat()))
                stats['torches_deleted'] = cursor.rowcount
                
                # Clean up old processing history
                cursor = await db.execute("""
                    DELETE FROM processing_history WHERE started_at < ?
                """, (cutoff_str,))
                stats['processing_records_deleted'] = cursor.rowcount
                
                # Clean up old MCP messages
                cursor = await db.execute("""
                    DELETE FROM mcp_messages WHERE timestamp < ?
                """, (cutoff_str,))
                stats['mcp_messages_deleted'] = cursor.rowcount
                
                # Clean up unused assets (not accessed in the time period)
                cursor = await db.execute("""
                    DELETE FROM assets WHERE last_accessed < ?
                """, (cutoff_str,))
                stats['assets_deleted'] = cursor.rowcount
                
                await db.commit()
        
        logger.info(f"Cleanup completed: {stats}")
        return stats
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with various statistics
        """
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Torch statistics
            async with db.execute("SELECT COUNT(*) FROM torches") as cursor:
                stats['total_torches'] = (await cursor.fetchone())[0]
            
            async with db.execute("""
                SELECT COUNT(*) FROM torches 
                WHERE timestamp > datetime('now', '-24 hours')
            """) as cursor:
                stats['torches_last_24h'] = (await cursor.fetchone())[0]
            
            # Campfire statistics
            async with db.execute("SELECT COUNT(*) FROM campfires") as cursor:
                stats['total_campfires'] = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM campfires WHERE is_running = 1") as cursor:
                stats['running_campfires'] = (await cursor.fetchone())[0]
            
            # Processing statistics
            async with db.execute("SELECT COUNT(*) FROM processing_history") as cursor:
                stats['total_processing_records'] = (await cursor.fetchone())[0]
            
            async with db.execute("""
                SELECT COUNT(*) FROM processing_history 
                WHERE success = 1 AND completed_at IS NOT NULL
            """) as cursor:
                stats['successful_processing'] = (await cursor.fetchone())[0]
            
            async with db.execute("""
                SELECT COUNT(*) FROM processing_history 
                WHERE success = 0 AND completed_at IS NOT NULL
            """) as cursor:
                stats['failed_processing'] = (await cursor.fetchone())[0]
            
            # Asset statistics
            async with db.execute("SELECT COUNT(*) FROM assets") as cursor:
                stats['total_assets'] = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT SUM(size_bytes) FROM assets") as cursor:
                result = await cursor.fetchone()
                stats['total_asset_size_bytes'] = result[0] if result[0] else 0
            
            # MCP statistics
            async with db.execute("SELECT COUNT(*) FROM mcp_messages") as cursor:
                stats['total_mcp_messages'] = (await cursor.fetchone())[0]
            
            return stats
    
    async def close(self) -> None:
        """Close the state manager."""
        # SQLite connections are closed automatically with aiosqlite
        logger.info("State manager closed")


# Convenience functions for common operations
async def create_state_manager(db_path: str = "campfires_state.db") -> StateManager:
    """
    Create and initialize a state manager.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Initialized StateManager
    """
    manager = StateManager(db_path)
    await manager.initialize()
    return manager