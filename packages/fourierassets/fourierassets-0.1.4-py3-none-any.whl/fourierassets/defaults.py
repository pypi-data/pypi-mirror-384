"""
Default configuration for FourierAssets
"""

DEFAULT_S3_CONFIG = {
    "access_key": "Ya4FVtaPPn8ULEoquQXS",
    "secret_key": "T8EPwGG2XUHZCKegE3VEBjtgHp4VMA2LSXFjGXMY",
    "endpoint_url": "https://s3maxio.fftaicorp.com",
}


def get_default_config():
    """Get default S3 configuration."""
    return DEFAULT_S3_CONFIG.copy()
