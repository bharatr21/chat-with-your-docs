"""
Document metadata extraction and management
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manage document metadata storage"""

    def __init__(self, metadata_dir: str = "./.metadata"):
        self.metadata_dir = metadata_dir
        os.makedirs(metadata_dir, exist_ok=True)
        # Normalize and make absolute for security checks
        self.metadata_dir = os.path.abspath(self.metadata_dir)

    def _validate_doc_id(self, doc_id: str) -> None:
        """
        Validate doc_id to prevent path traversal attacks.

        Raises ValueError if doc_id is invalid or contains path traversal characters.
        """
        if not doc_id:
            raise ValueError("Document ID cannot be empty")

        # Check for path traversal characters
        if "/" in doc_id or "\\" in doc_id or ".." in doc_id:
            raise ValueError(f"Invalid document ID: {doc_id} contains path traversal characters")

        # Validate UUID format (documents are created with UUIDs)
        try:
            uuid.UUID(doc_id)
        except ValueError as e:
            raise ValueError(f"Invalid document ID format: {doc_id} is not a valid UUID") from e

    def _get_metadata_path(self, doc_id: str) -> str:
        """
        Get file path for metadata with path traversal protection.

        Raises ValueError if doc_id is invalid or would result in path traversal.
        """
        # Validate doc_id format
        self._validate_doc_id(doc_id)

        # Construct path
        metadata_path = os.path.join(self.metadata_dir, f"{doc_id}.json")

        # Normalize path to resolve any remaining issues
        metadata_path = os.path.normpath(metadata_path)
        metadata_path = os.path.abspath(metadata_path)

        # Ensure the resolved path is within the metadata directory
        # This prevents path traversal even if validation somehow fails
        if not os.path.commonpath([self.metadata_dir, metadata_path]) == self.metadata_dir:
            raise ValueError(f"Path traversal detected: {doc_id}")

        return metadata_path

    def save_metadata(self, doc_id: str, metadata: dict[str, Any]):
        """Save document metadata to file"""
        metadata_path = self._get_metadata_path(doc_id)

        # Copy to avoid mutating caller's dict
        metadata_copy = dict(metadata)

        # Add timestamps
        if "upload_date" not in metadata_copy:
            metadata_copy["upload_date"] = datetime.now(timezone.utc).isoformat()

        with open(metadata_path, "w") as f:
            json.dump(metadata_copy, f, indent=2, default=str)

    def load_metadata(self, doc_id: str) -> dict[str, Any]:
        """Load document metadata from file"""
        metadata_path = self._get_metadata_path(doc_id)

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata not found for document {doc_id}")

        with open(metadata_path) as f:
            return json.load(f)

    def delete_metadata(self, doc_id: str):
        """Delete document metadata"""
        metadata_path = self._get_metadata_path(doc_id)

        if os.path.exists(metadata_path):
            os.remove(metadata_path)

    def list_all_metadata(self) -> list[dict[str, Any]]:
        """List all document metadata"""
        metadata_list = []

        if not os.path.exists(self.metadata_dir):
            return metadata_list

        for filename in os.listdir(self.metadata_dir):
            if filename.endswith(".json"):
                doc_id = filename[:-5]  # Remove .json extension
                try:
                    metadata = self.load_metadata(doc_id)
                    metadata["id"] = doc_id
                    metadata_list.append(metadata)
                except Exception as e:
                    logger.warning(
                        "Failed to load metadata file, skipping",
                        extra={"doc_id": doc_id, "file_name": filename, "error": str(e)},
                    )
                    continue

        return metadata_list

    def exists(self, doc_id: str) -> bool:
        """Check if metadata exists for document"""
        metadata_path = self._get_metadata_path(doc_id)
        return os.path.exists(metadata_path)


# Global instance
metadata_manager = MetadataManager()
