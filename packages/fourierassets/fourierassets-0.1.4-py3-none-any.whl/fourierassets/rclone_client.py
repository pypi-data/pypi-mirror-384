"""
rclone-python based S3 client for fourierassets.
"""

import atexit
import os
import shutil
import tempfile
import threading
from datetime import datetime
from typing import Dict

from rclone_python import rclone

from .logger import get_logger

# Global config file registry for cleanup management
_config_registry = {}
_config_lock = threading.Lock()


def _cleanup_all_configs():
    """Cleanup all registered config files at program exit."""
    with _config_lock:
        for config_file in _config_registry.values():
            try:
                if os.path.exists(config_file):
                    os.unlink(config_file)
            except Exception:
                pass  # Ignore cleanup errors
        _config_registry.clear()


# Register cleanup function to run at program exit
atexit.register(_cleanup_all_configs)


class RcloneS3Client:
    """Rclone-based S3 client for fourierassets."""

    def __init__(
        self, endpoint_url=None, access_key=None, secret_key=None, verbose=False
    ):
        # Check rclone availability before proceeding
        from .rclone_installer import check_rclone_dependency, verify_rclone_silent
        
        if not verify_rclone_silent():
            check_rclone_dependency(verbose=verbose)
            
        self.logger = get_logger(f"{__name__}.RcloneS3Client")
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.remote_name = "fourierassets"
        self.verbose = verbose

        # Generate config key based on credentials
        config_key = (
            f"{access_key or 'none'}:{secret_key or 'none'}:{endpoint_url or 'default'}"
        )

        with _config_lock:
            if config_key in _config_registry:
                # Reuse existing config file
                self._config_file_path = _config_registry[config_key]
                self._config_file = None  # No need to create new file
                self.logger.debug(f"Reusing rclone config: {self._config_file_path}")
            else:
                # Create a new temporary config file
                self._config_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".conf", delete=False
                )
                self._config_file_path = self._config_file.name

                # Register the config file
                _config_registry[config_key] = self._config_file_path

                self._setup_rclone_config()

        # Try to find rclone executable in multiple locations
        rclone_path = shutil.which("rclone")
        if not rclone_path:
            # Check common installation locations
            common_paths = [
                os.path.expanduser("~/.local/bin/rclone"),
                "/usr/local/bin/rclone",
                "/usr/bin/rclone",
                "/opt/homebrew/bin/rclone",
            ]
            for path in common_paths:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    rclone_path = path
                    # Add the directory to PATH so rclone-python can find it
                    rclone_dir = os.path.dirname(path)
                    if rclone_dir not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = (
                            f"{rclone_dir}:{os.environ.get('PATH', '')}"
                        )
                    break

        if rclone_path:
            self.logger.debug("Found rclone at: %s", rclone_path)
            # Set the rclone executable path
            rclone.rclone_exe = rclone_path
        else:
            self.logger.warning("rclone executable not found in PATH")

        # Set the config file for rclone
        rclone.set_config_file(self._config_file_path)

    def _setup_rclone_config(self):
        """Setup rclone configuration for S3."""
        # Only setup if we have a new config file to write to
        if self._config_file is None:
            return

        # Determine region and path style based on endpoint URL
        region = "fourier-8"  # default
        force_path_style = "true"  # default for Fourier

        if self.endpoint_url:
            if "oss-cn-" in self.endpoint_url:
                # Alibaba Cloud OSS requires virtual hosted style
                import re

                match = re.search(r"oss-(cn-[^.]+)", self.endpoint_url)
                if match:
                    region = match.group(1)
                force_path_style = "false"
            elif "s3.amazonaws.com" in self.endpoint_url:
                # AWS S3 supports virtual hosted style
                region = "us-east-1"
                force_path_style = "false"
            elif "s3." in self.endpoint_url and ".amazonaws.com" in self.endpoint_url:
                # Extract region from AWS S3 endpoint like s3.us-west-2.amazonaws.com
                import re

                match = re.search(r"s3\.([^.]+)\.amazonaws\.com", self.endpoint_url)
                if match:
                    region = match.group(1)
                force_path_style = "false"
            elif "s3maxio.fftaicorp.com" in self.endpoint_url:
                # Fourier S3 service - use path style
                region = "fourier-8"
                force_path_style = "true"

        config_content = f"""[{self.remote_name}]
type = s3
provider = Other
access_key_id = {self.access_key or ""}
secret_access_key = {self.secret_key or ""}
endpoint = {self.endpoint_url or ""}
region = {region}
acl = private
force_path_style = {force_path_style}
no_check_bucket = true
"""

        self._config_file.write(config_content)
        self._config_file.close()

        self.logger.debug("Created rclone config: %s", self._config_file_path)

    def list_buckets(self) -> Dict:
        """List available buckets."""
        try:
            result = rclone.ls(f"{self.remote_name}:", max_depth=1, dirs_only=True)

            buckets_data = []
            for bucket_info in result:
                # Use 'Path' or 'Name' field (rclone returns capitalized keys)
                bucket_name = (
                    bucket_info.get("Path")
                    or bucket_info.get("Name")
                    or bucket_info.get("path")
                    or bucket_info.get("name", "unknown")
                )
                buckets_data.append(
                    {
                        "Name": bucket_name,
                        "CreationDate": datetime.now(),  # rclone doesn't provide creation date
                    }
                )

            return {"Buckets": buckets_data}

        except Exception as e:
            self.logger.error("Failed to list buckets: %s", e)
            raise

    def head_bucket(self, Bucket: str):
        """Check if bucket exists."""
        try:
            # Try to list the bucket to see if it exists
            s3_path = f"{self.remote_name}:{Bucket}"
            self.logger.debug("Checking bucket existence: %s", s3_path)
            result = rclone.ls(s3_path, max_depth=1)
            self.logger.debug(
                "Bucket check successful for %s, result: %s", Bucket, result
            )
            return {}  # Success, return empty dict

        except Exception as e:
            self.logger.debug("Bucket check failed for %s: %s", Bucket, e)
            error_msg = str(e).lower()

            # Check for specific error types in rclone output
            if (
                "403" in error_msg
                or "access denied" in error_msg
                or "forbidden" in error_msg
            ):
                from .exceptions import ClientError

                error_response = {"Error": {"Code": "403", "Message": "Access denied"}}
                raise ClientError(error_response, "HeadBucket") from e
            elif (
                "404" in error_msg
                or "not found" in error_msg
                or "no such bucket" in error_msg
            ):
                from .exceptions import ClientError

                error_response = {
                    "Error": {"Code": "404", "Message": "Bucket not found"}
                }
                raise ClientError(error_response, "HeadBucket") from e
            elif "permanentredirect" in error_msg or "redirect" in error_msg:
                from .exceptions import ClientError

                error_response = {
                    "Error": {
                        "Code": "301",
                        "Message": "Bucket requires different endpoint",
                    }
                }
                raise ClientError(error_response, "HeadBucket") from e
            else:
                # Default to NoSuchBucket for other errors
                from .exceptions import NoSuchBucket

                raise NoSuchBucket(
                    f"The specified bucket does not exist: {Bucket}"
                ) from e

    def head_object(self, Bucket: str, Key: str) -> Dict:
        """Get object metadata."""
        try:
            s3_path = f"{self.remote_name}:{Bucket}/{Key}"
            result = rclone.ls(s3_path, files_only=True)

            if not result:
                from .exceptions import NoSuchKey

                raise NoSuchKey(f"The specified key does not exist: {Key}")

            # Find the exact file
            for obj_info in result:
                obj_name = (
                    obj_info.get("name") or obj_info.get("path", "").split("/")[-1]
                )
                if obj_name == Key.split("/")[-1]:
                    return {
                        "ContentLength": obj_info.get("size", 0),
                        "LastModified": datetime.fromisoformat(
                            obj_info["modified_time"].replace("Z", "+00:00")
                        )
                        if "modified_time" in obj_info
                        else datetime.now(),
                    }

            # If we get here, object wasn't found
            from .exceptions import NoSuchKey

            raise NoSuchKey(f"The specified key does not exist: {Key}")

        except Exception as e:
            if "NoSuchKey" in str(type(e)):
                raise
            self.logger.error("Failed to head object %s: %s", Key, e)
            raise

    def list_objects_v2(
        self,
        Bucket: str,
        Prefix: str = "",
        MaxKeys: int = 1000,
        Delimiter: str = None,
        **kwargs,
    ) -> Dict:
        """List objects in bucket."""
        try:
            s3_path = f"{self.remote_name}:{Bucket}"
            if Prefix:
                s3_path += f"/{Prefix.strip('/')}"

            self.logger.debug("Listing objects at path: %s", s3_path)

            # Set max_depth based on delimiter
            max_depth = 1 if Delimiter else None

            result = rclone.ls(s3_path, max_depth=max_depth)
            self.logger.debug("rclone.ls result: %s", result)

            contents = []
            common_prefixes = []

            for obj_info in result:
                self.logger.debug("Processing object info: %s", obj_info)
                # Build full key path - handle rclone field names (Path, Name)
                obj_path = (
                    obj_info.get("Path")
                    or obj_info.get("path")
                    or obj_info.get("Name")
                    or obj_info.get("name", "")
                )

                if Prefix:
                    full_key = f"{Prefix.rstrip('/')}/{obj_path}"
                else:
                    full_key = obj_path

                if obj_info.get("IsDir", obj_info.get("is_dir", False)):
                    # Always add directories to common_prefixes, regardless of Delimiter
                    # This is important for recursive downloads
                    common_prefixes.append({"Prefix": full_key + "/"})
                else:
                    # Extract modification time - rclone uses 'ModTime' field
                    mod_time = obj_info.get("ModTime") or obj_info.get("modified_time")
                    if mod_time and mod_time != "2000-01-01T00:00:00.000000000Z":
                        try:
                            last_modified = datetime.fromisoformat(
                                mod_time.replace("Z", "+00:00")
                            )
                        except (ValueError, TypeError):
                            last_modified = datetime.now()
                    else:
                        last_modified = datetime.now()

                    contents.append(
                        {
                            "Key": full_key,
                            "Size": obj_info.get("Size", obj_info.get("size", 0)),
                            "LastModified": last_modified,
                        }
                    )

            # Limit results
            if len(contents) > MaxKeys:
                contents = contents[:MaxKeys]

            response = {"Contents": contents}
            if common_prefixes:
                response["CommonPrefixes"] = common_prefixes

            return response

        except Exception as e:
            self.logger.error("Failed to list objects in %s: %s", Bucket, e)
            raise

    def get_paginator(self, operation_name: str):
        """Get paginator for operations."""
        if operation_name == "list_objects_v2":
            return ListObjectsV2Paginator(self)
        else:
            raise ValueError(f"Unsupported paginator operation: {operation_name}")

    def download_file(self, Bucket, Key, Filename, Callback=None):
        """Download a file from S3."""
        try:
            s3_path = f"{self.remote_name}:{Bucket}/{Key}"

            # Ensure directory exists
            os.makedirs(os.path.dirname(Filename), exist_ok=True)

            # Use rclone copyto for single file download
            rclone.copyto(s3_path, Filename)

        except Exception as e:
            self.logger.error("Failed to download %s/%s: %s", Bucket, Key, e)
            raise

    def copyto_optimized(self, bucket: str, key: str, local_path: str):
        """Download a single file from S3 with rclone-python's beautiful progress visualization."""
        try:
            s3_path = f"{self.remote_name}:{bucket}/{key}"

            # Remove existing file/directory if it exists to avoid conflicts
            if os.path.exists(local_path):
                if os.path.isfile(local_path):
                    os.unlink(local_path)
                    self.logger.debug("Removed existing file: %s", local_path)
                elif os.path.isdir(local_path):
                    shutil.rmtree(local_path)
                    self.logger.debug("Removed existing directory: %s", local_path)

            # Ensure directory exists
            parent_dir = os.path.dirname(local_path)
            if parent_dir:
                # Check if parent directory path exists as a file (conflict)
                if os.path.exists(parent_dir) and os.path.isfile(parent_dir):
                    # Remove the conflicting file
                    os.unlink(parent_dir)
                    self.logger.debug(
                        "Removed conflicting file at directory path: %s", parent_dir
                    )

                os.makedirs(parent_dir, exist_ok=True)

            # Use rclone-python which provides beautiful gradient red progress bars
            self.logger.debug(
                "Downloading with rclone-python: %s -> %s", s3_path, local_path
            )

            if not self.verbose:
                # Disable progress display when not in verbose mode
                import sys

                # Redirect stdout/stderr to devnull during rclone operation
                with open(os.devnull, "w", encoding="utf-8") as devnull:
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    try:
                        sys.stdout = devnull
                        sys.stderr = devnull
                        # rclone copyto will overwrite by default
                        rclone.copyto(s3_path, local_path)
                    finally:
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
            else:
                # Show beautiful progress in verbose mode
                rclone.copyto(s3_path, local_path)

            self.logger.debug("rclone copyto completed successfully")
            return True

        except Exception as e:
            self.logger.error("Failed to download file %s/%s: %s", bucket, key, e)
            raise

    def upload_file(self, Filename: str, Bucket: str, Key: str, Callback=None):
        """Upload a file to S3."""
        try:
            s3_path = f"{self.remote_name}:{Bucket}/{Key}"

            # Use rclone copyto for single file upload
            rclone.copyto(Filename, s3_path)

            # Call callback if provided (for progress tracking)
            if Callback:
                try:
                    file_size = os.path.getsize(Filename)
                    Callback(file_size)
                except Exception:
                    pass  # Ignore callback errors

        except Exception as e:
            self.logger.error("Failed to upload %s: %s", Filename, e)
            raise

    def sync_directory(self, local_dir: str, bucket: str, prefix: str = ""):
        """Sync directory to S3."""
        try:
            s3_path = f"{self.remote_name}:{bucket}"
            if prefix:
                s3_path += f"/{prefix.strip('/')}"

            rclone.sync(local_dir, s3_path)
            return True

        except Exception as e:
            self.logger.error("Failed to sync directory %s: %s", local_dir, e)
            raise

    def copy_directory(self, bucket: str, prefix: str, local_dir: str):
        """Copy directory from S3."""
        try:
            s3_path = f"{self.remote_name}:{bucket}"
            if prefix:
                s3_path += f"/{prefix.strip('/')}"

            # Ensure local directory exists
            os.makedirs(local_dir, exist_ok=True)

            rclone.copy(s3_path, local_dir)
            return True

        except Exception as e:
            self.logger.error(
                "Failed to copy directory from %s/%s: %s", bucket, prefix, e
            )
            raise

    def copy_directory_optimized(self, bucket: str, prefix: str, local_dir: str):
        """Copy directory from S3 with rclone-python's beautiful progress visualization."""
        try:
            s3_path = f"{self.remote_name}:{bucket}"
            if prefix:
                s3_path += f"/{prefix.strip('/')}"

            # Ensure local directory exists
            if os.path.exists(local_dir) and os.path.isfile(local_dir):
                # Remove the conflicting file
                os.unlink(local_dir)
                self.logger.debug(
                    "Removed conflicting file at directory path: %s", local_dir
                )

            os.makedirs(local_dir, exist_ok=True)

            # Use rclone-python which provides beautiful gradient red progress bars
            self.logger.debug(
                "Copying directory with rclone-python: %s -> %s", s3_path, local_dir
            )

            if not self.verbose:
                # Disable progress display when not in verbose mode
                import sys

                # Redirect stdout/stderr to devnull during rclone operation
                with open(os.devnull, "w", encoding="utf-8") as devnull:
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    try:
                        sys.stdout = devnull
                        sys.stderr = devnull
                        # rclone copy will overwrite by default
                        rclone.copy(s3_path, local_dir)
                    finally:
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
            else:
                # Show beautiful progress in verbose mode
                rclone.copy(s3_path, local_dir)

            self.logger.debug("rclone copy completed successfully")
            return True

        except Exception as e:
            self.logger.error(
                "Failed to copy directory from %s/%s: %s", bucket, prefix, e
            )
            raise

    def delete_object(self, Bucket: str, Key: str):
        """Delete a single object from S3."""
        try:
            s3_path = f"{self.remote_name}:{Bucket}/{Key}"
            self.logger.debug("Deleting object: %s", s3_path)

            # Use rclone delete for single file
            rclone.delete(s3_path)

            self.logger.debug("Successfully deleted object: %s", Key)
            return True

        except Exception as e:
            self.logger.error("Failed to delete object %s/%s: %s", Bucket, Key, e)
            # Check if the error is because the object doesn't exist
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                from .exceptions import NoSuchKey

                raise NoSuchKey(f"The specified key does not exist: {Key}") from e
            raise

    def delete_objects(self, Bucket: str, Delete: dict):
        """Delete multiple objects from S3."""
        try:
            objects = Delete.get("Objects", [])
            errors = []
            deleted = []

            for obj in objects:
                key = obj["Key"]
                try:
                    self.delete_object(Bucket, key)
                    deleted.append({"Key": key})
                except Exception as e:
                    errors.append(
                        {"Key": key, "Code": "InternalError", "Message": str(e)}
                    )

            response = {"Deleted": deleted}
            if errors:
                response["Errors"] = errors

            return response

        except Exception as e:
            self.logger.error("Failed to delete objects in %s: %s", Bucket, e)
            raise

    def delete_directory(self, bucket: str, prefix: str):
        """Delete a directory (all objects with the given prefix) from S3."""
        try:
            s3_path = f"{self.remote_name}:{bucket}"
            if prefix:
                # Ensure prefix ends with / for directory deletion
                prefix = prefix.rstrip("/") + "/"
                s3_path += f"/{prefix}"

            self.logger.debug("Deleting directory: %s", s3_path)

            # Use rclone purge to delete directory and all contents
            rclone.purge(s3_path)

            self.logger.debug("Successfully deleted directory: %s", prefix)
            return True

        except Exception as e:
            self.logger.error("Failed to delete directory %s/%s: %s", bucket, prefix, e)
            # Check if the error is because the directory doesn't exist
            error_msg = str(e).lower()
            if (
                "not found" in error_msg
                or "404" in error_msg
                or "directory not found" in error_msg
            ):
                from .exceptions import NoSuchKey

                raise NoSuchKey(
                    f"The specified directory does not exist: {prefix}"
                ) from e
            raise

    @property
    def exceptions(self):
        """Provide exceptions attribute for compatibility."""
        from . import exceptions

        return exceptions

    def __del__(self):
        """Cleanup temporary config file."""
        if hasattr(self, "_config_file") and self._config_file:
            try:
                # Only delete if the file still exists and we're the owner
                if os.path.exists(self._config_file.name):
                    os.unlink(self._config_file.name)
                    self.logger.debug(
                        "Cleaned up config file: %s", self._config_file.name
                    )
            except Exception:
                pass  # Ignore cleanup errors


class ListObjectsV2Paginator:
    """Paginator for list_objects_v2 operation."""

    def __init__(self, client):
        self.client = client

    def paginate(self, **kwargs):
        """Paginate through list_objects_v2 results."""
        max_keys = kwargs.get("MaxKeys", 1000)
        bucket = kwargs["Bucket"]
        prefix = kwargs.get("Prefix", "")
        delimiter = kwargs.get("Delimiter")

        # For simplicity, we'll just return all results in one page
        # rclone doesn't have built-in pagination
        response = self.client.list_objects_v2(
            Bucket=bucket, Prefix=prefix, MaxKeys=max_keys, Delimiter=delimiter
        )

        yield response
