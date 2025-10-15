import os
from collections import defaultdict

from .logger import get_logger
from .utils import get_s3_client, parse_s3_url


class AssetLister:
    """List simulation assets from S3."""

    def __init__(self, endpoint_url=None):
        self.endpoint_url = endpoint_url
        self.logger = get_logger(f"{__name__}.AssetLister")

    def _format_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math

        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    def _build_tree_structure(self, objects, prefix):
        """Build a tree structure from S3 objects."""
        tree = defaultdict(lambda: {"dirs": set(), "files": []})

        for obj in objects:
            key = obj["Key"]
            # Remove the prefix to get relative path
            if prefix:
                if not key.startswith(prefix):
                    continue
                rel_path = key[len(prefix) :].lstrip("/")
            else:
                rel_path = key

            if not rel_path:  # Skip if empty after removing prefix
                continue

            parts = rel_path.split("/")
            current_path = ""

            # Build directory structure
            for _i, part in enumerate(parts[:-1]):
                parent_path = current_path
                current_path = (
                    os.path.join(current_path, part) if current_path else part
                )
                tree[parent_path]["dirs"].add(part)

            # Add file to its parent directory
            if len(parts) > 0:
                parent_path = "/".join(parts[:-1]) if len(parts) > 1 else ""
                tree[parent_path]["files"].append(
                    {
                        "name": parts[-1],
                        "size": obj["Size"],
                        "modified": obj["LastModified"],
                    }
                )

        return tree

    def _print_tree(self, tree, path="", indent="", show_details=False):
        """Print tree structure."""
        current_level = tree.get(path, {"dirs": set(), "files": []})

        # Sort directories and files
        dirs = sorted(current_level["dirs"])
        files = sorted(current_level["files"], key=lambda x: x["name"])

        # Print directories first
        for i, dir_name in enumerate(dirs):
            is_last_dir = (i == len(dirs) - 1) and len(files) == 0
            prefix = "└── " if is_last_dir else "├── "
            print(f"{indent}{prefix}{dir_name}/")

            # Recursively print subdirectory
            next_path = os.path.join(path, dir_name) if path else dir_name
            next_indent = indent + ("    " if is_last_dir else "│   ")
            self._print_tree(tree, next_path, next_indent, show_details)

        # Print files
        for i, file_info in enumerate(files):
            is_last = i == len(files) - 1
            prefix = "└── " if is_last else "├── "

            if show_details:
                size_str = self._format_size(file_info["size"])
                modified_str = file_info["modified"].strftime("%Y-%m-%d %H:%M")
                print(
                    f"{indent}{prefix}{file_info['name']} ({size_str}, {modified_str})"
                )
            else:
                print(f"{indent}{prefix}{file_info['name']}")

    def ls(self, s3_url, recursive=False, show_details=False):
        """List objects in S3 bucket/prefix."""
        bucket, prefix = parse_s3_url(s3_url)
        s3_client = get_s3_client(self.endpoint_url)

        try:
            # First, try to check if bucket exists
            try:
                s3_client.head_bucket(Bucket=bucket)
            except Exception as e:
                from .exceptions import ClientError

                if isinstance(e, ClientError):
                    error_code = e.response["Error"]["Code"]
                    if error_code == "404":
                        print(
                            f"Bucket '{bucket}' not found (404). Possible issues:\n"
                            f"  - Bucket name is incorrect\n"
                            f"  - Endpoint URL is incorrect\n"
                            f"  - Bucket doesn't exist at this endpoint\n"
                            f"Use 'fourierassets test --endpoint-url {self.endpoint_url}' to verify connection"
                        )
                    elif error_code == "403":
                        print(
                            f"Access denied to bucket '{bucket}'. Please check your credentials and permissions"
                        )
                raise e

            # List objects
            paginator = s3_client.get_paginator("list_objects_v2")

            if recursive:
                # List all objects recursively
                pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
            else:
                # List only immediate children (simulate directory listing)
                delimiter = "/"
                pages = paginator.paginate(
                    Bucket=bucket, Prefix=prefix, Delimiter=delimiter
                )

            all_objects = []
            common_prefixes = []

            for page in pages:
                # Collect objects (files)
                if "Contents" in page:
                    all_objects.extend(page["Contents"])

                # Collect common prefixes (directories) for non-recursive listing
                if not recursive and "CommonPrefixes" in page:
                    common_prefixes.extend(
                        [cp["Prefix"] for cp in page["CommonPrefixes"]]
                    )

            # Check if the prefix exists by looking for exact matches or objects under it
            prefix_exists = self._verify_prefix_exists(
                s3_client, bucket, prefix, all_objects, common_prefixes
            )

            if not prefix_exists:
                if prefix:
                    raise RuntimeError(
                        f"Path '{prefix}' does not exist in bucket '{bucket}'"
                    )
                else:
                    # Root bucket listing with no results
                    self.logger.info(f"Bucket '{bucket}' is empty")
                    return

            if not recursive:
                # For non-recursive listing, show directories and immediate files
                self.logger.info(f"Contents of {s3_url}:")

                # Show directories
                for common_prefix in sorted(common_prefixes):
                    dir_name = common_prefix.rstrip("/").split("/")[-1]
                    print(f"├── {dir_name}/")

                # Show files in current directory
                immediate_files = []
                for obj in all_objects:
                    key = obj["Key"]
                    if prefix:
                        if key.startswith(prefix):
                            rel_path = key[len(prefix) :].lstrip("/")
                        else:
                            continue
                    else:
                        rel_path = key

                    # Only show files in current directory (no subdirectories)
                    if "/" not in rel_path and rel_path:
                        immediate_files.append(
                            {
                                "name": rel_path,
                                "size": obj["Size"],
                                "modified": obj["LastModified"],
                            }
                        )

                for i, file_info in enumerate(
                    sorted(immediate_files, key=lambda x: x["name"])
                ):
                    is_last = (
                        i == len(immediate_files) - 1 and len(common_prefixes) == 0
                    )
                    prefix_char = "└── " if is_last else "├── "

                    if show_details:
                        size_str = self._format_size(file_info["size"])
                        modified_str = file_info["modified"].strftime("%Y-%m-%d %H:%M")
                        print(
                            f"{prefix_char}{file_info['name']} ({size_str}, {modified_str})"
                        )
                    else:
                        print(f"{prefix_char}{file_info['name']}")

            else:
                # For recursive listing, build and show tree structure
                if not all_objects:
                    self.logger.warning(f"No objects found in {s3_url}")
                    return

                self.logger.info(f"Tree structure of {s3_url}:")
                print()

                tree = self._build_tree_structure(all_objects, prefix)
                self._print_tree(tree, "", "", show_details)

            print()
            total_count = len(all_objects) + len(common_prefixes)
            if total_count > 0:
                print(
                    f"Total items: {total_count} ({len(all_objects)} files, {len(common_prefixes)} directories)"
                )
            else:
                print("No items found")

        except ValueError as e:
            # Re-raise ValueError from utils (better error messages)
            raise e
        except RuntimeError as e:
            # Re-raise our custom RuntimeErrors
            raise e
        except Exception as e:
            from .exceptions import ClientError

            if isinstance(e, ClientError):
                error_code = e.response["Error"]["Code"]
                status_code = e.response["ResponseMetadata"].get("HTTPStatusCode", 0)

                if error_code == "NoSuchBucket" or status_code == 404:
                    print(
                        f"Bucket '{bucket}' not found (404). Possible issues:\n"
                        f"  - Bucket name is incorrect\n"
                        f"  - Endpoint URL is incorrect\n"
                        f"  - Bucket doesn't exist at this endpoint\n"
                        f"Use 'fourierassets test --endpoint-url {self.endpoint_url}' to verify connection"
                    )
                elif error_code == "AccessDenied" or status_code == 403:
                    print(
                        f"Access denied to bucket '{bucket}'. Please check your credentials and permissions"
                    )
                elif error_code == "InvalidArgument" and "API port" in str(e):
                    print(
                        "Invalid S3 endpoint URL. The provided endpoint appears to be a web console URL.\n"
                        "Please use the S3 API endpoint instead. Contact your administrator for the correct endpoint."
                    )
            print(f"Failed to list objects in {s3_url}: {str(e)}")

    def _verify_prefix_exists(
        self, s3_client, bucket, prefix, all_objects, common_prefixes
    ):
        """Verify that the given prefix actually exists in the bucket."""
        if not prefix:
            # Root level always "exists" if we can access the bucket
            return True

        # Normalize prefix
        prefix = prefix.rstrip("/")

        # Check if there's an exact object match
        for obj in all_objects:
            key = obj["Key"].rstrip("/")
            if key == prefix or key.startswith(prefix + "/"):
                return True

        # Check if there's a common prefix match (directory)
        for common_prefix in common_prefixes:
            cp = common_prefix.rstrip("/")
            if cp == prefix or cp.startswith(prefix + "/"):
                return True

        # If no objects or prefixes match, try a more specific check
        try:
            # Try to list with the exact prefix to see if anything exists
            response = s3_client.list_objects_v2(
                Bucket=bucket, Prefix=prefix, MaxKeys=1
            )

            # If we get any contents or common prefixes, the path exists
            if "Contents" in response or "CommonPrefixes" in response:
                return True

            # Try with trailing slash for directory check
            response = s3_client.list_objects_v2(
                Bucket=bucket, Prefix=prefix + "/", MaxKeys=1
            )

            return "Contents" in response or "CommonPrefixes" in response
        except Exception:
            # If we can't verify, assume it doesn't exist
            return False
