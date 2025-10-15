"""
Utility functions and helpers for the Campfires framework.
"""

from .template_loader import (
    TemplateLoader, 
    RAGTemplateManager, 
    render_template, 
    load_config,
    get_template_loader,
    set_template_loader
)
from .hash_utils import (
    generate_hash, 
    verify_checksum,
    generate_file_hash,
    verify_file_checksum,
    generate_secure_token,
    generate_uuid_hash,
    generate_torch_id,
    generate_asset_id,
    HashValidator,
    quick_hash,
    quick_file_hash,
    secure_compare
)
from .cleanup import (
    AssetCleanup,
    CleanupRule,
    CleanupResult,
    ScheduledCleanup,
    cleanup_directory,
    create_size_based_rule
)

__all__ = [
    # Template utilities
    'TemplateLoader',
    'RAGTemplateManager', 
    'render_template',
    'load_config',
    'get_template_loader',
    'set_template_loader',
    
    # Hash utilities
    'generate_hash',
    'verify_checksum',
    'generate_file_hash',
    'verify_file_checksum',
    'generate_secure_token',
    'generate_uuid_hash',
    'generate_torch_id',
    'generate_asset_id',
    'HashValidator',
    'quick_hash',
    'quick_file_hash',
    'secure_compare',
    
    # Cleanup utilities
    'AssetCleanup',
    'CleanupRule',
    'CleanupResult',
    'ScheduledCleanup',
    'cleanup_directory',
    'create_size_based_rule'
]