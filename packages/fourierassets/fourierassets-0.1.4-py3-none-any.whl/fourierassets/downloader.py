import os
from pathlib import Path

from .defaults import get_default_config
from .logger import get_logger
from .utils import ensure_dir, get_s3_client, parse_s3_url


class AssetDownloader:
    """Download simulation assets from S3 using rclone's native caching."""

    def __init__(
        self, cache_dir="~/.fourierassets/cache", endpoint_url=None, verbose=False
    ):
        # Note: cache_dir is kept for backward compatibility but rclone handles caching internally
        self.cache_dir = Path(cache_dir).expanduser().resolve()
        self.verbose = verbose

        # Prioritize: explicit endpoint_url > user config > default config
        if endpoint_url:
            self.endpoint_url = endpoint_url
        else:
            # Get user's current configuration
            from .config import S3Config

            config = S3Config()
            user_creds = config.get_credentials()
            self.endpoint_url = user_creds.get(
                "endpoint_url"
            ) or get_default_config().get("endpoint_url")

        self.logger = get_logger(f"{__name__}.AssetDownloader")

    def download(self, s3_url):
        """Download asset from S3 URL and return local path.

        Simple approach: let rclone do what it does best.
        """
        # Parse S3 URL
        bucket, key = parse_s3_url(s3_url)
        s3_client = get_s3_client(self.endpoint_url, verbose=self.verbose)

        # Create a simple cache directory structure based on S3 path
        safe_bucket = bucket.replace("/", "_").replace(":", "_")
        if key:
            safe_key = key.replace("/", os.sep)
            cache_path = self.cache_dir / safe_bucket / safe_key
        else:
            cache_path = self.cache_dir / safe_bucket

        # Simple check: if it already exists, return it
        if cache_path.exists():
            self.logger.info("Asset already exists: %s", cache_path)
            return str(cache_path)

        try:
            # Ensure cache directory exists
            ensure_dir(cache_path.parent)

            self.logger.info("Downloading %s to %s", s3_url, cache_path)

            # Download to the exact target path
            # Check if this looks like a file (has extension) or directory
            if key and ("." in key.split("/")[-1]):
                # This looks like a file - download it as a file
                s3_client.copyto_optimized(bucket, key, str(cache_path))
            else:
                # This looks like a directory - download it as a directory
                s3_client.copy_directory_optimized(bucket, key, str(cache_path))

            # Verify the download
            if cache_path.exists():
                self.logger.info("Downloaded to expected path: %s", cache_path)
                return str(cache_path)
            else:
                raise FileNotFoundError(
                    f"Download failed - {cache_path} does not exist"
                )

        except Exception as e:
            self.logger.error("Failed to download asset %s: %s", s3_url, str(e))
            raise
