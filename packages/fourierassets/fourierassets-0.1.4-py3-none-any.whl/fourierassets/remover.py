# /usr/bin/env python3
"""
Copyright (C) 2015-2025 Fourier Intelligence Group Limited. All rights reserved.

@file    remover.py
@author  Stan
@date    16 Sep 25
@desc    Asset remover for S3
"""

from typing import List

from rclone_python import rclone

from .logger import get_logger
from .utils import get_s3_client, parse_s3_url


class AssetRemover:
    """Asset remover for S3 objects and directories."""

    def __init__(self, endpoint_url=None, verbose=False):
        """Initialize the asset remover.

        Args:
            endpoint_url: S3 endpoint URL override
            verbose: Enable verbose logging
        """
        self.logger = get_logger(f"{__name__}.AssetRemover")
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

    def remove_object(self, s3_url: str) -> bool:
        """Remove a single object from S3.

        Args:
            s3_url: S3 URL of the object to remove

        Returns:
            True if successful

        Raises:
            ValueError: If the S3 URL is invalid
            Exception: If the removal fails
        """
        try:
            bucket, key = parse_s3_url(s3_url)

            if not key:
                raise ValueError(f"Invalid S3 URL for file removal: {s3_url}")

            self.logger.info("Removing object: %s", s3_url)

            # Use rclone delete directly
            remote_path = f"{self.s3_client.remote_name}:{bucket}/{key}"
            rclone.delete(remote_path)

            if self.verbose:
                print(f"✓ Removed: {s3_url}")

            return True

        except Exception as e:
            self.logger.error("Failed to remove object %s: %s", s3_url, e)
            if "not found" in str(e).lower() or "404" in str(e):
                self.logger.warning("Object does not exist: %s", s3_url)
                return True  # Consider non-existent object as successfully removed
            raise

    def remove_directory(self, s3_url: str, recursive: bool = False) -> bool:
        """Remove a directory from S3.

        Args:
            s3_url: S3 URL of the directory to remove
            recursive: If True, remove all contents recursively

        Returns:
            True if successful

        Raises:
            ValueError: If recursive is False and directory is not empty
            Exception: If the removal fails
        """
        try:
            bucket, prefix = parse_s3_url(s3_url)

            self.logger.info("Removing directory: %s (recursive=%s)", s3_url, recursive)

            # Use rclone purge for recursive removal, rclone rmdir for non-recursive
            remote_path = f"{self.s3_client.remote_name}:{bucket}"
            if prefix:
                remote_path += f"/{prefix.rstrip('/')}"

            if recursive:
                # Use rclone purge to remove directory and all contents
                rclone.purge(remote_path)
            else:
                # Use rclone rmdir to remove empty directory only
                rclone.rmdir(remote_path)

            if self.verbose:
                print(f"✓ Removed directory: {s3_url}")

            return True

        except Exception as e:
            self.logger.error("Failed to remove directory %s: %s", s3_url, e)
            error_msg = str(e).lower()
            if (
                "not found" in error_msg
                or "404" in error_msg
                or "directory not found" in error_msg
            ):
                self.logger.warning("Directory does not exist: %s", s3_url)
                return True  # Consider non-existent directory as successfully removed
            elif "not empty" in error_msg and not recursive:
                raise ValueError(
                    f"Directory {s3_url} is not empty. Use --recursive to force removal."
                ) from e
            raise e

    def rm(
        self, s3_urls: List[str], recursive: bool = False, force: bool = False
    ) -> bool:
        """Remove multiple objects and/or directories from S3.

        Args:
            s3_urls: List of S3 URLs to remove
            recursive: If True, remove directories recursively
            force: If True, skip confirmation prompt

        Returns:
            True if all removals were successful

        Raises:
            Exception: If any removal fails in non-recursive mode
        """
        # Ask for confirmation unless force is specified
        if not force:
            if not self.confirm_removal(s3_urls, recursive=recursive):
                return False

        success_count = 0
        total_count = len(s3_urls)

        for s3_url in s3_urls:
            try:
                bucket, key = parse_s3_url(s3_url)

                # Simple heuristic: if URL ends with / or has no key, treat as directory
                if not key or key.endswith("/"):
                    success = self.remove_directory(s3_url, recursive=recursive)
                else:
                    # Try to remove as file first, then as directory if it fails
                    try:
                        success = self.remove_object(s3_url)
                    except Exception:
                        # If file removal fails, try as directory
                        success = self.remove_directory(s3_url, recursive=recursive)

                if success:
                    success_count += 1

            except Exception as e:
                self.logger.error("Failed to remove %s: %s", s3_url, e)
                if not recursive:  # In non-recursive mode, stop on first error
                    raise
                # In recursive mode, continue with other objects

        if success_count < total_count:
            self.logger.warning(
                "Removed %d out of %d objects", success_count, total_count
            )
            return False

        return True

    def confirm_removal(self, s3_urls: List[str], recursive: bool = False) -> bool:
        """Ask user for confirmation before removal.

        Args:
            s3_urls: List of S3 URLs to remove
            recursive: If True, will remove directories recursively

        Returns:
            True if user confirms, False otherwise
        """
        print("The following objects/directories will be removed:")
        for s3_url in s3_urls:
            bucket, key = parse_s3_url(s3_url)
            if not key or key.endswith("/"):
                if recursive:
                    print(f"  📁 {s3_url} (recursive)")
                else:
                    print(f"  📁 {s3_url}")
            else:
                # Check if it might be a directory by trying to list
                try:
                    response = self.s3_client.list_objects_v2(
                        Bucket=bucket, Prefix=key + "/", MaxKeys=1
                    )
                    if response.get("Contents") or response.get("CommonPrefixes"):
                        if recursive:
                            print(f"  📁 {s3_url} (recursive)")
                        else:
                            print(f"  📁 {s3_url}")
                    else:
                        print(f"  📄 {s3_url}")
                except Exception:
                    print(f"  📄 {s3_url}")

        print()
        try:
            response = (
                input("Are you sure you want to proceed? [y/N]: ").strip().lower()
            )
            return response in ["y", "yes"]
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return False
