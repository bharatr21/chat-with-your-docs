"""Security utilities for path validation."""

import os
import uuid


def validate_id_format(id_value: str, id_type: str = "ID") -> None:
    """
    Validate ID to prevent path traversal attacks.

    Args:
        id_value: The ID to validate
        id_type: Type of ID for error messages (e.g., "Session ID", "Document ID")

    Raises:
        ValueError: If ID is invalid or contains path traversal characters
    """
    if not id_value:
        raise ValueError(f"{id_type} cannot be empty")

    if "/" in id_value or "\\" in id_value or ".." in id_value:
        raise ValueError(f"Invalid {id_type}: {id_value} contains path traversal characters")

    try:
        uuid.UUID(id_value)
    except ValueError as e:
        raise ValueError(f"Invalid {id_type} format: {id_value} is not a valid UUID") from e


def get_secure_file_path(base_dir: str, file_id: str, extension: str) -> str:
    """
    Construct and validate a secure file path within base directory.

    Args:
        base_dir: Base directory (must be absolute)
        file_id: File identifier (will be validated)
        extension: File extension (e.g., ".json")

    Returns:
        Absolute path to file within base directory

    Raises:
        ValueError: If path would traverse outside base_dir
    """
    file_path = os.path.join(base_dir, f"{file_id}{extension}")
    file_path = os.path.normpath(os.path.abspath(file_path))
    base_dir_abs = os.path.normpath(os.path.abspath(base_dir))

    # Ensure path is within base directory
    if not os.path.commonpath([base_dir_abs, file_path]) == base_dir_abs:
        raise ValueError(f"Path traversal detected: {file_id}")

    return file_path
