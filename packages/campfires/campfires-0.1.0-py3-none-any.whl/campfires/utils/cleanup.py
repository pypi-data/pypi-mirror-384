"""
Asset cleanup utilities for managing storage and removing old data.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class CleanupRule:
    """
    Defines a cleanup rule for assets.
    """
    name: str
    max_age_days: Optional[int] = None
    max_size_mb: Optional[int] = None
    file_patterns: List[str] = None
    keep_count: Optional[int] = None
    condition_func: Optional[Callable[[Path], bool]] = None
    
    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = []


@dataclass
class CleanupResult:
    """
    Result of a cleanup operation.
    """
    files_removed: int = 0
    bytes_freed: int = 0
    errors: List[str] = None
    duration_seconds: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class AssetCleanup:
    """
    Manages cleanup of assets based on various criteria.
    """
    
    def __init__(self, base_directory: Union[str, Path]):
        """
        Initialize asset cleanup manager.
        
        Args:
            base_directory: Base directory for cleanup operations
        """
        self.base_directory = Path(base_directory)
        self.rules: List[CleanupRule] = []
        
        # Default cleanup rules
        self._add_default_rules()
    
    def _add_default_rules(self):
        """Add default cleanup rules."""
        # Remove files older than 30 days
        self.add_rule(CleanupRule(
            name="old_files",
            max_age_days=30,
            file_patterns=["*"]
        ))
        
        # Remove temporary files older than 1 day
        self.add_rule(CleanupRule(
            name="temp_files",
            max_age_days=1,
            file_patterns=["*.tmp", "*.temp", "*.cache"]
        ))
        
        # Keep only last 100 log files
        self.add_rule(CleanupRule(
            name="log_files",
            keep_count=100,
            file_patterns=["*.log"]
        ))
    
    def add_rule(self, rule: CleanupRule) -> None:
        """
        Add a cleanup rule.
        
        Args:
            rule: CleanupRule to add
        """
        self.rules.append(rule)
        logger.debug(f"Added cleanup rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove a cleanup rule by name.
        
        Args:
            rule_name: Name of the rule to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.debug(f"Removed cleanup rule: {rule_name}")
                return True
        return False
    
    def get_files_for_rule(self, rule: CleanupRule) -> List[Path]:
        """
        Get files that match a cleanup rule.
        
        Args:
            rule: CleanupRule to match against
            
        Returns:
            List of matching file paths
        """
        matching_files = []
        
        if not self.base_directory.exists():
            return matching_files
        
        # Find files matching patterns
        for pattern in rule.file_patterns:
            try:
                for file_path in self.base_directory.rglob(pattern):
                    if file_path.is_file():
                        matching_files.append(file_path)
            except Exception as e:
                logger.error(f"Error finding files with pattern {pattern}: {e}")
        
        # Apply additional filters
        filtered_files = []
        
        for file_path in matching_files:
            try:
                # Check custom condition
                if rule.condition_func and not rule.condition_func(file_path):
                    continue
                
                # Check age
                if rule.max_age_days is not None:
                    file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age.days <= rule.max_age_days:
                        continue
                
                # Check size (individual file)
                if rule.max_size_mb is not None:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    if file_size_mb <= rule.max_size_mb:
                        continue
                
                filtered_files.append(file_path)
                
            except Exception as e:
                logger.error(f"Error checking file {file_path}: {e}")
        
        # Apply keep_count filter (keep newest files)
        if rule.keep_count is not None and len(filtered_files) > rule.keep_count:
            # Sort by modification time (newest first)
            filtered_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            # Keep only the files beyond the keep_count
            filtered_files = filtered_files[rule.keep_count:]
        
        return filtered_files
    
    async def cleanup_by_rule(self, rule: CleanupRule, dry_run: bool = False) -> CleanupResult:
        """
        Perform cleanup based on a specific rule.
        
        Args:
            rule: CleanupRule to apply
            dry_run: If True, don't actually delete files
            
        Returns:
            CleanupResult with operation details
        """
        start_time = datetime.now()
        result = CleanupResult()
        
        try:
            files_to_remove = self.get_files_for_rule(rule)
            
            logger.info(f"Cleanup rule '{rule.name}': Found {len(files_to_remove)} files to remove")
            
            for file_path in files_to_remove:
                try:
                    file_size = file_path.stat().st_size
                    
                    if not dry_run:
                        file_path.unlink()
                        logger.debug(f"Removed file: {file_path}")
                    else:
                        logger.debug(f"Would remove file: {file_path}")
                    
                    result.files_removed += 1
                    result.bytes_freed += file_size
                    
                except Exception as e:
                    error_msg = f"Error removing {file_path}: {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
                
                # Yield control to allow other operations
                await asyncio.sleep(0)
        
        except Exception as e:
            error_msg = f"Error in cleanup rule '{rule.name}': {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)
        
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        return result
    
    async def cleanup_all(self, dry_run: bool = False) -> Dict[str, CleanupResult]:
        """
        Perform cleanup using all rules.
        
        Args:
            dry_run: If True, don't actually delete files
            
        Returns:
            Dictionary mapping rule names to CleanupResults
        """
        results = {}
        
        logger.info(f"Starting cleanup with {len(self.rules)} rules (dry_run={dry_run})")
        
        for rule in self.rules:
            try:
                result = await self.cleanup_by_rule(rule, dry_run)
                results[rule.name] = result
                
                logger.info(
                    f"Rule '{rule.name}': Removed {result.files_removed} files, "
                    f"freed {result.bytes_freed / (1024*1024):.2f} MB"
                )
                
            except Exception as e:
                error_result = CleanupResult()
                error_result.errors.append(f"Failed to execute rule '{rule.name}': {e}")
                results[rule.name] = error_result
                logger.error(f"Failed to execute cleanup rule '{rule.name}': {e}")
        
        return results
    
    def get_cleanup_preview(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a preview of what would be cleaned up without actually doing it.
        
        Returns:
            Dictionary with preview information for each rule
        """
        preview = {}
        
        for rule in self.rules:
            try:
                files_to_remove = self.get_files_for_rule(rule)
                total_size = sum(f.stat().st_size for f in files_to_remove)
                
                preview[rule.name] = {
                    'file_count': len(files_to_remove),
                    'total_size_bytes': total_size,
                    'total_size_mb': total_size / (1024 * 1024),
                    'files': [str(f) for f in files_to_remove[:10]]  # Show first 10
                }
                
            except Exception as e:
                preview[rule.name] = {
                    'error': str(e),
                    'file_count': 0,
                    'total_size_bytes': 0,
                    'total_size_mb': 0,
                    'files': []
                }
        
        return preview
    
    def get_directory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the base directory.
        
        Returns:
            Dictionary with directory statistics
        """
        stats = {
            'total_files': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0,
            'subdirectories': 0,
            'file_types': {},
            'oldest_file': None,
            'newest_file': None,
            'largest_file': None
        }
        
        if not self.base_directory.exists():
            return stats
        
        try:
            oldest_time = float('inf')
            newest_time = 0
            largest_size = 0
            
            for item in self.base_directory.rglob('*'):
                if item.is_file():
                    stats['total_files'] += 1
                    
                    # Size
                    size = item.stat().st_size
                    stats['total_size_bytes'] += size
                    
                    if size > largest_size:
                        largest_size = size
                        stats['largest_file'] = str(item)
                    
                    # Time
                    mtime = item.stat().st_mtime
                    if mtime < oldest_time:
                        oldest_time = mtime
                        stats['oldest_file'] = str(item)
                    
                    if mtime > newest_time:
                        newest_time = mtime
                        stats['newest_file'] = str(item)
                    
                    # File type
                    ext = item.suffix.lower()
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                
                elif item.is_dir():
                    stats['subdirectories'] += 1
            
            stats['total_size_mb'] = stats['total_size_bytes'] / (1024 * 1024)
            
        except Exception as e:
            logger.error(f"Error getting directory stats: {e}")
        
        return stats


class ScheduledCleanup:
    """
    Manages scheduled cleanup operations.
    """
    
    def __init__(self, cleanup_manager: AssetCleanup):
        """
        Initialize scheduled cleanup.
        
        Args:
            cleanup_manager: AssetCleanup instance to use
        """
        self.cleanup_manager = cleanup_manager
        self.is_running = False
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def start_scheduled_cleanup(
        self, 
        interval_hours: int = 24, 
        dry_run: bool = False
    ) -> None:
        """
        Start scheduled cleanup operations.
        
        Args:
            interval_hours: Hours between cleanup runs
            dry_run: If True, don't actually delete files
        """
        if self.is_running:
            logger.warning("Scheduled cleanup is already running")
            return
        
        self.is_running = True
        self.cleanup_task = asyncio.create_task(
            self._cleanup_loop(interval_hours, dry_run)
        )
        
        logger.info(f"Started scheduled cleanup (interval: {interval_hours}h, dry_run: {dry_run})")
    
    async def stop_scheduled_cleanup(self) -> None:
        """Stop scheduled cleanup operations."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped scheduled cleanup")
    
    async def _cleanup_loop(self, interval_hours: int, dry_run: bool) -> None:
        """
        Main cleanup loop.
        
        Args:
            interval_hours: Hours between cleanup runs
            dry_run: If True, don't actually delete files
        """
        interval_seconds = interval_hours * 3600
        
        while self.is_running:
            try:
                logger.info("Starting scheduled cleanup run")
                results = await self.cleanup_manager.cleanup_all(dry_run)
                
                # Log summary
                total_files = sum(r.files_removed for r in results.values())
                total_bytes = sum(r.bytes_freed for r in results.values())
                total_errors = sum(len(r.errors) for r in results.values())
                
                logger.info(
                    f"Scheduled cleanup completed: {total_files} files removed, "
                    f"{total_bytes / (1024*1024):.2f} MB freed, {total_errors} errors"
                )
                
                # Wait for next run
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduled cleanup: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(300)  # 5 minutes


# Convenience functions
async def cleanup_directory(
    directory: Union[str, Path], 
    max_age_days: int = 30, 
    dry_run: bool = False
) -> CleanupResult:
    """
    Simple cleanup function for a directory.
    
    Args:
        directory: Directory to clean up
        max_age_days: Maximum age of files to keep
        dry_run: If True, don't actually delete files
        
    Returns:
        CleanupResult with operation details
    """
    cleanup_manager = AssetCleanup(directory)
    cleanup_manager.rules.clear()  # Remove default rules
    
    rule = CleanupRule(
        name="simple_cleanup",
        max_age_days=max_age_days,
        file_patterns=["*"]
    )
    
    cleanup_manager.add_rule(rule)
    return await cleanup_manager.cleanup_by_rule(rule, dry_run)


def create_size_based_rule(name: str, max_total_size_mb: int, patterns: List[str]) -> CleanupRule:
    """
    Create a cleanup rule based on total directory size.
    
    Args:
        name: Name for the rule
        max_total_size_mb: Maximum total size in MB
        patterns: File patterns to include
        
    Returns:
        CleanupRule configured for size-based cleanup
    """
    def size_condition(file_path: Path) -> bool:
        # This is a simplified version - in practice, you'd want to
        # calculate total directory size and remove oldest files
        # when the limit is exceeded
        return True
    
    return CleanupRule(
        name=name,
        file_patterns=patterns,
        condition_func=size_condition
    )