# /usr/bin/env python3
"""
Copyright (C) 2015-2025 Fourier Intelligence Group Limited. All rights reserved.

@file    __init__.py
@author  Stan
@date    29 Sep 25
@desc    Backward compatibility layer for simassets package

This module provides backward compatibility for users who still import simassets.
All functionality is now provided by the fourierassets package.
"""

import warnings

# Re-export all public APIs from fourierassets for backward compatibility
from fourierassets import (
    AssetDownloader,
    AssetLister,
    AssetRemover,
    AssetUploader,
    S3Config,
)
# Re-export all modules for compatibility with "from simassets import module" style imports
from fourierassets import cli
from fourierassets import completion
from fourierassets import config
from fourierassets import defaults
from fourierassets import downloader
from fourierassets import exceptions
from fourierassets import lister
from fourierassets import logger
from fourierassets import rclone_client
from fourierassets import rclone_installer
from fourierassets import remover
from fourierassets import uploader
from fourierassets import utils

# Issue a deprecation warning when simassets is imported
warnings.warn(
    "The 'simassets' package is deprecated and will be removed in a future version. "
    "Please use 'pip install -U --force-reinstall fourierassets' to upgrade. "
    "Update your imports: 'from fourierassets import ...' or 'import fourierassets'",
    DeprecationWarning,
    stacklevel=2
)

# Make sure __all__ includes everything users might expect
__all__ = [
    # Main classes
    "AssetDownloader",
    "AssetUploader",
    "AssetLister",
    "AssetRemover",
    "S3Config",

    # Modules for "from simassets import module" compatibility
    "cli",
    "completion",
    "config",
    "defaults",
    "downloader",
    "exceptions",
    "lister",
    "logger",
    "rclone_client",
    "rclone_installer",
    "remover",
    "uploader",
    "utils",
]
