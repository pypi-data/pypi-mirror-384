# /usr/bin/env python3
"""
Copyright (C) 2015-2025 Fourier Intelligence Group Limited. All rights reserved.

@file    cli.py
@author  Stan
@date    24 Jun 25
@desc    cli
"""

import argparse
import sys

# PYTHON_ARGCOMPLETE_OK
import argcomplete


def cmd_download(args):
    from .downloader import AssetDownloader
    from .logger import get_logger
    from .rclone_installer import check_rclone_dependency, verify_rclone_silent

    """Download assets from S3 URL."""

    # Check rclone availability before proceeding
    if not verify_rclone_silent():
        check_rclone_dependency(verbose=getattr(args, "verbose", False))

    # Setup debug logging if requested
    if hasattr(args, "verbose") and args.verbose:
        import logging

        logging.getLogger("fourierassets").setLevel(logging.DEBUG)

    logger = get_logger("cli.download")
    try:
        downloader = AssetDownloader(
            cache_dir=args.cache_dir,
            endpoint_url=args.endpoint_url,
            verbose=args.verbose,
        )
        local_path = downloader.download(args.s3_url)
        print(local_path)
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        sys.exit(1)


def cmd_upload(args):
    from .rclone_installer import check_rclone_dependency, verify_rclone_silent
    from .uploader import AssetUploader

    """Upload local file or directory to S3."""

    # Check rclone availability before proceeding
    if not verify_rclone_silent():
        check_rclone_dependency(verbose=getattr(args, "verbose", False))

    # Setup debug logging if requested
    if hasattr(args, "verbose") and args.verbose:
        import logging

        logging.getLogger("fourierassets").setLevel(logging.DEBUG)

    try:
        uploader = AssetUploader(
            endpoint_url=args.endpoint_url, verbose=getattr(args, "verbose", False)
        )
        if uploader.upload(args.local_path, args.s3_url):
            print("Upload completed successfully!")
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def cmd_ls(args):
    """List objects in S3 bucket/prefix."""
    from .lister import AssetLister
    from .rclone_installer import check_rclone_dependency, verify_rclone_silent

    # Check rclone availability before proceeding
    if not verify_rclone_silent():
        check_rclone_dependency(verbose=getattr(args, "verbose", False))

    # Setup debug logging if requested
    if hasattr(args, "verbose") and args.verbose:
        import logging

        logging.getLogger("fourierassets").setLevel(logging.DEBUG)

    # Use default s3:// if no URL provided
    s3_url = args.s3_url if args.s3_url else "s3://"

    try:
        lister = AssetLister(endpoint_url=args.endpoint_url)
        lister.ls(s3_url=s3_url, recursive=args.recursive, show_details=args.details)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def cmd_clear_cache(args):
    """Clear the asset cache."""
    import shutil
    from pathlib import Path

    cache_path = Path(args.cache_dir).expanduser().resolve()

    if args.redundant_only:
        # For simplified cache, just clear everything
        # Note: rclone has its own cache management
        print(
            "Note: With rclone-based caching, redundant-only mode clears entire cache"
        )
        print("Use rclone's cache management for more granular control")

    # Clear entire cache directory
    if cache_path.exists():
        shutil.rmtree(cache_path)
        print(f"Cache cleared: {cache_path}")
    else:
        print("Cache directory does not exist.")


def cmd_rm(args):
    """Remove objects or directories from S3."""
    from .rclone_installer import check_rclone_dependency, verify_rclone_silent
    from .remover import AssetRemover

    # Check rclone availability before proceeding
    if not verify_rclone_silent():
        check_rclone_dependency(verbose=getattr(args, "verbose", False))

    # Setup debug logging if requested
    if hasattr(args, "verbose") and args.verbose:
        import logging

        logging.getLogger("fourierassets").setLevel(logging.DEBUG)

    try:
        remover = AssetRemover(
            endpoint_url=args.endpoint_url,
            verbose=args.verbose,
        )

        # Ask for confirmation unless --force is specified
        if not args.force:
            if not remover.confirm_removal(args.s3_urls, recursive=args.recursive):
                print("Operation cancelled.")
                return

        # Remove the objects/directories
        success = remover.rm(args.s3_urls, recursive=args.recursive, force=args.force)

        if success:
            print("All objects removed successfully!")
        else:
            print("Some objects could not be removed. Check the logs for details.")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def cmd_config_set_credentials(args):
    """Set S3 credentials."""
    from .config import S3Config

    try:
        config = S3Config()
        config.set_credentials(
            access_key=args.access_key,
            secret_key=args.secret_key,
            endpoint_url=args.endpoint_url,
        )
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def cmd_config_show(args):
    """Show current configuration."""
    from .config import S3Config

    try:
        config = S3Config()
        config.show_config()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def cmd_config_clear(args):
    """Clear S3 credentials."""
    from .config import S3Config

    try:
        config = S3Config()
        config.clear_credentials()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def cmd_config_reset(args):
    """Reset configuration to defaults."""
    from .config import S3Config

    try:
        config = S3Config()
        config.reset_to_defaults()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def cmd_test_connection(args):
    """Test S3 connection and endpoint."""
    from .exceptions import ClientError
    from .rclone_installer import check_rclone_dependency, verify_rclone_silent
    from .utils import get_s3_client

    # Check rclone availability before proceeding
    if not verify_rclone_silent():
        check_rclone_dependency(verbose=False)

    try:
        print("Testing S3 connection...")
        if args.endpoint_url:
            print(f"Using endpoint: {args.endpoint_url}")

        s3_client = get_s3_client(args.endpoint_url)

        # Try to list buckets to test connection
        print("Testing bucket listing...")
        response = s3_client.list_buckets()
        print("✓ Successfully connected to S3!")
        print(f"Found {len(response['Buckets'])} buckets:")

        # Test accessibility of each bucket
        accessible_buckets = []
        inaccessible_buckets = []

        for bucket in response["Buckets"]:
            bucket_name = bucket["Name"]
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                print(f"  ✓ {bucket_name} - accessible")
                accessible_buckets.append(bucket_name)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                if error_code == "404":
                    print(f"  ✗ {bucket_name} - not found (404)")
                elif error_code == "403":
                    print(f"  ✗ {bucket_name} - access denied (403)")
                else:
                    print(f"  ✗ {bucket_name} - error ({error_code})")
                inaccessible_buckets.append((bucket_name, error_code))
            except (OSError, ConnectionError, TimeoutError) as e:
                print(f"  ✗ {bucket_name} - connection error: {str(e)}")
                inaccessible_buckets.append((bucket_name, "connection_error"))

        # Summary
        print("\nSummary:")
        print(f"  Accessible buckets: {len(accessible_buckets)}")
        print(f"  Inaccessible buckets: {len(inaccessible_buckets)}")

        if inaccessible_buckets:
            print("\nInaccessible buckets details:")
            for bucket_name, error_type in inaccessible_buckets:
                if error_type == "404":
                    print(f"  - {bucket_name}: Bucket does not exist or wrong endpoint")
                elif error_type == "403":
                    print(f"  - {bucket_name}: Permission denied - check credentials")
                else:
                    print(f"  - {bucket_name}: {error_type}")

        # Show usage examples with accessible buckets
        if accessible_buckets:
            first_bucket = accessible_buckets[0]
            print(f"\nUsage examples with accessible bucket '{first_bucket}':")
            print("  # List objects in bucket:")
            print(f"  fourierassets ls s3://{first_bucket}/")
            print("  # Download from bucket:")
            print(f"  fourierassets download s3://{first_bucket}/path/to/file")
            print("  # Upload to bucket:")
            print(f"  fourierassets upload ./local/file s3://{first_bucket}/path/to/file")
        else:
            print(
                "\n⚠️  No accessible buckets found. Check your credentials and permissions."
            )

        # Test specific bucket if provided
        if args.bucket:
            print(f"\nTesting access to bucket '{args.bucket}'...")
            try:
                s3_client.head_bucket(Bucket=args.bucket)
                print(f"✓ Successfully accessed bucket '{args.bucket}'")

                # Try to list some objects
                response = s3_client.list_objects_v2(Bucket=args.bucket, MaxKeys=5)
                if "Contents" in response:
                    print(
                        f"Found {len(response['Contents'])} objects (showing first 5):"
                    )
                    for obj in response["Contents"]:
                        print(f"  - {obj['Key']}")
                else:
                    print("Bucket is empty or no objects found")

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "404":
                    print(f"✗ Bucket '{args.bucket}' does not exist at this endpoint")
                elif error_code == "403":
                    print(f"✗ Access denied to bucket '{args.bucket}'")
                else:
                    print(f"✗ Error accessing bucket '{args.bucket}': {str(e)}")

    except (OSError, ConnectionError, TimeoutError) as e:
        print(f"✗ Connection failed: {str(e)}", file=sys.stderr)
        print("\nTroubleshooting tips:", file=sys.stderr)
        print(
            "1. Check if your endpoint URL is correct (should be S3 API endpoint, not web console)",
            file=sys.stderr,
        )
        print(
            "2. Verify your credentials with 'fourierassets config show'", file=sys.stderr
        )
        print("3. Try different endpoint URL formats:", file=sys.stderr)
        print("   - http://192.168.3.100:9000 (MinIO default)", file=sys.stderr)
        print("   - https://s3.example.com", file=sys.stderr)
        print(
            "4. Contact your S3 service administrator for the correct API endpoint",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_check_permissions(args):
    """Check cache directory permissions."""
    import stat
    from pathlib import Path

    cache_path = Path(args.cache_dir).expanduser().resolve()

    print(f"Checking cache directory: {cache_path}")

    try:
        # Try to create the directory
        cache_path.mkdir(parents=True, exist_ok=True)
        print("✓ Cache directory exists or was created successfully")

        # Check permissions
        stat_info = cache_path.stat()
        permissions = stat.filemode(stat_info.st_mode)
        print(f"✓ Directory permissions: {permissions}")

        # Try to create a test file
        test_file = cache_path / "test_write_permission"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print("✓ Write permissions verified")
        except Exception as e:
            print(f"✗ Write permission test failed: {e}")
            return False

        # Check ownership
        import pwd

        try:
            owner = pwd.getpwuid(stat_info.st_uid).pw_name
            print(f"✓ Directory owner: {owner}")
        except KeyError:
            print(f"✓ Directory owner UID: {stat_info.st_uid}")

        return True

    except PermissionError as e:
        print(f"✗ Permission denied: {e}")
        print("Solutions:")
        print(f"1. Run: sudo chown -R $USER {cache_path}")
        print("2. Or use a different cache directory with --cache-dir")
        return False
    except Exception as e:
        print(f"✗ Error checking permissions: {e}")
        return False


def main():
    """FourierAssets - Manage assets provided by Fourier."""

    # Check if user explicitly requested help for main command only (no subcommands)
    # or if no arguments provided at all
    show_banner = (len(sys.argv) == 1) or (
        len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]
    )

    # Custom formatter that includes banner only for main help
    class BannerHelpFormatter(argparse.HelpFormatter):
        def format_help(self):
            help_text = super().format_help()
            if show_banner:
                # Add tip about starting with test command
                tip_text = "💡 Tip: Start your journey with 'fourierassets test' to verify your connection\n\n"
                return tip_text + help_text
            return help_text

    parser = argparse.ArgumentParser(
        description="FourierAssets - Manage assets provided by Fourier",
        formatter_class=BannerHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Test connection command (moved to first position)
    test_parser = subparsers.add_parser(
        "test",
        help="Test S3 connection and endpoint",
        epilog="Examples:\n"
        "  fourierassets test\n"
        "  fourierassets test --endpoint-url http://192.168.1.100:9000\n"
        "  fourierassets test --bucket my-bucket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    test_parser.add_argument(
        "--endpoint-url", default=None, help="S3 endpoint URL to test"
    )
    test_parser.add_argument(
        "--bucket", default=None, help="Specific bucket to test access"
    )
    test_parser.set_defaults(func=cmd_test_connection)

    # Download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download assets from S3 URL",
        epilog="Examples:\n"
        "  fourierassets download s3://bucket/file.txt\n"
        "  fourierassets download s3://bucket/directory/\n"
        "  fourierassets download -r s3://bucket/assets --cache-dir ~/my-cache",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    download_parser.add_argument("s3_url", help="S3 URL to download from")
    download_parser.add_argument(
        "--cache-dir",
        default="~/.fourierassets/cache",
        help="Directory to store cached assets",
    )
    download_parser.add_argument(
        "--endpoint-url", default=None, help="S3 endpoint URL (for custom S3 services)"
    )
    download_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Force recursive download (treat as directory even if it looks like a file)",
    )
    download_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    download_parser.set_defaults(func=cmd_download)

    # Upload command
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload local file or directory to S3",
        epilog="Examples:\n"
        "  fourierassets upload ./model.urdf s3://bucket/models/robot.urdf\n"
        "  fourierassets upload ./assets/ s3://bucket/simulation/assets/\n"
        "  fourierassets upload ./data.zip s3://bucket/archives/ --endpoint-url http://localhost:9000",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    upload_parser.add_argument("local_path", help="Local file or directory path")
    upload_parser.add_argument("s3_url", help="S3 URL destination")
    upload_parser.add_argument(
        "--endpoint-url", default=None, help="S3 endpoint URL (for custom S3 services)"
    )
    upload_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    upload_parser.set_defaults(func=cmd_upload)

    # List command
    ls_parser = subparsers.add_parser(
        "ls",
        help="List objects in S3 bucket/prefix",
        epilog="Examples:\n"
        "  fourierassets ls s3://bucket/\n"
        "  fourierassets ls s3://bucket/models/ -l\n"
        "  fourierassets ls s3://bucket/assets/ -r --details",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ls_parser.add_argument(
        "s3_url", nargs="?", default="s3://", help="S3 URL to list (default: s3://)"
    )
    ls_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="List recursively (show tree structure)",
    )
    ls_parser.add_argument(
        "-l",
        "--details",
        action="store_true",
        help="Show detailed information (size, modification time)",
    )
    ls_parser.add_argument(
        "--endpoint-url", default=None, help="S3 endpoint URL (for custom S3 services)"
    )
    ls_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    ls_parser.set_defaults(func=cmd_ls)

    # Remove command
    rm_parser = subparsers.add_parser(
        "rm",
        help="Remove objects or directories from S3",
        epilog="Examples:\n"
        "  fourierassets rm s3://bucket/file.txt\n"
        "  fourierassets rm s3://bucket/directory/ --recursive\n"
        "  fourierassets rm s3://bucket/file1.txt s3://bucket/file2.txt\n"
        "  fourierassets rm s3://bucket/assets/ --recursive --force",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    rm_parser.add_argument(
        "s3_urls", nargs="+", help="S3 URLs of objects or directories to remove"
    )
    rm_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Remove directories and their contents recursively",
    )
    rm_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force removal without confirmation prompt",
    )
    rm_parser.add_argument(
        "--endpoint-url", default=None, help="S3 endpoint URL (for custom S3 services)"
    )
    rm_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    rm_parser.set_defaults(func=cmd_rm)

    # Clear cache command
    clear_parser = subparsers.add_parser(
        "clear-cache",
        help="Clear the asset cache",
        epilog="Examples:\n"
        "  fourierassets clear-cache\n"
        "  fourierassets clear-cache --cache-dir ~/my-cache\n"
        "  fourierassets clear-cache --redundant-only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    clear_parser.add_argument(
        "--cache-dir", default="~/.fourierassets/cache", help="Cache directory to clear"
    )
    clear_parser.add_argument(
        "--redundant-only",
        action="store_true",
        help="Only clear redundant cache entries (keep non-overlapping caches)",
    )
    clear_parser.set_defaults(func=cmd_clear_cache)

    # Check permissions command
    check_parser = subparsers.add_parser(
        "check-permissions",
        help="Check cache directory permissions",
        epilog="Examples:\n"
        "  fourierassets check-permissions\n"
        "  fourierassets check-permissions --cache-dir ~/my-cache",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    check_parser.add_argument(
        "--cache-dir",
        default="~/.fourierassets/cache",
        help="Cache directory to check",
    )
    check_parser.set_defaults(func=cmd_check_permissions)

    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage S3 configuration",
        epilog="Examples:\n"
        "  fourierassets config show\n"
        "  fourierassets config set-credentials ACCESS_KEY SECRET_KEY\n"
        "  fourierassets config set-credentials ACCESS_KEY SECRET_KEY --endpoint-url https://s3.example.com\n"
        "  fourierassets config clear\n"
        "  fourierassets config reset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Configuration commands"
    )

    # Config set-credentials
    set_creds_parser = config_subparsers.add_parser(
        "set-credentials", help="Set S3 credentials"
    )
    set_creds_parser.add_argument("access_key", help="AWS Access Key ID")
    set_creds_parser.add_argument("secret_key", help="AWS Secret Access Key")
    set_creds_parser.add_argument(
        "--endpoint-url", default=None, help="S3 endpoint URL (optional)"
    )
    set_creds_parser.set_defaults(func=cmd_config_set_credentials)

    # Config show
    show_config_parser = config_subparsers.add_parser(
        "show", help="Show current configuration"
    )
    show_config_parser.set_defaults(func=cmd_config_show)

    # Config clear
    clear_config_parser = config_subparsers.add_parser(
        "clear", help="Clear S3 credentials"
    )
    clear_config_parser.set_defaults(func=cmd_config_clear)

    # Config reset
    reset_config_parser = config_subparsers.add_parser(
        "reset", help="Reset configuration to defaults"
    )
    reset_config_parser.set_defaults(func=cmd_config_reset)

    argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
