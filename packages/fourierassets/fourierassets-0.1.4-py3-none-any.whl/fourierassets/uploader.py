# /usr/bin/env python3
"""
Copyright (C) 2015-2025 Fourier Intelligence Group Limited. All rights reserved.

@file    uploader.py
@author  Stan
@date    24 Jun 25
@desc    Asset uploader for S3 - simplified to use rclone directly
"""

from pathlib import Path

from .logger import get_logger
from .utils import get_s3_client, parse_s3_url


class AssetUploader:
    """Upload simulation assets to S3 using rclone."""

    def __init__(self, endpoint_url=None, verbose=False):
        """Initialize the asset uploader.

        Args:
            endpoint_url: S3 endpoint URL override
            verbose: Enable verbose logging
        """
        self.logger = get_logger(f"{__name__}.AssetUploader")
        self.endpoint_url = endpoint_url
        self.verbose = verbose
        self._s3_client = None

    @property
    def s3_client(self):
        """Get S3 client instance."""
        if self._s3_client is None:
            self._s3_client = get_s3_client(
                endpoint_url=self.endpoint_url, verbose=self.verbose
            )
        return self._s3_client

    def upload(self, local_path, s3_url):
        """Upload local file or directory to S3 using rclone.

        Args:
            local_path: Local file or directory path
            s3_url: S3 URL destination

        Returns:
            True if successful

        Raises:
            FileNotFoundError: If local path does not exist
            Exception: If upload fails
        """
        try:
            bucket, key = parse_s3_url(s3_url)
            local_path = Path(local_path).resolve()

            if not local_path.exists():
                raise FileNotFoundError(f"Local path does not exist: {local_path}")

            self.logger.info("Uploading %s to %s", local_path, s3_url)

            if local_path.is_file():
                # Upload single file using rclone
                self.s3_client.upload_file(str(local_path), bucket, key)
                if self.verbose:
                    print(f"✓ Uploaded file: {local_path} -> {s3_url}")
                return True

            elif local_path.is_dir():
                # Upload directory using rclone sync
                success = self.s3_client.sync_directory(str(local_path), bucket, key)
                if success and self.verbose:
                    print(f"✓ Uploaded directory: {local_path} -> {s3_url}")
                return success

            else:
                raise ValueError(f"Invalid path type: {local_path}")

        except Exception as e:
            self.logger.error("Failed to upload %s to %s: %s", local_path, s3_url, e)
            raise
