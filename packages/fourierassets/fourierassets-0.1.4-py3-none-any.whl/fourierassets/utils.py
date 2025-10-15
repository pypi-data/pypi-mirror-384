import os
import threading
from urllib.parse import urlparse

from .rclone_client import RcloneS3Client

# Global client cache to reuse clients with same configuration
_client_cache = {}
_client_cache_lock = threading.Lock()


def parse_s3_url(s3_url):
    """Parse S3 URL into bucket and key components."""
    parsed = urlparse(s3_url)
    if parsed.scheme != "s3":
        raise ValueError(f"Invalid S3 URL: {s3_url}")

    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    return bucket, key


def get_s3_client(endpoint_url=None, verbose=False):
    """Get configured rclone S3 client with caching for efficiency."""
    # Check rclone availability before proceeding
    from .rclone_installer import check_rclone_dependency, verify_rclone_silent
    
    if not verify_rclone_silent():
        check_rclone_dependency(verbose=verbose)
    
    try:
        # Get credentials from config
        from .config import S3Config

        config = S3Config()
        creds = config.get_credentials()

        # Prioritize passed endpoint_url over stored one
        final_endpoint = endpoint_url or creds.get("endpoint_url")

        # Create cache key based on configuration
        cache_key = (
            final_endpoint or "default",
            creds.get("access_key") or "none",
            creds.get("secret_key") or "none",
            verbose,
        )

        with _client_cache_lock:
            if cache_key in _client_cache:
                # Return existing client
                return _client_cache[cache_key]

            # Create new client and cache it
            client = RcloneS3Client(
                endpoint_url=final_endpoint,
                access_key=creds.get("access_key"),
                secret_key=creds.get("secret_key"),
                verbose=verbose,
            )
            _client_cache[cache_key] = client
            return client

    except Exception as e:
        print(f"Error getting S3 client: {str(e)}")
        raise


def ensure_dir(path):
    """Ensure directory exists."""
    if path:  # Check if path is not empty
        os.makedirs(path, exist_ok=True)
