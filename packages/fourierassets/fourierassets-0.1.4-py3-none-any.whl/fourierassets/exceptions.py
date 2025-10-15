"""
Exception classes for rclone S3 client.
"""


class RcloneException(Exception):
    """Base exception for rclone operations."""


class NoSuchBucket(RcloneException):
    """Exception raised when a bucket does not exist."""


class NoSuchKey(RcloneException):
    """Exception raised when a key does not exist."""


class AccessDenied(RcloneException):
    """Exception raised when access is denied."""


class ClientError(RcloneException):
    """General client error for compatibility."""

    def __init__(self, error_response, operation_name=None):
        if isinstance(error_response, dict):
            self.response = error_response
            error_code = error_response.get("Error", {}).get("Code", "ClientError")
            error_message = error_response.get("Error", {}).get(
                "Message", "Unknown error"
            )
            super().__init__(f"{error_code}: {error_message}")
        else:
            # Handle string messages
            super().__init__(str(error_response))
            self.response = {
                "Error": {"Code": "ClientError", "Message": str(error_response)},
                "ResponseMetadata": {"HTTPStatusCode": 400},
            }
        self.operation_name = operation_name
