#/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2015-2025 Fourier Intelligence Group Limited. All rights reserved.

@file    cli.py
@author  Stan
@date    29 Sep 25
@desc    cli
"""

from fourierassets.cli import main

import warnings

# Issue a deprecation warning when simassets is imported
warnings.warn(
    "The 'simassets' package is deprecated and will be removed in a future version. "
    "Please use 'pip install -U --force-reinstall fourierassets' to upgrade. "
    "Update your cli with: 'fourierassets download', ...",
    DeprecationWarning,
    stacklevel=2
)

if __name__ == "__main__":
    main()
