import json
from pathlib import Path

from .utils import ensure_dir


class S3Config:
    """Manage S3 configuration including credentials."""

    def __init__(self, config_dir="~/.fourierassets"):
        self.config_dir = Path(config_dir).expanduser().resolve()
        self.config_file = self.config_dir / "config.json"
        self._load_config()
        self._ensure_default_config()

    def _load_config(self):
        """Load configuration from file."""
        ensure_dir(self.config_dir)
        if self.config_file.exists():
            with open(self.config_file) as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def _ensure_default_config(self):
        """Ensure default configuration is applied if no config exists."""
        if "s3" not in self.config:
            from .defaults import get_default_config

            default_config = get_default_config()
            self.config["s3"] = default_config
            self._save_config()
            print("Applied default S3 configuration")

    def _save_config(self):
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def set_credentials(self, access_key, secret_key, endpoint_url=None):
        """Set S3 credentials."""
        # Preserve existing S3 config and update only specified fields
        if "s3" not in self.config:
            self.config["s3"] = {}

        # Update credentials
        self.config["s3"]["access_key"] = access_key
        self.config["s3"]["secret_key"] = secret_key

        # Only update endpoint_url if explicitly provided
        if endpoint_url is not None:
            self.config["s3"]["endpoint_url"] = endpoint_url

        self._save_config()
        print("S3 credentials configured successfully")

    def get_credentials(self):
        """Get S3 credentials."""
        s3_config = self.config.get("s3", {})
        return {
            "access_key": s3_config.get("access_key"),
            "secret_key": s3_config.get("secret_key"),
            "endpoint_url": s3_config.get("endpoint_url"),
        }

    def clear_credentials(self):
        """Clear S3 credentials."""
        if "s3" in self.config:
            del self.config["s3"]
            self._save_config()
            print("S3 credentials cleared")
        else:
            print("No S3 credentials configured")

    def show_config(self):
        """Show current configuration (without exposing secrets)."""
        s3_config = self.config.get("s3", {})
        if s3_config:
            masked_key = s3_config.get("access_key", "")
            if len(masked_key) > 8:
                masked_key = (
                    masked_key[:4] + "*" * (len(masked_key) - 8) + masked_key[-4:]
                )

            print("Current S3 Configuration:")
            print(f"  Access Key: {masked_key}")
            print(
                f"  Secret Key: {'*' * 20 if s3_config.get('secret_key') else 'Not set'}"
            )
            print(
                f"  Endpoint URL: {s3_config.get('endpoint_url', 'Default (AWS S3)')}"
            )
        else:
            print("No S3 credentials configured")

    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        from .defaults import get_default_config

        self.config["s3"] = get_default_config()
        self._save_config()
        print("Configuration reset to defaults")
