# /usr/bin/env python3
"""
Copyright (C) 2015-2025 Fourier Intelligence Group Limited. All rights reserved.

@file    __init__.py
@author  Stan
@date    24 Jun 25
@desc    __init__
"""

# -------------------------------------------------------------------------------
# Builtin variables
# -------------------------------------------------------------------------------

from .config import S3Config
from .downloader import AssetDownloader
from .lister import AssetLister
from .uploader import AssetUploader
from .remover import AssetRemover


# Initialize default configuration
def _ensure_default_config():
    """Ensure default configuration is applied."""
    try:
        S3Config()
        # Config initialization will automatically apply defaults if needed
    except Exception as e:
        print(f"Warning: Failed to initialize default configuration: {str(e)}")
        # Silently fail if config can't be initialized


# Apply default config on import
_ensure_default_config()

__all__ = [
    "AssetDownloader",
    "AssetUploader",
    "AssetLister",
    "AssetRemover",
    "S3Config",
]
